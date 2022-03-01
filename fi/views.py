from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
from .dolar import *
from datetime import date, datetime
from fi.models import *
from django.db import connection
from .funciones import *
from django.db.models import Sum
import random
from colormap import hex2rgb
from django.views.decorators.csrf import csrf_protect
import json
import hashlib
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from datetime import *
from django.utils import timezone

tope = 500
inicio = 2021
sl = 1500
dsl = sl + sl/2

def index(request):
    template = loader.get_template('login.html')
    context = {}
    context['false'] = False   
    return HttpResponse(template.render(context, request))

@login_required
def logout_view(request):
    logout(request)
    DjangoSession.objects.all().delete()
    return index(request)

def login(request):
    if request.method == 'POST':
        username = request.POST.get('user')
        password = request.POST.get('psw')
        usuario = authenticate(username=username, password=password) 
        if usuario:
            auth_login(request,usuario)
            request.session.set_expiry(600)
            s = DjangoSession.objects.last()
            date = s.expire_date
            dia = date.today() + timedelta(hours=1) # expire_date
            DjangoSession.objects.filter(session_key=s.session_key).update(expire_date=dia)
            return home(request,None,None,None)
 
    template = loader.get_template('login.html')
    context = {}
    context['false'] = True
    return HttpResponse(template.render(context, request))

@login_required
def home(request,a=None, m=None, num=None):
    user = request.user.id
    # a: anio | m: mes | num: acarreo
    template = loader.get_template('index.html')
    fecha = definirFecha(a, m, num)
    mes = int(fecha.strftime('%m')) # fecha a la que me muevo
    anio =  int(fecha.strftime('%Y'))# fecha a la que me muevo
    mesHoy = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context = {}
    context['fecha'] = fecha
    context['mes'] = mes
    context['anio'] = anio
    context['mesHoy'] = mesHoy
    context['anioHoy'] = anioHoy # para carga de los indicadores
    context['arrow'] = True

    # Indicadores
    if mes == mesHoy and anio == anioHoy:
        [v, c] = obtenerBlue()
        context['dolarCompra'] = c
        context['dolarVenta'] = v
        context['dolarOficial'] = obtenerOficial()
        context['bk'] = Movimientos.obtenerDepositosPorMes2(mes, user, anio)
        nexT = obtenerValorDolarizado(mes+1, anio, user)
        context['next'] = nexT
        context['nextDif'] = round((nexT - tope)*c,2) # revisar!!!!
        context['tope'] = tope
        myDolar = Cotizacion.objects.all().last()
        miCambio = MiCambio.objects.all().last()
        dif = myDolar.venta - miCambio.cambio
        if dif == 0:
            dif = " "
        context['dif'] = dif

    # Resumen
    ing = Movimientos.obtenerTotalPorMes(mes, user, anio, 1)# presupuesto por mes
    context['ing'] = ing
    egr = Movimientos.obtenerTotalPorMes(mes, user, anio, 2)
    context['egr'] = egr  # los gastos son negativos
    saldo = Movimientos.obtenerSaldoPorMes(mes, user, anio)
    context['saldo'] = saldo
    if ing != 0:
        context['porcIng'] = round((saldo * 100 / ing), 1)
        context['porcEgr'] = round((egr * 100 / ing), 1)
    else:
        context['porcIng'] = 0
        context['porcEgr'] = 0

    # Categorias
    listUserCategorias = crearCategorias(mes, user, anio)

    # Torta
    porcentajeSaldo = float(round(saldo * 100 / ing, 1)) # porcentaje del saldo del mes
    primerElemento = UserCategoriaAux('Saldo', ing ,saldo, porcentajeSaldo,'rgb(101,275,102)')
    listUserCategorias.insert(0,primerElemento) # Hasta aca tengo una lista =[ UserCategoriaAux, UserCategoria,... ]
    # para la torta son 3 listas
    [nombresTorta, coloresTorta, coloresPorc] = torta(listUserCategorias, ing, True)
    context['nombresTorta'] = nombresTorta
    context['coloresTorta'] = coloresTorta
    context['coloresPorc'] = coloresPorc
    listUserCategorias.pop(0) # saco UserCategoriaAux
    context['categorias'] = listUserCategorias
    return HttpResponse(template.render(context, request))

