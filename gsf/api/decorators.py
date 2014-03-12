from django.http import HttpResponseForbidden, HttpResponseBadRequest
from api.models import APIKey

class auth_required(object):

   def __init__(self, func):
      self.func = func

   def __call__(self, request, *args, **kwargs):
      if request.method == 'POST':
         key = request.POST.get('key', None)
         
         if key == None:
            return HttpResponseForbidden("Invalid or disabled app key")
         
         #Check if the user provided API key has access to the view being called
         try:
            APIKey.objects.get(key=key).allowed_fcns.get(
                                                   name=self.func.__name__)
         except APIKey.DoesNotExist:
            return HttpResponseForbidden(
                  "You do not have permission to access that API")
            
         return self.func(request, *args, **kwargs)
   elif request.method == 'GET':
      pass
   else:
      return HttpResponseBadRequest("Operation not supported\n")
