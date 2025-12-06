from django.apps import AppConfig
import threading

class ItemmasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itemmaster'
    def ready(self):
        from itemmaster.scheduler import start_scheduler_in_itemmaster
        scheduler_thread = threading.Thread(target=start_scheduler_in_itemmaster, daemon=True)
        scheduler_thread.start()
 

   