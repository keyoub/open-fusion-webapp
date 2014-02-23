from rest_framework import serializers
from api.models import Data

from decimal import Decimal 

class Point(object):
   """
   A point coordinate represented as [x, y]
   """
   def __init__(self, type, x, y):
      assert(type == "Point")
      assert(x >= -180 and y >= -90)
      assert(x <= 180 and y <= 90)
      self.point['type'] = type
      self.point['coordinates'] = [x, y]

class PointField(serializers.WritableField):
   """
   Point field is serialized into 
   """
   def to_native(self, obj):
      return obj.point

   def from_native(self, data):
      #data = data.strip('[').rstrip(']')
      #x, y = [Decimal(num) for num in data.split(',')]
      #return Point(data['type'], data['coordinates'])
      pass

"""class LocationSerializer(serializers.Serializer):
   type        = serializers.CharField(required=True)
   #coordinates = PointField(required=True)
   coordinates = [serializers.DecimalField(), serializers.DecimalField()]
   
   def restore_object(self, attrs, instance=None):
      return "{\"type\": \"%s\", \"coordinates\": [%d, %d]}" \
               % (attrs['type'], attrs.['coordinates'].[0], attrs.['coordinates'].[1])"""

class DataSerializer(serializers.Serializer):
   source      = serializers.CharField(required=True, max_length=50)
   #location    = PointField(required=True)
   location    = {
                  'type': 'Point',
                  'coordinates': [serializers.DecimalField(), serializers.DecimalField()]
                 }
   altitude    = serializers.DecimalField(required=False)
   h_accuracy  = serializers.DecimalField(required=False)
   v_accuracy  = serializers.DecimalField(required=False)
   timestamp   = serializers.IntegerField(required=True)
   text        = serializers.CharField(required=False, max_length=1000)
   image       = serializers.ImageField(required=False)
   noise_level = serializers.DecimalField(required=False)
   temperature = serializers.DecimalField(required=False)
   humidity    = serializers.DecimalField(required=False)
   population  = serializers.IntegerField(required=False)

   def restore_object(self, attrs, instance=None):
      return Data(**attrs)
      #data = Data(source=attrs['source

