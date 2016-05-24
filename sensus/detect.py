#!/usr/bin/env python

""""""

import sys
import logging
import os
import time
import cv2


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
    """"""
    return cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml').detectMultiScale(image)


def detect_frontalface(image, cascade='alt'):  # default | alt | alt2 | alt_tree
    """"""
    if image.size < 1:
        return []
    return cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_'+cascade+'.xml').detectMultiScale(image)
    #return cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_'+cascade+'.xml').detectMultiScale(
    #    image,
    #    scaleFactor=1.07,  # (1,2] lower means missed faces less likely, non-faces more likely (lower takes longer too)
    #    minNeighbors=5     # [3,6] lower means missed faces less likely, non-faces more likely
    #)


def detect_people(image):

    """"""

    if image.size < 1:
        return []

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return hog.detectMultiScale(image)[0]
    #return hog.detectMultiScale(
    #    image,
    #    winStride=(8, 8),
    #    padding=(32, 32),
    #    scale=1.05
    #)[0]

    #return [(rx, ry, rw, rh) for (rx, ry), (rw, rh) in list(cv2.cv.HOGDetectMultiScale(
    #    cv2.cv.fromarray(image),
    #    cv2.cv.CreateMemStorage(0),
    #    hit_threshold=0.5,
    #    group_threshold=2
    #))]

    #cascades = {
    #    'fullbody': cv2.CascadeClassifier('haarcascades/haarcascade_fullbody.xml'),
    #    'pedestrians': cv2.CascadeClassifier('hogcascades/hogcascade_pedestrians.xml')
    #}
    #return cascades['pedestrians'].detectMultiScale(image)


def census(filename, frontalface_cascade='alt'):

    """"""

    log = logging.getLogger(__name__)

    log.debug(filename+' Loading...')
    image = cv2.imread(filename)

    log.debug(filename+' Converting to grayscale...')
    gray = image_grayscale(image, True)

    log.debug(filename+' Detecting people...')
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
    log.info(
        filename+' '+str(len(people))+' people (' +
        str(probabilities[1])+' confirmed, ' +
        str(probabilities[0]+probabilities[2])+' probable, ' +
        str(probabilities[3])+' potential)'
    )

    log.debug(filename+' Detecting faces...')
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
    log.info(
        filename+' '+str(len(faces))+' faces (' +
        str(probabilities[2])+' confirmed, ' +
        str(probabilities[1]+probabilities[3])+' probable, ' +
        str(probabilities[0]+probabilities[4])+' potential)'
    )

    return image


if __name__ == '__main__':
    log_file = 'detection.log'
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    face_cascade = 'alt'
    folder = 'detected/'+str(int(time.time()*1000))+'.'+face_cascade
    if not os.path.exists(folder):
        os.makedirs(folder)
    arg_max = 0
    for arg in sys.argv[1:]:
        arg_len = len(arg)
        if arg_len > arg_max:
            arg_max = arg_len
    for arg in sys.argv[1:]:
        print('{filename:<'+str(arg_max)+'}').format(filename=arg),
        start = time.time()
        cv2.imwrite(os.path.join(folder, os.path.basename(arg)), census(arg, face_cascade))
        end = time.time()
        print '{runtime:>15.10f}s'.format(runtime=end-start)
    os.rename(log_file, folder+'/'+log_file)
