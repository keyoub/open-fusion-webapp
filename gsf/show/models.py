from mongoengine import *
from gsf.settings import _MONGODB_NAME

import datetime

connect(_MONGODB_NAME)

class Data(Document):
	name = StringField(max_length=220, required=True)
	speech = StringField(max_length=500, required=True)
	timestamp = DateTimeField(default=datetime.datetime.now)
