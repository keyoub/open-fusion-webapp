from django.core.management.base import BaseCommand, CommandError
from gsf.settings import TWITTER_CONSUMER_KEY, TWITTER_ACCESS_TOKEN
from api.models import OgreQueries, Features
from twython import TwythonRateLimitError
from ogre import OGRe
from ogre.exceptions import OGReLimitError
import logging, json, datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
   args = "number_of_queries"
   help = "Gets data using the retriever and the saved user queries"
   
   def handle(self, *args, **options):        
      query_limit = 1
      number_of_queries = 100
      
      for number in args:
         number_of_queries = number
               
      retriever = OGRe ({
         "Twitter": {
            "consumer_key": TWITTER_CONSUMER_KEY,
            "access_token": TWITTER_ACCESS_TOKEN,
         }
      })
      
      queries = OgreQueries.objects.all().as_pymongo()[:number_of_queries]
      for query in queries:
         query.pop("_id", None)
         query.pop("date_added", None)
         query.pop("ip", None)
         if query.get("location", None):
            query["location"].append("km")
         else:
            query.pop("location", None)
         query["quantity"] = query_limit*100
         query["query_limit"] = query_limit
         query["fail_hard"] = True
         
         # Get tweets from twitter
         tweets = {}
         try:
            tweets = retriever.fetch(**query)
         except (OGReLimitError, TwythonRateLimitError) as e:
            logger.error(e)
            break
         except Exception, e:
            logger.error(e)
         
         # Cache the data in db
         for tweet in tweets.get("features", []):
            kwargs = {
                     "geometry": tweet["geometry"],
                     "properties__time": tweet["properties"]["time"],
                     "properties__text": tweet["properties"]["text"],
                     }
            if not Features.objects.filter(**kwargs):
               feature = Features(**tweet)
               try:
                  feature.save()
               except Exception, e:
                  logger.debug(e)
         
         
      
   
