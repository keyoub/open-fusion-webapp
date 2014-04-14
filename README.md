Open Fusion Web Application
===========================
**The Django web application suite for the Geotagged Sensor Fusion senior design project.**

Installation
------------
Follow the steps below and you should have a fully running Open Fusion web app in no time. 
Just keep in mind that you will need a fully operational mongodb backend before you can run the web app.

1. `git clone https://github.com/bkeyoumarsi/open-fusion-webapp`
2. `pip install mongoengine`
3. `pip install ogre`
4. `pip install django-bootstrap3-datetimepicker`
5. `pip install django-bootstrap3`
6. `pip install django-admin-bootstrapped`
7. `pip install minidetector`
8. `pip install pygeocoder`
9. `pip install recaptcha-client`
10. `cd gsf/static/; git clone https://github.com/dmtucker/vizit.git`
11. Create a database in mongodb and create a super user for that db.
    Add the super user and password and the name of the db as parameters
    in a file called `local_settings.py` within the gsf/gsf/ directory

