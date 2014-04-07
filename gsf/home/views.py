from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.forms.formsets import formset_factory
from mongoengine.queryset import Q
from gsf.settings import BASE_DIR, TWITTER_CONSUMER_KEY, \
                         TWITTER_ACCESS_TOKEN
from api.models import Features
from pygeocoder import Geocoder
from ogre import OGRe
import os, io, json, time, hashlib, datetime, logging

logger = logging.getLogger(__name__)

retriever = OGRe ({
   "Twitter": {
      "consumer_key": TWITTER_CONSUMER_KEY,
      "access_token": TWITTER_ACCESS_TOKEN,
   }
})

"""
   The UI input form for the twitter retriever
"""
class TwitterForm(forms.Form):
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   addr     = forms.CharField(required=True, max_length=500, label="*Address",
                help_text="eg. Santa Cruz, CA or Mission st, San Francisco")
   radius   = forms.FloatField(required=True, label="*Radius",
                help_text="in Kilometers")
   t_from   = forms.DateTimeField(required=False, label="From",
               help_text="Enter starting date and time",
               widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
   t_to     = forms.DateTimeField(required=False, label="To",
               help_text="Enter ending date and time",
               widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
   text     = forms.BooleanField(required=False)
   images   = forms.BooleanField(required=False)

"""
   Helper function that builds the context for index.html 
"""
def form_errors(address_flag, no_result_flag, time_flag):
   form = TwitterForm()
   context = {
                "form": form,
                "address_flag": address_flag,
                "no_result_flag": no_result_flag,
                "time_flag": time_flag,
             }
   return context

"""
   The home page query UI controller.
      - Handles queries on local db
      - Handles queries for the retriever
"""
def index(request):
   if request.method == "POST":
      form = TwitterForm(request.POST)

      # Get query parameters
      if form.is_valid():
         # Initialize variables and flags
         address_flag, no_result_flag, time_flag = False, False, False
         lat, lon = 0.0, 0.0
         params = {"what":None,"where":None}
         
         # Get data from the from
         keywords = form.cleaned_data["keywords"]
         addr = form.cleaned_data["addr"]
         radius = form.cleaned_data["radius"]
         t_from = form.cleaned_data["t_from"]
         t_to = form.cleaned_data["t_to"]
         text = form.cleaned_data["text"]
         images = form.cleaned_data["images"]

         # Get coordinates from the address entered
         if addr:
            try:
               results = Geocoder.geocode(addr)
               lat = float(results[0].coordinates[0])
               lon = float(results[0].coordinates[1])
            except:
               # If the geocoder API doesn"t return with results
               # return the user to home page with the address error flag
               return render(request, "home/index.html", 
                        form_errors(True, no_result_flag, time_flag))

            # Start building the query for the retriever
            params["where"] = (lat, lon, radius, "km")

         if images and text:
            params["what"] = ("text", "image")
         elif images:
            params["what"] = ("image",)
         else:
            params["what"] = ("text",)

         # Get time span and convert to epoch time
         if t_from and t_to:
            t_from = int(time.mktime(
               time.strptime(str(t_from)[:19], "%Y-%m-%d %H:%M:%S"))) - time.timezone
            t_to   = int(time.mktime(
               time.strptime(str(t_to)[:19], "%Y-%m-%d %H:%M:%S"))) - time.timezone
            params["when"] = (t_from, t_to)
         # Return to home page with error if only one field id provided
         elif t_from or t_to:
            return render(request, "home/index.html", 
                     form_errors(address_flag, no_result_flag, True))

         # Get twitter data
         data = None
         try:
            data = retriever.get(("Twitter",),
                                 keyword=keywords, 
                                 what=params["what"],
                                 where=params["where"])
         except:
            pass

         # Return to home page if no tweets were found
         if not data or not data["features"]:
            return render(request, "home/index.html", 
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
         path = os.path.join(BASE_DIR, "static", "vizit", 
                              "data", file_name)
         with io.open(path, "w") as outfile:
            outfile.write(unicode(json.dumps(package,
               indent=4, separators=(",", ": "))))
         
         # redirect user to the visualizer
         # if mobile device detected, redirect to touchscreen version
         if request.mobile:
            redr_path = "/static/vizit/index.html?data=" + file_name
            return HttpResponseRedirect(redr_path)
         else:
            return render(request, "home/vizit.html", {"file_name":file_name})
   else:
      form = TwitterForm()

   return render(request, "home/index.html", {"form":form})


# Choices variables for the forms" select field
SOURCE_CHOICES = (
   ("twt", "Twitter"),
   #("owm", "Open Weather Map"),
   #("gsf", "GSF iOS App"),
)

IMAGE_CHOICES = (
   ("twt", "Images from Twitter"),
   ("imf", "Images with faces detected"),
   ("imb", "Images with bodies detected"),
   
)

OPERATORS = (
   ("", "="),
   ("__gt", ">"),
   ("__lt", "<"),
   ("__gte", ">="),
   ("__lte", "<="),
)

LOGICALS = (
   (0, "OR"),
   (1, "AND"), 
)

"""
   The Epicenters UI
"""
class EpicentersForm(forms.Form):
   sources  = forms.MultipleChoiceField(required=False, choices=SOURCE_CHOICES,
                widget=forms.CheckboxSelectMultiple())
   images   = forms.MultipleChoiceField(required=False, choices=IMAGE_CHOICES,
                widget=forms.CheckboxSelectMultiple())
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   # Local query fields
   temp_logic  = forms.ChoiceField(label="Temperature",
                     required=False, choices=OPERATORS)
   temperature = forms.DecimalField(label="",required=False,
                     help_text="eg. Temperature >= 60 &deg;F")

   humid_logic  = forms.ChoiceField(label="Humidity",
                     required=False, choices=OPERATORS)
   humidity = forms.DecimalField(label="",required=False,
                  help_text="eg. humidity <= 60 %")

   noise_logic  = forms.ChoiceField(label="Noise Level",
                     required=False, choices=OPERATORS)
   noise_level = forms.DecimalField(label="",required=False,
                     help_text="eg. Noise level < 80 dB")

"""
   The Aftershocks UI
"""
class AftershocksForm(forms.Form):
   # Remote data fields
   keywords = forms.CharField(required=False, help_text="Space separated keywords")
   radius   = forms.FloatField(required=True, label="*Radius",
                help_text="in Kilometers")
   text     = forms.BooleanField(required=False)
   images   = forms.BooleanField(required=False)

"""
   Passes user query to get data from the retriever
"""
def query_remote(sources, keywords, images):
   what = ()
   for image in images:
      if image == "twt":
         what = what + ("image",)

   if keywords:
      what = what + ("text",)
         
   # Get epicenters from twitter
   epicenters = None
   try:
      epicenters = retriever.get(sources,
                           keyword=keywords, 
                           what=what)
   except:
      logger.error("the retriever failed")

   return epicenters

"""
   Drop unwanted fields from query documents
"""
def exclude_fields(data, keys):
   for d in data:
      for k in keys:
         d["properties"].pop(k, None)

"""
   Query the local db for images
"""
def query_for_images(local_data, faces, bodies):
   exclude = [
      "oimage",
      "humidity",
      "noise_level",
      "temperature"
   ]
   data = []
   if faces:
      data = json.loads(
               local_data(Q(properties__fimage__exists=True) &
                  Q(properties__faces_detected__gt=0)).to_json()
             )
      if data:
         temp = exclude
         temp.extend(["pimage", "people_detected"])
         exclude_fields(data, temp)
         for d in data:
            d["properties"]["image"] = d["properties"].pop("fimage")
   if bodies:
      lis = json.loads(
               local_data(Q(properties__pimage__exists=True) &
                  Q(properties__people_detected__gt=0)).to_json()
            )
      if lis:
         temp = exclude
         temp.extend(["fimage", "faces_detected"])
         exclude_fields(lis, temp)
         for d in lis:
            d["properties"]["image"] = d["properties"].pop("pimage")
         data.extend(lis)
   return data

"""
   Query the local db for temperature data
"""
def query_for_temperature(local_data, temperature, temp_logic):
   EXCLUDE_FIELDS = [
      "oimage",
      "fimage",
      "pimage",
      "faces_detected",
      "people_detected",
      "humidity",
      "noise_level"
   ] 
   query_string = "properties__temperature" + temp_logic
   kwargs = { query_string: temperature }
   data = json.loads(local_data.filter(**kwargs).to_json())
   exclude_fields(data, EXCLUDE_FIELDS)
   return data
   
"""
   Query the local db for humidity data
"""
def query_for_humidity(local_data, humidity, hum_logic):
   EXCLUDE_FIELDS = [
      "oimage",
      "fimage",
      "pimage",
      "faces_detected",
      "people_detected",
      "temperature",
      "noise_level"
   ]
   query_string = "properties__humidity" + hum_logic
   kwargs = { query_string: humidity }
   data = json.loads(local_data.filter(**kwargs).to_json())
   exclude_fields(data, EXCLUDE_FIELDS)
   return data

"""
   Query the local db for noise_level data
"""
def query_for_noise_level(local_data, noise_level, noise_logic):
   EXCLUDE_FIELDS = [
      "oimage",
      "fimage",
      "pimage",
      "faces_detected",
      "people_detected",
      "humidity",
      "temperature"
   ]
   query_string = "properties__noise_level" + noise_logic
   kwargs = { query_string: noise_level }
   data = json.loads(local_data.filter(**kwargs).to_json())
   exclude_fields(data, EXCLUDE_FIELDS)
   return data

"""
   Add all the local data fields as html to the text key
      - this is required for nice looking output on the visualizer
"""
def beautify_results(packages):
   for package in packages:
      properties = package["properties"]
      if "text" not in properties:
         properties["text"] = ""
      if "noise_level" in properties:
         properties["text"] += "<br /><b>Noise Level</b>:" + \
                              str(properties["noise_level"]) + " dB"
      if "temperature" in properties:
         properties["text"] += "<br /><b>Temperature</b>: " + \
                              str(properties["temperature"]) + " &deg;F"
      if "humidity" in properties:
         properties["text"] += "<br /><b>Humidity</b>: " + \
                               str(properties["humidity"]) + " %"
      if "faces_detected" in properties:
         properties["text"] += "<br /><b>Number of Faces Detected: </b>: " + \
                               str(int(properties["faces_detected"]))
      if "people_detected" in properties:
         properties["text"] += "<br /><b>Number of Bodies Detected: </b>: " + \
                               str(int(properties["people_detected"]))

def prototype_ui(request):
   if request.method == "POST":
      epicenters_form = EpicentersForm(request.POST, prefix="epicenters")
      aftershocks_form = AftershocksForm(request.POST, prefix="aftershocks")

      # Get query parameters
      if epicenters_form.is_valid() and aftershocks_form.is_valid():
         # Initialize variables and flags
         no_result_flag = False
         epicenters, twitter_epicenters = [], {}
         params = {"what":None,"where":None}
         
         # Get epicenters parameters
         sources = epicenters_form.cleaned_data["sources"]
         images = epicenters_form.cleaned_data["images"]
         keywords = epicenters_form.cleaned_data["keywords"]
         temp_logic = epicenters_form.cleaned_data["temp_logic"]
         temperature = epicenters_form.cleaned_data["temperature"]
         humid_logic = epicenters_form.cleaned_data["humid_logic"]
         humidity = epicenters_form.cleaned_data["humidity"]
         noise_logic = epicenters_form.cleaned_data["noise_logic"]
         noise_level = epicenters_form.cleaned_data["noise_level"]

         # Start querying the local db for data
         query_data = Features.objects().all()
         faces, bodies = False, False
         for image in images:
            if image == "imf":
               faces = True
            elif image == "imb":
               bodies = True

         if faces or bodies:
            epicenters.extend(query_for_images(query_data, faces, bodies))

         if temperature:
            epicenters.extend(
               query_for_temperature(query_data, temperature, temp_logic))
         
         if humidity:
            epicenters.extend(json.loads(
               query_for_humidity(query_data, humidity, humid_logic).to_json()))

         if noise_level:
            epicenters.extend(json.loads(
               query_for_noise_level(query_data, noise_level, noise_logic).to_json()))

         beautify_results(epicenters)

         # Query twitter if user asked for it
         for source in sources:
            if source == "twt":
               twitter_epicenters = query_remote(("Twitter",), keywords, images)
         
         if twitter_epicenters:
            epicenters.extend(twitter_epicenters["features"])

         # The package that gets written to file for the visualizer
         package =   {
                        "OpenFusion": "1",
                        "type": "FeatureCollection",
                        "features": []
                     }

         # Get aftershocks parameters
         keywords = aftershocks_form.cleaned_data["keywords"]
         radius = aftershocks_form.cleaned_data["radius"]
         text = aftershocks_form.cleaned_data["text"]
         images = aftershocks_form.cleaned_data["images"]
         
         what = None
         if images and text:
            what = ("text", "image")
         elif images:
            what = ("image",)
         else:
            what = ("text",)
         
         # Create epicenters with aftershocks embedded
         data = []
         for feature in epicenters:
            # Get aftershocks
            lon = feature["geometry"]["coordinates"][0]
            lat = feature["geometry"]["coordinates"][1]
            # TODO: Add try catch
            aftershocks = retriever.get(
                              ("Twitter",),
                              keyword=keywords,
                              what=what,
                              where=(lat, lon, radius, "km")
                          )
            #logger.debug(feature)
            feature["properties"]["radius"] = (radius*1000)
            feature["properties"]["related"] = aftershocks
            data.append(feature)
         
         package["features"] = data

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
         path = os.path.join(BASE_DIR, "static", "vizit", 
                              "data", file_name)
         with io.open(path, "w") as outfile:
            outfile.write(unicode(json.dumps(package,
               indent=4, separators=(",", ": "))))
         
         # redirect user to the visualizer
         # if mobile device detected, redirect to touchscreen version
         if request.mobile:
            redr_path = "/static/vizit/index.html?data=" + file_name
            return HttpResponseRedirect(redr_path)
         else:
            return render(request, "home/vizit.html", {"file_name":file_name})
   else:
      epicenters_form = EpicentersForm(prefix="epicenters")
      aftershocks_form = AftershocksForm(prefix="aftershocks")

   return render(request, "home/proto.html",
                 {
                  "epicenters_form": epicenters_form,
                  "aftershocks_form": aftershocks_form,
                 })
   
