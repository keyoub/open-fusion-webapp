import logging, cv2, os
from gsf.settings import BASE_DIR

folder = "home/management/commands/haarcascades/"
BASE_DIR = os.path.join(BASE_DIR, folder)

logger = logging.getLogger(__name__)

def image_show(image, title=None):
   """"""
   if title is None:
     title = str(image.shape[1])+'x'+str(image.shape[0])
   cv2.imshow(title, image)
   while True:
     key = cv2.waitKey()
     if key == 27 or key == ord('q'):  # Press esc or q to close.
         break
   cv2.destroyAllWindows()


def image_grayscale(image, equalize=False):
   """"""
   grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
   if equalize:
     grayscale = cv2.equalizeHist(grayscale)
   return grayscale


def detect_eyes(image):
   path = os.path.join(BASE_DIR, "haarcascade_eye.xml")
   return cv2.CascadeClassifier(path).detectMultiScale(image)


def detect_frontalface(image, cascade='alt'):  # default | alt | alt2 | alt_tree

   """"""
   
   if image.size < 1:
      return []
   path = os.path.join(BASE_DIR, "haarcascade_frontalface_"+cascade+".xml")
   return cv2.CascadeClassifier(path).detectMultiScale(image)

def detect_people(image):
   if image.size < 1:
      return []
   
   hog = cv2.HOGDescriptor()
   hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
   return hog.detectMultiScale(image)[0]


def census(filename, frontalface_cascade="alt"):
   
   """"""
   
   logger.debug(filename + " Decoding image")   
   image = cv2.imread(filename)
   
   logger.debug("Converting to grayscale...")
   gray = image_grayscale(image, True)
   
   logger.debug("Detecting people...")
   people = detect_people(gray)
   probabilities = [0, 0, 0, 0]
   for (px, py, pw, ph) in people:
     faces = len(detect_frontalface(gray[py:py+ph, px:px+pw], frontalface_cascade))
     probabilities[min(faces, 3)] += 1
     color = {  # BGR
         1: (0, 255, 0),
         2: (255, 0, 255)
     }.get(faces, (255, 0, 0))
     if color != (255, 0, 0):
         cv2.rectangle(image, (px, py), (px+pw, py+ph), color, 2)
         
   logger.info(
     str(len(people))+' people (' +
     str(probabilities[1])+' confirmed, ' +
     str(probabilities[0]+probabilities[2])+' probable, ' +
     str(probabilities[3])+' potential)'
   )
   
   logger.debug("Detecting faces...")
   faces = detect_frontalface(gray, frontalface_cascade)
   probabilities = [0, 0, 0, 0, 0]
   for (fx, fy, fw, fh) in faces:
     eyes = len(detect_eyes(gray[fy:fy+fh, fx:fx+fw]))
     probabilities[min(eyes, 4)] += 1
     color = {  # BGR
         1: (0, 255, 255),
         2: (0, 255, 0),
         3: (0, 255, 255)
     }.get(eyes, (0, 0, 255))
     center = ((fx+(fx+fw))/2, (fy+(fy+fh))/2)
     radius = (((fx-center[0])**2)+((fy-center[1])**2))**(1.0/2)
     cv2.circle(image, center, int(round(radius)), color, 2)
   logger.info(
     str(len(faces))+' faces (' +
     str(probabilities[2])+' confirmed, ' +
     str(probabilities[1]+probabilities[3])+' probable, ' +
     str(probabilities[0]+probabilities[4])+' potential)'
   )
   
   return [len(faces), len(people)]
