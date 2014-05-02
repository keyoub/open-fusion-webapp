from django.contrib import admin
from django.db import IntegrityError
from api.models import APIKey
from random import randint

def generate_key():
   return str(randint(100000, 99999999))

class APIKeyAdmin(admin.ModelAdmin):
   fieldsets = (
      ('Generate iOS API Key', {
         'fields': ('full_name', 'email', 'phone_number', 'cell_carrier',
                      ('application', 'organization', 'key'))
      }),
   )

   readonly_fields = ('key', 'application', 'organization')
   
   list_display = ('full_name', 'organization', 'email', 'phone_number', 'cell_carrier', 
                   'application', 'key', 'upload', 'download')

   list_filter  = ('upload', 'download', 'application')

   search_fields = ['dev_name', 'application', 'email', 'organization',
                    'phone_number', 'cell_carrier']

   # Generate API key and prefill the static fields
   def save_model(self, request, obj, form, change):
      obj.key = generate_key()
      obj.application = "iPhone"
      obj.organization = "LLNL"
      obj.upload = True
      obj.save()

admin.site.register(APIKey, APIKeyAdmin)
