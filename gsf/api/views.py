from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import Data
from api.serializers import DataSerializer


# Receive data from iOS app and store in db
@api_view(['POST'])
def upload(request):
   if request.method == 'POST':
      serializer = DataSerializer(data=request.DATA)
      if serializer.is_valid():
         serializer.save()
         return Response(status.status.HTTP_201_CREATED)
      else:
         return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
			
	
