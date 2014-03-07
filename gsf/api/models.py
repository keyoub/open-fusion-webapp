from mongoengine import *
from gsf.settings import MONGODB_NAME

import datetime, base64, hashlib, random

connect(MONGODB_NAME)

# The Data collection layout
class Data(Document):
   date_added  = DateTimeField(default=datetime.datetime.now)
   source      = StringField(required=True, max_length=50)
   timestamp   = DecimalField(required=True)
   location    = PointField(required=True)
   altitude    = DecimalField(precision=5)
   h_accuracy  = DecimalField(precision=5)
   v_accuracy  = DecimalField(precision=5)
   text        = StringField(max_length=1000)
   o_image     = StringField()
   p_image     = StringField()
   f_image     = StringField()
   noise_level = DecimalField(precision=5)
   temperature = DecimalField(precision=5)
   humidity    = DecimalField(precision=5)
   faces_detected  = IntField()
   people_detected = IntField()

   class Meta:
      ordering = ('date_added',)

"""
   API Key random generator
"""
def generate_key():
   key = base64.b64encode(hashlib.sha256( \
            str(random.getrandbits(256)) ).digest(), \
            random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
   return key

class APIKey(Document):
   date_created = DateTimeField(default=datetime.datetime.now)
   key          = StringField()
   application  = StringField(required=True, max_length=100)
   organization = StringField(max_length=100)
   dev_name     = StringField(required=True, max_length=200)
   email        = EmailField(required=True)

   class Meta:
      ordering = ('date_created',)
   
   def save(self, *args, **kwargs):
      self.key = generate_key()
      #while not APIKey.objects(key__exists=self.key):
      #   self.key = generate_key()
      super(APIKey, self).save(*args, **kwargs)


