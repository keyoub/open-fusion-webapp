from django.contrib import admin
from api.models import Features, APIKey
from random import randint

class APIKeyAdmin(admin.ModelAdmin):
   fieldsets = (
      ('Generate iOS API Key', {
         'fields': ('dev_name', 'email',
                      ('application', 'organization', 'key'))
      }),
   )

   readonly_fields = ('key', 'application', 'organization')
   
   list_display = ('dev_name', 'email', 'application', 'key', 'upload', 'download')

   list_filter  = ('upload', 'download', 'application')

   search_fields = ['dev_name', 'application', 'email', 'organization']

   save_on_top = True

   def save_model(self, request, obj, form, change):
      obj.key = randint(10000000, 99999999)
      obj.application = "iPhone"
      obj.organization = "LLNL"
      obj.upload = True
      obj.save() 

admin.site.register(APIKey, APIKeyAdmin)
