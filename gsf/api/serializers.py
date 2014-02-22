from rest_framework import serializers

from api.models import Data

class DataSerializer(serializers.Serializer):
   source = serializers.CharField(required=True, max_length=100)
   text   = serializers.CharField(required=False, max_length=500)

   def restore_object(self, attrs, instance=None):
      return Data(**attrs)
