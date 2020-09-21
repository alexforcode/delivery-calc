from .base import *


DEBUG = False


ADMINS = (
    ('Girin A', 'girin@tp-iv.ru'),
)

ALLOWED_HOSTS = ['calcproject.com', 'www.calcproject.com']


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '-%212$0pkr28-r2oi+5ksiv4uy8wd)!r!%m%0hxjy^7m)5t16+')


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'djcalc',
        'USER': 'djalex',
        'PASSWORD': 'WB9uf47Gyf',
        'HOST': '127.0.0.1',
    }
}
