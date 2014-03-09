from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, \
                        HttpResponseServerError, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django import forms
from api.models import Features, Properties, APIKey
import json, logging

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
      form = SignupForm(request.POST)
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
         recipient = [email]

         # Send email
         #from django.core.mail import send_mail
         #send_mail(subject, message, sender, recipient)
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
         if json_data_top_level['type'] != "FeatureCollection":
            logger.error("Failed to match type with FeaturedCollection")
            return HttpResponseBadRequest(
               "The request cannot be processed. Your geoJSON is malformed\n")
         features_list = json_data_top_level['features']
      except KeyError:
         logger.error("Failed to match type or features key")
         return HttpResponseBadRequest(
            "The request cannot be processed. Your geoJSON is malformed\n")
      for dictionary in features_list:
         try:
            # Set up variables to store proper data in the db
            feature = Features()
            feature.geometry = dictionary['geometry']
            properties_dict  = dictionary['properties']
            feature_property = Properties(source="iPhone")
            feature_property.timestamp = properties_dict['timestamp']
            # If any of the below are available add them to the Document
            for key in properties_dict.keys():
               if key == "altitude":
                  feature_property.altitude = properties_dict[key]
               elif key == "h_accuracy":
                  feature_property.h_accuracy = properties_dict[key]
               elif key == "v_accuracy":
                  feature_property.v_accuracy = properties_dict[key]
               elif key == "text":
                  feature_property.text = properties_dict[key]
               elif key == "oimage":
                  logger.debug("Found oimage tag")
                  feature_property.o_image = properties_dict[key]
               elif key == "pimage":
                  logger.debug("Found pimage tag")
                  feature_property.p_image = properties_dict[key]
               elif key == "fimage":
                  logger.debug("Found fimage tag")
                  feature_property.f_image = properties_dict[key]
               elif key == "noise_level":
                  feature_property.noise_level = properties_dict[key]
               elif key == "temperature":
                  feature_property.temperature = properties_dict[key]
               elif key == "humidity":
                  feature_property.humidity = properties_dict[key]
               elif key == "faces_detected":
                  feature_property.faces_detected = properties_dict[key]
               elif key == "people_detected":
                  feature_property.people_detected = properties_dict[key]              
            #try:
               feature.properties = feature_property
               feature.save()
            #except:
            #   logger.error("Failed to save the sent data")
            #   return HttpResponseBadRequest(
            #      "The request cannot be processed due to bad data types.\n")
         except KeyError:
            logger.error(
               "Failed to match keys from one or all of the dict in the list")
            return HttpResponseBadRequest(
               "The request cannot be processed due malformed geoJSON.\n")
      return HttpResponse("Data was received\n", status=201)
   else:
      logger.error("GET req can't be processed")
      return HttpResponse("You can only upload with POST you fool!\n")

"""			
 Send requested data to the third party application
"""
def download(request):
   pass
   
	
