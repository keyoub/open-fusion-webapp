from mongoengine import *
from gsf.settings import _MONGODB_NAME

import datetime

connect(_MONGODB_NAME)

# The Data collection layout
class Data(Document):
	source      = StringField(max_length=50, required=True)
	latitude    = DecimalField(precision=10, required=True)
	longitude   = DecimalField(precision=10, required=True)
	timestamp   = DateTimeField(default=datetime.datetime.now)
	text        = StringField(max_length=500)
	image       = ImageField()
	noise_level = DecimalField(precision=5)
	temperature = DecimalField(precision=5)
	humidity    = DecimalField(precision=5)
	population  = IntField()
