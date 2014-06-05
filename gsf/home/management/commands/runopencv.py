from django.core.management.base import BaseCommand, CommandError
from api.models import Features
from detect import census
from base64 import b64decode
from gsf.settings import BASE_DIR
import logging, os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
   args = "number_of_images"
   help = "Run OpenCV on newly added images to the database."
   
   def handle(self, *args, **options):
      try:
         number_of_images = 100

         for num in args:
            number_of_images = int(num)

         images = Features.objects(properties__image__exists=True,
            properties__opencv_flag=False)[:number_of_images]
         
         for image in images:
            img = b64decode(image.properties.image)
            folder = "home/management/commands/tempdata/temp.jpg"
            path = os.path.join(BASE_DIR, folder)
            with open(path, 'wb') as f:
               f.write(img)
            f.close()
            results = census(path, "alt")
            faces = results[0]
            bodies = results[1]
            
            if image.properties.faces_detected or \
               image.properties.people_detected:
               avg_faces  = (image.properties.faces_detected + faces)/2
               avg_bodies = (image.properties.people_detected + bodies)/2
               image.properties.faces_detected = avg_faces
               image.properties.people_detected = avg_bodies
            else:
               image.properties.faces_detected = faces
               image.properties.people_detected = bodies
               
            image.properties.opencv_flag = True
            image.save()

         logger.info("runopencv completed on %d images." % len(images))
      except Exception as e:
         logger.debug(e)
   
