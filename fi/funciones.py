from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
from .dolar import *
from datetime import date, datetime
from fi.models import *
from django.db import connection
from django.db.models import Sum
import random
from colormap import hex2rgb
import datetime
import json
import hashlib
import os

tope = 500
catAuto = 77
catMoto = 76
catPublico = 78
arregloAuto = 989
sube = 402
taxi = 6
patenteMoto = 191

def definirFecha(a, m, num):
    # Devuelve la fecha + num
    if num == None: #estoy en el mes actual
        num= 0
        fecha = date.today()
    else: # sino es NUll entonces me tengo que mover de mes
        if num == 2: #mes anterior sino mes siguiente
            num = -1
        mes = m + num  
        anio = a
        if mes > 12:
            mes = mes - 12
            anio = anio + 1
        if mes < 1:
            mes = 12 + mes 
            anio = anio - 1
        fecha = datetime.date(anio, mes, 1) # fecha a la que me muevo
    return fecha

def obtenerMovimientosDelMes(mes, user, anio):
    # Movimientos del mes por año
    movimientos =  Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio)
    listaMov = []
    for ul in movimientos:
        listaMov.append(ul)# los pongo en una lista
    for a in listaMov :
        if a.total < 0:
            a.total = - a.total # le cambio el signo a los gastos!
    listaMov .sort()
    return listaMov

def obtenerMovimientosDelMesPorTipo(mes, user, anio, tipo):
    # Movimientos del mes por tipo
    movimientos =  Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=tipo)
    listaMov = []
    for ul in movimientos:
        listaMov.append(ul)# los pongo en una lista
    for a in listaMov :
        if a.total < 0:
            a.total = - a.total # le cambio el signo a los gastos!
    listaMov .sort()
    return listaMov

def obtenerMovDelMesPorCategoriaTipo(mes, user, anio, cat, tipo):
    #Movimientos por tipo del mes, por categoria y año 
    total = 0 
    movimientos =  Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio, categoria=cat,tipo=tipo)

    listaMov = []
    for ul in movimientos:
        listaMov.append(ul)# movimientos de esa categoria
    for a in listaMov :
        if a.total < 0:
            a.total = - a.total # le cambio el signo a los gastos!
        total = total + a.total # total por tipo de es catagoria
    listaMov .sort()
    c = Categorias.objects.all().filter(idcategoria=cat)
    for i in c:
        categoria = i.categoria

    # pague el presupuesto?
    if tipo == 1:
        pagos =  Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio, categoria=cat,tipo=2)
        for g in pagos:
            for i in listaMov:
                if g.categoria == i.categoria and g.producto == i.producto:
                    i.categoria.pago = True
                    i.categoria.gastos = - g.total

    return (listaMov, round(total, 2), categoria)

def listaUsuariosCategorias(c, mes, user, anio):
    # devuelve una tupla con los totales de la categoria (saldo, ingresos,gastos) por mes y año
    s = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,
                                             categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# saldo por categoria
    i = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=1,
                                         categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# ingreso por categoria
    g = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=2,
                                         categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# gasto por categoria
    if s['total__sum'] is None:
        s['total__sum'] = 0
    if i['total__sum'] is None:
        i['total__sum'] = 0
    if g['total__sum'] is None:
        g['total__sum'] = 0
    lista = [s['total__sum'], i['total__sum'], g['total__sum']]
    return lista

