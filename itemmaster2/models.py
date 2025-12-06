import decimal

from itemmaster.models import *
from django.db import models
from django.contrib.auth.models import User
from itemmaster.Utils.CommanUtils import *
from datetime import datetime
from EnquriFromapi.models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from itemmaster.Utils.stockAddtinons import *

targe_modules = {
    "Leads": {"Lead Value": "lead_value"}
}
PAY_BY = [
        ('Account', 'Account'),
        ('Supplier & Customer', 'Supplier & Customer'),
        ('Employee', 'Employee')
    ]
PAY_MODE = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank')
    ]
CREDIT_NOTE_REASON = [
    ('Not Applicable', 'Not Applicable'),
    ('Returns of goods or cancellations of services', 'Returns of goods or cancellations of services'),
    ('Post Sales Discount', 'Post Sales Discount'),
    ('Correction in Invoice', 'Correction in Invoice'),
    ('Others', 'Others'),
]
transfer_via = (
    ("UPI", "UPI"),
    ("Neft/RTGS", "Neft/RTGS"),
    ("Cheque", "Cheque"),
    )

from decimal import Decimal

def CalculateTheTarget(model, salesPerson, instance, currency,created_at):
    current_date = datetime.today()

    current_target = Target.objects.filter(
        financial_year_start__lte=current_date,
        financial_year_end__gte=current_date,
        target_module=model,
        target_sales_person__sales_person__id=salesPerson
    ).first()
    if not current_target:
        return

    month = datetime.now().month
    target_field_month = current_target.target_module
    target_field_name = current_target.target_field

    instance_value = getattr(instance, targe_modules[target_field_month][target_field_name], None)
    if instance_value is None:
        return

    # Ensure it's a Decimal for safe arithmetic
    instance_value = Decimal(instance_value)

    # Currency adjustment
    instance_value *= currency.rate

    for salesperson in current_target.target_sales_person.all():
        if salesperson.sales_person.id == salesPerson:
            for target_month in salesperson.target_months.all():
                if target_month.month == month and target_month.target_value > 0:
                    current_achievement = target_month.target_achievement or Decimal("0.00")
                    target_month.target_achievement = current_achievement + instance_value
                    target_month.save()
                    return

class CallLog(models.Model):
    types = models.CharField(default="call", max_length=5)
    subject_call_log = models.CharField(max_length=50)
    outcome_call_log = models.TextField()
    sales_person = models.ForeignKey(User, related_name="sales_person", on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, related_name="CallLogcreate", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="CallLogmodified", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject_call_log} - {str(self.id)}"

class Meeting(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    subject = models.CharField(max_length=50)
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    planned_start_time = models.TimeField()
    planned_end_time = models.TimeField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    outcome = models.TextField(default="default_Text")
    sales_person = models.ForeignKey(User, related_name="sales_personMeeting", on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, related_name="Meetingcreate", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="Meetingmodified", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.status} - {str(self.id)}"

class Notes(models.Model):
    note = models.TextField()
    created_by = models.ForeignKey(User, related_name="creatednote", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="modifiednote", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class EmailResource(models.Model):
    name = models.CharField(max_length=50)
    modal_name = models.CharField(max_length=50, null=True, blank=True)
    email_tags = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class EmailTemplete(models.Model):
    title = models.CharField(max_length=50)
    resource = models.ForeignKey(EmailResource, on_delete=models.PROTECT)
    active = models.BooleanField(default=False)
    subject = models.TextField(blank=True)
    email_body = models.TextField()
    mail_template = models.BooleanField(default=False)
    whats_app_template = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="createdEmailTempleted", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="modifiedEmailTempleted", on_delete=models.SET_NULL,
                                    null=True, blank=True)

    def save(self, *args, **kwargs):
        history_list = {
            "title": "Title",
            "resource": "Resource",
            "active": "Active",
            "email_body": "Email Body"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", EmailTemplete, history_list)
            super(EmailTemplete, self).save(*args, **kwargs)
        elif self.pk is None:
            super(EmailTemplete, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", EmailTemplete, history_list)
        return instance
    
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class ActivityType(models.Model):
    name = models.CharField(max_length=50)
    time_tracking = models.BooleanField(default=False)
    due_date = models.BooleanField(default=False)
    geotagging = models.BooleanField(default=False)
    participants = models.BooleanField(default=False)
    remainder_mail = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    icon = models.CharField(max_length=50, null=True, blank=True)
    status = models.BooleanField(default=False)
    sales = models.BooleanField(default=False)
    service = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="createdActivityType", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="modifiedActivityType", on_delete=models.SET_NULL, null=True,
                                    blank=True)

    def save(self, *args, **kwargs):
        history_list = {
            "name": "Name",
            "time_tracking": "Time Tracking",
            "due_date": "Due Date",
            "geotagging": "Geotagging",
            "participants": "Participants",
            "remainder_mail": "Remainder Mail",
            "active": "Active",
            "icon": "Icon",
            "status": "Status",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ActivityType, history_list)
            super(ActivityType, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ActivityType, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ActivityType, history_list)
        return instance

    def __str__(self):
        return self.name

class EmailRecord(models.Model):
    sent_to = models.TextField()
    cc = models.TextField(null=True, blank=True)
    bcc = models.TextField(null=True, blank=True)
    subject = models.TextField(null=True, blank=True)
    email_body = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="createdEmailRecord", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Activites(models.Model):
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT, null=True, blank=True)
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True)
    subject = models.TextField()
    outcome = models.TextField(blank=True)
    assigned = models.ForeignKey(User, related_name="assigned", on_delete=models.PROTECT)
    planned_start_date_time = models.DateTimeField(null=True, blank=True)
    planned_end_date_time = models.DateTimeField(null=True, blank=True)
    actual_start_date_time = models.DateTimeField(null=True, blank=True)
    actual_end_date_time = models.DateTimeField(null=True, blank=True)
    due_date_time = models.DateTimeField(null=True, blank=True)
    over_due = models.BooleanField(default=False)
    # geotagging
    user_participants = models.ManyToManyField(User, related_name="user_participants", blank=True)
    customer_participants = models.ManyToManyField(ContactDetalis, blank=True)
    Contact = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT, related_name="activites_contact", null=True,
                                blank=True)
    customer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, null=True, blank=True)
    remainder_mail = models.BooleanField(default=False)
    email_templete = models.ForeignKey(EmailTemplete, on_delete=models.PROTECT, null=True, blank=True)
    actual_email = models.JSONField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="createdActivity", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="modifiedActivity", on_delete=models.SET_NULL, null=True,
                                    blank=True)

    def save(self, *args, **kwargs):
        history_list = {
            "activity_type": "Activity Type",
            "status": "Status",
            "subject": "Subject",
            "outcome": "Outcome",
            "assigned": "Assigned",
            "planned_start_date_time": "Planned Start Date Time",
            "planned_end_date_time": "Planned End Date Time",
            "actual_start_date_time": "Actual Start Date Time",
            "actual_end_date_time": "Actual End Date Time",
            "due_date_time": "Due Time",
            "email_templete": "Email Template",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Activites, history_list)
            super(Activites, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Activites, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Activites, history_list)
        return instance

    def pass_wanted_date(self):
        """Returns the date to consider based on status."""
        if self.status and self.status.name == "Planned" and self.activity_type.time_tracking:
            return self.planned_start_date_time.date() if self.planned_start_date_time else None
        elif self.status and self.status.name == "Planned" and self.activity_type.due_date:
            return self.due_date_time.date() if self.due_date_time else None

