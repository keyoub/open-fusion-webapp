from rest_framework import serializers

from api import Data

class DataSerializer(serializers.ModelSerializer):

	class Meta:
		model = Data
		fields = ('')


