from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, \
                        HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api.models import Data, Tokens
import json, base64, hashlib, random, logging

logger = logging.getLogger(__name__)

"""
 Applications can request an API key to get data 
 from the Data collection
"""
def key_request(request):
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

"""
 Currently only accepts data from the iOS app 
 with the appropriate API key given with the request
"""
@csrf_exempt
def upload(request):
   if request.method == 'POST':
      try:
         json_data_top_level = json.loads(request.body)
      except:
         logger.error("Failed to load json from request body")
         return HttpResponseBadRequest(
            "The request cannot be processed. We couldn't find json in the body.\n")
      try:
         data_list = json_data_top_level['mapdata']
      except KeyError:
         logger.error("Failed to match mapdata key")
         return HttpResponseBadRequest(
            "The request cannot be processed. Your KEY does not match.\n")
      for json_data in data_list:
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
               elif key == "faces_detected":
                  data.faces_detected = json_data[key]
               elif key == "people_detected":
                  data.people_detected = json_data[key]              
            try:
               data.save()
            except:
               logger.error("Failed to save the sent data")
               return HttpResponseBadRequest(
                  "The request cannot be processed due to bad data types.\n")
         except KeyError:
            logger.error(
               "Failed to match keys from one or all of the dict in the list")
            return HttpResponseBadRequest(
               "The request cannot be processed due malformed JSON.\n")
      return HttpResponse("Data was received\n", status=201)
   else:
      logger.error("GET req can't be processed")
      return HttpResponse("You can only upload with POST you fool!\n")

"""			
 Send requested data to the third party application
"""
def download(request):
   pass
   
	
