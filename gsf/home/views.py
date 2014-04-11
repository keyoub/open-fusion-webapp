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
               # If the geocoder API doesn't return with results
               # return the user to home page with the address error flag
               message = """The address you gave us is in another
                            dimension. Try again with an earthly address please."""
               return render(request, "home/errors.html",
                        {"url": "", "message": message})
               #return render(request, "home/index.html", 
               #         form_errors(True, no_result_flag, time_flag))

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
            message = """If you expect time interval search you have to 
                         give us both beginning and end!"""
            return render(request, "home/errors.html",
                     {"url": "", "message": message})
            #return render(request, "home/index.html", 
            #         form_errors(address_flag, no_result_flag, True))

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
            message = """Either you gave us a lousy query or
                         we sucked at finding results for you."""
            return render(request, "home/errors.html",
                     {"url": "", "message": message})
            #return render(request, "home/index.html", 
            #         form_errors(address_flag, True, time_flag))

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


# Choices variables for the forms select fields
#SOURCE_CHOICES = (
   #("twt", "Twitter"),
   #("owm", "Open Weather Map"),
   #("gsf", "GSF iOS App"),
#)

TWITTER_CHOICES = (
   ("img", "Images"),
   ("txt", "Text"),
)

GSF_IMAGE_CHOICES = (
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
   The Epicenters form constructor for GSF data querying
"""
class GSFEpicentersForm(forms.Form):
   images   = forms.MultipleChoiceField(required=False, choices=GSF_IMAGE_CHOICES,
             widget=forms.CheckboxSelectMultiple())
   #keywords = forms.CharField(required=False,
   #            help_text="for twitter search. eg. Wild AND Stallions")
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
   
"""
   The Aftershocks form constructor for GSF data querying
"""
class GSFAftershocksForm(GSFEpicentersForm):
   radius = forms.FloatField(required=True, label="*Aftershock Radius",
                help_text="in Kilometers")

"""
   The Epicenters form constructor for Twitter querying
"""
class TwitterFusionForm(forms.Form):
   options = forms.ChoiceField(required=False, choices=TWITTER_CHOICES,
                widget=forms.CheckboxSelectMultiple())
   keywords = forms.CharField(required=False, help_text="eg. Wild OR Stallions")

"""
   Passes user query to get data from the retriever
"""
def query_third_party(sources, keyword, options, location):
   media = ()
   
   # Create the media variable
   for option in options:  
      if option == "img":
         media = media + ("image",)
      if option == "txt":
         media = media + ("text",)

   # Get results from third party provider
   results = {}
   try:
      results = retriever.fetch(sources,
                           media=media,
                           keyword=keyword,
                           quantity=10,
                           location=location,
                           interval=None)
   except:
      logger.error("the retriever failed")

   return results.get("features")

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
def query_numeric_data(keyword, logic, value, exclude_list, geo, coords, radius):
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

"""
   Process the two UI forms for GSF querying and get 
   results for each form query parameters
"""
def process_gsf_form(params, aftershocks, coords):
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
               query_numeric_data(
                  k, params[k+"_logic"], v, temp_list,
                  geo=True, coords=coords, radius=params["radius"]
               )
            )
         else:
            results.extend(
               query_numeric_data(
                  k, params[k+"_logic"], v, temp_list,
                  geo=False, coords=None, radius=None
               )
            )

   beautify_results(results)

   return results

"""
   The prototype UI for the Fusion interface 
"""
def prototype_ui(request):
   if request.method == "POST":
      gsf_epicenters_form = GSFEpicentersForm(request.POST, prefix="gsf_epicenters")
      gsf_aftershocks_form = GSFAftershocksForm(request.POST, prefix="gsf_aftershocks")

      twitter_epicenters_form = TwitterFusionForm(request.POST, prefix="twitter_epicenters")
      twitter_aftershocks_form = TwitterFusionForm(request.POST, prefix="twitter_aftershocks")

      # Get query parameters
      if gsf_epicenters_form.is_valid() and \
         gsf_aftershocks_form.is_valid() and \
         twitter_epicenters_form.is_valid() and \
         twitter_aftershocks_form.is_valid():
         
         # Initialize variables
         epicenters, aftershocks = [], []

         # Get twitter epicenters
         twt_params = twitter_epicenters_form.cleaned_data
         if twt_params["options"]:
            epicenters.extend(query_third_party(
                  ("Twitter",), twt_params["keywords"], twt_params["options"], None
               )
            )

         # Get gsf epicenters
         gsf_epicenter_params = gsf_epicenters_form.cleaned_data
         epicenters.extend(process_gsf_form(
               gsf_epicenter_params, aftershocks=False, coords=None
            )
         )

         if not epicenters:
            message = """Either you gave us a lousy query or
                         we sucked at finding results for you."""
            return render(request, "home/errors.html",
                     {"url": "/proto/", "message": message})

         # The package that gets written to file for the visualizer
         package =   {
                        "OpenFusion": "1",
                        "type": "FeatureCollection",
                        "features": []
                     }

         # Get aftershocks parameters
         gsf_aftershock_params = gsf_aftershocks_form.cleaned_data
         twt_params = twitter_aftershocks_form.cleaned_data

         # Check if we need to do third party queries
         twt_flag = False
         if twt_params["options"]:
            twt_flag = True

         # Create epicenters with aftershocks embedded
         results = []
         for epicenter in epicenters:
            # Get aftershocks
            aftershocks = []
            lon = epicenter["geometry"]["coordinates"][0]
            lat = epicenter["geometry"]["coordinates"][1]

            # Get twitter aftershocks
            if twt_flag:
               location=(lat, lon, gsf_aftershock_params["radius"], "km")
               aftershocks.extend(query_third_party(
                     ("Twitter",), twt_params["keywords"],
                     twt_params["option"], location
                  )
               )

            # Get gsf aftershocks
            aftershocks.extend(process_gsf_form(
                 gsf_aftershock_params, aftershocks=True, coords=[lon, lat]
               )
            )
            
            # Add the epicenter with added aftershocks to the package
            epicenter["properties"]["radius"] = (gsf_aftershock_params["radius"]*1000)
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
      gsf_epicenters_form = GSFEpicentersForm(prefix="gsf_epicenters")
      gsf_aftershocks_form = GSFAftershocksForm(prefix="gsf_aftershocks")

      twitter_epicenters_form = TwitterFusionForm(prefix="twitter_epicenters")
      twitter_aftershocks_form = TwitterFusionForm(prefix="twitter_aftershocks")

   return render(request, "home/proto.html",
                 {
                  "gsf_epicenters_form": gsf_epicenters_form,
                  "gsf_aftershocks_form": gsf_aftershocks_form,
                  "twitter_epicenters_form": twitter_epicenters_form,
                  "twitter_aftershocks_form": twitter_aftershocks_form,
                 })
   