def listaUsuariosCategoriasAnual(c, user, anio):
    # devuelve una tupla con los totales de la categoria por año (saldo, ingresos,gastos)
    s = Movimientos.objects.all().filter(usuario=user, fecha__year=anio,
                                             categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# saldo por categoria
    i = Movimientos.objects.all().filter(usuario=user, fecha__year=anio,tipo=1,
                                         categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# ingreso por categoria
    g = Movimientos.objects.all().filter(usuario=user, fecha__year=anio,tipo=2,
                                         categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# gasto por categoria
    if s['total__sum'] is None:
        s['total__sum'] = 0
    if i['total__sum'] is None:
        i['total__sum'] = 0
    if g['total__sum'] is None:
        g['total__sum'] = 0
    lista = [s['total__sum'], i['total__sum'], g['total__sum']]
    return lista

def asignarUserCategoria(c, s ,i ,g, barra):
    c.userCategoria.presupuesto = round(i ,2)
    c.userCategoria.gastos = round(-g, 2)
    c.userCategoria.saldo = round(s, 2)
    c.userCategoria.color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) # color de categorias torta
    c.userCategoria.rgb = 'rgb'+''.join(str(hex2rgb(c.userCategoria.color))) # color rgb torta
    c.userCategoria.barra = barra

def torta(listUserCategorias, ing, saldo):
    coloresPorc = []
    nombresTorta = []
    coloresTorta = []
    if saldo:
        if listUserCategorias[0].porcentaje > 0:  # 1ero el saldo
            coloresPorc.append(listUserCategorias[0].porcentaje)
            nombresTorta.append(listUserCategorias[0].categoria)
            coloresTorta.append(listUserCategorias[0].rgb)
    for n in range(1, len(listUserCategorias)):
        if listUserCategorias[n].userCategoria.gastos != 0:
            nombresTorta.append(listUserCategorias[n].userCategoria.categoria)
            coloresTorta.append(listUserCategorias[n].userCategoria.rgb)
            coloresPorc.append(round(listUserCategorias[n].userCategoria.gastos * 100 / ing, 1)) # porcentaje de las categorias
    return [nombresTorta, coloresTorta, coloresPorc]

def tortaPresupuesto(listUserCategorias, total):
    coloresPorc = []
    nombresTorta = []
    coloresTorta = []
    for n in range(1, len(listUserCategorias)):
        if listUserCategorias[n].userCategoria.presupuesto != 0:
            nombresTorta.append(listUserCategorias[n].userCategoria.categoria)
            coloresTorta.append(listUserCategorias[n].userCategoria.rgb)
            coloresPorc.append(round(listUserCategorias[n].userCategoria.presupuesto * 100 / total, 1)) # porcentaje de las categorias
    return [nombresTorta, coloresTorta, coloresPorc]

def tortaPorCategoria(categoria, user, a, m,tipo):
    coloresPorc = []
    nombresTorta = []
    coloresTorta = []
    mov = Movimientos.objects.all().filter(categoria=categoria, usuario=user, tipo=tipo, fecha__year=a, fecha__month=m)
    f = Movimientos.objects.all().filter(categoria=categoria, usuario=user, tipo=tipo, fecha__year=a, fecha__month=m).aggregate(Sum('total'))
    if f['total__sum'] is None:
        f['total__sum'] = 0
    if tipo == 1:
        for m in mov:
            nombresTorta.append(m.producto.nombreproducto)
            coloresTorta.append('rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])))))
            coloresPorc.append(round(m.total * 100 / f['total__sum'], 1))
    else:
        productos = []
        for k in mov:
            productos.append(k.producto)
            productos = list(set(productos)) #saco repetidos!
        for j in productos:
            g = Movimientos.objects.all().filter(categoria=categoria, usuario=user, tipo=tipo, fecha__year=a, fecha__month=m,producto=j).aggregate(Sum('total'))
            if g['total__sum'] is None:
                g['total__sum'] = 0
            nombresTorta.append(j.nombreproducto)
            coloresTorta.append('rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])))))
            coloresPorc.append(round(-g['total__sum'], 1))
    return (nombresTorta, coloresTorta, coloresPorc)

def tortaPorProducto(user, a, m,tipo):
    coloresPorc = []
    nombresTorta = []
    coloresTorta = []
    mov = Movimientos.objects.all().filter(usuario=user, tipo=tipo, fecha__year=a, fecha__month=m)
    productos = []
    for k in mov:
        productos.append(k.producto)
        productos = list(set(productos)) #saco repetidos!
    for j in productos:
        g = Movimientos.objects.all().filter(usuario=user, tipo=tipo, fecha__year=a, fecha__month=m,producto=j).aggregate(Sum('total'))
        if g['total__sum'] is None:
            g['total__sum'] = 0
        nombresTorta.append(j.nombreproducto)
        coloresTorta.append('rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])))))
        coloresPorc.append(round(-g['total__sum'], 1))
    return (nombresTorta, coloresTorta, coloresPorc)

def obtenerBlue():
    myDolar = Cotizacion.objects.all().last()
    v = round( myDolar.venta, 2)
    c = round( myDolar.compra, 5)
    return [c, v]

def obtenerOficial():
    myDolar = Dolar.objects.all().last()
    d = round( myDolar.venta, 2)
    imp1 = 0
    imp2 = 0
    return round(d + d * imp1 + d * imp2, 2)

def obtenerValorDolarizado(mes, anio,user):
    presupuesto = 0
    ah = 0
    presupuesto = Movimientos.obtenerTotalPorMes(mes, user, anio, 1)
    myDolar = Cotizacion.objects.all().last()
    a = Ahorros.obtenerAhorrosPorMes(mes, user, anio).aggregate(Sum('ingreso'))
    if a['ingreso__sum'] is None:
        a['ingreso__sum'] = 0
    dolar = round(((presupuesto - a['ingreso__sum']) / myDolar.venta),2)
    return round(dolar, 2)

def crearCategorias(mes, user, anio):
    # devuelve una lista <UserCategorias> por mes y año
    listUserCategorias = []
    listAux = [] # para ordenar antes 
    coloresBarra = ['success','warning','danger','primary','info']
    k = 0
    cat = UserCategoria.objects.all().filter(usuario=user)# categorias que usa el usuario
    for d in cat: # ordeno alfabeticamente
        if d.esVisible:
            listAux.append(d)
        listAux.sort()
    for c in listAux: # asigno los valores
        barra = None
        [s, i, g] = listaUsuariosCategorias(c, mes, user, anio)
        if s > 0:
            barra = coloresBarra[k]
            k+= 1
            if k > 4:
                k = 0
        asignarUserCategoria(c, s ,i ,g, barra)
        listUserCategorias.append(c)
    listUserCategorias.sort()
    return listUserCategorias

def crearCategoriasAnual(user, anio):
    # devuelve una lista <UserCategorias> por año
    listUserCategorias = []
    listAux = [] # para ordenar antes 
    coloresBarra = ['success','warning','danger','primary','info']
    k = 0
    cat = UserCategoria.objects.all().filter(usuario=user)# categorias que usa el usuario
    for d in cat: # ordeno alfabeticamente
        listAux.append(d)
    listAux.sort()
    for c in listAux: # asigno los valores
        barra = None
        [s, i, g] = listaUsuariosCategoriasAnual(c,user, anio)
        if s > 0:
            barra = coloresBarra[k]
            k+= 1
            if k > 4:
                k = 0
        asignarUserCategoria(c, s ,i ,g, barra)
        listUserCategorias.append(c)
    listUserCategorias.sort()
    return listUserCategorias

def inicializarListaCategorias(user):
    # devuelve una lista <Categorias> con valores 0
    cat = UserCategoria.objects.all().filter(usuario=user)# categorias que usa el usuario
    lista = []
    for d in cat: 
       lista.append(0)
    return lista
    
def obtenerJsonSelect(lista, user):
    # funcion recibe una lista y devuelve json a partir de un diccionario creado de la lista
    # se usa para los select
    dicc = {}
    for p in lista:
        k = 0 # flag para elegir entre producto o personal
        productos = []
        if p.userCategoria.idcategoria != 10:
            prod = Productos.objects.all().filter(categoria=p.userCategoria.idcategoria)
        else:
            prod = Personales.objects.all().filter(categoria=10, usuario=user)
            k += 1 
        if k == 0:
            for i in prod:
                a = i.nombreproducto
                productos.append(a)
        else:
            for i in prod:
                if i.producto.idproducto != 0:
                    a = i.producto.nombreproducto
                    productos.append(a)
        productos.sort()
        productos.insert(0, '-') # el primer elemento
        dicc[p.userCategoria.idcategoria] = productos
    return json.dumps(dicc)

def obtenerProductosAumento(user, c):
    listProductos = []
    m = Movimientos.objects.all().filter(usuario=user, categoria=c,tipo=2)
    for p in m:
        try: # Algunos productos no existen en la base de datos
            if p.producto not in listProductos:
                primero = Movimientos.objects.all().filter(usuario=user, categoria=c,tipo=2,producto=p.producto.idproducto).first()
                precioPrimero = -primero.total / primero.cantidad
                ultimo = Movimientos.objects.all().filter(usuario=user, categoria=c,tipo=2,producto=p.producto.idproducto).last()
                precioUltimo = -ultimo.total / ultimo.cantidad

                # barra de progreso
                p.producto.dif = round((precioUltimo - precioPrimero)*100/ precioPrimero,1)
                p.producto.primero = round(precioPrimero,1)
                p.producto.ultimo = round(precioUltimo, 1)
                p.producto.fechaPrimero = primero.fecha
                p.producto.fechaUltimo = ultimo.fecha
                listProductos.append(p.producto)
        except :
            continue       
    listProductos.sort()
    return listProductos

def obtenerUserCategorias(user):
    listUserCategoria = []
    uCat = UserCategoria.objects.all().filter(usuario=user)
    for u in uCat:
        if u.esVisible:
            u.rgb = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
            listUserCategoria.append(u)
    listUserCategoria.sort()
    return listUserCategoria

def obtenerGraficoBarras(user, inicio, anioHoy):
    listGraficoBarras = []
    cat = obtenerUserCategorias(user) # categorias que usa el usuario
    k = 0 # nro de chart
    for d in cat:
        g = GraficoBarras(d.userCategoria, k, None) # prod = None
        k += 1
        for a in range(inicio, anioHoy+1):
            data = []
            for i in range(1, 14):
                mov = Movimientos.objects.all().filter(usuario=user, tipo=2, fecha__year=a, fecha__month=i, 
                                                    categoria=d.userCategoria.idcategoria).aggregate(Sum('total'))
                if mov['total__sum'] is None:
                    mov['total__sum'] = 0
                data.append(-mov['total__sum'] )
            ds = DatasetsBarra(a, data)
            g.data.append(ds)
        listGraficoBarras.append(g) 
    listGraficoBarras.sort()
    return listGraficoBarras

def obtenerComercios():
    listComercios = []
    com = Comercios.objects.all()
    for c in com:
        listComercios.append(c)
    listComercios.sort()
    return listComercios

def gastacionGrafico(user, inicio, anioHoy):
    # años acumulados
    totales = inicializarListaCategorias(user)
    nombres = []
    rgb = []
    #lista de totales 
    for i in range(inicio, anioHoy+1):
        listUserCategorias = crearCategoriasAnual(user, i)
        k = 0
        for j in listUserCategorias:
            totales[k] = totales[k] + j.userCategoria.gastos
            k+= 1
    # lista de nombres
    for j in listUserCategorias:
        nombres.append(j.userCategoria.categoria)
        rgb.append(j.userCategoria.rgb)
    return (totales, nombres, rgb)

def obtenerFechaPOST(fechaMov):
    nuevaFecha = ''
    i=0
    while(i < len(fechaMov)):
        if fechaMov[i] != '-':
            nuevaFecha = nuevaFecha + fechaMov[i]
        i=i+1
    anio = int(nuevaFecha[0:4])
    mes = int(nuevaFecha[4:6])
    dia = int(nuevaFecha[6:])
    fecha = datetime.date(anio, mes, dia)
    return (fecha, anio, mes)

# Presupuesto
def obtenerGraficoResumen(user):
    presupuesto = []
    gastos = []
    for m in range(0,14):
        anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
        if m == 0:
            m = 12
            anioHoy = anioHoy-1
        if m == 13:
            m = 1
            anioHoy = anioHoy + 1
        z = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user).aggregate(Sum('total'))
        a = z['total__sum']
        g = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user).aggregate(Sum('total'))
        if z['total__sum'] is None:
            z['total__sum'] = 0.00
        if g['total__sum'] is None:
            g['total__sum'] = 0.00
        presupuesto.append(round(z['total__sum'],2))
        gastos.append(round(-g['total__sum'],2))
    return (presupuesto, gastos)

# fijos y tarjetas
def obtenerFijosAndTarjetas(user):
    categorias = [] 
    userCategorias = UserCategoria.objects.all().filter(usuario=user).distinct() # categorias del usuario
    for c in userCategorias: 
        uCatAux = UserCategoriaAux(categoria=c.userCategoria, presupuesto=0.0,saldo=0, porcentaje=0,rgb=0)
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            pCat = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user, categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))
            if pCat['total__sum'] is None:
                pCat['total__sum'] = 0.00
            uCatAux.valores.append(pCat['total__sum']) # cargo el presupuesto de fijo o de tarjeta 
        categorias.append(uCatAux)
    categorias.sort()
    return categorias

# ahorros
def obtenerAhorros(user):
    usuario = Usuarios.objects.filter(id_user=user)
    for i in usuario:
        u = i
    ahorros = []
    for m in range(0,14):
        anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
        if m == 0:
            m = 12
            anioHoy = anioHoy-1
        if m == 13:
            m = 1
            anioHoy = anioHoy + 1
        ah = Ahorros.objects.all().filter(fecha__month=m,fecha__year=anioHoy,usuario=user).aggregate(Sum('ingreso'))
        aH = Ahorros.objects.all().filter(fecha__month=m,fecha__year=anioHoy,usuario=user)
        if ah['ingreso__sum'] is None:
            ah['ingreso__sum'] = 0.00
        if not aH.exists():
            a = Ahorros(fecha=date.today(),anterior=0,ingreso=0,usuario=i,ahorro=0,idahorro=0)
        else:
            for j in aH:
                a = j
                a.ahorro = round(ah['ingreso__sum'],2)
        ahorros.append(a)
    return ahorros

# ahorros
def obtenerAhorrosINPUT(user):
    usuario = Usuarios.objects.filter(id_user=user)
    for i in usuario:
        u = i
    ahorros = []
    for m in range(0,14):
        anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
        if m == 0:
            m = 12
            anioHoy = anioHoy-1
        if m == 13:
            m = 1
            anioHoy = anioHoy + 1
        mesInput = Input(m,anioHoy)
        ah = Ahorros.objects.all().filter(fecha__month=m,fecha__year=anioHoy,usuario=user).aggregate(Sum('ingreso'))
        aH = Ahorros.objects.all().filter(fecha__month=m,fecha__year=anioHoy,usuario=user)
        if ah['ingreso__sum'] is None:
            ah['ingreso__sum'] = 0.00
        if not aH.exists():
            mesInput.valor = 0
        else:
            for j in aH:
                mesInput.valor = round(ah['ingreso__sum'],2)
                mesInput.idMov = j.idahorro
        ahorros.append(mesInput)
    return ahorros

# por cubrir
def porCubrir(user, presupuesto, ahorros):
    porCubrir = []
    dolares = []
    [v, c] = obtenerBlue()
    for i in range(0,len(presupuesto)):
        porCubrir.append(round((presupuesto[i] - ahorros[i].ahorro),1))
        dolares.append(round((presupuesto[i] - ahorros[i].ahorro)/c,2))
    return (porCubrir, dolares,c)

# otros
def obtenerOtrosResumen(user):
    categorias = []
    userCategorias = UserCategoria.objects.all().filter(usuario=user).distinct() # categorias del usuario
    for c in userCategorias: 
        uCatAux = UserCategoriaAux(categoria=c.userCategoria, presupuesto=0.0,saldo=0, porcentaje=0,rgb=0)
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            pCat = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user, categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))
            if pCat['total__sum'] is None:
                pCat['total__sum'] = 0.00
            uCatAux.valores.append(pCat['total__sum']) # cargo el presupuesto de fijo o de tarjeta 
        categorias.append(uCatAux)
    categorias.sort()

    otros = [] # grafico
    otrosPresupuesto = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    otrosGastos = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for h in categorias:
        if h.categoria.idcategoria != 10 and h.categoria.tarjeta != True:
            otros.append(h)
    for o in otros:
        total = 0
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            k = m # para que no me pise el mes en otrosPresupuesto[k] = otrosPresupuesto[k] + t['total__sum']
            if m == 0:
                m = 12
                anioHoy = anioHoy - 1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=o.categoria).aggregate(Sum('total'))
            z = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=o.categoria).aggregate(Sum('total'))
            if z['total__sum'] is None:
                z['total__sum'] = 0.00
            if t['total__sum'] is None:
                t['total__sum'] = 0.00
            otrosPresupuesto[k] = otrosPresupuesto[k] + round(t['total__sum'],2)
            otrosGastos[k] = otrosGastos[k] + round(z['total__sum']*(-1) ,2)
    return (otrosPresupuesto, otrosGastos, otros)

