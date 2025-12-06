import os
import sys
import django
import pandas as pd

# Add project folder
sys.path.append(r"D:\Maxnik\staanErpApi_v2")

# Set settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "staanErpApi_v2.Staanenquiryfromwithazure.settings")
django.setup()

from itemmaster.services.debit_note import DebitNoteSerivce

df = pd.read_excel(r"D:\Maxnik\test_debitnote.xlsx")

for index, row in df.iterrows():
    data = {
        "vendor": int(row["vendor_id"]),
        "company": int(row["company_id"]),
        "status": row["status"],
        "item_detail": [
            {
                "item_master": int(row["item_master"]),
                "qty": float(row["qty"]),
                "rate": float(row["rate"]),
                "gst": int(row["gst_id"]),
                "amount": float(row["qty"]) * float(row["rate"]),
            }
        ]
    } 
    # service = DebitNoteSerivce(data=data, info=None, status=row["status"])
    # response = service.process()
    # print(response)
