import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')

# Create a dummy Celery app that doesn't actually connect to Redis
class DummyCelery:
    def __init__(self, *args, **kwargs):
        self.conf = type('obj', (object,), {
            'beat_schedule': {},
            'task_routes': {},
        })
        
    def autodiscover_tasks(self, *args, **kwargs):
        pass
        
    def config_from_object(self, *args, **kwargs):
        pass
        
    def task(self, *args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper.delay = lambda *a, **kw: None
            wrapper.apply_async = lambda *a, **kw: None
            return wrapper
        return decorator
        
    def shared_task(self, *args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper.delay = lambda *a, **kw: None
            wrapper.apply_async = lambda *a, **kw: None
            return wrapper
        return decorator

# Use the dummy Celery app
app = DummyCelery('fagierrandsbackup')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'clean-old-notifications': {
        'task': 'notifications.tasks.clean_old_notifications',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight every day
        'args': (30,),  # Keep notifications for 30 days
    },
    'calculate-daily-metrics': {
        'task': 'admin_dashboard.tasks.calculate_daily_metrics',
        'schedule': crontab(hour=1, minute=0),  # Run at 1 AM every day
    },
    'calculate-daily-metrics': {
        'task': 'admin_dashboard.tasks.calculate_daily_metrics',
        'schedule': crontab(hour=1, minute=0),  # Run at 1 AM every day
    },
}