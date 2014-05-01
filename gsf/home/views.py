from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.forms.formsets import formset_factory
from django.core.mail import send_mail
from mongoengine.queryset import Q
from gsf.settings import BASE_DIR, TWITTER_CONSUMER_KEY, \
                         TWITTER_ACCESS_TOKEN
from api.models import Features, APIKey, Coordinates
from pygeocoder import Geocoder
from ogre import OGRe
from twython import TwythonRateLimitError, TwythonError
import os, io, json, time, hashlib, datetime, logging, random

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
                        "OpenFusion": "5",
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
TWITTER_CHOICES = (
   ("image", "Images"),
   ("text", "Text"),
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
class GSFFusionForm(forms.Form):
   images   = forms.MultipleChoiceField(required=False, choices=GSF_IMAGE_CHOICES,
             widget=forms.CheckboxSelectMultiple())
   temperature_logic  = forms.ChoiceField(label="Temperature",
                     required=False, choices=OPERATORS)
   temperature = forms.DecimalField(label="",required=False,
                     help_text="eg. Temperature >= 60 &deg;F",
                     min_value=1, max_value=150)
   humidity_logic  = forms.ChoiceField(label="Humidity",
                     required=False, choices=OPERATORS)
   humidity = forms.DecimalField(label="",required=False,
                  help_text="eg. humidity <= 60 %",
                  min_value=0, max_value=100)
   noise_level_logic  = forms.ChoiceField(label="Noise Level",
                     required=False, choices=OPERATORS)
   noise_level = forms.DecimalField(label="",required=False,
                     help_text="eg. Noise level < 80 dB",
                     min_value=-120, max_value=100)
   
"""
   The Aftershocks form constructor for GSF data querying
"""
class MiscForm(forms.Form):
   radius = forms.FloatField(required=False, label="Aftershock Radius",
                help_text="in Kilometers", min_value = 0.1, max_value=5)

"""
   The Epicenters form constructor for Twitter querying
"""
class TwitterFusionForm(forms.Form):
   options = forms.MultipleChoiceField(required=False, choices=TWITTER_CHOICES,
                widget=forms.CheckboxSelectMultiple())
   keywords = forms.CharField(required=False, help_text="eg. Wild OR Stallions")
   number = forms.DecimalField(required=False, label="Number of Tweets",
            min_value = 1, max_value = 15, help_text="""Default 1, Max 15. 
            Beware that large requests take a long time to get back from twitter""")

"""
   Query the local db for cached third party data before
   passing requests to the retriever
"""
def query_cached_third_party(source, keyword, options, location, quantity):
   data_set = Features.objects(properties__source=source)
   if location:
      coords = [location[1], location[0]]
      radius = location[2]
      logger.debug(coords)
      logger.debug(radius)
      #data_set = data_set(geometry__geo_within_center=[coords, radius*0.6213])
      data_set = data_set(geometry__near=coords, geometry__max_distance=radius*1000)
   if keyword:
      data_set = data_set(properties__text__icontains=keyword)
   if "image" in options:
      data_set = data_set(properties__image__exists=True)
   data_set = list(data_set.as_pymongo())
   random.shuffle(data_set)
   logger.debug(len(data_set))
   return data_set[:quantity]
      
"""
   Passes user query to get third party data
"""
def query_third_party(sources, keyword, options, location, quantity):
   results = []
   error = ""
   # Get data from local cache first
   for source in sources:
      results.extend(query_cached_third_party(
            source, keyword, options, location, quantity
         )
      )

   # Get results from third party provider if needed
   if len(results) < quantity:
      quantity = quantity - len(results)
      logger.debug(quantity)
      outside_data = {}
      try:
         outside_data = retriever.fetch(sources,
                              media=options,
                              keyword=keyword,
                              quantity=quantity,
                              location=location,
                              interval=None)
      except TwythonRateLimitError, e:
         logger.error(e)
         error = """Unfortunately our Twitter retriever has been rate
            limited. We cannot do anything but wait for Twitter's tyranny to end."""
      except TwythonError, e:
         logger.error(e)
      except Exception as e:
         logger.error(e)
      
      #logger.debug(outside_data.get("features", []))
      # Cache the data in local db
      for data in outside_data.get("features", []):
         feature = Features(**data)
         try:
            feature.save()
         except Exception, e:
            logger.debug(e)  
      results.extend(outside_data.get("features", []))

   return (error, results)

"""
   Drop unwanted fields from query documents
"""
def exclude_fields(data, keys):
   for d in data:
      if keys:
         for k in keys:
            d["properties"].pop(k, None)
      else:
         d.pop("_id", None)
         d["properties"].pop("date_added", None)

"""
   Query the local db for images
"""
def query_for_images(faces, bodies, geo, coords, radius):
   data_set = Features.objects(properties__image__exists=True)
   if geo:
      data_set = data_set(geometry__near=coords, geometry__max_distance=radius*1000)
      #data_set = data_set(geometry__geo_within_center=[coords, radius])
   EXCLUDE = [
      "humidity",
      "noise_level",
      "temperature"
   ]
   data = []
   if faces:
      data.extend(data_set(properties__faces_detected__gt=0).as_pymongo())
   if bodies:
      data.extend(data_set(properties__people_detected__gt=0).as_pymongo())
   exclude_fields(data, EXCLUDE)
   return data

"""
   Query the local db for non-image data
"""
def query_numeric_data(keyword, logic, value, exclude_list, geo, coords, radius):
   data_set = Features.objects.all()
   if geo:
      data_set = data_set(geometry__near=coords, geometry__max_distance=radius*1000)
      #data_set = data_set(geometry__geo_within_center=[coords, radius])
   query_string = "properties__" + keyword + logic
   kwargs = { query_string: value }
   data = data_set.filter(**kwargs).as_pymongo()
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
def process_gsf_form(params, aftershocks, coords, radius):
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
            coords=coords, radius=radius
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
   exclude_list = ["image", "faces_detected", "people_detected",
                   "humidity", "noise_level", "temperature"] 
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
                  geo=True, coords=coords, radius=radius
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
   Write the Geojson data to the filesystem   
"""
def dump_data_to_file(name, base_path, package):
   # Build unique output file name using user ip and timestamp
   ip = ""
   try:
      ip = request.get_host()
   except:
      pass
   now = str(datetime.datetime.now())

   file_name = name + \
      str(hashlib.sha1(ip+now).hexdigest()) + ".geojson"

   # Write data to the file
   path = os.path.join(base_path, file_name)
   
   with io.open(path, "w") as outfile:
      outfile.write(unicode(json.dumps(package,
         indent=4, separators=(",", ": "))))

   return file_name


"""
   The prototype UI for the Fusion interface 
"""
def prototype_ui(request):
   if request.method == "POST":
      gsf_epicenters_form = GSFFusionForm(request.POST,
         prefix="gsf_epicenters")
      gsf_aftershocks_form = GSFFusionForm(request.POST,
         prefix="gsf_aftershocks")

      twitter_epicenters_form = TwitterFusionForm(request.POST,
         prefix="twitter_epicenters")
      twitter_aftershocks_form = TwitterFusionForm(request.POST,
         prefix="twitter_aftershocks")

      misc_form = MiscForm(request.POST, prefix="misc_form")

      # Get query parameters
      if gsf_epicenters_form.is_valid() and \
         gsf_aftershocks_form.is_valid() and \
         twitter_epicenters_form.is_valid() and \
         twitter_aftershocks_form.is_valid() and \
         misc_form.is_valid():
         
         # Initialize variables
         epicenters, aftershocks = [], []
         radius = misc_form.cleaned_data["radius"]

         # Get twitter epicenters
         twt_params = twitter_epicenters_form.cleaned_data
         if twt_params["options"]:
            result = query_third_party(
               ("Twitter",), twt_params["keywords"], twt_params["options"], 
               None, int(twt_params["number"] if twt_params["number"] else 1)
            )
            if (result[0] != "") and (len(result[1]) == 0):
               return render(request, "home/errors.html",
                  {"url": "/proto/", "message": result[0]})
            epicenters.extend(result[1])

         # Get gsf epicenters
         gsf_epicenter_params = gsf_epicenters_form.cleaned_data
         epicenters.extend(process_gsf_form(
               gsf_epicenter_params, aftershocks=False, coords=None, radius=None
            )
         )

         if not epicenters:
            message = """Either you gave us a lousy query or
                         we sucked at finding results for you."""
            return render(request, "home/errors.html",
                     {"url": "/proto/", "message": message})

         # The package that gets written to file for the visualizer
         package =   {
                        "OpenFusion": "5",
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

         results = []
         # Create epicenters with aftershocks embedded if radius given
         if radius:
            for epicenter in epicenters:
               # Get aftershocks
               aftershocks = []
               lon = epicenter["geometry"]["coordinates"][0]
               lat = epicenter["geometry"]["coordinates"][1]

               # Get twitter aftershocks
               if twt_flag:
                  location=(lat, lon, radius, "km")
                  result = query_third_party(
                     ("Twitter",), twt_params["keywords"],
                     twt_params["options"], location, 
                     int(twt_params["number"] if twt_params["number"] else 1)
                  )
                  aftershocks.extend(result[1])

               # Get gsf aftershocks
               aftershocks.extend(process_gsf_form(
                    gsf_aftershock_params, aftershocks=True,
                    coords=[lon, lat], radius=radius
                  )
               )
               
               exclude_fields(aftershocks, None)
               # Add the epicenter with added aftershocks to the package
               epicenter["properties"]["radius"] = radius*1000               
               epicenter["properties"]["related"] = { 
                  "type": "FeatureCollection",
                  "features": aftershocks
               }
               results.append(epicenter)
         else:
            results = epicenters
         
         exclude_fields(results, None)
         package["features"] = results

         # Creat the path for the visualizer data and write to file
         base_path = os.path.join(BASE_DIR, "static", "vizit", "data")
         vizit_file = dump_data_to_file("points_", base_path, package)
         
         # Check if the admin is logged in and make a list of
         # active phones available to send coordinates to
         field_agents, coords_id = None, None
         if request.user.is_superuser:
            points = []
            for p in package["features"]:
               points.append(p["geometry"])
            
            coordinates = Coordinates(geometries=points)
            coordinates.save()
            coords_id = coordinates.id

            # Get list of field agents
            field_agents = APIKey.objects.filter(organization="LLNL")
         
         # redirect user to the visualizer 
         #  - if mobile device detected, redirect to touchscreen version
         if request.mobile:
            redr_path = "/static/vizit/index.html?data=" + vizit_file
            return HttpResponseRedirect(redr_path)
         else:
            return render(request, "home/vizit.html",
                {
                  "vizit_file":vizit_file,
                  "coords_id":coords_id,
                  "field_agents":field_agents,
                })
   else:
      gsf_epicenters_form = GSFFusionForm(prefix="gsf_epicenters")
      gsf_aftershocks_form = GSFFusionForm(prefix="gsf_aftershocks")

      twitter_epicenters_form = TwitterFusionForm(prefix="twitter_epicenters")
      twitter_aftershocks_form = TwitterFusionForm(prefix="twitter_aftershocks")
      
      misc_form = MiscForm(prefix="misc_form")

   return render(request, "home/proto.html",
                 {
                  "gsf_epicenters_form": gsf_epicenters_form,
                  "gsf_aftershocks_form": gsf_aftershocks_form,
                  "twitter_epicenters_form": twitter_epicenters_form,
                  "twitter_aftershocks_form": twitter_aftershocks_form,
                  "misc_form": misc_form,
                 })
   
def send_coordinates(request):
   if request.user.is_superuser:
      key = request.GET.get("key")
      coords_id = request.GET.get("id")
      agent = APIKey.objects.get(key=key)

      # Send text message with the coordinates id to the agent
      sender = "GSF Admin"
      message = "comsdpllnl://?" + str(coords_id)
      recipient = [agent.phone_number+agent.cell_carrier]
 
      send_mail("", message, sender, recipient)

   return render(request, "home/coords-sent.html",
                 {
                  "agent":agent,
                 })
      



