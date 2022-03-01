from fi.models import * 
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
from datetime import date
import datetime
from django.db import connection
from .models import *

def webScrapDolar(url):
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	soup = BeautifulSoup(response.text, 'lxml')
	valor = soup.find_all('div', class_="value")

	p = [] #guardo en la lista los objetos como bs4
	for x in valor:
	    p.append(str(x))
	return p

def obtenerValorDolarBlue(): #recibe el indice de la lista: [dolarBajo, dolarAlto]
	p = webScrapDolar('https://dolarhoy.com/cotizaciondolarblue')

	n = [] 
	for i in p[0]: #me fijo que es digito - venta
		if i.isdigit():
			n.append(i)

	v = 0 #convierto a numero n
	j = 1
	for i in range(0, len(n)):
		v += int(n[i]) * 100 /j
		j*= 10

	n = [] 
	for i in p[1]: #me fijo que es digito - compra
		if i.isdigit():
			n.append(i)

	c = 0 #convierto a numero n
	j = 1
	for i in range(0, len(n)):
		c += int(n[i]) * 100 /j
		j*= 10

	p = webScrapDolar('https://dolarhoy.com/cotizaciondolaroficial')

	n = [] 
	for i in p[1]: #me fijo que es digito - mas alto->compra
		if i.isdigit():
			n.append(i)

	of = 0 #convierto a numero n
	j = 1
	for i in range(0, len(n)):
		of += int(n[i]) * 100 /j
		j*= 10

	imp1 = 0.30
	imp2 = 0.35	
	of = round(of+of*imp1+ of*imp2, 2)
	return [v, c, of]












