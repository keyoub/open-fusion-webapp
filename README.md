OpenFusion
==========

The Django Web Application for the 2014 Geotagged Sensor Fusion Senior Design Project at UCSC


Deployment
------------

Getting started is quick and easy.

Clone this repository:
``` sh
git clone --recursive https://github.com/bkeyoumarsi/open-fusion-webapp
cd open-fusion-webapp
mkdir -p data/db
```

Use Docker to create an instance of MongoDB:
``` sh
$ docker-compose run -d --name openfusion_db_setup db
$ docker exec -it openfusion_db_setup /bin/bash
```

Create a database in MongoDB, and create a super user for that database:
``` sh
sleep 120 # mongod usually takes a moment to start.
mongo
```
```
use openfusion
db.createUser(
  {
    user: "<username>",
    pwd: "<password>",
    roles: [
      {
        role: "root",
        db: "admin"
      }
    ]
  }
)
exit
```
``` sh
exit
```

Stop the MongoDB container (a new one will be created in a moment):
``` sh
docker stop openfusion_db_setup
```

Create `gsf/gsf/local_settings.py` to configure Django:
``` python
SECRET_KEY = '<pick-a-key>'

_MONGODB_USER = '<username>'
_MONGODB_PASSWD = '<password>'
_MONGODB_HOST = 'db'
MONGODB_NAME = 'openfusion'
MONGODB_DATABASE_HOST = \
    'mongodb://%s:%s@%s/%s' \
    % (_MONGODB_USER, _MONGODB_PASSWD, _MONGODB_HOST, MONGODB_NAME)

reCAPTCHA_KEY = '<reCaptcha-key>'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = '<Gmail-for-Developers-username>'
EMAIL_HOST_PASSWORD = '<password>'
EMAIL_PORT = 587

TWITTER_CONSUMER_KEY = '<consumer-key>'
TWITTER_ACCESS_TOKEN = '<access-token>'
```

Bring everything up with Docker Compose:
``` sh
docker-compose up
```

Open a browser and navigate to http://localhost:8000/.
