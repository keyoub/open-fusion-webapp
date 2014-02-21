from mongoengine import *
from gsf.settings import MONGODB_NAME

import datetime

connect(MONGODB_NAME)

# The Data collection layout
class Data(Document):
   date_added  = DateTimeField(default=datetime.datetime.now)
   source      = StringField(max_length=50, required=True)
   #latitude    = DecimalField(precision=10, required=True)
   #longitude   = DecimalField(precision=10, required=True)
   location    = PolygonField()
   timestamp   = IntField()
   text        = StringField(max_length=500)
   image       = ImageField()
   noise_level = DecimalField(precision=5)
   temperature = DecimalField(precision=5)
   humidity    = DecimalField(precision=5)
   population  = IntField()

   class Meta:
      ordering = ('date_added',)
