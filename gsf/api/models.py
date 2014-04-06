from mongoengine import *
from gsf.settings import MONGODB_NAME
from django.db import models

import datetime

connect(MONGODB_NAME)

"""
   The properties of a location
"""
class Properties(EmbeddedDocument):
   date_added  = DateTimeField(default=datetime.datetime.now)
   source      = StringField(required=True, max_length=50)
   timestamp   = StringField(required=True)
   altitude    = DecimalField(precision=5)
   h_accuracy  = DecimalField(precision=5)
   v_accuracy  = DecimalField(precision=5)
   text        = StringField(max_length=1000)
   oimage      = StringField()
   pimage      = StringField()
   fimage      = StringField()
   noise_level = DecimalField(precision=5)
   temperature = DecimalField(precision=5)
   humidity    = DecimalField(precision=5)
   faces_detected  = IntField()
   people_detected = IntField()

"""
   The main geoJSON formated data 
"""
class Features(Document):
   type        = StringField(default="Feature")
   geometry    = PointField(required=True)
   properties  = EmbeddedDocumentField(Properties)

"""
   The SQL model for API Keys so that Django
   admin library can be used
"""
class APIKey(models.Model):
   date_created = models.DateTimeField(default=datetime.datetime.now)
   key          = models.CharField(max_length=38, unique=True)
   application  = models.CharField(max_length=200)
   organization = models.CharField(max_length=200)
   dev_name     = models.CharField(max_length=200)
   email        = models.EmailField()
   upload       = models.BooleanField(default=False)
   download     = models.BooleanField(default=True)

   class Meta:
      ordering = ('date_created',)
