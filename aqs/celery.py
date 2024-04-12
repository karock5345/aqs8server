# celery.py
import os
from celery import Celery, chain
import logging
from aqs.settings import celery_name

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aqs.settings')

# Create a Celery instance and configure it to use the Django settings
app = Celery(celery_name)

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps (tasks.py files).
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    # print(f'Request: {self.request!r}')
    logger.info(f'Request: {self.request!r}')




