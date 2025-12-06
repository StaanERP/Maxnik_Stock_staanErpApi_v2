from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
from itemmaster2.models import *
from .models import *

def update_activity_over_due():
    try:
        yesterday = datetime.now().date() - timedelta(days=1)

        # Get all activities that should be marked as overdue
        activity_list = Activites.objects.filter(
            (
                    Q(planned_start_date_time__date=yesterday) |
                    Q(planned_start_date_time__isnull=True, due_date_time__date=yesterday)
            ) &
            Q(status__name='Planned')
        )

        # Bulk update activities
        activity_list.update(over_due=True)

        # Get all overdue enquiries linked to these activities
        over_due_enquiry = enquiryDatas.objects.filter(activity__in=activity_list)

        # Bulk update enquiries
        over_due_enquiry.update(over_due=True)

        # Bulk Update Lead
        over_due_lead = Leads.objects.filter(
            Q(activity__in=activity_list) | Q(Enquiry__activity__in=activity_list)
        )
        over_due_lead.update(over_due=True)
    except Exception as e:
        print(e)

 
def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(update_activity_over_due, 'cron', hour=0, minute=0)
    scheduler.start()