@login_required
def dolar(request):
    user = request.user.id
    template = loader.get_template('dolar.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    a = int(date.today().strftime('%Y'))
    m = int(date.today().strftime('%m'))
    context['mesHoy'] = m # en la fecha de hoy
    anioHoy = a # en la fecha de hoy
    context['anioHoy'] = anioHoy

    # Indicadores
    [bv, bc,  of ] = obtenerValorDolarBlue()
    context['dolarCompra'] = bv
    context['dolarVenta'] = bc #creo estan invertidos en la plantilla
    context['dolarOficial'] = of
    Dolar.guardarDolarOficial(of)
    context['bk'] = Movimientos.obtenerDepositosPorMes(m, user, a, 1, 1)
    nexT = obtenerValorDolarizado(m+1, a, user)
    context['next'] = nexT
    context['nextDif'] = round((nexT - tope)*bv,2)

    context['tope'] = tope
    dif = Cotizacion.guardarValorDolar(bv, bc)
    if dif == 0:
        dif = " "
    context['dif'] = dif

    context['valoresDolar'] = Cotizacion.valoresHistoricoDolar()
    return HttpResponse(template.render(context, request))

@login_required
def gastacion(request):
    user = request.user.id
    template = loader.get_template('gastacion.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy

    # Grafico
    (totales, nombres, rgb) = gastacionGrafico(user, inicio, anioHoy)
    context['nombres'] = nombres
    context['valores'] = totales
    context['rgb'] = rgb

    # Fijos
    (nom ,val, color) = Productos.obtenerVarios(user, 10)
    context['nom'] = nom
    context['val'] = val
    context['color'] = color

    # Varios
    (nomVarios ,valVarios, colorVarios) = Productos.obtenerVarios(user, 6)
    context['nomVarios'] = nomVarios
    context['valVarios'] = valVarios
    context['colorVarios'] = colorVarios

    # Productos
    (nomProductos ,valProductos, colorProductos) = Productos.obtenerProductosTorta(user)
    context['nomProductos'] = nomProductos
    context['valProductos'] = valProductos
    context['colorProductos'] = colorProductos
    return HttpResponse(template.render(context, request))

@login_required
def categorias(request):
    user = request.user.id
    template = loader.get_template('categorias.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy

    context['grafico'] = obtenerGraficoBarras(user, inicio, anioHoy)
    return HttpResponse(template.render(context, request))

@login_required
def gastos(request,cat, a=None, m=None):
    user = request.user.id
    template = loader.get_template('gastos.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy

    # boton volver
    context['mes'] = m
    context['anio'] = a

    # Movimientos
    (movimientos, total, categoria) = obtenerMovDelMesPorCategoriaTipo(m, user, a, cat, 2)
    context['movimientos'] = movimientos
    context['total'] = total
    context['categoria'] = categoria

    # Torta de gastos por categoria
    # para la torta son 3 listas
    (nombresTorta, coloresTorta, coloresPorc) = tortaPorCategoria(cat, user, a, m,2)
    if nombresTorta != []:
        context['grafico'] = True
        context['nombresTorta'] = nombresTorta
        context['coloresTorta'] = coloresTorta
        context['coloresPorc'] = coloresPorc
    else:
        context['grafico'] = False
    return HttpResponse(template.render(context, request))

@login_required
def presupuesto(request,a=None, m=None, num=None):
    user = request.user.id
    # a: anio | m: mes | num: acarreo
    template = loader.get_template('presupuesto.html')

    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy
    total = Movimientos.obtenerTotalPorMes(m, user, a, 1)
    context['total'] = total
    context['fecha'] = definirFecha(a, m, 0)

    # boton volver
    context['mes'] = m
    context['anio'] = a
    listUserCategorias = crearCategorias(m, user, a)
    context['categorias'] = listUserCategorias

    # Torta
    # para la torta son 3 listas
    [nombresTorta, coloresTorta, coloresPorc] = tortaPresupuesto(listUserCategorias, total)
    context['nombresTorta'] = nombresTorta
    context['coloresTorta'] = coloresTorta
    context['coloresPorc'] = coloresPorc

    # Torta fijos
    # para la torta son 3 listas
    (nombresTortaFijos, coloresTortaFijos, coloresPorcFijos) = tortaPorCategoria(10, user, a, m,1)
    context['nombresTortaFijos'] = nombresTortaFijos
    context['coloresTortaFijos'] = coloresTortaFijos
    context['coloresPorcFijos'] = coloresPorcFijos

    return HttpResponse(template.render(context, request))

@login_required
def presuCategoria(request,cat, a=None, m=None):
    user = request.user.id
    template = loader.get_template('presuCategoria.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy

    # boton volver
    context['mes'] = m
    context['anio'] = a

    # Movimientos
    (movimientos, total, categoria) = obtenerMovDelMesPorCategoriaTipo(m, user, a, cat, 1)
    context['movimientos'] = movimientos
    context['total'] = total
    context['categoria'] = categoria
    return HttpResponse(template.render(context, request))

@login_required
def movimientos(request, a=None, m=None,t=None):
    user = request.user.id
    template = loader.get_template('movimientos.html')
    context = {}
    context['arrow'] = False
    context['grafico'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['anioHoy'] = anioHoy
    context['fecha'] = definirFecha(a, m, 0)
    # boton volver
    context['mes'] = m
    context['anio'] = a
    # Movimientos
    if t == 0:
        context['mov'] = 'Movimientos'
        context['movimientos'] = obtenerMovimientosDelMes(m, user, a)
    if t == 2:
        context['mov'] = 'Gastos'
        context['movimientos'] = obtenerMovimientosDelMesPorTipo(m, user, a,t)
        # Torta de gastos por categoria
        # para la torta son 3 listas
        (nombresTorta, coloresTorta, coloresPorc) = tortaPorProducto(user, a, m,2)
        if nombresTorta != []:
            context['grafico'] = True
            context['nombresTorta'] = nombresTorta
            context['coloresTorta'] = coloresTorta
            context['coloresPorc'] = coloresPorc
    return HttpResponse(template.render(context, request))

@login_required
def prodCateg(request):
    user = request.user.id
    # a: anio | m: mes | num: acarreo
    template = loader.get_template('prodCateg2.html')
    context = {}
    context['arrow'] = False
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    context['anioHoy'] = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['categorias'] = obtenerUserCategorias(user)
    return HttpResponse(template.render(context, request))

@login_required
def categoria(request, c=None):
    user = request.user.id
    # a: anio | m: mes | num: acarreo
    template = loader.get_template('categoria.html')
    context = {}
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    context['anioHoy'] = int(date.today().strftime('%Y'))  # en la fecha de hoy

    #nombre de la categoria
    categ = Categorias.objects.all().filter(idcategoria=c)
    for ct in categ:
        myCat = ct
    context['categoria'] = myCat.categoria

    # Productos
    context['productos'] = obtenerProductosAumento(user, c)
    return HttpResponse(template.render(context, request))

@login_required
def deleteMovimiento(request, idMov=None, a=None, m=None):
    Movimientos.objects.filter(idmovimiento=idMov).delete()
    return home(request,None,None,None)

@login_required
def nuevoMovimiento(request, t=None):
    user = request.user.id
    # a: anio | m: mes | num: acarreo
    template = loader.get_template('nuevoMovimiento.html')
    context = {}
    # para el link /dolar/anio/mes
    context['mesHoy'] = int(date.today().strftime('%m')) # en la fecha de hoy
    context['anioHoy'] = int(date.today().strftime('%Y'))  # en la fecha de hoy
    context['mes'] = date.today().strftime('%m')
    context['anio'] = date.today().strftime('%Y')
    context['dia'] = date.today().strftime('%d')
    context['tipo'] = t
    context['user'] = user

    # Comercios
    context['comercios'] = obtenerComercios()
    # Categorias
    listUserCategoria = obtenerUserCategorias(user)
    context['userCategorias'] = listUserCategoria
    # Productos
    context['productosCat'] = obtenerJsonSelect(listUserCategoria, user) 
    return HttpResponse(template.render(context, request))

@login_required
def guardarMovimento(request):
    user = request.user.id
    template = loader.get_template('confirmacion.html')
    context = {}
    guardado = True
    ingreso = True

    if request.POST['boton'] == 'cancelar': 
        Tmp.objects.all().delete()
        return home(request,None,None,None)
    else:
        (fecha, anio, mes) = obtenerFechaPOST(request.POST['fecha'])
        context['anio'] = anio
        context['mes'] = mes
        cm = request.POST['com']
        pd = request.POST['producto']
        if pd == '-':
            pd = '.'
        ct = request.POST['categorias']
        cant = request.POST['cant']
        tipo = request.POST['tipo']
        precio = request.POST['precio']
        if int(tipo) == 2:
            ingreso = False
            precio = -int(precio)
        notas = request.POST['notas']
        try:
            Movimientos.guardarMovimiento(cm,pd,ct,fecha,cant,precio,notas,user,tipo)
        except :
            guardado = False

        context['ingreso'] = ingreso
        context['guardado'] = guardado
        return HttpResponse(template.render(context, request))

@login_required
def tck(request, t=None):
    user = request.user.id
    template = loader.get_template('tck.html')
    context = {}
    context['tipo'] = t
    context['mes'] = date.today().strftime('%m')
    context['anio'] = date.today().strftime('%Y')
    context['dia'] = date.today().strftime('%d')

    # tmp
    listTmp = []
    total = 0
    tmp = Tmp.objects.all().filter(usuario=user)
    if tmp.exists():
        for t in tmp:
            if t .total < 0:
                t.total = - t.total
            total = total + t.total
            listTmp.append(t)
    context['tmp'] = listTmp
    context['total'] = total

    # Comercios
    context['comercios'] = obtenerComercios()
    # Categorias
    listUserCategoria = obtenerUserCategorias(user)
    context['userCategorias'] = listUserCategoria
    # Productos
    context['productosCat'] = obtenerJsonSelect(listUserCategoria, user) 
    return HttpResponse(template.render(context, request))

@login_required
def guardarItem(request):
    user = request.user.id
    guardado = True
    ingreso = True
    cm = request.POST['com_aux']
    pd = request.POST['producto']
    if pd == '-':
        pd = '.'
    ct = request.POST['categorias']
    cant = request.POST['cantidad']
    tipo = request.POST['tipo']
    precio = request.POST['precio']
    if int(tipo) == 2:
        ingreso = False
        precio = -int(precio)
    notas = request.POST['notas']

    Tmp.guardarMovimientoTmp(cm,pd,ct,cant,precio,notas,user,tipo)
    return tck(request, t=tipo)

@login_required
def borrarItem(request, idTemp=None, tipo=None):
    Tmp.objects.filter(idTempt=idTemp).delete()
    return tck(request, t=tipo)

@login_required
def guardarTCK(request, t=None):
    user = request.user.id
    if request.POST['boton'] == 'cancelar': 
        Tmp.objects.all().delete()
        return nuevoMovimiento(request, t=t)
    else:
        guardado = True
        template = loader.get_template('confirmacion.html')
        context = {}
        (fecha, anio, mes) = obtenerFechaPOST(request.POST['fecha'])
        context['anio'] = anio
        context['mes'] = mes
        try:
            tmp = Tmp.objects.all()
            for t in tmp:
                comercio = t.comercio
                producto = t.producto
                categoria = t.categoria
                cant = int(t.cantidad)
                precio = int(t.total)
                tipo = t.tipo
                notas = t.notas
            
                mov = Movimientos(fecha=fecha,comercio=comercio,producto=producto,categoria=categoria,cantidad=cant,total=precio,
                    tipo=tipo,adjunto=None,usuario=user,notas=notas)
                mov.save()
            Tmp.objects.all().delete()  
        except:
            guardado = False
        context['guardado'] = guardado
        return HttpResponse(template.render(context, request))

@login_required
def nuevaCategoria(request):
    template = loader.get_template('nuevaCategoria.html')
    return HttpResponse(template.render({}, request))

@login_required
def nuevoComercio(request):
    template = loader.get_template('nuevoComercio.html')
    return HttpResponse(template.render({}, request))

@login_required
def nuevoProducto(request):
    user = request.user.id
    template = loader.get_template('nuevoProducto.html')
    # Categorias y subcategorias
    context = {}
    listUserCategoria = obtenerUserCategorias(user)
    context['categorias'] = listUserCategoria
    context['subCategoria'] = listUserCategoria
    return HttpResponse(template.render(context, request))

@login_required
def guardarCategoria(request):
    user = request.user.id
    template = loader.get_template('confirmacion2.html')
    context = {}
    guardado = True
    categoria = request.POST['categoria']
    if Categorias.objects.filter(categoria=categoria).exists():# Me fijo si existe!
        guardado = False
        categoria = '1'
    else:    
        try:
            request.POST['tarjeta'] # me fijo si es tarjeta!
            tarjeta = True
        except:
            tarjeta = False
        try:
            request.POST['pagoDolar'] # me fijo si pago dolares
            dolar = True
        except:
            dolar = False
        try:
            cat = Categorias(categoria=categoria, tarjeta=tarjeta,pagoDolar=dolar)
            cat.save()
        except:
            guardado = False
            context['guardado'] = guardado
            return HttpResponse(template.render(context, request))
        try:
            usuario = Usuarios.objects.filter(id_user=user)
            for u in usuario:
                myUser = u
            userCat = UserCategoria(usuario=myUser, userCategoria=cat,esVisible=True)
            userCat.save()
        except:
            Categorias.objects.filter(categoria=cat).delete()
            guardado = False
    context['nombre'] = categoria
    context['guardado'] = guardado
    return HttpResponse(template.render(context, request))

@login_required
def guardarProducto(request):
    user = request.user.id
    template = loader.get_template('confirmacion2.html')
    context = {}
    guardado = True

    producto = request.POST['producto']
    if Productos.objects.filter(nombreproducto=producto).exists():# Me fijo si existe!
        guardado = False
        producto = '1'
    else:    
        marca = request.POST['marca']
        categoria = request.POST['categoria']
        if categoria == '0':
            context['guardado'] = False
            return HttpResponse(template.render(context, request))

        c = Categorias.objects.filter(idcategoria=categoria)
        for cat in c:
            categ = cat
        try:
            request.POST['banco']
            banco = True
        except:
            banco = False
        subCategoria = request.POST['subCategoria']
        try:
            if marca != '':
                myProd = producto +'-'+marca
            else:
                myProd = producto
            p = Productos(nombreproducto=myProd,marca=marca,categoria=categoria,subcategoria=subCategoria)
            p.save()
        except:
            context['guardado'] = False
            return HttpResponse(template.render(context, request))
        try: 
            if categoria == '6' or categoria == '10' or categ.tarjeta == True:
                usuario = Usuarios.objects.filter(id_user =user)
                for u in usuario:
                    myUser = u
                per = Personales(usuario=myUser, producto=p,categoria=categ, banco=banco,visible=1)
                per.save()
        except:
            Productos.objects.filter(nombreproducto=myProd).delete()
            guardado = False      
    context['nombre'] = producto
    context['guardado'] = guardado
    return HttpResponse(template.render(context, request))

@login_required
def guardarComercio(request):
    template = loader.get_template('confirmacion2.html')
    context = {}
    guardado = True
    comercio = request.POST['comercio']
    if Comercios.objects.filter(comercio=comercio).exists():# Me fijo si existe!
        guardado = False
        comercio= '1' # muestro YA EXISTE!
    else:    
        direccion = request.POST['direccion']
        try:
            c = Comercios(comercio=comercio,direccion=direccion)
            c.save()
        except:
            guardado = False     
    context['nombre'] = comercio
    context['guardado'] = guardado
    return HttpResponse(template.render(context, request))

@login_required
def presupuestacion(request,tipo=None):
    user = request.user.id
    template = loader.get_template('proyeccion2.html')
    context = {}
    context['guardar'] = True # boton para guardar cambios
    context['mesHoy'] = int(date.today().strftime('%m')) # int() para que valide el if!!
    context['anio'] = int(date.today().strftime('%Y'))
    mitad = sl/2
    mitad2 = dsl/2
    context['res'] = False
    context['fj'] = False
    context['cards'] = False
    context['others'] = False
    context['bk'] = False

    #Resumen
    if tipo == "res":
        context['res'] = True
        (presupuesto, gastos) = obtenerGraficoResumen(user)
        presupuestoCubrir = presupuesto
        context['presupuesto'] = presupuesto
        context['gastos'] = gastos
        context['tope'] = tope

        # fijos y tarjetas
        context['categorias'] = obtenerFijosAndTarjetas(user)

        # pesos
        ahorros2 = obtenerAhorrosINPUT(user)
        context['pesos'] = ahorros2
        
        # por cubrir
        (porCub, dolares,c) = porCubrir(user,presupuestoCubrir, obtenerAhorros(user))
        context['porCubrir'] = porCub
        context['dolares'] = dolares

        # lineas tope en el grafico de resumen
        cincuenta = []
        quince = []
        for i in range(0,14):
            if i == 12 or i == 0 or i == 6:
                cin = mitad2 * c
                q= mitad2*2*c
            else:
                cin = mitad * c
                q= mitad*2*c
            cincuenta.append(cin)
            quince.append(q)
        context['cincuenta'] = cincuenta 
        context['quince'] = quince

        # otros
        (otrosPresupuesto, otrosGastos, otros) = obtenerOtrosResumen(user)
        context['otrosGastos'] = otrosGastos
        context['otrosPresupuesto'] = otrosPresupuesto
        context['otros'] = otros

        #bk
        context['bank'] = Movimientos.obtenerDepositos(user, False)
    
    # Fijos
    if tipo == "fijos":
        context['fj'] = True
        # grafico
        (presupuestoFijos, gastosFijos) = obtenerGraficoFijos(user)
        context['gastosFijos'] = gastosFijos
        context['presupuestoFijos'] = presupuestoFijos

        # resumen
        context['personalesFijos'] = obtenerResumenFijos2(user,10)

    # Tarjetas
    if tipo == "cards":
        context['cards'] = True
        context['tarjetas'] = obtenerTarjetas2(user)
        context['dolarTarjeta'] = obtenerDolarParaTarjeta()

    # otros
    if tipo == "others":
        context['others'] = True

        # grafico
        (otrosPresupuesto,otrosGastos, otros) = obtenerOtros(user)
        context['otrosGastos'] = otrosGastos
        context['otrosPresupuesto'] = otrosPresupuesto
        context['otros'] = otros

        # resumen
        context['otrosLista'] = obtenerResumenOtros2(user)

    # bk
    if tipo == "bk":
        context['guardar'] = True # boton para guardar cambios
        context['bk'] = True
        (bank, bkProd) = Movimientos.obtenerDepositos(user, True)
        context['bank'] = bank
        context['bkProd'] = bkProd
      
    return HttpResponse(template.render(context, request))

@login_required
def guardarPresupuesto(request):
    user = request.user.id
    template = loader.get_template('confirmacion3.html')
    context = {}
    context['mesHoy'] = int(date.today().strftime('%m'))
    context['anio'] = date.today().strftime('%Y')
    context['link'] = actualizarProyeccion(request,user) # dividir para optimar + en url!!!!      
    context['guardado'] = True           
    return HttpResponse(template.render(context, request))

@login_required
def auto(request,q=None):
    user = request.user.id
    template = loader.get_template('auto.html')
    context = {}
    context['arrow'] = False
    (suma, auto, anios) = movilidad(q, inicio)
    context['anios'] = anios
    context['auto'] = auto 
    context['suma'] = suma
    context['movil'] = q
    return HttpResponse(template.render(context, request))

@login_required
def nuevoCambio(request):
    template = loader.get_template('nuevoCambio.html')
    context = {}
    guardado = True
    context['mes'] = date.today().strftime('%m')
    context['anio'] = date.today().strftime('%Y')
    context['dia'] = date.today().strftime('%d')
    return HttpResponse(template.render(context, request))

@login_required
def guardarCambio(request):
    user = request.user.id
    template = loader.get_template('confirmacion4.html')
    context = {}
    guardado = True
    cambio = request.POST['cambio']
    (fecha, anio, mes) = obtenerFechaPOST(request.POST['fecha'])
    try:
        ch = MiCambio(fecha=fecha,cambio=float(cambio))
        ch.save()
    except:
        guardado = False
    context['guardado'] = guardado
    return HttpResponse(template.render(context, request))

@login_required
def config(request,t=None):
    user = request.user.id
    template = loader.get_template('configuracion.html')
    context = {}
    context['prod'] = False
    context['fijos'] = False

    # Productos
    if t == 'productos':
        productos = []
        prod = Productos.objects.all()
        for p in prod:
            sub = Categorias.objects.filter(idcategoria=p.subcategoria)
            for c in sub:
                p.sub = c
            productos.append(p)
        productos.sort()
        categorias = []
        cat = Categorias.objects.all()
        for c in cat:
            categorias.append(c)
        categorias.sort()
        context['prod'] = True
        context['productos'] = productos
        context['categorias'] = categorias

    # Fijos
    if t == 'fijos':
        personalesFijos= []
        cat = Categorias.objects.get(idcategoria=10) # objeto excato con get!!!!
        per = Personales.objects.filter(usuario=user,categoria=cat)
        for p in per:
            personalesFijos.append(p)
        personalesFijos.sort()
        context['personalesFijos'] = personalesFijos
        context['fijos'] = True

    # Tarjetas
    if t == 'tarjeta':
        card = []
        ct = Categorias.objects.filter(tarjeta=1)
        for cat in ct:
            tarjetas = [] 
            per = Personales.objects.filter(usuario=user,categoria=cat)
            for p in per:
                tarjetas.append(p)
            tarjetas.sort()
            card.append(tarjetas)
        card.sort()
        context['tarjetas'] = card
        context['tarjeta'] = True

    # Varios
    if t == 'varios':
        productos = []
        prod = Productos.objects.filter(categoria=6)
        for p in prod:
            sub = Categorias.objects.filter(idcategoria=p.subcategoria)
            for c in sub:
                p.sub = c
            productos.append(p)
        productos.sort()
        categorias = []
        cat = Categorias.objects.all()
        for c in cat:
            categorias.append(c)
        categorias.sort()
        context['prod'] = True
        context['productos'] = productos
        context['categorias'] = categorias

    # Mis tarjetas
    if t == 'tarjetas':
        productos = []
        prod = Productos.objects.all()
        for p in prod:
            try:
                if p.categoria.tarjeta: 
                    sub = Categorias.objects.filter(idcategoria=p.subcategoria)
                    for c in sub:
                        p.sub = c
                    productos.append(p)
                productos.sort()
            except:
                continue
        categorias = []
        cat = Categorias.objects.all()
        for c in cat:
            categorias.append(c)
        categorias.sort()
        context['prod'] = True
        context['productos'] = productos
        context['categorias'] = categorias

    # Categorias
    if t == 'categorias':
        categorias = []
        uCat = UserCategoria.objects.filter(usuario=user)
        for p in uCat:
            categorias.append(p)
        categorias.sort()
        context['categoria'] = True
        context['MisCategorias'] = categorias

    context['config'] = t
    context['guardarConfig'] = True
    return HttpResponse(template.render(context, request))

@login_required
def guardarConfig(request):
    user = request.user.id
    template = loader.get_template('confirmacion5.html')
    context = {}
    guardado = False

    # Productos
    for k,v in request.POST.items():
        if v == 'on': # filtro los que son ON !!!
            if request.POST[k+'.categoria'] != None:
                ct = Categorias.objects.filter(idcategoria=request.POST[k+'.categoria'])
                for cat in ct:
                    c = cat
            else:
                cat = None
            if request.POST[k+'.subCategoria'] != None:
                sub = request.POST[k+'.subCategoria']
            else:
                sub = None
            try:
                Productos.objects.filter(idproducto=k).update(categoria=c)
                Productos.objects.filter(idproducto=k).update(subcategoria=sub)
                guardado = True
            except:
                guardado = False
        
        # Fijos
        try:
            # es banco?
            if k[0] == 'b':
                idPer = ''
                for i in range(2,len(k)):
                    idPer = idPer + k[i]
                Personales.objects.filter(idPersonal=idPer).update(banco=int(v))
            # es visible?
            if k[0] == 'v':
                idPer = ''
                for i in range(2,len(k)):
                    idPer = idPer + k[i]
                Personales.objects.filter(idPersonal=idPer).update(visible=int(v))
            guardado = True
        except:
            guardado = False

        # Tarjetas
        try:
            # es visible?
            if k[0] == 'v':
                idPer = ''
                for i in range(2,len(k)):
                    idPer = idPer + k[i]
                Personales.objects.filter(idPersonal=idPer).update(visible=int(v))
            guardado = True
        except:
            guardado = False

        # Categorias
        try:
            # es visible userCategoria! 
            if k[0] == 'u':
                idUserCat = ''
                for i in range(2,len(k)):
                    idUserCat = idUserCat + k[i]
                UserCategoria.objects.filter(idUserCat=idUserCat).update(esVisible=int(v))
            guardado = True
        except:
            guardado = False

    context['guardado'] = guardado
    context['link'] = request.POST['link']
    return HttpResponse(template.render(context, request))

@login_required
def deletePersonal(request, i=None):
    Personales.objects.filter(idPersonal=i).delete()
    t = 'tarjeta'
    return config(request,t)




