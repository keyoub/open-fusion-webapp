from ogre import OGRe
from api.views import logger
from api.models import Features
from pygeocoder import Geocoder
from localquery import query_cached_third_party
from twython import TwythonRateLimitError, TwythonError
from gsf.settings import TWITTER_CONSUMER_KEY, TWITTER_ACCESS_TOKEN

retriever = OGRe ({
   "Twitter": {
      "consumer_key": TWITTER_CONSUMER_KEY,
      "access_token": TWITTER_ACCESS_TOKEN,
   }
})
      
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
      logger.debug("Number of tweets requested from twitter %d" % quantity)
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

      # Cache the data in db
      for data in outside_data.get("features", []):
         kwargs = {
                  "geometry": data["geometry"],
                  "properties__time": data["properties"]["time"],
                  "properties__text": data["properties"]["text"],
                  }
         if not Features.objects.filter(**kwargs):
            feature = Features(**data)
            try:
               feature.save()
            except Exception, e:
               logger.debug(e)

      results.extend(outside_data.get("features", []))

   return (error, results)
   
"""
   Get epicenters from user inputed addresses using Google Maps API
"""
def create_epicenters_from_addresses(addresses):
   epicenters = []
   address_list = addresses.rstrip("\r\n").split("\n")
   for address in address_list:
      try:
         results = Geocoder.geocode(address)
         lat = float(results[0].coordinates[0])
         lon = float(results[0].coordinates[1])
         epicenter = {
            "type": "Feature",
            "geometry": {
               "type": "Point",
               "coordinates": [lon, lat]
            },
            "properties": {
               "text": address,
            }
         }
         epicenters.append(epicenter)
      except Exception, e:
         logger.debug(e)
   return epicenters
