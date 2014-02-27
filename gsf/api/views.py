from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, \
                        HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api.models import Data, Tokens
import json, base64, hashlib, random

def token_request(request):
   if request.method == 'GET':
      application = request.GET.get('application')
      organization = request.GET.get('organization')
      dev_fullname = request.GET.get('developer')
      if not application or not dev_fullname:
         return HttpResponseBadRequest("Can't process request due to missing info.\n")
      # Check if the token for the app already exist
      if not Tokens.objects(application__exists=application):     
         # Generate secret token
         key = base64.b64encode(hashlib.sha256( \
                   str(random.getrandbits(256)) ).digest(), \
                   random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
         entry = Tokens(api_key=key) 
         entry.application = application
         entry.organization = organization
         entry.dev_fullname = dev_fullname
         try:
            entry.save()
            response_data = {}
            response_data['key'] = key
            return HttpResponse(json.dumps(response_data),
                                  content_type="application/json")
         except:
            return HttpResponseServerError("Your request could not be completed due"\
                        " to internal errors. Try again later.")
      else:
         return HttpResponse("You already have a token with us. If you have " \
                       "lost it please contact bkeyouma@ucsc.edu")
   else:
      return HttpResponseBadRequest("You can only get a token with GET request.\n")

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
         try:
            data.save()
         except:
            return HttpResponseBadRequest(
               "The request cannot be processed due to wrong JSON format.\n")
      except KeyError:
         return HttpResponseBadRequest(
            "The request cannot be processed due to wrong JSON format.\n")
      return HttpResponse("Got json data.\n")
   else: 
      return HttpResponse("You can only upload with POST you fool!\n")
			
# Send requested data to the third party application
def download(request):
   pass
   
	
