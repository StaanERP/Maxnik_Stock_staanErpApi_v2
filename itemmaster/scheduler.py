from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, date
from .models import *

def update_hsn_effective():
    list_of_id = []
    current_date = date.today()
    hsn_effective_dates = HsnEffectiveDate.objects.filter(
        effective_date=current_date
    ).order_by("-id")

    hsn_updates = []  # List of updated Hsn instances

    with transaction.atomic():
        for entry in hsn_effective_dates:
            hsn_id = entry.hsn_id_id
            if hsn_id and hsn_id not in list_of_id:
                hsn_data = entry.hsn_id
                hsn_data.hsn_code = entry.hsn_code
                hsn_data.gst_rates = entry.gst_rates
                hsn_data.cess_rate = entry.cess_rate
                hsn_data.rcm = entry.rcm
                hsn_data.itc = entry.itc
                hsn_updates.append(hsn_data)
                list_of_id.append(hsn_id)
        # Perform bulk update
        if hsn_updates:
            Hsn.objects.bulk_update(
                hsn_updates,
                ['hsn_code', 'gst_rates', 'cess_rate', 'rcm', 'itc']
            )


def update_otherExpenses():
    current_date = date.today()

    # Filter OtherExpenses linked to any comman_hsn_effective_date for today
    current_changes_objects = OtherExpenses.objects.\
        filter(comman_hsn_effective_date__effective_date=current_date)

    updated_expenses = []
    seen_hsn_ids = set()

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
                    entry.HSN = hsn_effective.hsn_id
                    entry.modified_by = hsn_effective.created_by
                    updated_expenses.append(entry)
                    seen_hsn_ids.add(hsn_id)

        if updated_expenses:
            OtherExpenses.objects.bulk_update(updated_expenses, ['HSN', 'modified_by'])

def update_tds_tcs_Master():
    today = date.today()
    effective_entries = TdsTcsEffectiveDate.objects.filter(effective_date=today).order_by("-id")

    tds_updates = []
    tcs_updates = []

    for entry in effective_entries:
        if entry.tds:
            tds = entry.tds
            tds.percent_individual_with_pan = entry.percent_individual_with_pan
            tds.percent_other_with_pan = entry.percent_other_with_pan
            tds.effective_date = entry.effective_date
            tds_updates.append(tds)
        elif entry.tcs:
            tcs = entry.tcs
            tcs.percent_individual_with_pan = entry.percent_individual_with_pan
            tcs.percent_individual_without_pan = entry.percent_individual_without_pan
            tcs.percent_other_with_pan = entry.percent_other_with_pan
            tcs.percent_other_without_pan = entry.percent_other_without_pan
            tcs.effective_date = entry.effective_date
            tcs_updates.append(tcs)

    with transaction.atomic():
        if tds_updates:
            TDSMaster.objects.bulk_update(
                tds_updates,
                ['percent_individual_with_pan', 'percent_other_with_pan', 'effective_date']
            )
        if tcs_updates:
            TCSMaster.objects.bulk_update(
                tcs_updates,
                ['percent_individual_with_pan', 'percent_individual_without_pan',
                 'percent_other_with_pan', 'percent_other_without_pan', 'effective_date']
            )




def start_scheduler_in_itemmaster(): 
    scheduler = BackgroundScheduler()
    # scheduler.add_job(update_otherExpenses, 'interval', seconds=10)  # Runs every 10 seconds
    scheduler.add_job(update_hsn_effective, 'cron', hour=0, minute=0)
    scheduler.add_job(update_otherExpenses, 'cron', hour=0, minute=0)
    scheduler.add_job(update_tds_tcs_Master, 'cron', hour=0, minute=0)
    scheduler.start()