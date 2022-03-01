from django.db import models
from datetime import datetime
from django.db import connection
from .dolar import *
from django.db.models import Sum
from colormap import hex2rgb
import random

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'

class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)

class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)

class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'

class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)

class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)

class Categorias(models.Model):
    idcategoria = models.AutoField(db_column='IdCategoria', primary_key=True)  # Field name made lowercase.
    categoria = models.CharField(db_column='Categoria', max_length=100, blank=True, null=True)  # Field name made lowercase.
    tarjeta = models.IntegerField(db_column='tarjeta')
    pagoDolar = models.BooleanField(db_column='pagoDolar')
    saldo = 0 # agregados para index!!!
    gastos = 0
    presupuesto = 0
    color = None
    rgb = None
    porcentaje = 0
    barra = None
    pago = False

    class Meta:
        managed = False
        db_table = 'categorias'

    def __str__(self):
        return self.categoria +', ' +str(self.tarjeta)

    def __gt__(self, cat):
        return self.categoria > cat.categoria

    def obtenerCategoriasTarjeta():
        tarjetas = Categorias.objects.all().filter(tarjeta=1)
        return tarjetas

    def nuevaCategoria():
        c = Categorias(idcategoria=0, categoria="",tarjeta=0)
        c.categoria = ""
        c.saldo = 0
        c.porcentaje = 0
        c.rgb = None
        c.barra = None
        return c

class Comercios(models.Model):
    idcomercio = models.AutoField(db_column='IdComercio', primary_key=True)  # Field name made lowercase.
    comercio = models.CharField(db_column='Comercio', max_length=100, blank=True, null=True)  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'comercios'

    def __str__(self):
        return self.comercio

    def __gt__(self, otro):
        return self.comercio > otro.comercio

class Cotizacion(models.Model):
    idcotizacion = models.AutoField(db_column='idCotizacion', primary_key=True)  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.
    compra = models.FloatField(db_column='Compra')  # Field name made lowercase.
    venta = models.FloatField(db_column='Venta')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'cotizacion'
        ordering = ['fecha']

    def __str__(self):
        return str(self.idcotizacion)+ ', ' +self.fecha.strftime("%d-%m-%Y") +', ' +str(self.venta)+', ' +str(self.compra)
    
    def guardarValorDolar(v, c):
        dif = 0 
        myDolar = Cotizacion.objects.all().last()
        today = date.today()
        miCambio = MiCambio.objects.all().last()

        if myDolar.fecha != today: #registro el dia sino lo tengo
            d = Cotizacion(fecha=today, venta=v, compra=c)
            d.save()

        if myDolar.venta != v or myDolar.compra != c:
            d = Cotizacion(idcotizacion=myDolar.idcotizacion,fecha=today, venta=v, compra=c)
            d.save()
        dif = myDolar.venta - miCambio.cambio
        return round(dif,2)

    def valoresHistoricoDolar():
        valores = []
        for i in range(0,14):
            anio = int(date.today().strftime('%Y'))
            mes = i
            if i == 0:
                mes = 12
                anio = anio - 1
            myDolar = Cotizacion.objects.all().filter(fecha__year=anio, fecha__month=mes).last()
            if myDolar != None:
                if myDolar.compra != None:  
                    valores.append(myDolar.compra)
                else:
                    valores.append(0)
            else:
                valores.append(0)
        return valores

class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'

class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)

class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class Dolar(models.Model):
    iddolar = models.AutoField(db_column='idDolar', primary_key=True)  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.
    compra = models.FloatField(db_column='compra')  # Field name made lowercase.
    venta = models.FloatField(db_column='venta')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'dolar'

    def guardarDolarOficial(o):
        myDolar = Dolar.objects.all().last()
        today = date.today()
        if myDolar.fecha != today: #registro el dia sino lo tengo
            d = Dolar(fecha=today, venta=o, compra=None)
            d.save()

        if myDolar.venta != o:
            d = Dolar(idcotizacion=myDolar.iddolar,fecha=today, venta=o, compra=None)
            d.save()

class MiCambio(models.Model):
    idcambio = models.AutoField(db_column='idCambio', primary_key=True)  # Field name made lowercase.
    cambio = models.FloatField(db_column='Cambio')  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'micambio'

class Usuarios(models.Model):
    id_user = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    name_user = models.CharField(max_length=50)
    password = models.BinaryField(max_length=500)
    email = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=13, blank=True, null=True)
    foto = models.CharField(max_length=100, blank=True, null=True)
    permisos_acceso = models.CharField(max_length=11)
    status = models.CharField(max_length=9)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    login = False

    class Meta:
        managed = False
        db_table = 'usuarios'

    def __str__(self):
        return self.username

    def existe(usuario):
        u = Usuarios.objects.filter(username=usuario)
        if u != None:
            for us in u:
                return us
        else:
            return None

