from autoperry.settings import *

from autoperry.production_secrets import *

DEBUG = False

ALLOWED_HOSTS = ['autoperry.cambridgeringing.info']

STATIC_ROOT = '/home/jonw/www/autoperry-static.cambridgeringing.info/static/'
STATIC_URL = '//autoperry-static.cambridgeringing.info/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jonw',
        'USER': 'jonw',
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

host: 'smtp-auth.mythic-beasts.com'
port: '587'
username: 'autoperry@cambridgeringing.info'
password: EMAIL_PASSWORD
use_tls: True
