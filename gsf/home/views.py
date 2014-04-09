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
#SOURCE_CHOICES = (
   #("twt", "Twitter"),
   #("owm", "Open Weather Map"),
   #("gsf", "GSF iOS App"),
#)

IMAGE_CHOICES = (
   ("twt", "From Twitter"),
   ("imf", "With faces detected"),
   ("imb", "With bodies detected"),
   
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
   Shared form fields
"""
#sources  = forms.MultipleChoiceField(required=False, choices=SOURCE_CHOICES,
#             widget=forms.CheckboxSelectMultiple())
images   = forms.MultipleChoiceField(required=False, choices=IMAGE_CHOICES,
             widget=forms.CheckboxSelectMultiple())
keywords = forms.CharField(required=False, 
            help_text="for twitter search. eg. Wild AND Stallions")
temperature_logic  = forms.ChoiceField(label="Temperature",
                  required=False, choices=OPERATORS)
temperature = forms.DecimalField(label="",required=False,
                  help_text="eg. Temperature >= 60 &deg;F")
humidity_logic  = forms.ChoiceField(label="Humidity",
                  required=False, choices=OPERATORS)
humidity = forms.DecimalField(label="",required=False,
               help_text="eg. humidity <= 60 %")
noise_level_logic  = forms.ChoiceField(label="Noise Level",
                  required=False, choices=OPERATORS)
noise_level = forms.DecimalField(label="",required=False,
                  help_text="eg. Noise level < 80 dB")
radius   = forms.FloatField(required=True, label="*Aftershock Radius",
             help_text="in Kilometers")

class EpicentersForm(forms.Form):
   #sources     = sources 
   images      = images
   keywords    = keywords
   temperature_logic  = temperature_logic
   temperature = temperature
   humidity_logic = humidity_logic
   humidity    = humidity
   noise_level_logic = noise_level_logic
   noise_level = noise_level

"""
   The Aftershocks UI
"""
class AftershocksForm(forms.Form):
   #sources     = sources 
   images      = images
   keywords    = keywords
   temperature_logic  = temperature_logic
   temperature = temperature
   humidity_logic = humidity_logic
   humidity    = humidity
   noise_level_logic = noise_level_logic
   noise_level = noise_level
   radius      = radius

"""
   Passes user query to get data from the retriever
"""
def query_third_party(sources, keywords, images, where):
   what = ()
   for image in images:
      if image == "twt":
         what = what + ("image",)

   if keywords:
      what = what + ("text",)
   logger.debug(what)
   logger.debug(keywords)
   # Get results from third party provider
   results = None
   try:
      results = retriever.get(sources,
                           keyword=keywords, 
                           what=what,
                           where=where)
   except:
      logger.error("the retriever failed")

   return results

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
def query_for_images(faces, bodies, geo, coords, radius):
   data_set = Features.objects.all()
   if geo:
      data_set = data_set(geometry__geo_within_center=[coords, radius])
   EXCLUDE = [
      "oimage",
      "humidity",
      "noise_level",
      "temperature"
   ]
   data = []
   if faces:
      data = json.loads(
               data_set(Q(properties__fimage__exists=True) &
                  Q(properties__faces_detected__gt=0)).to_json()
             )
      if data:
         exclude_fields(data, EXCLUDE)
         for d in data:
            d["properties"]["image"] = d["properties"].pop("fimage")
            d["properties"].pop("pimage", None)
   if bodies:
      lis = json.loads(
               data_set(Q(properties__pimage__exists=True) &
                  Q(properties__people_detected__gt=0)).to_json()
            )
      if lis:
         exclude_fields(lis, EXCLUDE)
         for d in lis:
            d["properties"]["image"] = d["properties"].pop("pimage")
            d["properties"].pop("fimage", None)
         data.extend(lis)
   return data

"""
   Query the local db for non-image data
"""
def query_local_data(keyword, logic, value, exclude_list, geo, coords, radius):
   data_set = Features.objects.all()
   if geo:
      data_set = data_set(geometry__geo_within_center=[coords, radius])
   query_string = "properties__" + keyword + logic
   kwargs = { query_string: value }
   data = json.loads(data_set.filter(**kwargs).to_json())
   exclude_fields(data, exclude_list)
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

def process_form(params, aftershocks, coords):
   results, third_party_results = [], {}
   faces, bodies = False, False
   for image in params["images"]:
      if image == "imf":
         faces = True
      elif image == "imb":
         bodies = True

   if (faces or bodies) and aftershocks:
      results.extend(
         query_for_images(
            faces, bodies, geo=True,
            coords=coords, radius=params["radius"]
         )
      )
   elif faces or bodies:
      results.extend(
         query_for_images(
            faces, bodies, geo=False,
            coords=None, radius=None
         )
      )

   generic_list = ["temperature", "humidity", "noise_level"]
   exclude_list = ["oimage", "fimage", "pimage", "faces_detected",
                   "people_detected", "humidity", "noise_level", "temperature"] 
   for k,v in params.items():
      if (k in generic_list) and v:
         temp_list = []
         for elem in exclude_list:
            if elem != k:
               temp_list.append(elem)
         if aftershocks:
            results.extend(
               query_local_data(
                  k, params[k+"_logic"], v, temp_list,
                  geo=True, coords=coords, radius=params["radius"]
               )
            )
         else:
            results.extend(
               query_local_data(
                  k, params[k+"_logic"], v, temp_list,
                  geo=False, coords=None, radius=None
               )
            )

   beautify_results(results)

   # Query third party sources if requested by the user
   thd_party_image_flag = False
   for choice in params["images"]:
      if choice in params["images"]:
         thd_party_image_flag = True
   if (thd_party_image_flag or params["keywords"]) and aftershocks:
      where=(coords[1], coords[0], params["radius"], "km")
      third_party_results = query_third_party(
         ("Twitter",), params["keywords"], params["images"], where
      )
   elif thd_party_image_flag or params["keywords"]:
      third_party_results = query_third_party(
         ("Twitter",), params["keywords"], params["images"], None
      )
   
   if third_party_results:
      results.extend(third_party_results["features"])

   return results


def prototype_ui(request):
   if request.method == "POST":
      epicenters_form = EpicentersForm(request.POST, prefix="epicenters")
      aftershocks_form = AftershocksForm(request.POST, prefix="aftershocks")

      # Get query parameters
      if epicenters_form.is_valid() and aftershocks_form.is_valid():
         # Initialize variables and flags
         no_result_flag = False
         
         # Get epicenters parameters
         epicenter_params = {}
         for k,v in epicenters_form.cleaned_data.items():
            epicenter_params[k] = v

         epicenters = process_form(epicenter_params,
                        aftershocks=False, coords=None
                      )

         # The package that gets written to file for the visualizer
         package =   {
                        "OpenFusion": "1",
                        "type": "FeatureCollection",
                        "features": []
                     }

         # Get aftershocks parameters
         aftershock_params = {}
         for k,v in aftershocks_form.cleaned_data.items():
            aftershock_params[k] = v
         
         # Create epicenters with aftershocks embedded
         results = []
         for epicenter in epicenters:
            # Get aftershocks
            lon = epicenter["geometry"]["coordinates"][0]
            lat = epicenter["geometry"]["coordinates"][1]
            aftershocks = process_form(aftershock_params,
                           aftershocks=True, coords=[lon, lat])
            epicenter["properties"]["radius"] = (aftershock_params["radius"]*1000)
            epicenter["properties"]["related"] = { 
                                                   "type": "FeatureCollection",
                                                   "features": aftershocks
                                                 }
            results.append(epicenter)
         
         package["features"] = results

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
         #  - if mobile device detected, redirect to touchscreen version
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
   
