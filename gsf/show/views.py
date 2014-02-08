from django.shortcuts import render
from django.http import HttpResponse
from show.models import Data
import datetime

def index(request):
	data = Data.objects
	return HttpResponse(data)

def insert(request):
	data = Data(name="Bardia Keyoumarsi")
	data.speech = "I have a dream that one day ..."
	data.save()
	return HttpResponse("Data was inserted, please go to index to see")