# Resumen fijos
def obtenerGraficoFijos(user):
    presupuestoFijos = []
    gastosFijos = []
    for m in range(0,14):
        anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
        if m == 0:
            m = 12
            anioHoy = anioHoy-1
        if m == 13:
            m = 1
            anioHoy = anioHoy + 1
        p = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=10).aggregate(Sum('total'))
        g = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=10).aggregate(Sum('total'))
        if p['total__sum'] is None:
            p['total__sum'] = 0.00
        if g['total__sum'] is None:
            g['total__sum'] = 0.00
        presupuestoFijos.append(round(p['total__sum'],2))
        gastosFijos.append(round(-g['total__sum'],2))
    return (presupuestoFijos, gastosFijos)

# resumen
def obtenerResumenFijos(user):
    personalesFijos = []
    per = Personales.objects.all().filter(usuario=user,categoria=10)
    for p in per:
        p.valores = []
        #p.producto.nombreproducto = p.producto.nombreproducto[0:8]
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            mesInput = Input(m,anioHoy)
            try:
                t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,producto=p.producto).aggregate(Sum('total'))
                if t['total__sum'] is None:
                    r = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=p.producto).aggregate(Sum('total'))
                    if r['total__sum'] is None:
                        r['total__sum'] = 0.00
                    mesInput.valor = r['total__sum']
                    p.valores.append(mesInput)
                else:
                    mesInput.valor = t['total__sum']
                    p.valores.append(mesInput)     
            except:
                continue
        personalesFijos.append(p)
    personalesFijos.sort()
    return personalesFijos

