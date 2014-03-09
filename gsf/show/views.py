from django.shortcuts import render
from django.http import HttpResponse
from api.models import Features
import datetime, random

def index(request):
	data = Features.objects.all()
	context = {'data' : data}
	return render(request, 'show/index.html', context)

