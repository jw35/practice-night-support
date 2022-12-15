from settings import *

from production_secrets import *

DEBUG = False

ALLOWED_HOSTS = ['autoperry.cambridgeringing.info']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

#host: EMAIL_HOST
#port: EMAIL_PORT
#username: EMAIL_HOST_USER
#password: EMAIL_HOST_PASSWORD
#use_tls: EMAIL_USE_TLS
#use_ssl: EMAIL_USE_SSL
#timeout: EMAIL_TIMEOUT
#ssl_keyfile: EMAIL_SSL_KEYFILE
#ssl_certfile: EMAIL_SSL_CERTFILE


