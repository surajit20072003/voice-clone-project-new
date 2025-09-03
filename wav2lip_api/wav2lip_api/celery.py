import os
from celery import Celery

# Django settings ko Celery ke liye set karein
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wav2lip_api.settings')

# Celery application instance banayein
app = Celery('wav2lip_api')

# Django settings se configuration load karein
app.config_from_object('django.conf:settings', namespace='CELERY')

# Sabhi installed apps mein tasks.py files ko automatically dhoondein aur register karein
app.autodiscover_tasks()
