Open Fusion Web Application
===========================
**The Django web application suite for the Geotagged Sensor Fusion senior design project.**

Installation
------------
Follow the steps below and you should have a fully running Open Fusion web app in no time. 
Just keep in mind that you will need a fully operational mongodb backend before you can run the web app.

1. `git clone --recursive https://github.com/bkeyoumarsi/open-fusion-webapp`
2. `pip install mongoengine`
3. `pip install ogre`
4. `pip install django-bootstrap3-datetimepicker`
5. `pip install django-bootstrap3`
6. `pip install django-admin-bootstrapped`
7. `pip install minidetector`
8. `pip install pygeocoder`
9. `pip install recaptcha-client`
10. Create a database in mongodb and create a super user for that db.
11. Add the super user and password and the name of the db as parameters
    in a file called `local_settings.py` within the gsf/gsf/ directory. Your `local_settings.py`
    file should look like the following:
    ```python
    SECRET_KEY = <create your own secret key>

    _MONGODB_USER = <super user>
    _MONGODB_PASSWD = <super user password>
    _MONGODB_HOST = 'localhost'
    MONGODB_NAME = <name of the mongodb database you created>
    MONGODB_DATABASE_HOST = \
        'mongodb://%s:%s@%s/%s' \
        % (_MONGODB_USER, _MONGODB_PASSWD, _MONGODB_HOST, MONGODB_NAME)

    reCAPTCHA_KEY = <your reCaptcha key>

    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = <your gmail for developers signup form>
    EMAIL_HOST_PASSWORD = <your gmail password>
    EMAIL_PORT = 587

    TWITTER_CONSUMER_KEY = <your consumer key>
    TWITTER_ACCESS_TOKEN = <your access token>

