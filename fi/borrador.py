 # Categorias
    listaCatComparativo = [] # Grafico comparativo de categorias 
    listCat = []
    cat = UserCategoria.objects.all().filter(usuario=user)# categorias que usa el usuario
    p = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=tipo).aggregate(Sum('total'))# ingresos!
    if p['total__sum'] is None: 
            p['total__sum'] = 1
    saldoPresupuesto = p['total__sum'] # torta
    listaTorta = [] # torta
    listaNombres = [] # nombres torta
    for c in cat:
        t = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,
                                             categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# saldo por categoria
        r = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=tipo,
                                             categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# ingreso por categoria
        g = Movimientos.objects.all().filter(fecha__month=mes, usuario=user, fecha__year=anio,tipo=gasto,
                                             categoria=c.userCategoria.idcategoria).aggregate(Sum('total'))# gasto por categoria
        if t['total__sum'] is None:
            t['total__sum'] = 0
        if r['total__sum'] is None:
            r['total__sum'] = 0
        if g['total__sum'] is None:
            g['total__sum'] = 0
        u = Movimientos.nuevoMovimiento(c.userCategoria, round(t['total__sum'],user), 2)# new Mov()
        color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) # color de categorias
        movAux = MovimientoAux(u, round(r['total__sum']), round(-g['total__sum'], 2), color)# new MovAux(Mov, TotalIngreso, TotalGasto, color)
        listCat.append(movAux)
        


        # Torta
        listaColores = []
        listaPorc = []
        #listaTorta.append(movAux)
        saldoPresupuesto = saldoPresupuesto - movAux.gasto
    #listaTorta.sort()
    listCat.sort()