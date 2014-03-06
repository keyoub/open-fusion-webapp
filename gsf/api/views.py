from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, \
                        HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django import forms
from api.models import Data, APIKey
import json, base64, hashlib, random, logging

"""try:
   from modules import *
except ImportError:
   pass"""

logger = logging.getLogger(__name__)

"""
 The Sign up form for the developers API key
"""
class SignupForm(forms.Form):
   developer_name = forms.CharField(required=True)
   organization = forms.CharField()
   application_name = forms.CharField(required=True)
   email = forms.EmailField(required=True)
   
"""
 Process developer request for an API key
"""
def dev_signup(request):
   if request.method == 'POST':
      form = ContactForm(request.POST)
      if form.is_valid():
         dev_name = form.cleaned_data['developer_name']         
         organization = form.cleaned_data['organization']         
         app_name = form.cleaned_data['application_name']         
         email = form.cleaned_data['email']

         # Generate API key
         key_req = APIKey(application=app_name)
         key_req.organization = organization
         key_req.dev_name = dev_name
         key_req.email = email
         key_req.save()

         # Prepare email
         sender = ['admin@gsf.soe.ucsc.edu']
         message = ("Thank you for signing up for an API Key.\n\n" +
                   "Your Key: %s ") % key_req.key
         subject = "Your Geotagged Sensor Fusion API Key"

         # Send email
         from django.core.email import send_mail
         send_mail(subject, message, sender, email)
         return HttpResponseRedirect('/')
   else:
      form = SignupForm()
            
   return render(request, 'api/devsignup.html', 
      {'form': form,}
   )

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
   
	
