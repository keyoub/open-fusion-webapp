from localquery import *
from remotequery import *
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
   Process the two Twitter Forms
"""
def process_twitter_form(params, location):
   data, cached_tweets, live_tweets = [], [], []
   
   # First search the local cache and if no results are found,
   # pass the query to the OGRe
   cached_tweets = query_cached_third_party(
      "Twitter", params["keywords"], 
      params["options"], location
   )
   if len(cached_tweets) is 0:
      live_tweets = query_third_party(
         ("Twitter",), params["keywords"], params["options"], 
         location, None, None, False
      )
      data.extend(live_tweets[1])
      """if (result[0] != "") and (len(result[1]) == 0):
         return render(request, "home/errors.html",
            {"url": "/", "message": result[0]})"""
   data.extend(cached_tweets)
      
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