from django.contrib import admin
from api.models import Features, APIKey
from random import randint

class APIKeyAdmin(admin.ModelAdmin):
   fieldsets = (
      ('Generate iOS API Key', {
         'fields': ('application', 'organization',
                    'dev_name', 'email','key')
      }),
   )

   readonly_fields = ('key',)
   
   list_display = ('dev_name', 'email', 'key')

   def save_model(self, request, obj, form, change):
      obj.key = randint(10000000, 99999999)
      obj.upload = True
      obj.save() 

admin.site.register(APIKey, APIKeyAdmin)
