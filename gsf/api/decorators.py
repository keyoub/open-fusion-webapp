from django.http import HttpResponseForbidden, HttpResponseBadRequest
from api.models import APIKey

allowed_methods = ['POST', 'GET']

class auth_required(object):
   def __init__(self, func):
      self.func = func

   def __call__(self, request, *args, **kwargs):
      if request.method in allowed_methods:
         if request.method == 'POST':
            try:
               key = request.META['HTTP_AUTHORIZATION']
            except:
               return HttpResponseForbidden("Missing HTTP Authorization\n")

            if key == None:
               return HttpResponseForbidden("Invalid or disabled app key\n")
            
            #Check if the user provided API key has access to the view being called
            try:
               APIKey.objects.get(key=key, upload=True)
            except APIKey.DoesNotExist:
               return HttpResponseForbidden(
                     "You do not have permission to access the %s API" % self.func.__name__)
         else:
            key = request.GET.get('key')

            if key == None:
               return HttpResponseForbidden("Invalid or disabled app key\n")
            
            #Check if the user provided API key has access to the view being called
            try:
               APIKey.objects.get(key=key, download=True)
            except APIKey.DoesNotExist:
               return HttpResponseForbidden(
                     "You do not have permission to access the %s API" % self.func.__name__)

         return self.func(request, *args, **kwargs)
      else:
         return HttpResponseBadRequest("Request method not supported\n")
