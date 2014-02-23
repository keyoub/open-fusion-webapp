from django.shortcuts import render
from django.http import HttpResponse
from api.models import Data
import datetime, random

def index(request):
	#data = Data.objects.all()
	context = {'data' : 'test'}
	return render(request, 'index.html', context)

def insert(request):
	#data = Data(source="iOS App")
	#data.latitude = random.uniform(-100, 100)
	#data.longitude = random.uniform(-100, 100)
	#data.temperature = random.uniform(0, 105)
	#data.save()
	return HttpResponse("Data was NOT inserted, visit <a href=\"/show/\">main page</a> to view.")

