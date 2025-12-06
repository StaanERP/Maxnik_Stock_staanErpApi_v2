import threading
from django.apps import AppConfig


class Itemmaster2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itemmaster2'
    def ready(self):
        from itemmaster2.scheduler import start_scheduler_in_itemmaster2
        scheduler_thread = threading.Thread(target=start_scheduler_in_itemmaster2, daemon=True)
        scheduler_thread.start()
