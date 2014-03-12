from django.contrib import admin
from api.models import Features, APIKey

class APIKeyAdmin(admin.ModelAdmin):
   fields = ['application', 'organization',
             'dev_name', 'email', 'upload', 'download']

admin.site.register(APIKey, APIKeyAdmin)
