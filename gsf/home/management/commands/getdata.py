from django.core.management.base import BaseCommand, CommandError
from api.models import OgreQueries, Features
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
   help = "Gets data using the retriever and saved user queries"
   
   def handle(self, *args, **options):
      queries = OgreQueries.objects.all().as_pymongo()
      #logger.debug(queries)
      for query in queries:
         # TODO: add limit to number of queries to run
         query.pop("_id", None)
         query.pop("date_added", None)
         query["location"].append("km")
         query["quantity"] = 15
         #logger.debug(query)
         
      
   
