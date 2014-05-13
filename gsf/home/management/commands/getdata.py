from django.core.management.base import BaseCommand, CommandError
from gsf.settings import TWITTER_CONSUMER_KEY, TWITTER_ACCESS_TOKEN
from api.models import OgreQueries, Features
from ogre import OGRe
import logging, json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
   args = "query_limit"
   help = "Gets data using the retriever and saved user queries"
   
   def handle(self, *args, **options):
      query_limit = 1
      for limit in args:
         query_limit = limit
         
      retriever = OGRe ({
         "Twitter": {
            "consumer_key": TWITTER_CONSUMER_KEY,
            "access_token": TWITTER_ACCESS_TOKEN,
         }
      })
      
      queries = OgreQueries.objects.all().as_pymongo()[:350]
      for query in queries:
         # TODO: add limit to number of queries to runl
         query.pop("_id", None)
         query.pop("date_added", None)
         if query.get("location", None):
            query["location"].append("km")
         else:
            query.pop("location", None)
         query["quantity"] = query_limit*100
         query["query_limit"] = query_limit
         
         # Get tweets from twitter
         tweets = {}
         try:
            tweets = retriever.fetch(**query)
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
         
         
      
   
