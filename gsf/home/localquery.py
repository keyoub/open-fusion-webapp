from api.models import Features, Coordinates, OgreQueries
import logging, random

logger = logging.getLogger(__name__)

"""
   Drop unwanted fields from query documents
"""
def exclude_fields(data, keys):
   for d in data:
      if keys:
         for k in keys:
            d["properties"].pop(k, None)
      d.pop("_id", None)
      d["properties"].pop("date_added", None)

"""
   Query the local db for cached third party data before
   passing requests to the retriever
"""
def query_cached_third_party(source, keyword, options, location):
   # Get cached data 
   data_set = Features.objects(properties__source=source)
   if location:
      coords = [location[1], location[0]]
      radius = location[2]
      data_set = data_set(geometry__geo_within_sphere=[coords, radius/6371.0])
   if "image" in options and "text" not in options:
      data_set = data_set(properties__image__exists=True)
   if keyword:
      data_set = data_set(properties__text__icontains=keyword)
      
   data_set = list(data_set.as_pymongo())
   random.shuffle(data_set)
   
   exclude_fields(data_set, None)
   
   return data_set
   
"""
   Query the local db for images
"""
def query_for_images(faces, bodies, geo, coords, radius):
   data_set = Features.objects(properties__image__exists=True)
   if geo:
      data_set = data_set(geometry__geo_within_sphere=[coords, radius/6371.0])
   EXCLUDE = [
      "humidity",
      "noise_level",
      "temperature"
   ]
   data = []
   if faces:
      data_set = data_set(properties__faces_detected__gt=0)
      #data.extend(data_set(properties__faces_detected__gt=0).as_pymongo())
   if bodies:
      data_set = data_set(properties__people_detected__gt=0)
      #data.extend(data_set(properties__people_detected__gt=0).as_pymongo())
   data.extend(data_set.as_pymongo())
   exclude_fields(data, EXCLUDE)
   return data

"""
   Query the local db for non-image data
"""
def query_numeric_data(keyword, logic, value,
                       exclude_list, geo, coords, radius):
   data_set = Features.objects.all()
   if geo:
      data_set = data_set(geometry__geo_within_sphere=[coords, radius/6371.0])
   query_string = "properties__" + keyword + logic
   kwargs = { query_string: value }
   data_set = data_set.filter(**kwargs).as_pymongo()
   exclude_fields(data_set, exclude_list)
   return data_set
