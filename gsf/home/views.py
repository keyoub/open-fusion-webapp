import os, io, json, time, hashlib, datetime, logging
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from gsf.settings import BASE_DIR
from api.models import Features, APIKey, Coordinates
from uiforms import *
from localquery import *
from remotequery import *
from processforms import *
from pygeocoder import Geocoder

logger = logging.getLogger(__name__)

"""
   The prototype UI for the Fusion interface 
"""
def index(request):
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
         addresses = misc_form.cleaned_data["addresses"]
         
         if addresses:
            epicenters.extend(create_epicenters_from_addresses(addresses))

         # Get twitter epicenters
         twt_params = twitter_epicenters_form.cleaned_data
         if twt_params["options"]:
            epicenters.extend(process_twitter_form(
                  twt_params, None
               )
            )

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
                     {"url": "/", "message": message})

         # The package that gets written to file for the visualizer
         package =   {
                        "OpenFusion": "5",
                        "type": "FeatureCollection",
                        "features": []
                     }

         # Get aftershocks parameters
         gsf_aftershock_params = gsf_aftershocks_form.cleaned_data
         twt_params = twitter_aftershocks_form.cleaned_data

         results = []
         # Create epicenters with aftershocks embedded if radius given
         if radius:
            for epicenter in epicenters:
               # Get aftershocks
               aftershocks = []
               lon = epicenter["geometry"]["coordinates"][0]
               lat = epicenter["geometry"]["coordinates"][1]

               # Get twitter aftershocks
               if twt_params["options"]:
                  location=(lat, lon, radius, "km")
                  aftershocks.extend(process_twitter_form(
                        twt_params, location
                     )
                  )

               # Get gsf aftershocks
               aftershocks.extend(process_gsf_form(
                    gsf_aftershock_params, aftershocks=True,
                    coords=[lon, lat], radius=radius
                  )
               )
               
               #exclude_fields(aftershocks, None)
               
               # Add the epicenter with added aftershocks to the package
               epicenter["properties"]["radius"] = radius*1000               
               epicenter["properties"]["related"] = { 
                  "type": "FeatureCollection",
                  "features": aftershocks
               }
               results.append(epicenter)
         else:
            results = epicenters
         
         #exclude_fields(results, None)
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
                  "back_url":"/"
                })
   else:
      gsf_epicenters_form = GSFFusionForm(prefix="gsf_epicenters")
      gsf_aftershocks_form = GSFFusionForm(prefix="gsf_aftershocks")

      twitter_epicenters_form = TwitterFusionForm(prefix="twitter_epicenters")
      twitter_aftershocks_form = TwitterFusionForm(prefix="twitter_aftershocks")
      
      misc_form = MiscForm(prefix="misc_form")
      misc_fields = list(misc_form)

   return render(request, "home/index.html",
                 {
                  "gsf_epicenters_form": gsf_epicenters_form,
                  "gsf_aftershocks_form": gsf_aftershocks_form,
                  "twitter_epicenters_form": twitter_epicenters_form,
                  "twitter_aftershocks_form": twitter_aftershocks_form,
                  "radius": misc_fields[0],
                  "addresses": misc_fields[1],
                 })

"""
   The home page query UI controller.
      - Handles queries on local db
      - Handles queries for the retriever
"""
def twitter(request):
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
            except Exception, e:
               # If the geocoder API doesn't return with results
               # return the user to home page with the address error flag
               logger.error(e)
               message = """The address you gave us is in another
                            dimension. Try again with an earthly address please."""
               return render(request, "home/errors.html",
                        {"url": "/twitter/", "message": message})

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
                     {"url": "/twitter/", "message": message})

         # Get twitter data
         data = None
         try:
            data = retriever.get(("Twitter",),
                                 keyword=keywords, 
                                 what=params["what"],
                                 where=params["where"])
         except Exception, e:
            logger.debug(e)

         # Return to error page if no tweets were found
         if not data or not data["features"]:
            message = """Either you gave us a lousy query or
                         we sucked at finding results for you."""
            return render(request, "home/errors.html",
                     {"url": "/twitter/", "message": message})

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
         # Creat the path for the visualizer data and write to file
         base_path = os.path.join(BASE_DIR, "static", "vizit", "data")
         vizit_file = dump_data_to_file("points_", base_path, package)

         # redirect user to the visualizer
         # if mobile device detected, redirect to touchscreen version
         if request.mobile:
            redr_path = "/static/vizit/index.html?data=" + vizit_file
            return HttpResponseRedirect(redr_path)
         else:
            return render(request, "home/vizit.html", 
               {
                  "vizit_file":vizit_file,
                  "back_url":"/twitter/",
               })
   else:
      form = TwitterForm()

   return render(request, "home/twitter.html", {"form":form})

"""
   Allow the site admin to send set of coordinates to field
   agents available in the database
"""   
def send_coordinates(request):
   if request.user.is_superuser:
      key = request.GET.get("key")
      coords_id = request.GET.get("id")
      # TODO: add error checking
      agent = APIKey.objects.get(key=key)

      # Send text message with the coordinates id to the agent
      sender = "GSF Admin"
      message = "comsdpllnl://?" + str(coords_id)
      address = agent.phone_number+agent.cell_carrier
      if agent.cell_carrier == "@tmomail.net":
         address = "1" + address
      recipient = [address]
 
      send_mail("", message, sender, recipient)

      return render(request, "home/coords-sent.html",
                 {
                  "agent":agent,
                 })
   else:
      raise PermissionDenied
      

