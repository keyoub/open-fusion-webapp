from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from api.models import Data
import json

# Receive data from iOS app and store in db
def upload(request):
   if request.method == 'POST':
      json_data = json.loads(request.body)
      try:
         source = json_data['source']
      except KeyError:
         return HttpResponseServerError("Malformed data!")
      return HttpResponse("Got json data you said source: %s" % source)
   else: 
      return HttpResponse("Can't upload with GET request you fool")
			
# Send requested data to the third party application
def download(request):
   pass
   
	
