from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from ogre import OGRe
import io, json, time

class TwitterForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   lat      = forms.FloatField(label='Latitude', required=True )
   lon      = forms.FloatField(label='Longitude', required=True )
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
         keywords = form.cleaned_data['keywords']
         lat = form.cleaned_data['lat']
         lon = form.cleaned_data['lon']
         radius = form.cleaned_data['radius']
         t_from = form.cleaned_data['t_from']
         t_to = form.cleaned_data['t_to']
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
                                 "text": "Epicenter of tweets",
                                 "radius": radius
                              }
                           }
                        ]
                      }

         # The complete JSON obj that gets written to .geoJSON file
         package = {
                     "type": "FeatureCollection",
                     "features": [epicenter, data]
                   }
         with io.open('home/templates/viz/test.geojson', 'w') as outfile:
            outfile.write(unicode(json.dumps(package, indent=4, separators=(",", ": "))))

         temp = json.dumps(package, indent=4, separators=(",", ": "))

         #return render(request, '/home/viz/')
         return HttpResponse(temp, content_type='application/json')
   else:
      form = TwitterForm()

      return render(request, 'home/index.html', {'form':form})