def obtenerResumenFijos2(user,cat):
    personalesFijos = []
    per = Personales.objects.all().filter(usuario=user,categoria=cat)
    for p in per:
        if p.visible:
            p.valores = []
            for m in range(0,14):
                anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
                if m == 0:
                    m = 12
                    anioHoy = anioHoy-1
                if m == 13:
                    m = 1
                    anioHoy = anioHoy + 1
                mesInput = Input(m,anioHoy)
                try:
                    t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,producto=p.producto).aggregate(Sum('total'))
                    if t['total__sum'] is None:
                        r = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=p.producto).aggregate(Sum('total'))
                        
                        if r['total__sum'] is None:
                            r['total__sum'] = 0.00
                            mesInput.idMov = 0
                        else:
                            mov = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=p.producto)
                            for movi in mov:
                                mesInput.idMov = movi.idmovimiento
                            mesInput.valor = r['total__sum']
                        p.valores.append(mesInput)
                    else:
                        mov = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,producto=p.producto)
                        for movi in mov:
                            mesInput.idMov = movi.idmovimiento
                        mesInput.valor = t['total__sum']
                        p.valores.append(mesInput)     
                except:
                    continue
            personalesFijos.append(p)
    personalesFijos.sort()
    return personalesFijos

def obtenerTarjetas2(user):
    #----------------------------------------------------------------------------
    # grafico de tarjetas dentro de cada categoria
    j = 2 # nro de grafico
    tarjetas = [] 
    aux = [] # lista principal para la vista
    cateG = Categorias.objects.filter(tarjeta=1)
    for ct in cateG:
        tarj = UserCategoria.objects.all().filter(usuario=user,userCategoria =ct,esVisible=1)
        for t in tarj:
            if t.userCategoria.tarjeta and t.userCategoria.idcategoria not in tarjetas:
                tarjetas.append(t.userCategoria.idcategoria)
    for i in tarjetas:
        cat = Categorias.objects.filter(idcategoria=i)
        for c in cat:
            c.listaPresupuesto =[] # valores 
            c.listaGastos = [] # valores 
            c.nroChart = j # nro de grafico 
            c.listaPersonalesTarjeta = [] # nombres de los productos de la categoria 
            j = j + 1
            aux.append(c)
    aux.sort() # una lista de Categorias con los atributos anteriores!
    #print(aux)
    for c in aux: 
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            p = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=c).aggregate(Sum('total'))
            g = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=c).aggregate(Sum('total'))
            if p['total__sum'] is None:
                p['total__sum'] = 0.00
            if g['total__sum'] is None:
                g['total__sum'] = 0.00
            c.listaPresupuesto.append(round(p['total__sum'],2))
            c.listaGastos.append(round(-g['total__sum'],2))
