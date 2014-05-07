from mongoengine import *
from gsf.settings import MONGODB_NAME
from django.db import models

import datetime, dateutil.parser

connect(MONGODB_NAME)

"""
   The properties of a location
"""
class Properties(EmbeddedDocument):
   date_added  = DateTimeField()
   source      = StringField(required=True, max_length=50)
   time        = StringField(required=True)
   altitude    = DecimalField(precision=5)
   h_accuracy  = DecimalField(precision=5)
   v_accuracy  = DecimalField(precision=5)
   text        = StringField(max_length=1000)
   image       = StringField()
   noise_level = DecimalField(precision=5)
   temperature = DecimalField(precision=5)
   humidity    = DecimalField(precision=5)
   faces_detected  = IntField()
   people_detected = IntField()
   
   def clean(self):
      """Saves the ISO time string as django DateTimeField"""
      self.date_added = dateutil.parser.parse(self.time)
      
"""
   The main geoJSON formated data 
"""
class Features(Document):
   type        = StringField(default="Feature")
   geometry    = PointField(required=True)
   properties  = EmbeddedDocumentField(Properties)

"""
   Coordinates to be sent to field agents
"""
class Coordinates(Document):
   type        = StringField(default="GeometryCollection")
   geometries  = ListField(PointField())
   date_added  = DateTimeField(default=datetime.datetime.utcnow())
   
"""  
   Retriever queries enterd by users, stored to use for 
   building the local cache of open data
"""
class OgreQueries(Document):
   date_added = DateTimeField(default=datetime.datetime.utcnow())
   sources    = ListField(StringField())
   media      = ListField(StringField())
   keyword    = StringField()
   location   = ListField(FloatField())
   
   @queryset_manager
   def objects(doc_cls, queryset):
      return queryset.order_by("-date_added")
      

"""
   The SQL model for API Keys so that Django
   admin library can be used
"""
class APIKey(models.Model):
   CARRIER_CHOICES = (
      ("@txt.att.net", "AT&T"),
      ("@vtext.com", "Verizon"),
      ("@messaging.sprintpcs.com", "Sprint"),
      ("@tmomail.net", "T-Mobile"),
   )

   date_created = models.DateTimeField(default=datetime.datetime.now)
   key          = models.CharField(max_length=38, unique=True)
   application  = models.CharField(max_length=200)
   organization = models.CharField(max_length=200)
   full_name    = models.CharField(max_length=200)
   phone_number = models.CharField(max_length=10, 
      help_text="Only 10 digit number. No spaces or dashes. Eg. 8008889999")
   cell_carrier = models.CharField(max_length=50,
                                   choices=CARRIER_CHOICES)
   email        = models.EmailField()
   upload       = models.BooleanField(default=False)
   download     = models.BooleanField(default=True)

   class Meta:
      ordering = ('date_created',)
