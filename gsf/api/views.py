from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api.models import Data
import json


@csrf_exempt
# Receive data from iOS app and store in db
def upload(request):
   if request.method == 'POST':
      json_data = json.loads(request.body)
      try:
         # Get required data from the JSON obj
         data = Data(source="iPhone")
         data.location = json_data['location']
         data.timestamp = json_data['timestamp']
         # If any of the below are available add them to the Document
         for key in json_data.keys():
            if key == "altitude":
               data.altitude = json_data[key]
            elif key == "h_accuracy":
               data.h_accuracy = json_data[key]
            elif key == "v_accuracy":
               data.v_accuracy = json_data[key]
            elif key == "text":
               data.text = json_data[key]
            elif key == "image":
               data.image = json_data[key]
            elif key == "noise_level":
               data.noise_level = json_data[key]
            elif key == "temperature":
               data.temperature = json_data[key]
            elif key == "humidity":
               data.humidity = json_data[key]
            elif key == "population":
               data.population = json_data[key]
         data.save()
      except KeyError:
         return HttpResponseServerError(
         "The request cannot be processed due to wrong JSON format.\n")
      return HttpResponse("Got json data.")
   else: 
      return HttpResponse("You can only upload with POST")
			
# Send requested data to the third party application
def download(request):
   pass
   
	
