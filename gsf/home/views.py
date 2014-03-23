from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from gsf.settings import BASE_DIR
from pygeocoder import Geocoder
from ogre import OGRe
import os, io, json, time, hashlib, datetime


"""
   The UI input form for the twitter retriever
"""
class TwitterForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   addr     = forms.CharField(required=True, max_length=500, label='*Address',
                help_text='eg. Santa Cruz, CA or Mission st, San Francisco')
   radius   = forms.FloatField(required=True, label='*Radius',
                help_text='in Kilometers')
   t_from   = forms.DateTimeField(required=False, label='From',
               help_text='Enter starting date and time',
               widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
   t_to     = forms.DateTimeField(required=False, label='To',
               help_text='Enter ending date and time',
               widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
   text     = forms.BooleanField(required=False)
   images   = forms.BooleanField(required=False)

"""
   Helper function that builds the context for index.html 
"""
def form_errors(address_flag, no_result_flag, time_flag):
   form = TwitterForm()
   context = {
                'form': form,
                'address_flag': address_flag,
                'no_result_flag': no_result_flag,
                'time_flag': time_flag,
             }
   return context

"""
   The home page query UI controller.
      - Handles queries on local db
      - Handles queries for the retriever
"""
def index(request):
   if request.method == 'POST':
      form = TwitterForm(request.POST)
      
      # Get query parameters
      if form.is_valid():
         # Initialize variables and flags
         address_flag, no_result_flag, time_flag = False, False, False
         lat, lon = 0, 0
         
         # Get data from the from
         keywords = form.cleaned_data['keywords']
         addr = form.cleaned_data['addr']
         radius = form.cleaned_data['radius']
         t_from = form.cleaned_data['t_from']
         t_to = form.cleaned_data['t_to']
         text = form.cleaned_data['text']
         images = form.cleaned_data['images']
         
         # Get coordinates from the address entered
         try:
            results = Geocoder.geocode(addr)
            lat = float(results[0].coordinates[0])
            lon = float(results[0].coordinates[1])
         except:
            # If the geocoder API doesn't return with results
            # return the user to home page with the address error flag
            return render(request, 'home/index.html', 
                     form_errors(True, no_result_flag, time_flag))

         # Start building the query for the retriever
         params = {
                     "where": (lat, lon, radius, "km"),
                  }

         if images and text:
            params['what'] = ("text", "image")
         elif images:
            params['what'] = ("image",)
         else:
            params['what'] = ("text",)

         # Get time span and convert to epoch time
         if t_from and t_to:
            t_from = int(time.mktime(
               time.strptime(str(t_from)[:19], '%Y-%m-%d %H:%M:%S'))) - time.timezone
            t_to   = int(time.mktime(
               time.strptime(str(t_to)[:19], '%Y-%m-%d %H:%M:%S'))) - time.timezone
            params['when'] = (t_from, t_to)
         # Return to home page with error if only one field id provided
         elif t_from or t_to:
            return render(request, 'home/index.html', 
                     form_errors(address_flag, no_result_flag, True))

         # Get twitter data
         data = OGRe.get(("twitter",), keywords, params)

         # Return to home page if no tweets were found
         if not data['features']:
            return render(request, 'home/index.html', 
                     form_errors(address_flag, True, time_flag))

         # The center pin for the visualizer
         epicenter = {
                        "type": "FeatureCollection",
                        "features": [
                           { 
                              "type": "Feature",
                              "geometry": {
                                 "type": "Point",
                                 "coordinates": [lon, lat]
                              },
                              "properties": {
                                 "data": "Epicenter of tweets",
                                 "radius": (radius*1000)
                              }
                           }, 
                           data
                        ]
                      }

         # The complete JSON obj that gets written to .geoJSON file
         package = {
                     "type": "FeatureCollection",
                     "features": [epicenter]
                   }

         # Build unique output file name using user ip and timestamp
         try:
            ip = request.get_host()
         except:
            pass
         now = str(datetime.datetime.now())

         file_name = "points_" + \
            str(hashlib.sha1(ip+now).hexdigest()) + ".geojson"
         
         # Write data to the file
         path = os.path.join(BASE_DIR, 'static', 'vizit', 
                              'data', file_name)
         with io.open(path, 'w') as outfile:
            outfile.write(unicode(json.dumps(package,
               indent=4, separators=(",", ": "))))
         
         # redirect user to the visualizer
         # if mobile device detected, redirect to touchscreen version
         if request.mobile:
            redr_path = "/static/vizit/index.html?data=" + file_name
            return HttpResponseRedirect(redr_path)
         else:
            return render(request, 'home/vizit.html', {'file_name':file_name})
   else:
      form = TwitterForm()

   return render(request, 'home/index.html', {'form':form})
