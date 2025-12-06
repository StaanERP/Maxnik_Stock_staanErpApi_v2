import threading

from django.apps import AppConfig


class EnqurifromapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'EnquriFromapi'

    def ready(self): 
        from EnquriFromapi.scheduler import start_scheduler

        # Start the scheduler in a new thread to prevent blocking
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()