#------------------------------------------------------------------------------------------------
    # resumen de tarjetas
    for c in aux:
        per = Personales.objects.all().filter(categoria=c.idcategoria,usuario=user,visible=1) # es visible!
        for p in per:
            if p.visible:
                p.valores = []
                for m in range(0,14):
                    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
                    if m == 0:
                        m = 12
                        anioHoy = anioHoy-1
                    if m == 13:
                        m = 1
                        anioHoy = anioHoy + 1
                    mesInput = Input(m, anioHoy)
                    try:
                        t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,producto=p.producto,categoria=c).aggregate(Sum('total'))
                        if t['total__sum'] is None:
                            r = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=p.producto,categoria=c).aggregate(Sum('total'))
                            if r['total__sum'] is None:
                                r['total__sum'] = 0.00
                                mesInput.idMov = 0
                            else:
                                mov = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=p.producto)
                                for movi in mov:
                                    mesInput.idMov = movi.idmovimiento
                                mesInput.valor = r['total__sum']
                            p.valores.append(mesInput)
                        else:
                            mov = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,producto=p.producto)
                            for movi in mov:
                                mesInput.idMov = movi.idmovimiento
                            mesInput.valor = t['total__sum']
                            p.valores.append(mesInput)     
                    except:
                        continue
                c.listaPersonalesTarjeta.append(p)
        c.listaPersonalesTarjeta.sort()
    return aux


