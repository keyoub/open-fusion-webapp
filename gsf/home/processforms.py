from localquery import *
from remotequery import *
from api.models import OgreQueries
import logging, io, os, hashlib, datetime, json, random

logger = logging.getLogger(__name__)

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

   if faces or bodies:
      results.extend(
         query_for_images(
            faces, bodies, geo=aftershocks,
            coords=coords, radius=radius
         )
      )

   generic_list = ["temperature", "humidity", "noise_level"]
   exclude_list = ["image", "faces_detected", "people_detected"] 
   for k,v in params.items():
      if (k in generic_list) and v:
         results.extend(
            query_numeric_data(
               k, params[k+"_logic"], v, exclude_list,
               geo=aftershocks, coords=coords, radius=radius
            )
         )
         

   beautify_results(results)

   return results

"""
   Process the two Twitter Forms
"""
def process_twitter_form(params, location, metadata, live_search_flag):
   data, cached_tweets, live_tweets = [], [], []

   # Save the user query for cache buliding system
   try:
      query = OgreQueries(sources=["Twitter"],
         media=params["options"],
         keyword=params["keywords"],
         metadata=metadata,
         location=location[:-1] if location else None)
      query.save()
   except Exception, e:
      logger.debug(e)
   
   if live_search_flag:
      live_tweets = query_third_party(
         ("Twitter",), params["keywords"], params["options"], 
         location, None, 1
      )
      data.extend(live_tweets[1])
   else:
      cached_tweets = query_cached_third_party(
         "Twitter", params["keywords"], 
         params["options"], location
      )     
      data.extend(cached_tweets[:30])
      
   return data

"""
   Write the Geojson data to the filesystem   
"""
def dump_data_to_file(name, base_path, package):
   # Build unique output file name using user ip and timestamp      
   now = str(datetime.datetime.now()) 
   file_name = name + \
      str(hashlib.sha1(now+str(random.random())).hexdigest()) + ".geojson"

   # Write data to the file
   path = os.path.join(base_path, file_name)
   
   with io.open(path, "w") as outfile:
      outfile.write(unicode(json.dumps(package,
         indent=4, separators=(",", ": "))))
         
   outfile.close()

   return file_name
