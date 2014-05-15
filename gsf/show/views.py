from django.shortcuts import render
from django.http import HttpResponse
from api.models import Features, OgreQueries
import datetime, random

def index(request):
   data = Features.objects()
   context = {'data' : data}
   return render(request, 'show/index.html', context)

def queries(request):
   data = OgreQueries.objects()
   context = {'data' : data}
   return render(request, 'show/queries.html', context)