# otros
def obtenerOtros(user):
    # listado de categorias otros
    categorias = []
    userCategorias = UserCategoria.objects.all().filter(usuario=user).distinct() # categorias del usuario
    for c in userCategorias: 
        uCatAux = UserCategoriaAux(categoria=c.userCategoria, presupuesto=0.0,saldo=0, porcentaje=0,rgb=0)
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            pCat = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user, categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))
            if pCat['total__sum'] is None:
                pCat['total__sum'] = 0.00
            uCatAux.valores.append(pCat['total__sum']) # cargo el presupuesto de fijo o de tarjeta 
        categorias.append(uCatAux)
    categorias.sort()

    # grafico
    otros = [] 
    otrosPresupuesto = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    otrosGastos = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for h in categorias:
        if h.categoria.idcategoria != 10 and h.categoria.tarjeta != True:
            otros.append(h)
    for o in otros:
        total = 0
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            k = m # para que no me pise el mes en otrosPresupuesto[k] = otrosPresupuesto[k] + t['total__sum']
            if m == 0:
                m = 12
                anioHoy = anioHoy - 1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=o.categoria).aggregate(Sum('total'))
            z = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=o.categoria).aggregate(Sum('total'))
            if z['total__sum'] is None:
                z['total__sum'] = 0.00
            if t['total__sum'] is None:
                t['total__sum'] = 0.00
            otrosPresupuesto[k] = round(otrosPresupuesto[k] + t['total__sum'],2)
            otrosGastos[k] = round(otrosGastos[k] + z['total__sum']*(-1),2)
    return(otrosPresupuesto,otrosGastos, otros)

def obtenerResumenOtros(user, otros):
    auxOtros = [] # lista principal para la vistas
    for t in otros:
        auxOtros.append(t.categoria)
    auxOtros.sort()   
    for c in auxOtros: # resumen de tarjetas
        c.valores = []
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            mesInput = Input(m, anioHoy)
            t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=c).aggregate(Sum('total'))
            if t['total__sum'] is None:
                r = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=c).aggregate(Sum('total'))
                if r['total__sum'] is None:
                    r['total__sum'] = 0.00
                mesInput.valor = r['total__sum']
                c.valores.append(mesInput)
            else:
                mesInput.valor = t['total__sum']
                c.valores.append(mesInput) 
    return auxOtros

def obtenerResumenOtros2(user):
    otros = [] # lista principal 
    cateG = Categorias.objects.filter(tarjeta=0) # no son tarjetas
    for ct in cateG:
        tarj = UserCategoria.objects.all().filter(usuario=user,userCategoria =ct,esVisible=1)
        for t in tarj:
            if t.userCategoria.idcategoria != 10 and t.userCategoria.idcategoria not in otros: # no es categ 10
                otros.append(t)
    otros.sort() # una lista de las otras Categorias!
    for c in otros: 
        c.valores = []
        for m in range(0,14):
            anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
            if m == 0:
                m = 12
                anioHoy = anioHoy-1
            if m == 13:
                m = 1
                anioHoy = anioHoy + 1
            mesInput = Input(m, anioHoy)
            t = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=c.userCategoria).aggregate(Sum('total'))
            if t['total__sum'] is None:
                r = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=c.userCategoria).aggregate(Sum('total'))
                if r['total__sum'] is None:
                    r['total__sum'] = 0.00
                    mesInput.idMov = 0
                else:
                    mov = Movimientos.objects.all().filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=c.userCategoria)
                    for movi in mov:
                        mesInput.idMov = movi.idmovimiento
                    mesInput.valor = r['total__sum']
                c.valores.append(mesInput)
            else:
                mov = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=2,usuario=user,categoria=c.userCategoria)
                for movi in mov:
                    mesInput.idMov = movi.idmovimiento
                mesInput.valor = t['total__sum']
                c.valores.append(mesInput)    
    return otros

