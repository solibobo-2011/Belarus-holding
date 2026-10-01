# blog/apps.py fayli ichida:
from django.apps import AppConfig

class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'  # Bu yerda ham 'apps.blog' emas, shunchaki 'blog' bo'lishi shart!