class Sales(models.Model):
    idSal = models.AutoField(db_column='idSal', primary_key=True)  # Field name made lowercase.
    sal = models.BinaryField(db_column='Sal', max_length=250, blank=True, null=True)
    usuario = models.ForeignKey(Usuarios, db_column='usuario',on_delete=models.CASCADE) # Field name made lowercase.
    

    class Meta:
        managed = False
        db_table = 'sales'

class Ahorros(models.Model):
    idahorro = models.AutoField(db_column='idAhorro', primary_key=True)  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.
    anterior = models.FloatField(db_column='Anterior', blank=True, null=True)  # Field name made lowercase.
    ingreso = models.FloatField(db_column='Ingreso', blank=True, null=True)  # Field name made lowercase.
    usuario = models.ForeignKey(Usuarios, db_column='usuario',on_delete=models.CASCADE) # Field name made lowercase.
    ahorro = models.FloatField(db_column='Ahorro', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ahorros'

    def __str__(self):
        return self.fecha.strftime("%d-%m-%Y")+', '+ str(self.ingreso)

    def obtenerAhorrosPorMes(mes, user, anio):
        ah = Ahorros.objects.all().filter(fecha__month=mes, usuario = user, fecha__year=anio)
        return ah

class Productos(models.Model):
    idproducto = models.AutoField(db_column='IdProducto', primary_key=True)  # Field name made lowercase.
    nombreproducto = models.CharField(db_column='NombreProducto', max_length=255)  # Field name made lowercase.
    marca = models.CharField(db_column='Marca', max_length=255, blank=True, null=True)  # Field name made lowercase.
    categoria = models.ForeignKey(Categorias, db_column='categoria',on_delete=models.CASCADE)
    subcategoria = models.IntegerField(db_column='Subcategoria', blank=True, null=True)  # Field name made lowercase.
    prom = 0
    primero = 0
    ultimo = 0
    dif = 0
    fechaPrimero = None
    fechaPrimero = None
    sub = Categorias

    class Meta:
        managed = False
        db_table = 'productos'
        ordering = ['idproducto']

    def __str__(self):
        return str(self.idproducto)+', '+self.nombreproducto

    def __gt__(self,otro):
        return self.nombreproducto > otro.nombreproducto

    def obtenerVarios(user, cat):
        movimientos = []
        nombres = []
        valores = []
        colores = []
        t = Movimientos.objects.all().filter(categoria=cat,usuario=user,tipo=2).aggregate(Sum('total'))
        total = -t['total__sum']
        mov = Movimientos.objects.all().filter(categoria=cat, usuario=user, tipo=2)
        for m in mov:
            try:
                if m.producto not in movimientos:
                    movimientos.append(m.producto) # lista con los movimientos que son cat=6
            except:
                continue
        for j in movimientos:  
            m = Movimientos.objects.all().filter(categoria=cat,usuario=user,producto=j.idproducto, tipo=2).aggregate(Sum('total'))
            if m['total__sum'] is not None:
                nombres.append(j.nombreproducto)
                valores.append(round( -m['total__sum']*100/total, 2))
                colores.append('rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])))))
        return [nombres,valores,colores]

    def obtenerProductosTorta(user):
        movimientos = []
        nombres = []
        valores = []
        colores = []
        t = Movimientos.objects.all().filter(usuario=user,tipo=2).aggregate(Sum('total'))
        total = -t['total__sum']
        mov = Movimientos.objects.all().filter(usuario=user, tipo=2)
        
        for m in mov:
            try:
                if m.categoria.idcategoria != 6 and m.categoria.idcategoria != 10 and m.categoria.idcategoria != 11 and m.categoria.idcategoria != 12 and m.producto not in movimientos:
                    movimientos.append(m.producto)
            except:
                continue

        for j in movimientos:  
            try:
                m = Movimientos.objects.all().filter(usuario=user,producto=j.idproducto, tipo=2).aggregate(Sum('total'))
                if m['total__sum'] is not None:
                    nombres.append(j.nombreproducto)
                    valores.append(round( -m['total__sum']*100/total, 2))
                    colores.append('rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])))))
            except:
                continue
        return [nombres,valores,colores]
      
class Personales(models.Model):
    idPersonal = models.AutoField(db_column = 'idPersonal', primary_key=True)
    usuario = models.ForeignKey(Usuarios, db_column='usuario',on_delete=models.CASCADE)
    producto = models.ForeignKey(Productos, db_column='producto',on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categorias, db_column='categoria',on_delete=models.CASCADE)
    banco = models.IntegerField()
    visible = models.IntegerField()
    valores = []

    class Meta:
        managed = False
        db_table = 'personales'
        ordering = ['idPersonal']

    def esTarjeta(self):
        bancoBool = ' '
        if self.banco == 1:
            bancoBool = 'BANCO'
        return bancoBool

    def __str__(self):
        return 'id:'+str(self.idPersonal)+',user:'+self.usuario.username + ',idprod:' + str(self.producto.idproducto) + ',cat:' + self.categoria.categoria +', bk:'+ (self.esTarjeta()) + str(self.categoria.tarjeta)

    def __gt__(self, otro):
        return self.producto > otro.producto

    def obtenerPersonalesBanco(user):
        bancos = Personales.objects.all().filter(banco=1,usuario=user)
        return bancos

class Movimientos(models.Model):
    idmovimiento = models.AutoField(primary_key=True,db_column='IdMovimiento')  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.
    comercio = models.ForeignKey(Comercios, db_column='comercio',on_delete=models.CASCADE)  # Field name made lowercase.
    producto = models.ForeignKey(Productos, db_column='producto',on_delete=models.CASCADE) # Field name made lowercase.
    categoria = models.ForeignKey(Categorias, db_column='categoria',on_delete=models.CASCADE)  # Field name made lowercase.
    cantidad = models.FloatField(db_column='Cantidad', blank=True, null=True)  # Field name made lowercase.
    total = models.FloatField(db_column='Total', blank=True, null=True)  # Field name made lowercase.
    tipo = models.IntegerField(db_column='Tipo')  # Field name made lowercase.
    adjunto = models.TextField(db_column='Adjunto', blank=True, null=True)  # Field name made lowercase.
    usuario = models.IntegerField(db_column='Usuario')  # Field name made lowercase.
    notas = models.TextField(db_column='Notas', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'movimientos'
        ordering = ['idmovimiento']

    def __str__(self):
        return str(self.idmovimiento) + ", " + self.categoria.categoria + ", " +self.fecha.strftime("%d-%m-%Y")+', '+str(self.total)+', '+self.producto.nombreproducto

    def __gt__(self, otro):
        return self.fecha < otro.fecha

    def guardarMovimiento(cm,pd,ct,fecha,cant,precio,notas,user,tipo):
        com = Comercios.objects.all().filter(idcomercio=cm)
        for c in com:
            comercio = c

        prod = Productos.objects.all().filter(nombreproducto=pd)
        for p in prod:
            producto = p

        cat = Categorias.objects.all().filter(idcategoria=ct)
        for c in cat:
            categoria = c

        mov = Movimientos(fecha=fecha,comercio=comercio,producto=producto,categoria=categoria,cantidad=cant,total=precio,
            tipo=tipo,adjunto=None,usuario=user,notas=notas)
        
        mov.save()

    def obtenerTotalPorMes(mes, user, anio, tipo):
        m = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=tipo).aggregate(Sum('total'))# presupuesto del mes
        if m['total__sum'] is None and tipo == 2: 
            m['total__sum'] = 0
        if m['total__sum'] is None and tipo == 1: 
            m['total__sum'] = 1
        if m['total__sum'] < 0:
            m['total__sum'] = - m['total__sum']
        return round(float(m['total__sum']),2)

    def obtenerSaldoPorMes(mes, user, anio):
        s = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio).aggregate(Sum('total'))# saldo del mes
        if s['total__sum'] is None: 
            s['total__sum'] = 0
        return round(float(s['total__sum']),2)

    def obtenerDepositosPorMes(mes,user,anio,tipo,number):
        mes +=1 #busco el mes siguiente
        bancos = Personales.obtenerPersonalesBanco(user)
        bk = 0
        for i in bancos:
            if i.banco:
                queryBanco = "SELECT total FROM `movimientos` WHERE month(fecha)=" + str(mes) + " and YEAR(fecha)=" + str(anio) + " and tipo=" + str(tipo) + " and producto =" + str(i.producto.idproducto) + " and usuario=" + str(user)
                with connection.cursor() as cursor:
                    cursor.execute(queryBanco)
                    row = cursor.fetchall() #row es una tupla doble
                    n = [r[0] for r in row] #magia para el nombre!!!
                    for v in n: #es necesario para extrater de la lista:[valor]
                        bk += v #hasta aca como arme la base, tengo los depositos que no son tarjetas!!!!
        #Mis tarjetas
        tarjetas = Categorias.obtenerCategoriasTarjeta()
        for cat in tarjetas:
            if cat.tarjeta == 1:
                querytarjeta = "SELECT total FROM `movimientos` WHERE month(fecha)=" + str(mes) + " and YEAR(fecha)=" + str(anio) + " and tipo=" + str(tipo) + " and usuario=" + str(user) +" and categoria="+ str(cat.idcategoria)
                #print(querytarjeta)
            with connection.cursor() as cursor:
                cursor.execute(querytarjeta)
                row2 = cursor.fetchall() 
                n2 = [r2[0] for r2 in row2] 
                for v2 in n2: 
                    bk += v2 
        return round(bk,2)

    def obtenerDepositosPorMes2(mes,user,anio):
        mes +=1 #busco el mes siguiente
        bancos = Personales.obtenerPersonalesBanco(user)
        bk = 0
        for i in bancos:
            if i.banco:
                b = Movimientos.objects.filter(fecha__month=mes,fecha__year=anio,tipo=1,usuario=user,producto=i.producto).aggregate(Sum('total'))
                if b['total__sum'] is None:
                    b['total__sum'] = 0.00
                bk += b['total__sum']
        #Mis tarjetas
        tarjetas = Categorias.obtenerCategoriasTarjeta()
        for cat in tarjetas:
            if cat.tarjeta == 1:
                c = Movimientos.objects.filter(fecha__month=mes,fecha__year=anio,tipo=1,usuario=user,categoria=cat).aggregate(Sum('total'))
                if c['total__sum'] is None:
                    c['total__sum'] = 0.00
                bk += c['total__sum']
  
        return round(bk,2)

    def obtenerDepositos(user, prod):
        # si prod es True devuelve (bk, productos) sino bk
        bancos = Personales.obtenerPersonalesBanco(user) # ya verifica que banco = 1!!
        bk = [0,0,0,0,0,0,0,0,0,0,0,0,0,0] # totales por mes
        productos = []
        for b in bancos:
            b.valores =[]
            for m in range(0,14):
                k = m
                anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
                k = m # para que no me pise el mes 
                if m == 0:
                    m = 12
                    anioHoy = anioHoy - 1
                if m == 13:
                    m = 1
                    anioHoy = anioHoy + 1
                m = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,producto=b.producto).aggregate(Sum('total'))
                if m['total__sum'] is None:
                    m['total__sum'] = 0.00
                bk[k] = bk[k] + round(m['total__sum'],2)
                b.valores.append(round(m['total__sum'],2))
            productos.append(b)
        productos.sort()   
        tarjetas = Categorias.obtenerCategoriasTarjeta()
        for cat in tarjetas:
            if cat.tarjeta == 1:
                cat.valores =[]
                for m in range(0,14):
                    k = m
                    anioHoy = int(date.today().strftime('%Y'))  # en la fecha de hoy
                    k = m # para que no me pise el mes 
                    if m == 0:
                        m = 12
                        anioHoy = anioHoy - 1
                    if m == 13:
                        m = 1
                        anioHoy = anioHoy + 1
                    m = Movimientos.objects.filter(fecha__month=m,fecha__year=anioHoy,tipo=1,usuario=user,categoria=cat).aggregate(Sum('total'))
                    if m['total__sum'] is None:
                        m['total__sum'] = 0.00
                    bk[k] = round(bk[k] + m['total__sum'],2)
                    cat.valores.append(round(m['total__sum'],2))
                productos.append(cat)
        if prod:
            return (bk, productos)
        else:
            return bk

class Saldo(models.Model):
    idsaldo = models.AutoField(db_column='idSaldo', primary_key=True)  # Field name made lowercase.
    fecha = models.DateField(db_column='Fecha')  # Field name made lowercase.
    saldo = models.FloatField(db_column='Saldo')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'saldo'

class Tarjetas(models.Model):
    usuario = models.ForeignKey(Usuarios, db_column='usuario',on_delete=models.CASCADE)
    categ = models.ForeignKey(Categorias, db_column='categoria',on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tarjetas'

    def __str__(self):
        return self.usuario.username +', '+self.categoria.categ

class Tipos(models.Model):
    idtipo = models.AutoField(db_column='IdTipo', primary_key=True)  # Field name made lowercase.
    tipo = models.CharField(db_column='Tipo', max_length=8, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tipos'

    def __str__(self):
        return self.tipo

class Tmp(models.Model):
    idTempt = models.AutoField(primary_key=True,db_column='id')
    comercio = models.ForeignKey(Comercios, db_column='comercio',on_delete=models.CASCADE)  # Field name made lowercase.
    producto = models.ForeignKey(Productos, db_column='producto',on_delete=models.CASCADE) # Field name made lowercase.
    categoria = models.ForeignKey(Categorias, db_column='categoria',on_delete=models.CASCADE)  # Field name made lowercase.
    cantidad = models.FloatField(db_column='Cantidad')  # Field name made lowercase.
    total = models.FloatField(db_column='Total')  # Field name made lowercase.
    tipo = models.IntegerField(db_column='Tipo')  # Field name made lowercase.
    adjunto = models.TextField(db_column='Adjunto', blank=True, null=True)  # Field name made lowercase.
    usuario = models.IntegerField(db_column='Usuario')  # Field name made lowercase.
    notas = models.TextField(db_column='Notas', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tmp'

    def __str__(self):
        return self.producto.nombreproducto+self.comercio.comercio+self.categoria.categoria

    def guardarMovimientoTmp(cm,pd,ct,cant,precio,notas,user,tipo):
        com = Comercios.objects.all().filter(idcomercio=cm)
        for c in com:
            comercio = c

        prod = Productos.objects.all().filter(nombreproducto=pd)
        for p in prod:
            producto = p

        cat = Categorias.objects.all().filter(idcategoria=ct)
        for c in cat:
            categoria = c

        tmp = Tmp(comercio=comercio,producto=producto,categoria=categoria,cantidad=cant,total=precio,
        tipo=tipo,adjunto=None,usuario=user,notas=notas)
        tmp.save()

class UserCategoria(models.Model):
    idUserCat = models.AutoField(db_column='id', primary_key=True) 
    usuario = models.ForeignKey(Usuarios, db_column='usuario',on_delete=models.CASCADE)
    userCategoria = models.ForeignKey(Categorias, db_column='user_categoria',on_delete=models.CASCADE)
    esVisible = models.BooleanField(db_column='esVisible')

    class Meta:
        managed = False
        db_table = 'usercategoria'
        ordering = ['userCategoria']

    def __str__(self):
        return self.userCategoria.categoria +', '+str(self.usuario)+', '+str(self.userCategoria.gastos)
        
    def __gt__(self, otro):
        return self.userCategoria > otro.userCategoria

class UserCategoriaAux: # Torta
    #clase aux para crear una lista = [Movimientos, totalDeIngreso, etc]
    categoria = ""
    presupuesto = 0.0
    saldo = 0
    porcentaje = 0
    rgb = ""
    visible = True
    valores = []

    def __init__(self, categoria, presupuesto,saldo, porcentaje, rgb):
        self.categoria = categoria
        self.presupuesto = presupuesto
        self.saldo = saldo
        self.porcentaje = porcentaje
        self.rgb = rgb
        self.visible = True
        self.valores = []
    
    def __gt__(self,otro):
        return self.categoria > otro.categoria

    def __repr__(self):
        return self.categoria+', '+str(self.presupuesto)+', '+self.rgb
   
class DatasetsBarra:
    anio = ""
    data = []
    backgroundColor = ""

    def __init__(self, anio, data):
        self.anio = anio
        self.data = data
        self.backgroundColor = 'rgb'+''.join(str(hex2rgb("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]))))

class GraficoBarras:
    categoria = Categorias
    producto = Productos
    data = [] # lista de DatasetsBarra
    myChart = ""
    etiquetas = ""
    etiquetasValores = []
    ctx = ""

    def __init__(self, categoria, i, producto):
        self.categoria = categoria
        self.producto = producto
        self.data = []
        self.myChart = 'myChart'+''.join(str(i))
        self.etiquetas = 'etiquetas'+''.join(str(i))
        self.etiquetasValores = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
        self.ctx = 'ctx'+''.join(str(i))

    def __repr__(self):
        return self.categoria.categoria+', '+ self.myChart

    def __gt__(self, otro):
        return self.categoria.categoria > otro.categoria.categoria

class Input:
    # la uso para los presupuestos !
    mes = 0
    anio = 0
    valor = 0
    name = ''
    idMov = 0
    cat = 0

    def __init__(self, mes,anio):
        self.anio = anio
        self.mes = mes
        self.valor = 0
        self.name = ''
        self.idMov = 0
        self.cat = 0

    def __gt__(self, otro):
        return self.name > otro.name

class ProdAux:
    # clase aux para los resumenes de autos, etc 
    prod = Productos
    anio = 0
    lista = []
    suma = 0

    def __init__(self, producto):
        self.prod = producto
        self.anio = 0
        self.lista = []
        self.suma = 0

    def __gt__(self, otro):
        return self.prod > otro.prod

