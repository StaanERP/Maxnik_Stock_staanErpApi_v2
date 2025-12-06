from django.utils.timezone import activate
import logging

logger = logging.getLogger(__name__)

class TimezoneAdjustmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info("Executing TimezoneAdjustmentMiddleware")  # Debug log
        activate('Asia/Kolkata')
        response = self.get_response(request)
        logger.info("TimezoneAdjustmentMiddleware completed")  # Debug log
        return response
