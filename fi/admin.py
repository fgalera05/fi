from django.contrib import admin
from .models import *
@admin.register(UserCategoria)
class UserCategoria(admin.ModelAdmin):
	list_display = ('usuario', 'userCategoria', 'esVisible')
	list_filter = ('usuario','usuario')
@admin.register(Movimientos)
class Movimientos(admin.ModelAdmin):
	list_display = ('idmovimiento', 'categoria', 'producto')
	list_filter = ('categoria','categoria')
	
