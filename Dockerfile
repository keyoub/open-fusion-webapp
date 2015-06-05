FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y apache2 python python-pip
RUN pip install mongoengine django-bootstrap3 django-bootstrap3-datetimepicker django-admin-bootstrapped minidetector pygeocoder recaptcha-client ogre
ADD gsf /var/www/gsf
RUN service apache2 start
EXPOSE 80