def movilidad(cat, inicio): # Arreglar usuarios!!!!
    if cat == 'auto':
        ct = catAuto
    elif cat == 'moto':
        ct = catMoto
    else:
        ct = catPublico

    anios = []
    for a in range(inicio-1,int(date.today().strftime('%Y'))+2):
        anios.append(a)
   
    prod = Productos.objects.filter(subcategoria=ct)
    auto = []
    suma = []
    for b in anios:
        suma.append(0) # inicializo suma = [0,0,0,0,0,....]

    for pr in prod:
        pAux = ProdAux(pr)
        for a in anios: # filtro por algunos que me interesan
            if pr.idproducto == arregloAuto or pr.idproducto == sube or pr.idproducto == taxi or pr.idproducto == patenteMoto or a <= int(date.today().strftime('%Y')):
                t = Movimientos.objects.filter(tipo=2,producto=pr,fecha__year=a).aggregate(Sum('total'))
                if t['total__sum'] is None:
                    t['total__sum'] = 0
                    r = Movimientos.objects.filter(tipo=1,producto=pr,fecha__year=a).aggregate(Sum('total'))
                    if r['total__sum'] is None:
                        r['total__sum'] = 0
                    pAux.lista.append(round(r['total__sum'],2))
                else:
                    pAux.lista.append(round(t['total__sum'],2))
            else:
                r = Movimientos.objects.filter(tipo=1,producto=pr,fecha__year=a).aggregate(Sum('total'))
                if r['total__sum'] is None:
                    r['total__sum'] = 0
                pAux.lista.append(round(r['total__sum'],2))
        auto.append(pAux)
    auto.sort()
    
    for p in auto:
        for k in range(0,len(suma)):
            if p.lista[k] < 0:
                suma[k] -= p.lista[k]
            else:
                suma[k] += p.lista[k]
    return (suma, auto, anios)
    
