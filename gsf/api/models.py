from mongoengine import *
from gsf.settings import MONGODB_NAME

import datetime

connect(MONGODB_NAME)

# Location accuracy and details structure used in the Data model
"""class LocationDetails(EmbeddedDocument):
   altitude    = DecimalField(precision=5)
   h_accuracy  = DecimalField(precision=5)
   v_accuracy  = DecimalField(precision=5)"""

# The Data collection layout
class Data(Document):
   date_added  = DateTimeField(default=datetime.datetime.now)
   source      = StringField(max_length=50)
   #location    = PointField(required=True)
   #loc_details = EmbeddedDocumentField(LocationDetails)
   #timestamp   = IntField(required=True)
   text        = StringField(max_length=500)
   image       = ImageField()
   noise_level = DecimalField(precision=5)
   temperature = DecimalField(precision=5)
   humidity    = DecimalField(precision=5)
   population  = IntField()

   class Meta:
      ordering = ('date_added',)


