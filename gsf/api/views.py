from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from api.models import Data
import json

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
         try:
            data.altitude = json_data['altitude']
            data.h_accuracy = json_data['h_accuracy']
            data.v_accuracy = json_data['v_accuracy']
            data.text = json_data['text']
            data.image = json_data['image']
            data.noise_level = json_data['noise_level']
            data.temperature = json_data['temperature']
            data.humidity = json_data['humidity']
            data.population = json_data['population']
         except:
            pass
         data.save()
      except KeyError:
         return HttpResponseServerError("The request cannot be processed\
                due to wrong JSON format.\n")
      return HttpResponse("Got json data. Here is what I saved: %s\n\n"\
                 % json.dumps(data), content_type="application/json")
   else: 
      return HttpResponse("You can only upload with POST")
			
# Send requested data to the third party application
def download(request):
   pass
   
	
