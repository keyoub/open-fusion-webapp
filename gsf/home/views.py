from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from django import forms
from gsf.settings import BASE_DIR
from pygeocoder import Geocoder
from ogre import OGRe
import os, io, json, time

"""def validate_addr(value):

   # Check if the address is valid
   if not Geocoder.geocode(value).valid_address:
      raise forms.ValidationError("Please enter a valid address")
"""
   
      

class TwitterForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   #lat      = forms.FloatField(label='Latitude', required=True )
   #lon      = forms.FloatField(label='Longitude', required=True )
   addr     = forms.CharField(required=True, max_length=500, label='Address',
                help_text='eg. Santa Cruz, CA or Mission st, San Francisco')
   radius   = forms.FloatField(required=True)
   t_from   = forms.DateTimeField(label='From', required=False,
                                  input_formats=['%Y-%m-%d %H:%M:%S'])
   t_to     = forms.DateTimeField(label='To', required=False,
                                  input_formats=['%Y-%m-%d %H:%M:%S'])
   #text     = forms.BooleanField()
   #images   = forms.BooleanField()

def index(request):
   if request.method == 'POST':
      form = TwitterForm(request.POST)
      
      if form.is_valid():
         lat, lon = 0, 0
         keywords = form.cleaned_data['keywords']
         #lat = form.cleaned_data['lat']
         #lon = form.cleaned_data['lon']
         addr = form.cleaned_data['addr']
         radius = form.cleaned_data['radius']
         t_from = form.cleaned_data['t_from']
         t_to = form.cleaned_data['t_to']

         results = Geocoder.geocode(addr)

         lat = float(results[0].coordinates[0])
         lon = float(results[0].coordinates[1])

         params = {
                     "where": (lat, lon, radius, "km"),
                     "what" : ("text",)
                  }
         
         # Get time span and convert to epoch time
         if t_from and t_to:
            t_from = int(time.mktime(
               time.strptime(str(t_from)[:19], '%Y-%m-%d %H:%M:%S'))) - time.timezone
            t_to   = int(time.mktime(
               time.strptime(str(t_to)[:19], '%Y-%m-%d %H:%M:%S'))) - time.timezone
            params['when'] = (t_from, t_to)
         
         # Get twitter data
         data = OGRe.get(("twitter",), keywords, params)
         
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
         path = os.path.join(BASE_DIR, 'static', 'vizit', 
                              'data', 'test.geojson')
         with io.open(path, 'w') as outfile:
            outfile.write(unicode(json.dumps(package, indent=4, separators=(",", ": "))))

         temp = json.dumps(package, indent=4, separators=(",", ": "))

         return HttpResponseRedirect('/static/vizit/index.html?data=test.geojson')
   else:
      form = TwitterForm()

      return render(request, 'home/index.html', {'form':form})