def actualizarProyeccion(request,user):
    for k,v in request.POST.items():
        # Resumen
        # Pesos 
        # si es ! y no esta vacio guardo en la base
        if k[0] == '!' and v:
            # mes
            m = ''
            j = 1
            while k[j] != '.':
                m = m + k[j]
                j = j + 1

            # anio
            a = ''
            h = j+1
            while k[h] != '.':
                a = a + k[h]
                h = h + 1
            fecha = datetime.date(int(a), int(m), 1)

            # pesos
            u = Usuarios.objects.filter(id_user=user)
            for us in u:
                myUser = us
                ah = Ahorros(fecha=fecha,anterior=None,ingreso=float(v), usuario=myUser,ahorro=None)
                ah.save()

        # si es @ actualizo el valor por idahorro
        if k[0] == '@' or (k[0] == '@' and v ==''):
            idAh = ''
            j = 2
            while k[j] != '.':
                idAh = idAh + k[j]
                j = j + 1
            # valor a guardar
            valor = v
            value = ''
            if v != '': # sino esta vacio extraigo el valor
                for i in range(0,len(v)):
                    if valor[i] == ',':
                        value = value + '.'
                    else:
                        value = value + valor[i]
            else:
                value = 0
            Ahorros.objects.filter(idahorro=int(idAh)).update(ingreso=float(value))

        # Fijos
        # si # y no esta vacio
        # # 10.942.3.2022 
        if k[0] == '#' and v:
            # categoria
            c = ''
            d = 1
            while k[d] != '.':
                c = c + k[d]
                d = d + 1
            cat = Categorias.objects.filter(idcategoria=c)
            for cate in cat:
                categ = cate
            # producto
            idProd = ''
            p = d + 1
            while k[p] != '.':
                idProd = idProd + k[p]
                p = p + 1
            prod = Productos.objects.filter(idproducto=idProd)
            for pr in prod:
                myProd = pr
            # mes
            m = ''
            j = p + 1
            while k[j] != '.':
                m = m + k[j]
                j = j + 1
            # anio
            a = ''
            h = j+1
            while k[h] != '.':
                a = a + k[h]
                h = h + 1
            fecha = datetime.date(int(a), int(m), 1)
            # comercio
            com = Comercios.objects.filter(idcomercio=28)
            for co in com:
                comercio = co
            mov = Movimientos(fecha=fecha,usuario=user,comercio=comercio,producto=myProd,categoria=categ,cantidad=1,total=float(v),tipo=1,adjunto=None,notas=None)
            mov.save()

        # Update *
        if k[0] == '*' or (k[0] == '*' and v ==''):
            idMov = ''
            j = 2
            while k[j] != '.':
                idMov = idMov + k[j]
                j = j + 1
            # valor a guardar
            valor = v
            value = ''
            if v != '': # sino esta vacio extraigo el valor
                for i in range(0,len(v)):
                    if valor[i] == ',':
                        value = value + '.'
                    else:
                        value = value + valor[i]
            else:
                value = 0
            Movimientos.objects.filter(idmovimiento=int(idMov)).update(total=float(value))

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
            
        # Tarjetas
        # $cat.prod.mes.anio
        if k[0] == '$' and v:
            # categoria
            c = ''
            d = 1
            while k[d] != '.':
                c = c + k[d]
                d = d + 1
            cat = Categorias.objects.filter(idcategoria=c)
            for cate in cat:
                categ = cate
            # producto
            idProd = ''
            p = d + 1
            while k[p] != '.':
                idProd = idProd + k[p]
                p = p + 1
            prod = Productos.objects.filter(idproducto=idProd)
            for pr in prod:
                myProd = pr
            # mes
            m = ''
            j = p + 1
            while k[j] != '.':
                m = m + k[j]
                j = j + 1
            # anio
            a = ''
            h = j+1
            while k[h] != '.':
                a = a + k[h]
                h = h + 1
            fecha = datetime.date(int(a), int(m), 1)
            # comercio
            com = Comercios.objects.filter(idcomercio=28)
            for co in com:
                comercio = co
            mov = Movimientos(fecha=fecha,usuario=user,comercio=comercio,producto=myProd,categoria=categ,cantidad=1,total=float(v),tipo=1,adjunto=None,notas=None)
            mov.save()

        # & Update!
        if k[0] == '&' or (k[0] == '&' and v ==''):
            idMov = ''
            j = 2
            while k[j] != '.':
                idMov = idMov + k[j]
                j = j + 1
            # valor a guardar
            valor = v
            value = ''
            if v != '': # sino esta vacio extraigo el valor
                for i in range(0,len(v)):
                    if valor[i] == ',':
                        value = value + '.'
                    else:
                        value = value + valor[i]
            else:
                value = 0
            Movimientos.objects.filter(idmovimiento=int(idMov)).update(total=float(value))

        # Others
        # $cat.mes.anio
        if k[0] == '~' and v:
            # categoria
            c = ''
            d = 1
            while k[d] != '.':
                c = c + k[d]
                d = d + 1
            cat = Categorias.objects.filter(idcategoria=c)
            for cate in cat:
                categ = cate
            # producto -> '.'
            prod = Productos.objects.filter(idproducto=174)
            for pr in prod:
                myProd = pr
            # mes
            m = ''
            j = d + 1
            while k[j] != '.':
                m = m + k[j]
                j = j + 1
            # anio
            a = ''
            h = j+1
            while k[h] != '.':
                a = a + k[h]
                h = h + 1
            fecha = datetime.date(int(a), int(m), 1)
            # comercio
            com = Comercios.objects.filter(idcomercio=28)
            for co in com:
                comercio = co
            mov = Movimientos(fecha=fecha,usuario=user,comercio=comercio,producto=myProd,categoria=categ,cantidad=1,total=float(v),tipo=1,adjunto=None,notas=None)
            mov.save()

        # ? Update!
        if k[0] == '?' or (k[0] == '?' and v ==''):
            idMov = ''
            j = 2
            while k[j] != '.':
                idMov = idMov + k[j]
                j = j + 1
            # valor a guardar
            valor = v
            value = ''
            if v != '': # sino esta vacio extraigo el valor
                for i in range(0,len(v)):
                    if valor[i] == ',':
                        value = value + '.'
                    else:
                        value = value + valor[i]
            else:
                value = 0
            Movimientos.objects.filter(idmovimiento=int(idMov)).update(total=float(value))

        # es visible la categoria ?
        if k[0] == '^':
            idUserCat = ''
            for j in range(2,len(k)):
                if k[j] != '.':
                    idUserCat = idUserCat + k[j]
            UserCategoria.objects.filter(idUserCat=idUserCat).update(esVisible=int(v)) 

    # link para volver de confirmacion!
    try :
        link = request.POST['fijos']
    except:
        try :
            link = request.POST['cards']
        except:
            try :
                link = request.POST['kk']
            except:
                try :
                    link = request.POST['others']
                except:
                    link = 'res'
    return link

def obtenerDolarParaTarjeta():
    dolarTarjeta = []
    for m in range(0,14):
        anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
        if m == 0:
            m = 12
            anioHoy = anioHoy-1
        if m == 13:
            m = 1
            anioHoy = anioHoy + 1
        mesInput = Input(m, anioHoy)
        d = Dolar.objects.filter(fecha__month=m,fecha__year=anioHoy).last()
        if d == None:
            mesInput.valor = 0  
        else:
            myOf = d.venta
            mesInput.valor = round(d.venta,1)    
        dolarTarjeta.append(mesInput)
    mesHoy = int(date.today().strftime('%m'))  # en la fecha de hoy
    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
    for o in dolarTarjeta:
        if o.mes > mesHoy and o.anio >= anioHoy or o.anio > anioHoy:
            o.valor = myOf
    return dolarTarjeta  


    





