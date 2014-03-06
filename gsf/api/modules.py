"""
 Applications can request an API key to get data 
 from the Data collection
"""
def key_request(object):
   pass
   """if request.method == 'GET':
      application = request.GET.get('application')
      organization = request.GET.get('organization')
      dev_fullname = request.GET.get('developer')

      if not application or not dev_fullname:
         return HttpResponseBadRequest("Can't process request due to missing info.\n")

      # Check if the token for the app already exist
      if not Tokens.objects(application__exists=application):     
         # Generate secret token
         key = base64.b64encode(hashlib.sha256( \
                   str(random.getrandbits(256)) ).digest(), \
                   random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
         entry = Tokens(api_key=key) 
         entry.application = application
         entry.organization = organization
         entry.dev_fullname = dev_fullname
         try:
            entry.save()
            response_data = {}
            response_data['key'] = key
            return HttpResponse(json.dumps(response_data),
                                  content_type="application/json")
         except:
            return HttpResponseServerError("Your request could not be completed due"\
                        " to internal errors. Try again later.")
      else:
         return HttpResponse("You already have a token with us. If you have " \
                       "lost it please contact bkeyouma@ucsc.edu")
   else:
      return HttpResponseBadRequest("You can only get a token with GET request.\n")"""