class Leads(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True)
    lead_no = models.CharField(max_length=15, null=True, blank=True, editable=False)
    lead_name = models.CharField(max_length=100)
    customer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT)
    over_due = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    contact = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT, null=True, blank=True)
    requirement = models.TextField()
    rext_follow_up = models.DateField(null=True, blank=True)
    lead_currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    lead_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    expected_closing_date = models.DateField()
    Enquiry = models.ForeignKey("EnquriFromapi.EnquiryDatas", on_delete=models.PROTECT, null=True, blank=True)
    priority = models.IntegerField()
    sales_person = models.ForeignKey(User, related_name="sales_personLeads", on_delete=models.PROTECT)
    activity = models.ManyToManyField(Activites, blank=True)
    call_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    task_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    meeting_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    mail_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    note = models.ManyToManyField(Notes, blank=True)
    email_record = models.ManyToManyField(EmailRecord, blank=True)
    quotation_ids = models.ManyToManyField("Quotations", blank=True)
    sales_order_id = models.ManyToManyField("SalesOrder_2", blank=True)
    lead_reason = models.TextField(null=True, blank=True)
    lead_reason_dec = models.TextField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    won_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="createdLeads", on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, related_name="modifiedLeads", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        starting_id = "00001"
        prefix = "LEAD"
        if self.pk is None:
            last_serial_id_record = ManualIdSeries.objects.filter(
                name__iexact="Lead").first()
            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.lead_no = f'{prefix}-{new_serial_id:05}'
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name='Lead', id_series=new_serial_id,
                                              created_by=self.created_by)
        history_list = {
            "lead_no": "Lead No",
            "status": "Status",
            "lead_name": "Lead Name",
            "customer": "Customer",
            "lead_currency": "Lead Currency",
            "lead_value": "Lead Value",
            "expected_closing_date": "Expected Closure Date",
            "sales_person": "Sales Person",
            "requirement": "Requirements",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Leads, history_list)
            super(Leads, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Leads, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Leads, history_list)
        if self.status.name == "Won":
                    CalculateTheTarget("Leads", self.sales_person.id, self, self.lead_currency, self.created_at)
                    self.won_date = datetime.now().date()
                    super(Leads, self).save(*args, **kwargs)
        return instance
    def delete(self, *args, **kwargs):
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        if self.activity.exists():
            self.activity.all().delete()
        if self.email_record.exists():
            self.email_record.all().delete()
        if self.note.exists():
            self.note.all().delete()
        super().delete(*args, **kwargs)

