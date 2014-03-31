from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from gsf.settings import BASE_DIR, TWITTER_CONSUMER_KEY, \
                         TWITTER_ACCESS_TOKEN
from pygeocoder import Geocoder
from ogre import OGRe
import os, io, json, time, hashlib, datetime


retriever = OGRe ({
   'Twitter': {
      'consumer_key': TWITTER_CONSUMER_KEY,
      'access_token': TWITTER_ACCESS_TOKEN,
   }
})

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
         lat, lon = 0.0, 0.0
         params = {"what":None,"where":None}
         
         # Get data from the from
         keywords = form.cleaned_data['keywords']
         addr = form.cleaned_data['addr']
         radius = form.cleaned_data['radius']
         t_from = form.cleaned_data['t_from']
         t_to = form.cleaned_data['t_to']
         text = form.cleaned_data['text']
         images = form.cleaned_data['images']

         # Get coordinates from the address entered
         if addr:
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
            params['where'] = (lat, lon, radius, "km")

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
         data = None
         try:
            data = retriever.get(("Twitter",),
                                 keyword=keywords, 
                                 what=params['what'],
                                 where=params['where'])
         except:
            pass

         # Return to home page if no tweets were found
         if not data or not data['features']:
            return render(request, 'home/index.html', 
                     form_errors(address_flag, True, time_flag))

         # The center pin for the visualizer
         package =   {
                        "OpenFusion": "1",
                        "type": "FeatureCollection",
                        "features": [
                           { 
                              "type": "Feature",
                              "geometry": {
                                 "type": "Point",
                                 "coordinates": [lon, lat]
                              },
                              "properties": {
                                 "radius": (radius*1000),
                                 "related": data,
                              }
                           }
                        ]
                     }

         # Build unique output file name using user ip and timestamp
         ip = ""
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

"""
   The Epicenters UI
"""
class EpicentersForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   text     = forms.BooleanField(required=False)
   images   = forms.BooleanField(required=False)

"""
   The Aftershocks UI
"""
class AftershocksForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   radius   = forms.FloatField(required=True, label='*Radius',
                help_text='in Kilometers')
   text     = forms.BooleanField(required=False)
   images   = forms.BooleanField(required=False)

def prototype_ui(request):
   if request.method == 'POST':
      epicenters_form = EpicentersForm(request.POST, prefix='epicenters')
      aftershocks_form = AftershocksForm(request.POST, prefix='aftershocks')

      # Get query parameters
      if epicenters_form.is_valid() and aftershocks_form.is_valid():
         # Initialize variables and flags
         no_result_flag = False
         lat, lon = 0.0, 0.0
         params = {"what":None,"where":None}
         
         # Get epicenters parameters
         keywords = epicenters_form.cleaned_data['keywords']
         text = epicenters_form.cleaned_data['text']
         images = epicenters_form.cleaned_data['images']

         if images and text:
            params['what'] = ("text", "image")
         elif images:
            params['what'] = ("image",)
         else:
            params['what'] = ("text",)

         # Get epicenters from twitter
         epicenters = None
         try:
            epicenters = retriever.get(("Twitter",),
                                 keyword=keywords, 
                                 what=params['what'])
         except:
            pass
         
         # The center pin for the visualizer
         package =   {
                        "OpenFusion": "1",
                        "type": "FeatureCollection",
                        "features": []
                     }

         # Get aftershocks parameters
         keywords = aftershocks_form.cleaned_data['keywords']
         radius = aftershocks_form.cleaned_data['radius']
         text = aftershocks_form.cleaned_data['text']
         images = aftershocks_form.cleaned_data['images']
         
         what = None
         if images and text:
            what = ("text", "image")
         elif images:
            what = ("image",)
         else:
            what = ("text",)
         
         # Create epicenters with aftershocks embedded
         data = []
         for feature in epicenters['features']:
            # Get aftershocks
            lon = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]
            aftershocks = retriever.get(
                              ('Twitter',),
                              keyword=keywords,
                              what=what,
                              where=(lat, lon, radius, 'km')
                          )
            feature['properties']['radius'] = (radius*1000)
            feature['properties']['related'] = aftershocks
            data.append(feature)
         
         package['features'] = data

         # Build unique output file name using user ip and timestamp
         ip = ""
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
      epicenters_form = EpicentersForm(prefix='epicenters')
      aftershocks_form = AftershocksForm(prefix='aftershocks')

   return render(request, 'home/proto.html',
                 {
                  'epicenters_form': epicenters_form,
                  'aftershocks_form': aftershocks_form,
                 })
   

