from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .models import *


def update_other_Income():
    print("-------")
    current_date = datetime.now().date() + timedelta(days=1)

    # # Filter OtherExpenses linked to any comman_hsn_effective_date for today
    current_changes_objects = OtherIncomeCharges.objects.\
        filter(comman_hsn_effective_date__effective_date=current_date)

    updated_other_Income = []
    seen_hsn_ids = set()
    try:
        with transaction.atomic():
            for entry in current_changes_objects:
                # Get all related effective dates for this OtherExpenses object
                related_effective_dates = entry.comman_hsn_effective_date.filter(
                    effective_date=current_date
                ).order_by("-id")  # Latest first
                if related_effective_dates.exists():
                    hsn_effective = related_effective_dates.first()
                    hsn_id = hsn_effective.hsn_id_id

                    if hsn_id and hsn_id not in seen_hsn_ids:
                        entry.hsn = hsn_effective.hsn_id
                        entry.modified_by = hsn_effective.created_by
                        updated_other_Income.append(entry)
                        seen_hsn_ids.add(hsn_id)

            if updated_other_Income:
                OtherIncomeCharges.objects.bulk_update(updated_other_Income, ['hsn', 'modified_by'])
    except Exception as e:
        print(e)    

def start_scheduler_in_itemmaster2(): 
    scheduler = BackgroundScheduler()
    # scheduler.add_job(update_other_Income, 'interval', seconds=10)  # Runs every 10 seconds
    scheduler.add_job(update_other_Income, 'cron', hour=0, minute=0)
    scheduler.start()