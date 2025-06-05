from django.apps import AppConfig
from django.conf import settings
import os


class GestionaleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestionale'

# Application definition
INSTALLED_APPS = [
    'django_tables2',
    'django_filters',
    'gestionale',
]
BASE_DIR = settings.BASE_DIR
# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django-tables2
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4.html"

# Login redirect
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'