class OtherIncomeCharges(models.Model):
    name = models.CharField(max_length=50, unique=True)
    account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    active = models.BooleanField(default=True)
    comman_hsn_effective_date = models.ManyToManyField(CommanHsnEffectiveDate, blank=True)
    modified_by = models.ForeignKey(User, related_name="OtherIncomeCharges_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="OtherIncomeCharges_create", on_delete=models.PROTECT, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        # Check if a record with the same normalized name already exists
        if OtherIncomeCharges.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        history_list = {
            "name": "Name",
            "account": "Account",
            "hsn": "HSN",
            "active": "Active"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", OtherIncomeCharges, history_list)
            super(OtherIncomeCharges, self).save(*args, **kwargs)
        elif self.pk is None:
            super(OtherIncomeCharges, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", OtherIncomeCharges, history_list)
        return instance

    def __str__(self):
        return self.name
    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here

        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        if self.comman_hsn_effective_date.exists():
            self.comman_hsn_effective_date.all().delete()
        super().delete(*args, **kwargs)

class QuotationsOtherIncomeCharges(models.Model):
    other_income_charges_id = models.ForeignKey(OtherIncomeCharges, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    after_discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="QuotationsOtherIncomeCharges_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="QuotationsOtherIncomeCharges_create", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QuotationsItemComboItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    parent = models.ForeignKey(Item_Combo, on_delete=models.SET_NULL, blank=True, null=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    display = models.CharField(max_length=50, blank=True, null=True)
    is_mandatory = models.BooleanField(default=True)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_QuotationsItemComboItemDetails",
                                on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_QuotationsItemComboItemDetails",
                                    on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QuotationsItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.TextField(max_length=250, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    item_combo = models.BooleanField(default=False)
    item_combo_item_details = models.ManyToManyField(QuotationsItemComboItemDetails, blank=True)
    item_combo_total_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_QuotationsItemDetails", on_delete=models.PROTECT,
                                   null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_QuotationsItemDetails", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # Clear the many-to-many relationship before deleting
        self.item_combo_item_details.all().delete()
        super().delete(*args, **kwargs)

class Quotations(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    quotation_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES, null=True, blank=True)
    quotation_date = models.DateField(null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales_personQuotations",
                                    null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    customer_id = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT)
    customer_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT)
    customer_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                                related_name="Quotations_customer_contact_person", null=True,
                                                blank=True)
    gstin_type = models.CharField(max_length=50, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    remarks = models.TextField(null=True, blank=True)
    lead_no = models.ForeignKey(Leads, on_delete=models.PROTECT, null=True, blank=True)
    # sales_order_no = models.ForeignKey('SalesOrder_2', on_delete=models.PROTECT, null=True, blank=True)
    itemDetails = models.ManyToManyField(QuotationsItemDetails)
    #     """amount details"""
    overall_discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    overall_discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_income_charge = models.ManyToManyField(QuotationsOtherIncomeCharges, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    parent_order = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='child_orders')
    child_count = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    "Activities"
    note = models.ManyToManyField(Notes, blank=True)
    email = models.EmailField(null=True, blank=True)
    email_record = models.ManyToManyField(EmailRecord, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedQuotations", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createQuotations", on_delete=models.PROTECT, null=True,
                                   blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.quotation_date:
            self.quotation_date = datetime.today().date()
        if not self.id:
            if not self.parent_order:
                conditions = {'resource': 'Quotations', 'default': True, "department": self.department}
                response = create_serial_number(conditions)
                if response['success']:
                    self.quotation_no = response['instance']
                    self.active = True
                else:
                    raise CommonError(response['errors'])
            else:
                old_numbering_series = self.quotation_no.numbering_Seriel_link
                old_numbering_series_id = self.quotation_no.linked_model_id
                if self.child_count > 1:
                    old_numbering_series_id = str(old_numbering_series_id).rsplit("-", 1)[0]
                self.active = True
                try:
                    instance = NumberingSeriesLinking.objects.create(
                        numbering_Seriel_link=old_numbering_series,
                        linked_model_id=f"{old_numbering_series_id}-{self.child_count}"
                    )
                    self.quotation_no = instance
                    parent = self.parent_order
                    parent.active = False
                    parent.save()
                except Exception as e:
                    print(e)
        history_list = {
            "quotation_no": "Quotation No",
            "status": "Status",
            "quotation_date": "Quotation Date",
            "lead_no": "Lead No",
            "department": "Department",
            "sales_person": "Sales Person",
            "currency": "Currency",
            "remarks": "Remarks",
            "customer_address": "Address",
            "customer_contact_person": "Contact Person",
            "taxable_value": "Taxable Value",
            "net_amount": "Net Amount",
            "tax_total": "Tax Total"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Quotations, history_list)
            super(Quotations, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Quotations, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Quotations, history_list)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.itemDetails.exists():
            self.itemDetails.all().delete()
        if self.other_income_charge.exists():
            self.other_income_charge.all().delete()
        if self.note.exists():
            self.note.all().delete()
        if self.email_record.exists():
            self.email_record.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        parent_order = self.parent_order
        super().delete(*args, **kwargs)
        if parent_order:
            parent_order.delete()

class SalesOrder_2_temComboItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    parent = models.ForeignKey(Item_Combo, on_delete=models.SET_NULL, blank=True, null=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    display = models.CharField(max_length=50, blank=True, null=True)
    is_mandatory = models.BooleanField(default=True)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_have_draft = models.BooleanField(default=False)
    dc_submit_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_SalesOrder_2",
                                on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_SalesOrder_2",
                                    on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesOrder_2_otherIncomeCharges(models.Model):
    other_income_charges_id = models.ForeignKey(OtherIncomeCharges, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    after_discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True,
        blank=True,
        related_name='child_income_charges'
    )
    modified_by = models.ForeignKey(User, related_name="SalesOrder_2_otherIncomeChargesOtherIncomeCharges_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="SalesOrder_2_otherIncomeChargesOtherIncomeCharges_create",
                                   on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  f"{self.id}--- {self.parent}"

class SalesOrder_2_ItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.TextField(max_length=250, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    item_combo = models.BooleanField(default=False)
    item_combo_item_details = models.ManyToManyField(SalesOrder_2_temComboItemDetails, blank=True)
    is_have_draft = models.BooleanField(default=False)
    dc_submit_count = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_SalesOrder_2ItemDetails", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_SalesOrder_2ItemDetails", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # Clear the many-to-many relationship before deleting
        self.item_combo_item_details.all().delete()
        super().delete(*args, **kwargs)

class SalesOrder_2(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES, null=True, blank=True)
    sales_order_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True)
    sales_order_date = models.DateField(null=True, blank=True)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT)
    due_date = models.DateField()
    credit_period = models.IntegerField()
    payment_terms = models.TextField(null=True, blank=True)
    customer_po_no = models.TextField(null=True, blank=True)
    customer_po_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    lead_no = models.ForeignKey(Leads, on_delete=models.PROTECT, null=True, blank=True)
    quotations = models.ForeignKey(Quotations, on_delete=models.PROTECT, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    buyer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="SalesOrder_2_buyer")
    buyer_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="SalesOrder_2_buyer_address")
    buyer_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                        related_name="SalesOrder_2_buyer_contact_person")
    buyer_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    buyer_gstin = models.CharField(max_length=15, null=True, blank=True)
    buyer_state = models.CharField(max_length=50, null=True, blank=True)
    buyer_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    consignee = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="SalesOrder_2_consignee")
    consignee_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                        related_name="SalesOrder_2_consignee_address")
    consignee_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                        related_name="SalesOrder_2_consignee_contact_person")
    consignee_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    consignee_gstin = models.CharField(max_length=15, null=True, blank=True)
    consignee_state = models.CharField(max_length=50, null=True, blank=True)
    consignee_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    """item details"""
    item_details = models.ManyToManyField(SalesOrder_2_ItemDetails, blank=True)
    other_income_charge = models.ManyToManyField(SalesOrder_2_otherIncomeCharges, blank=True)
    """amount details"""
    overall_discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    overall_discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    igst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cess_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    parent_order = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='child_orders')
    # dc_links = models.ManyToManyField("itemmaster2.SalesOrder_2_DeliveryChallan", blank=True)
    child_count = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    "Activities"
    note = models.ManyToManyField(Notes, blank=True)
    email = models.EmailField(null=True, blank=True)
    email_record = models.ManyToManyField(EmailRecord, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedSalesOrder_2", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createSalesOrder_2", on_delete=models.PROTECT, null=True,
                                blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.id:
            if not self.parent_order:
                conditions = {'resource': 'SalesOrder', 'default': True, "department": self.department}
                response = create_serial_number(conditions)
                if response['success']:
                    self.sales_order_no = response['instance']
                    self.active = True
                else:
                    raise ValidationError(response['errors'])
            else:
                old_numbering_series = self.parent_order.sales_order_no.numbering_Seriel_link
                old_numbering_series_id = self.parent_order.sales_order_no.linked_model_id
                if self.child_count > 1:
                    old_numbering_series_id = str(old_numbering_series_id).rsplit("-", 1)[0]
                self.active = True
                try:
                    instance = NumberingSeriesLinking.objects.create(
                        numbering_Seriel_link=old_numbering_series,
                        linked_model_id=f"{old_numbering_series_id}-{self.child_count}"
                    )
                    self.sales_order_no = instance
                    parent = self.parent_order
                    parent.active = False
                    parent.save()

                except Exception as e:
                    print("serial", e)
        history_list = {
            "sales_order_no": "Sales Order No",
            "status": "Status",
            "sales_order_date": "Sales Order Date",
            "sales_person": "Sales Person",
            "due_date": "Due Date",
            "credit_period": "Credit Period",
            "payment_terms": "Payment Terms",
            "customer_po_no": "Customer PO No",
            "customer_po_date": "Customer PO Date",
            "department": "Department",
            "lead_no": "lead No",
            "quotations": "Quotations",
            "currency": "Currency",
            "buyer": "Buyer",
            "buyer_address": "Buyer Address",
            "buyer_contact_person": "Buyer - Contact Person",
            "buyer_gstin_type": "Buyer - GSTIN Type",
            "buyer_gstin": "Buyer - GSTIN",
            "buyer_state": "Buyer - State",
            "buyer_place_of_supply": "Buyer - Place Of Supply",
            "consignee": "Consignee",
            "consignee_address": "Consignee Address",
            "consignee_contact_person": "Consignee - Contact Person",
            "consignee_gstin_type": "Consignee - GSTIN Type",
            "consignee_gstin": "Consignee - GSTIN",
            "consignee_state": "Consignee - State",
            "consignee_place_of_supply": "Consignee - Place Of Supply",
            "taxable_value": "Taxable Value",
            "tax_total": "Tax Total",
            "net_amount": "Net Amount"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", SalesOrder_2, history_list)
            super(SalesOrder_2, self).save(*args, **kwargs)
        elif self.pk is None:
            super(SalesOrder_2, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", SalesOrder_2, history_list)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_details.exists():
            self.item_details.all().delete()
        if self.other_income_charge.exists():
            self.other_income_charge.all().delete()
        if self.note.exists():
            self.note.all().delete()
        if self.email_record.exists():
            self.email_record.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        parent_order = self.parent_order
        super().delete(*args, **kwargs)
        if parent_order:
            parent_order.delete()

class TargetMonth(models.Model):
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    target_value = models.DecimalField(max_digits=12, decimal_places=2)
    target_achievement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

class TargetSalesperson(models.Model):
    is_head = models.BooleanField(default=False)
    role = models.ForeignKey("userManagement.Roles", on_delete=models.PROTECT, null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT)
    target_months = models.ManyToManyField(TargetMonth, related_name="salespersons", blank=True)

    def delete(self, *args, **kwargs):
        if self.target_months.exists():
            self.target_months.all().delete()

class Target(models.Model):
    target_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True,
                                  editable=False)
    target_name = models.CharField(max_length=255)
    financial_year_start = models.DateField()
    financial_year_end = models.DateField()
    target_module = models.CharField(max_length=50)
    target_field = models.CharField(max_length=50)
    target_mode = models.CharField(max_length=50, null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT)
    total_target_value = models.DecimalField(max_digits=15, decimal_places=2)  # Increased precision
    target_sales_person = models.ManyToManyField(TargetSalesperson, related_name="targets")
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedTarget", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createTarget", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "target_name": "Target Name",
            "target_module": "Target Module",
            "target_field": "Target Field",
            "currency": "currency",
            "total_target_value": "Total Target Value"
        }
        if not self.id:
            conditions = {'resource': 'Target', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.target_no = response['instance']
            else:
                raise ValidationError(response['errors'])
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Target, history_list)
            super(Target, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Target, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Target, history_list)
        return instance

    def delete(self, *args, **kwargs):
        if self.target_sales_person.exists():
            for salesperson in self.target_sales_person.all():
                if salesperson.target_months.exists():
                    salesperson.target_months.all().delete()
            self.target_sales_person.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

    def get_target_achievement_exists(self):
        for sales_person in self.target_sales_person.all():
            if sales_person.target_months.all().exists():
                for target in sales_person.target_months.all():
                    if type(target.target_achievement) == decimal.Decimal and (target.target_achievement) > 0:
                        return {
                        "sales_person": sales_person.sales_person.username,
                        "target_achievement": target.target_achievement,
                        "status": True
                    }   
        return {"status":False}

class SalesOrder_2_RetunBatch(models.Model):
    item= models.ForeignKey("SalesOrder_2_DeliveryChallanItemDetails", on_delete=models.CASCADE, null=True, blank=True)
    item_combo = models.ForeignKey("SalesOrder_2_DeliverChallanItemCombo", on_delete=models.CASCADE, null=True, blank=True)
    batch = models.ForeignKey(BatchNumber, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    is_stock_reduce = models.BooleanField(default=False)

    def clean(self):
        errors = {}

        if not self.item and not self.item_combo:
            errors["item_combo"] = "Either item or item_combo must be provided."

        if errors:
            raise ValidationError(errors)

class SalesOrder_2_DeliverChallanItemCombo(models.Model):
    item_combo = models.ForeignKey(SalesOrder_2_temComboItemDetails, on_delete=models.PROTECT)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    stock_reduce = models.BooleanField(default=False)
    qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    return_draft_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    return_submit_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    invoice_draft_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    invoice_submit_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_delivery_challan_item_combo", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_delivery_challan_item_combo", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesOrder_2_DeliveryChallanItemDetails(models.Model):
    sales_order_item_detail = models.ForeignKey(SalesOrder_2_ItemDetails, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    stock_reduce = models.BooleanField(default=False)
    invoice_draft_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    invoice_submit_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    return_draft_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    return_submit_count = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    item_combo_itemdetails = models.ManyToManyField(SalesOrder_2_DeliverChallanItemCombo, blank=True)
    created_by = models.ForeignKey(User, related_name="created_delivery_challan_item_details", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_delivery_challan_item_details", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sales Order Item Detail Delivery Challan"
        verbose_name_plural = "Sales Order Item Details Delivery Challans"

class SalesOrder_2_DeliveryChallan(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True)
    dc_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True,
                                editable=True)
    dc_date = models.DateField()
    e_way_bill = models.CharField(max_length=20, null=True, blank=True)
    e_way_bill_date = models.DateField(null=True, blank=True)
    all_stock_reduce = models.BooleanField(default=False)
    sales_order = models.ForeignKey(SalesOrder_2, on_delete=models.PROTECT, null=True, blank=True, related_name="delivery_challans")
    item_details = models.ManyToManyField(SalesOrder_2_DeliveryChallanItemDetails)
    other_income_charge = models.ManyToManyField(SalesOrder_2_otherIncomeCharges, blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    comman_store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    before_tax = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    nett_amount = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    # sales_invoice = models.ForeignKey("itemmaster2.SalesInvoice", null=True, blank=True, on_delete=models.SET_NULL)
    # own_vehicle--  Vehicle No & Driver Name
    vehicle_no = models.CharField(max_length=20, null=True, blank=True)
    driver_name = models.CharField(max_length=20, null=True, blank=True)
    # # Transporter -- Vehicle No & Transporter Name 
    transport = models.ForeignKey(SupplierFormData,null=True,blank=True,on_delete=models.PROTECT)
    #courier -- Docket No & Docket Date
    docket_no = models.CharField(max_length=30, null=True, blank=True)
    docket_date = models.DateField(null=True, blank=True)
    # Other mode
    other_model = models.TextField(null=True, blank=True)
    sales_return = models.ManyToManyField("SalesReturn", blank=True)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_delivery_challan", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_delivery_challan", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debits':[],
            "credit" : {}

        }
        if self._state.adding:
            conditions = {
                'resource': 'SalesOrder Delivery Challan',
                'default': True,
                'department': self.sales_order.department.id
            }
            response = create_serial_number(conditions)
            if response['success']:
                self.dc_no = response['instance']
            else:
                raise CommonError(response['errors'])
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster2.services.salesorder_delivery_challan_service import sales_dc_general_update
            debits = []
            company_master = company_info()
            account = company_master.stock_account
            sales_pending_account = company_master.sales_pending_account
            if  not account:
                raise CommonError(["Stock account not found in company master."])
            
            if not sales_pending_account:
                raise CommonError(["Sales pending account not found in company master."])
            
            product_total_amount = 0


            for item in self.item_details.all():
                itemmaster = item.sales_order_item_detail.itemmaster
                if itemmaster and not itemmaster.item_sales_account :
                    raise CommonError(f"{itemmaster} sales account not found.")

                if itemmaster.item_types == "Product":
                    product_total_amount += (item.amount or 0)
                    continue

                debits.append({
                    "date": self.dc_date,
                    "voucher_type": "Sales Deliver Challan",
                    "sales_dc_voucher_no": self.id,
                    "account": item.sales_order_item_detail.itemmaster.item_sales_account.id,
                    "debit": item.amount,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if product_total_amount:
                debits.append({
                    "date": self.dc_date,
                    "voucher_type": "Sales Deliver Challan",
                    "sales_dc_voucher_no": self.id,
                    "account": sales_pending_account.id,
                    "debit": product_total_amount,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            account_general_ledger["debits"] = debits
            account_general_ledger["credit"] = {
                "date": self.dc_date,
                "voucher_type": "Sales Deliver Challan",
                "sales_dc_voucher_no": self.id,
                "account": account.id,
                "credit": self.before_tax,
                "remark": "",
                "created_by": self.created_by.pk,
            }
            
            if not self.is_account_general_ledger_upated:
                result = sales_dc_general_update(account_general_ledger, False)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True

        history_list = {
            "status": "Status",
            "dc_date": "Date",
            "e_way_bill": "E Way Bill",
            "e_way_bill_date": "E Way Bill Date",
            "vehicle_no": "Vehicle No",
            "driver_name": "Driver Name",
            "transport": "Transport",
            "docket_no": "Docket No",
            "docket_date": "Docket Date",
            "other_model": "Other Model"
        }

        
        action = "Add" if self._state.adding else "Update"
        
        if action == "Add":
            super(SalesOrder_2_DeliveryChallan, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, SalesOrder_2_DeliveryChallan, history_list)
        if action == "Update":
            super(SalesOrder_2_DeliveryChallan, self).save(*args, **kwargs)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_details.exists():
            self.item_details.all().delete()
        if self.other_income_charge.exists():
            self.other_income_charge.all().delete()
         
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sales Order Delivery Challan"
        verbose_name_plural = "Sales Order Delivery Challans"

class SalesInvoiceItemCombo(models.Model):
    item_combo = models.ForeignKey(SalesOrder_2_DeliverChallanItemCombo, null=True, blank=True, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_sales_invoice_item_detail_item_combo", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_sales_invoice_item_detail_item_combo", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesInvoiceItemDetail(models.Model):
    item = models.ForeignKey(SalesOrder_2_DeliveryChallanItemDetails, null=True, blank=True, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    tax = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    item_combo = models.ManyToManyField(SalesInvoiceItemCombo, blank=True)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tcs_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tds_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_sales_invoice_item_detail", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_sales_invoice_item_detail", on_delete=models.PROTECT,
                                null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesInvoice(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    sales_invoice_date = models.DateField()
    sales_invoice_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True,
                                editable=True)
    sales_dc = models.ManyToManyField(SalesOrder_2_DeliveryChallan, blank=True)
    due_date = models.DateField(null=True, blank=True)
    buyer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="SalesInvoice_buyer", null=True, blank=True)
    buyer_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,related_name="SalesInvoice_buyer_address",
                                    null=True, blank=True)
    buyer_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                    related_name="SalesInvoice_buyer_contact_person", null=True, blank=True)
    buyer_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    buyer_gstin = models.CharField(max_length=15,null=True, blank=True)
    buyer_state = models.CharField(max_length=20,null=True, blank=True)
    buyer_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    consignee = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="SalesInvoice_consignee", null=True, blank=True)
    consignee_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="SalesInvoice_consignee_address", null=True, blank=True)
    consignee_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                    related_name="SalesInvoice_consignee_contact_person", null=True, blank=True)
    consignee_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    consignee_gstin = models.CharField(max_length=15,null=True, blank=True)
    consignee_state = models.CharField(max_length=20,null=True, blank=True)
    consignee_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    creadit_period = models.IntegerField(null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    payment_term = models.TextField(null=True, blank=True)
    customer_po = models.CharField(max_length=50, null=True, blank=True)
    customer_po_date = models.DateField(max_length=50, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    item_detail = models.ManyToManyField(SalesInvoiceItemDetail,blank=True)
    other_income_charge = models.ManyToManyField(SalesOrder_2_otherIncomeCharges, blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tds_bool = models.BooleanField(default=False)
    tcs_bool = models.BooleanField(default=False)
    tds_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    overall_discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    overall_discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    # gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    sales_return = models.ManyToManyField("SalesReturn", blank=True)
    "Activities"
    note = models.ManyToManyField(Notes, blank=True)
    email = models.EmailField(null=True, blank=True)
    email_record = models.ManyToManyField(EmailRecord, blank=True)

    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_sales_invoice", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_sales_invoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit':{},
            "credits" : []
        }
        history_list = {
            "status": "Status",
            "sales_invoice_no": "Sales Invoice No",
            "sales_invoice_date": "Date",
            "buyer": "Buyer",
            "buyer_address": "Buyer Address",
            "buyer_contact_person": "Buyer Contact Person",
            "buyer_gstin_type": "Buyer GSTIN Type",
            "buyer_gstin": "Buyer GSTIN",
            "buyer_state": "Buyer State",
            "buyer_place_of_supply": "Buyer Place of Supply",
            "remarks" : "Remarks",
        } 
        if self._state.adding:
            conditions = {'resource': 'Sales Invoice', 'default': True, "department": self.department.id}
            response = create_serial_number(conditions)
            if response['success']:
                self.sales_invoice_no = response['instance']
            else:
                raise CommonError(response['errors'])
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster2.services.sales_invoice_services import sales_invoice_general_update
            credits = []
            debit_account = company_info().receivable_account
            sales_pending_account = company_info().sales_pending_account
            sales_account = company_info().sales_account
            if not debit_account:
                raise CommonError(["Receivables not found in company master."])
            
            if not sales_pending_account:
                raise CommonError(["Sales pending account not found in company master."])
            
            if not sales_account:
                raise CommonError(["Sales account not found in company master."])
            
            sales_produce_total = 0
            for item in self.item_detail.all():
                related_item = item.item
                account = None
                if related_item:
                    account = related_item.sales_order_item_detail.itemmaster.item_sales_account

                if related_item.sales_order_item_detail.itemmaster.item_types.name == "Product":
                    sales_produce_total += (item.amount or 0)
                    continue

                if not account:
                    raise CommonError([f'{related_item.sales_order_item_detail.itemmaster} account not found.'])
                credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": account.id,
                    "credit": (item.amount or 0),
                    "purchase_account" : sales_account.id ,
                    "purchase_amount" : (item.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if sales_produce_total:
                credits.append({
                        "date": self.sales_invoice_date,
                        "voucher_type": "Sales Invoice",
                        "sales_invoice_voucher_no": self.id,
                        "account": sales_pending_account.id,
                        "credit": sales_produce_total,
                        "purchase_account" : sales_account.id,
                        "purchase_amount" : sales_produce_total,
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.other_income_charge.exists():
                for charges in self.other_income_charge.all():
                    
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": charges.other_income_charges_id.account.id,
                    "credit":  (charges.after_discount_value or 0) if charges.after_discount_value else (charges.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
            
            if self.igst_value and Decimal(self.igst_value) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": igst_account.id,
                    "credit": (self.igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst_value and  Decimal(self.sgst_value) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": sgst_account.id,
                    "credit": (self.sgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cgst_value and  Decimal(self.cgst_value) > 0:
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": cgst_account.id,
                    "credit": (self.cgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cess_value and  Decimal(self.cess_value) > 0:
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": cess_account.id,
                    "credit": (self.cess_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tds_total and  Decimal(self.tds_total) > 0:
                tds_account = company_info().tds_account
                if not tds_account:
                    raise CommonError(["TDS not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": tds_account.id,
                    "credit": (self.tds_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": tcs_account.id,
                    "credit": (self.tcs_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.round_off is not None and self.round_off != 0  and  self.round_off !="":
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in account."])
                else: 
                    credits.append({
                    "date": self.sales_invoice_date,
                    "voucher_type": "Sales Invoice",
                    "sales_invoice_voucher_no": self.id,
                    "account": round_off_account.id,
                    "credit": (self.round_off or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            

            account_general_ledger["credits"] = credits
            account_general_ledger['debit'] = {
                "date": self.sales_invoice_date,
                "voucher_type": "Sales Invoice",
                "sales_invoice_voucher_no": self.id,
                "account": debit_account.id,
                "customer_supplier" :self.buyer.id,
                "debit": (self.net_amount or 0),
                "remark": self.remarks,
                "created_by": self.created_by.pk,
            }
            
            if not self.is_account_general_ledger_upated:
                result = sales_invoice_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True

        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(SalesInvoice, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, SalesInvoice, history_list)
        if action == "Update":
            super(SalesInvoice, self).save(*args, **kwargs)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_detail.exists():
            self.item_detail.all().delete()
        if self.other_income_charge.exists():
            self.other_income_charge.all().delete()
         
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class DirectSalesInvoiceItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.TextField(max_length=250, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tds_percentage = models.IntegerField(null=True, blank=True)
    tcs_percentage = models.IntegerField(null=True, blank=True)
    tds_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_DirectSalesInvoice", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_DirectSalesInvoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DirectSalesInvoice(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    direct_sales_invoice_date = models.DateField()
    direct_sales_invoice_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT,  
                                editable=True, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES, null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    buyer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="Direct_sales_invoice_buyer", null=True, blank=True)
    buyer_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="Direct_sales_invoice_buyer_address", null=True, blank=True)
    buyer_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                    related_name="Direct_sales_invoice_buyer_contact_person", null=True, blank=True)
    buyer_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    buyer_gstin = models.CharField(max_length=15,null=True, blank=True)
    buyer_state = models.CharField(max_length=20,null=True, blank=True)
    buyer_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    consignee = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="Direct_sales_invoice_consignee", null=True, blank=True)
    consignee_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="Direct_sales_invoice_consignee_address", null=True, blank=True)
    consignee_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                    related_name="Direct_sales_invoice_consignee_contact_person", null=True, blank=True)
    consignee_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    consignee_gstin = models.CharField(max_length=15,null=True, blank=True)
    consignee_state = models.CharField(max_length=20,null=True, blank=True)
    consignee_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    creadit_period = models.IntegerField(null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    payment_term = models.TextField(null=True, blank=True)
    customer_po = models.CharField(max_length=50, null=True, blank=True)
    customer_po_date = models.DateField(max_length=50, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    item_detail = models.ManyToManyField(DirectSalesInvoiceItemDetails,blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT)
    terms_conditions_text = models.TextField()
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tds_bool = models.BooleanField(default=False)
    tcs_bool = models.BooleanField(default=False)
    tds_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    overall_discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    overall_discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Direct_sales_invoice", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_Direct_sales_invoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit':{},
            "credits" : []
        }
        if self.status.name == "Submit":
            from itemmaster2.services.direct_sales_invoice_services import  sales_invoice_general_update
            credits = []
            
            debit_account = company_info().receivable_account
            sales_account = company_info().sales_account
            if not debit_account:
                raise CommonError(["Receivables not found in account."])
            
            if not sales_account:
                raise CommonError(["Sales account not found in company master."])
            sales_produce_total = 0
            for item in self.item_detail.all():
                itemmaster = item.itemmaster
                if itemmaster.item_types.name == "Product":
                    sales_produce_total += (item.amount or 0)
                    continue

                account = itemmaster.item_sales_account
                if account is None:
                    raise CommonError([f"Account not found in {itemmaster}."])
                
                credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": account.id,
                    "credit": item.amount,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if sales_produce_total:
                credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": sales_account.id,
                    "credit": sales_produce_total,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            
            
            if self.igst_value and  Decimal(self.igst_value) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": igst_account.id,
                    "credit": self.igst_value,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst_value and  Decimal(self.sgst_value) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": sgst_account.id,
                    "credit": self.sgst_value,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cgst_value and  Decimal(self.cgst_value) > 0:
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": cgst_account.id,
                    "credit": self.cgst_value,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cess_value and  Decimal(self.cess_value) > 0:
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": cess_account.id,
                    "credit": self.cess_value,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tds_total and Decimal(self.tds_total) > 0:
                tds_account = company_info().tds_account
                if not tds_account:
                    raise CommonError(["TDS not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": tds_account.id,
                    "credit": self.tds_total,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": tcs_account.id,
                    "credit": self.tcs_total,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.round_off is not None and self.round_off !=0 and self.round_off != "" :
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in account."])
                else:
                    credits.append({
                    "date": self.direct_sales_invoice_date,
                    "voucher_type": "Direct Sales Invoice",
                    "direct_sales_voucher_no": self.id,
                    "account": round_off_account.id,
                    "credit": self.round_off,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            account_general_ledger["credits"] = credits
            account_general_ledger['debit'] = {
                "date": self.direct_sales_invoice_date,
                "voucher_type": "Direct Sales Invoice",
                "direct_sales_voucher_no": self.id,
                "account": debit_account.id,
                "customer_supplier" :self.buyer.id,
                "debit": self.net_amount,
                "remark": self.remarks,
                "created_by": self.created_by.pk,
            }
            
            if not self.is_account_general_ledger_upated: 
                result = sales_invoice_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True
        
        history_list = {
            "status": "Status",
            "sales_invoice_no": "Sales Invoice No",
            "sales_invoice_date": "Date",
            "buyer": "Buyer",
            "buyer_address": "Buyer Address",
            "buyer_contact_person": "Buyer Contact Person",
            "buyer_gstin_type": "Buyer GSTIN Type",
            "buyer_gstin": "Buyer GSTIN",
            "buyer_state": "Buyer State",
            "buyer_place_of_supply": "Buyer Place of Supply",
            "remarks" : "Remarks",
        }
        if self._state.adding:
            conditions = {'resource': 'Sales Invoice', 'default': True, "department": self.department.id}
            response = create_serial_number(conditions)
            if response['success']:
                self.direct_sales_invoice_no = response['instance']
            else:
                raise CommonError(response['errors'])
        
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(DirectSalesInvoice, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, DirectSalesInvoice, history_list)
        if action == "Update":
            super(DirectSalesInvoice, self).save(*args, **kwargs)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_detail.exists():
            self.item_detail.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class SalesReturnBatch_item(models.Model):
    item_detail = models.ForeignKey("SalesReturnItemDetails", on_delete=models.CASCADE, null=True, blank=True)
    item_combo = models.ForeignKey("SalesReturnItemCombo", on_delete=models.CASCADE, null=True, blank=True)
    batch = models.ForeignKey(SalesOrder_2_RetunBatch, on_delete=models.PROTECT, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    is_stock_added = models.BooleanField(default=False)
    
class SalesReturnItemCombo(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    item_detail = models.ForeignKey("SalesReturnItemDetails", on_delete=models.CASCADE, null=True, blank=True)
    dc_item_combo = models.ForeignKey(SalesOrder_2_DeliverChallanItemCombo, on_delete=models.PROTECT, null=True, blank=True)
    sales_invoice_item_combo = models.ForeignKey(SalesInvoiceItemCombo, on_delete=models.PROTECT, null=True, blank=True)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    allowed_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    is_stock_added = models.BooleanField(default=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_sales_retun_item_detail_item_combo", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_sales_retun_item_detail_item_combo", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesReturnItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    sales_return = models.ForeignKey("SalesReturn", on_delete=models.CASCADE, null=True, blank=True, )
    dc_item_detail = models.ForeignKey(SalesOrder_2_DeliveryChallanItemDetails, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="dc_item_sales_return")
    sales_invoice_item_detail = models.ForeignKey(SalesInvoiceItemDetail, on_delete=models.PROTECT, null=True, blank=True)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    is_stock_added = models.BooleanField(default=False)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    # allowed_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_sales_return_item_details", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_sales_return_item_details", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesReturnOtherIncomeCharges(models.Model):
    sales_return = models.ForeignKey("SalesReturn", on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey("SalesOrder_2_otherIncomeCharges", on_delete=models.PROTECT, null=True, blank=True)
    other_income_charges_id = models.ForeignKey(OtherIncomeCharges, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="SalesReturn_otherIncomeChargesOtherIncomeCharges_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="SalesReturn_otherIncomeChargesOtherIncomeCharges_create",
                                on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  f"{self.id}--- {self.parent}"

class SalesReturn(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    sr_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, 
                            null=True, blank=True, editable=True)
    sr_date = models.DateField()
    sales_order = models.ForeignKey(SalesOrder_2, on_delete=models.PROTECT)
    e_way_bill = models.CharField(max_length=20, null=True, blank=True)
    e_way_bill_date = models.DateField(null=True, blank=True)
    comman_store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3) 
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedSalesReturn", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createSalesReturn", on_delete=models.PROTECT, )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debits':[],
            "credit" : {}
        }
        history_list = {
            "status__name": "Status",
            "sr_date": "sr_date",
            "e_way_bill": "E Way Bill",
            "e_way_bill_date": "E Way Bill Date",
            "comman_store": "Comman Store",
            "reason": "Reason",
            "item_total_befor_tax": "Item Total Befor Tax",
            "tax_total": "Tax Total",
            "taxable_value": "Taxable Value",
            "round_off": "Round Off",
            "round_off_method": "Round Off Method",
            "net_amount": "Net Amount",
        }
        if self._state.adding:
            conditions = {'resource': 'Sales Return', 'default': True, "department": self.sales_order.department.id}
            response = create_serial_number(conditions)
            if response['success']:
                self.sr_no = response['instance']
            else:
                raise CommonError(response['errors'])
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster2.services.sales_return_serives import  sales_return_general_update
            debits = []
            stock_account = company_info().stock_account
            sales_return_account = company_info().sales_return_account
            
            if not stock_account:
                raise CommonError(["Stock account not found in company master."])

            if not sales_return_account:
                raise CommonError(["Sales return account not found in company master."])

            sales_produce_total = 0
            for item in self.salesreturnitemdetails_set.all():
                itemmaster = item.itemmaster
                account = None
                if itemmaster.item_types.name == "Product":
                    sales_produce_total += (item.amount or 0)
                    continue
                account  = itemmaster.item_sales_account

                if not account:
                    raise CommonError([f'{itemmaster} account not found.'])
                debits.append({
                    "date": self.sr_date,
                    "voucher_type": "Sales Return",
                    "sales_return_voucher_no": self.id,
                    "account": account.id,
                    "debit": (item.amount or 0),
                    "purchase_account" : None ,
                    "purchase_amount" : 0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if sales_produce_total:
                debits.append({
                    "date": self.sr_date,
                    "voucher_type": "Sales Return",
                    "sales_return_voucher_no": self.id,
                    "account": stock_account.id,
                    "debit": (sales_produce_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            account_general_ledger['debits'] = debits
            account_general_ledger['credit'] = {
                    "date": self.sr_date,
                    "voucher_type": "Sales Return",
                    "sales_return_voucher_no": self.id,
                    "account": stock_account.id,
                    "credit": (sales_produce_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
            }
            result = sales_return_general_update(account_general_ledger)
            if not result['success']:
                raise CommonError(result['errors'])
            else:
                self.is_account_general_ledger_upated = True
        
        if self.status.name == "Canceled" and self.is_account_general_ledger_upated:
            agl_qs = AccountsGeneralLedger.objects.filter(sales_return_voucher_no=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()

        
        
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(SalesReturn, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, SalesReturn, history_list)
        if action == "Update":
            super(SalesReturn, self).save(*args, **kwargs)
        return instance

class ReceiptVoucherAdvanceDetails(models.Model):
    receipt_voucher_line = models.ForeignKey("ReceiptVoucherLine", on_delete=models.CASCADE ,null=True, blank=True)
    adv_remark = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ReceiptVoucherAdvanceDetails_modified",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReceiptVoucherAdvanceDetails_created", on_delete=models.PROTECT)

class ReceiptVoucherAgainstInvoice(models.Model):
    receipt_voucher_line = models.ForeignKey("ReceiptVoucherLine", on_delete=models.CASCADE ,null=True, blank=True)
    sales_invoice = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT)
    adjusted = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ReceiptVoucherAgainstInvoice_modified",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReceiptVoucherAgainstInvoice_created", on_delete=models.PROTECT)
 
class ReceiptVoucherLine(models.Model):
    receipt_voucher = models.ForeignKey("ReceiptVoucher", on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT, null=True, blank=True)
    cus_sup = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, null=True, blank=True)
    employee = models.ForeignKey("userManagement.Employee", on_delete=models.PROTECT,null=True, blank=True)
    pay_for = models.ForeignKey(AccountsMaster, related_name="ReceiptVoucherEmployee_pay_for", on_delete=models.PROTECT,
                                null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    modified_by = models.ForeignKey(User, related_name="ReceiptVoucherAccount_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReceiptVoucherAccount_created", on_delete=models.PROTECT)

class ReceiptVoucher(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True,  editable=True)
    rv_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT,
                            null=True, blank=True, editable=True)
    rv_date = models.DateField()
    pay_by = models.CharField(max_length=20, choices=PAY_BY, null=True, blank=True)
    pay_mode = models.CharField(max_length=20, choices=PAY_MODE, null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT,
                            null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    against_invoice = models.BooleanField(default=False)
    advance = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    bank = models.ForeignKey(AccountsMaster, related_name="ReceiptVoucher_bank",
                            on_delete=models.PROTECT, null=True, blank=True)
    transfer_via = models.CharField(choices=transfer_via, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    chq_ref_no = models.CharField(max_length=50, null=True, blank=True)
    chq_date = models.DateField(null=True, blank=True)
    is_account_general_ledger_updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ReceiptVoucher_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReceiptVoucher_created", on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit':{},
            "credits" : []
        }
        if not self.id:
            
            conditions = {'resource': 'Receipt Voucher', 'default': True}
            response = create_serial_number(conditions)
            if response['success']: 
                self.rv_no = response['instance']
            else:
                raise ValidationError(response['errors'])
            
        history_list = {
            "status__name": "Status",
            "rv_date": "Receipt Voucher Date",
            "pay_by": "Pay By",
            "pay_mode": "Pay Mode",
            "sales_person": "Sales Person",
            "currency": "Currency",
            "exchange_rate": "Exchange Rate",
            "employee": "Employee",
            "emp_amount": "Employee Amount",
            "cus_sup": "CUS_SUP",
            "cus_sup_amount": "CUS_SUP Net Amount",
            "against_invoice": "Against Invoice",
            "advance":"Advance",
            "bank" : "Bank",
            "transfer_via" : "transfer_via"
        }
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_updated:
            from itemmaster2.services.serivece_class import receipt_voucher_genral_update
            receivable_account = None
            if self.pay_by == "Supplier & Customer":
                receivable_account = company_info().receivable_account
                if not receivable_account:
                    raise CommonError(["Receivable account not found in company master."])
            credits = []

            for rv_line in self.receiptvoucherline_set.all():
                if self.pay_by == "Supplier & Customer":
                    credits.append({
                    "date": self.rv_date,
                    "voucher_type": "Receipt Voucher",
                    "receipt_voucher_voucher_no": self.id,
                    "account": receivable_account.id ,
                    "credit": (rv_line.amount or 0),
                    "customer_supplier" : rv_line.cus_sup.id,
                    "purchase_account" :  None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })

                elif self.pay_by == "Employee":
                    credits.append({
                    "date": self.rv_date,
                    "voucher_type": "Receipt Voucher",
                    "receipt_voucher_voucher_no": self.id,
                    "account": rv_line.pay_for.id,
                    "credit": (rv_line.amount or 0),
                    "employee":rv_line.employee.id,
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
                
                else:
                    credits.append({
                    "date": self.rv_date,
                    "voucher_type": "Receipt Voucher",
                    "receipt_voucher_voucher_no": self.id,
                    "account": rv_line.account.id ,
                    "credit": (rv_line.amount or 0),
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
                
            account_general_ledger['credits'] = credits
            account_general_ledger['debit'] = {
                    "date": self.rv_date,
                    "voucher_type": "Receipt Voucher",
                    "receipt_voucher_voucher_no": self.id,
                    "account": self.bank.id ,
                    "debit": (self.total_amount or 0),
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": self.remark,
                    "created_by": self.created_by.pk,
                    }
            result = receipt_voucher_genral_update(account_general_ledger)
            if not result['success']:
                raise CommonError(result['errors'])
            else:
                self.is_account_general_ledger_updated = True
        
        if self.status.name == "Canceled" and self.is_account_general_ledger_updated:
            agl_qs = AccountsGeneralLedger.objects.filter(receipt_voucher_voucher_no=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()
            sales_paid = SalesPaidDetails.objects.filter(receipt_voucher=self.id)
            if sales_paid.exists():
                sales_paid.delete()
        
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ReceiptVoucher, history_list)
            super(ReceiptVoucher, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ReceiptVoucher, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ReceiptVoucher, history_list)
        return instance

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class SalesPaidDetails(models.Model):
    sales_invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)
    receipt_voucher = models.ForeignKey(ReceiptVoucher, on_delete=models.CASCADE, 
                                        null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="SalesPaidDetails_created", on_delete=models.PROTECT)



class CreditNoteOtherIncomeCharges(models.Model):
    credit_note = models.ForeignKey("CreditNote", on_delete=models.CASCADE, null=True, blank=True)
    other_income_charges = models.ForeignKey(OtherIncomeCharges, on_delete=models.PROTECT)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    modified_by = models.ForeignKey(User, related_name="CreditNoteOtherIncomeCharges_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="CreditNoteOtherIncomeCharges_create", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CreditNoteAccount(models.Model):
    index = models.IntegerField(null=True, blank=True)
    credit_note = models.ForeignKey("CreditNote", on_delete=models.CASCADE, null=True, blank=True)
    account_master = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    description = models.CharField(max_length=100, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tcs_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_by = models.ForeignKey(User, related_name="creditnoteaccount_created_by", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="creditnoteaccount_modified_by", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CreditNoteComboItemDetails(models.Model):
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    credit_note_item = models.ForeignKey("CreditNoteItemDetails", on_delete=models.CASCADE, null=True, blank=True)
    sales_return_combo_item = models.ForeignKey(SalesReturnItemCombo, on_delete=models.PROTECT, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    display = models.CharField(max_length=50, blank=True, null=True)
    is_mandatory = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_credit_note_combo_item_details", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_credit_note_combo_item_details", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CreditNoteItemDetails(models.Model):
    index = models.IntegerField(null=True, blank=True)
    credit_note = models.ForeignKey("CreditNote", on_delete=models.CASCADE, null=True, blank=True)
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    sales_return_item = models.ForeignKey(SalesReturnItemDetails, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(max_length=250)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tcs_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_credit_note_item_details", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_credit_note_item_details", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CreditNote(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT, null=True, blank=True,  editable=True)
    cn_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, 
                            null=True, blank=True, editable=True)
    cn_date = models.DateField()
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.PROTECT, null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales_person_credit_note")
    reason = models.CharField(max_length=50, choices=CREDIT_NOTE_REASON)
    remarks = models.TextField(null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=6, decimal_places=2)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    e_way_bill_no = models.CharField(max_length=20, null=True, blank=True,)
    e_way_bill_date = models.DateField(null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT)
    buyer = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="credit_note_buyer")
    buyer_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="credit_note_buyer_address")
    buyer_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                        related_name="credit_note_buyer_contact_person")
    buyer_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    buyer_gstin = models.CharField(max_length=15, null=True, blank=True)
    buyer_state = models.CharField(max_length=50, null=True, blank=True)
    buyer_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    consignee = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="credit_note_consignee")
    consignee_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                        related_name="credit_note_consignee_address")
    consignee_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                        related_name="credit_note_consignee_contact_person")
    consignee_gstin_type = models.CharField(max_length=50, null=True, blank=True)
    consignee_gstin = models.CharField(max_length=15, null=True, blank=True)
    consignee_state = models.CharField(max_length=50, null=True, blank=True)
    consignee_place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    tds_bool = models.BooleanField(default=False)
    tcs_bool = models.BooleanField(default=False)
    tds_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_total = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3) 
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_credit_note", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="created_credit_note", on_delete=models.PROTECT, )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debits':[],
            "credit" : {}
        }
        if not self.id:
            conditions = {'resource': 'Credit Note', 'department' : self.department.id,  'default': True}
            response = create_serial_number(conditions)
            if response['success']: 
                self.cn_no = response['instance']
            else:
                raise ValidationError(response['errors'])
                
        history_list = {
            "status__name": "Status",
            "cn_date": "Receipt Voucher Date",
            "sales_person": "Sales Person",
            "reason": "Reason",
            "remarks": "Remarks",
            "currency__Currency__name": "Currency",
            "exchange_rate": "Exchange Rate",
            "department__name": "Department",
            "e_way_bill_no": "Eway Bill No",
            "e_way_bill_date": "Eway Bill Date",
            "buyer" : "Buyer",
            "consignee" : "Consignee",
            "net_amount" : "net_amount"
        }
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster2.services.serivece_class import credit_note_genral_update
            debits = []
            sales_return_account = company_info().sales_return_account
            sales_account = company_info().sales_account

            if not sales_return_account:
                raise CommonError(["Sales return account not found in company master."])
            
            if not sales_account:
                raise CommonError(["Sales account not found in company master."])
            
            sales_produce_total = 0
            for item in self.creditnoteitemdetails_set.all():
                itemmaster = item.itemmaster
                account = None
                if itemmaster.item_types.name == "Product":
                    sales_produce_total += (item.amount or 0)
                    continue
                account = itemmaster.item_sales_account
                if not account:
                    raise CommonError([f'{itemmaster} account not found.'])
                debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": account.id if self.sales_return else sales_account.id,
                    "debit": (item.amount or 0),
                    "purchase_account" : sales_account.id  if self.sales_return else None,
                    "purchase_amount" :(item.amount or 0) if self.sales_return else 0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if sales_produce_total:
                debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": sales_return_account.id if self.sales_return else sales_account.id,
                    "debit": (sales_produce_total or 0),
                    "purchase_account" : sales_account.id if self.sales_return else None,
                    "purchase_amount" :(sales_produce_total or 0) if self.sales_return else 0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            for charge in self.creditnoteotherincomecharges_set.all():
                debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": charge.other_income_charges.account.id,
                    "debit": (charge.amount or 0),
                    "purchase_account" : None ,
                    "purchase_amount" : 0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.igst and  Decimal(cal_total_dic_value(self.igst)) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in account."])
                else:
                    igst_value =  cal_total_dic_value(self.igst)
                    debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": igst_account.id,
                    "debit": (igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst and  cal_total_dic_value(self.sgst) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in account."])
                else:
                    sgst_value = cal_total_dic_value(self.sgst)
                    debits.append({
                        "date": self.cn_date,
                        "voucher_type": "Credit Note",
                        "credit_note_voucher_no": self.id,
                        "account": sgst_account.id,
                        "debit": (sgst_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.cgst and   cal_total_dic_value(self.cgst) > 0 :
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in account."])
                else: 
                    cgst_value = cal_total_dic_value(self.cgst)
                    debits.append({
                        "date": self.cn_date,
                        "voucher_type": "Credit Note",
                        "credit_note_voucher_no": self.id,
                        "account": cgst_account.id,
                        "debit": (cgst_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.cess and   cal_total_dic_value(self.cess) > 0 :
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in account."])
                else:
                    cess_value = cal_total_dic_value(self.cess)
                    debits.append({
                        "date": self.cn_date,
                        "voucher_type": "Credit Note",
                        "credit_note_voucher_no": self.id,
                        "account": cess_account.id,
                        "debit": (cess_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in company master."])
                else:
                    debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": tcs_account.id,
                    "debit": (self.tcs_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
                    
            if self.tds_total and  Decimal(self.tds_total) > 0:
                tds_account = company_info().tds_account
                if not tds_account:
                    raise CommonError(["TDS not found in company master."])
                else:
                    debits.append({
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": tds_account.id,
                    "debit": (self.tds_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.round_off is not None and self.round_off != 0  and  self.round_off !="":
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in account."])
                else: 
                    debits.append({
                        "date": self.cn_date,
                        "voucher_type": "Credit Note",
                        "credit_note_voucher_no": self.id,
                        "account": round_off_account.id,
                        "debit": (self.round_off or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })

            account_general_ledger['debits'] = debits

            payable_account = company_info().payable_account
            if not payable_account:
                raise CommonError(["Payable Account not found in company master."])
            else:
                account_general_ledger["credit"] = {
                    "date": self.cn_date,
                    "voucher_type": "Credit Note",
                    "credit_note_voucher_no": self.id,
                    "account": payable_account.id,
                    "credit": (self.net_amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                    } 
            
            result = credit_note_genral_update(account_general_ledger)
            if not result['success']:
                raise CommonError(result['errors'])
            else:
                self.is_account_general_ledger_upated = True

        if self.status.name == "Canceled" and self.is_account_general_ledger_upated:
            agl_qs = AccountsGeneralLedger.objects.filter(credit_note_voucher_no=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()

        if self.pk is not None:
            instance = SaveToHistory(self, "Update", CreditNote, history_list)
            super(CreditNote, self).save(*args, **kwargs)
        elif self.pk is None:
            super(CreditNote, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", CreditNote, history_list)
        return instance



