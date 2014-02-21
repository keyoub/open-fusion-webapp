from rest_framework import serializers

from api.models import Data

class DataSerializer(serializers.ModelSerializer):

	class Meta:
		model = Data
		fields = ('')


