
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import re
from django.core.exceptions import ValidationError


NATURE_TYPE_CHOICES = [
        ('As per HSN', 'As per HSN'),
        ('Specify', 'Specify'),
        ('Import Purchase', 'Import Purchase'),
    ]

item_types = (("Product", "Product"),
              ("Service", "Service"))
Item_Indicators = (("Buyer", "Buyer"),
                   ("seller", "seller"),
                   ('both', 'both'))
hsn_types = (("HSN", "HSN"),
             ("SAC", "SAC"))
e_way_bill = (("BAGS", "BAGS"),
              ("BALE", "BALE"),
              ("BUNDLES", "BUNDLES"),
              ("BUCKLES", "BUCKLES "),
              ("BILLION OF UNITS", "BILLION OF UNITS"),
              ("BOX", "BOX"),
              ("BOTTLES", "BOTTLES"),
              ("BUNCHES", "BUNCHES"),
              ("CANS", "CANS"),
              ("CUBIC METERS", "CUBIC METERS"),
              ("CUBIC CENTIMETERS", "CUBIC CENTIMETERS"),
              ("CENTIMETERS", "CENTIMETERS"),
              ("CARTONS", "CARTONS"),
              ("DOZENS", "DOZENS"),
              ("DRUMS", "DRUMS"),
              ("GREAT GROSS", "GREAT GROSS"),
              ("GRAMMES", "GRAMMES"),
              ("GROSS", "GROSS"),
              ("GROSS YARDS", "GROSS YARDS"),
              ("KILOGRAMS", "KILOGRAMS"),
              ("KILOLITRE", "KILOLITRE"),
              ("KILOMETRE", "KILOMETRE"),
              ("LITRES", "LITRES"),
              ("MILILITRE", "MILILITRE"),
              ("METERS", "METERS"),
              ("METRIC TON", "METRIC TON"),
              ("NUMBERS", "NUMBERS"),
              ("OTHERS", "OTHERS"),
              ("PACKS", "PACKS"),
              ("PIECES", "PIECES"),
              ("PAIRS", "PAIRS"),
              ("QUINTAL", "QUINTAL"),
              ("ROLLS", "ROLLS"),
              ("SETS", "SETS"),
              ("SQUARE FEET", "SQUARE FEET"),
              ("SQUARE METERS", "SQUARE METERS"),
              ("SQUARE YARDS", "SQUARE YARDS"),
              ("TABLETS", "TABLETS"),
              ("TEN GROSS", "TEN GROSS"),
              ("THOUSANDS", "THOUSANDS"),
              ("TONNES", "TONNES"),
              ("TUBES", "TUBES"),
              ("US GALLONS", "US GALLONS"),
              ("UNITS", "UNITS"),
              ("YARDS", "YARDS"))
gst_rate = ((5, 5),
            (12, 12),
            (18, 18),
            (28, 28),)
Action = (("Add", 'Add'),
          ("Delete", 'Delete'),
          ("Update", 'Update'))
Accountsgroup_Type = (("Asset", "Asset"),
                      ("Income", "Income"),
                      ("Liabilities", "Liabilities"),
                      ("Expenses", "Expenses"))
Accounts_Type = (("Bank", "Bank"),
                 ("Tax", "Tax"),
                 ("Cash", "Cash"),
                 ("Swipe", "Swipe"),
                 ("Employee", "Employee"))
Type_of_tax = (("GST", "GST"),
                ("TDS", "TDS"),
                ("TCS", "TCS"),
                ("Others", "Others"))
gst_tax =  (("IGST", "IGST"),
            ("CGST", "CGST"),
            ("SGST/UTGST", "SGST/UTGST"),
            ("Csee", "Csee"))

address_types = (('Billing Address', "Billing Address"),
                 ('Shipping Address', 'Shipping Address'),
                 ('Others', 'Others'))
Item_Warranty_base_on = (("Invoice date", "Invoice date"),
                         ('Installation date', 'installation date'))
visibleTo_ = (("Myself", "Myself"),
              ("All User", "All User"),
              ("Select Users", "Select Users"),
              )
salutation = (('MR', 'MR'),
              ('MS', 'MS'),
              ('MRS', 'MRS'),
              ('DR', 'DR'),
              ('MS_', 'M/s'),)

gst_type = (('REGULAR', 'REGULAR'),
            ('UNREGISTERED/CONSUMER', 'UNREGISTERED/CONSUMER'),
            ('COMPOSITION', 'COMPOSITION'),
            ('GOVERNMENT ENTITY/TDS', 'GOVERNMENT ENTITY/TDS'),
            ('REGULAR-SEZ', 'REGULAR-SEZ'),
            ('REGULAR-DEEMED EXPORTER', 'REGULAR-DEEMED EXPORTER'),
            ('REGULAR-EXPORTS (EOU)', 'REGULAR-EXPORTS (EOU)'))

tcs = (('SALES', 'SALES'),
       ('PURCHASE', 'PURCHASE'),
       ('BOTH', 'BOTH'))
currencyFormate = (
    ('0,00,00,00', '0,00,00,00'),
    ('000,000,000', '000,000,000'))
Postypes_ = (('Sample', 'Sample'),
             ('Sales', 'Sales'))
PosStatus = (('Save', "Save"),
             ("Submited", "Submited"),
             ('Canceled', "Canceled"))

NumberingResource = (("Pos", "Pos"),
                    ("Purchase Order", "Purchase Order"),
                    ("Goods Inward Note", "Goods Inward Note"),
                    ("Goods Receipt Note", "Goods Receipt Note"),
                    ("Quality Inspection Report", "Quality Inspection Report"),
                    ("Rework Delivery Challan", "Rework Delivery Challan"),
                    ("Purchase Return Challan", "Purchase Return Challan"),
                    ("Direct Purchase Invoice", "Direct Purchase Invoice"),
                    ("Purchase Invoice", "Purchase Invoice"),
                    ("Quotations", "Quotations"),
                    ("SalesOrder", "SalesOrder"),
                    ("SalesOrder Delivery Challan", "SalesOrder Delivery Challan"),
                    ("Payment Voucher", "Payment Voucher"),
                    ("Target", "Target"),
                    ('Sales Invoice', 'Sales Invoice'),
                    ('Debit Note', 'Debit Note'),
                    ('Sales Return', 'Sales Return'),
                    ('Receipt Voucher', 'Receipt Voucher'),
                    ('Credit Note', 'Credit Note'),
                     )
TermsConditionsModels = (("Purchase Order", "Purchase Order"),
                         ("Sales", "Sales"),
                         ("Account", "Account"),
                         ("Service", "Service"),
                         ("Production", "Production"),
                         ("HR", "HR"),
                         ("Quotations", "Quotations"),
                         ("Sales_order", "Sales_order"),
                        ('SalesOrder Delivery Challan', 'SalesOrder Delivery Challan'),
                        ('Sales Invoice', 'Sales Invoice'),
                        ('Sales Return', 'Sales Return'),
                        ('Rework DC', 'Rework DC'),
                        ('Purchase Invoice', 'Purchase Invoice'),
                        ('Purchase Return', 'Purchase Return'),
                        ('Credit Note', 'Credit Note'),
                         
                         )

purchases_status = (('Draft', 'Draft'),
                    ('Submit', 'Submit'),
                    ('Canceled', 'Canceled'))

leave_type = (('Paid', 'Paid'),
              ('Loss Of Pay', 'Loss Of Pay'))



def SaveToHistory(instance, action, model_class, history_list):
    
    if action.lower() == "update":
        original_instance = model_class.objects.get(pk=instance.pk)
        history_record = ItemMasterHistory(
            Action=action,
            SavedBy=instance.modified_by  # Assuming you want to save the user who modified the instance
        )
    elif action.lower() == "add":
        original_instance = model_class.objects.get(pk=instance.pk)
        history_record = ItemMasterHistory(
            Action=action,
            SavedBy=instance.created_by  # Assuming you want to save the user who modified the instance
        )
    with transaction.atomic():
        try:
            for field in instance._meta.fields:
                 
                if field.name in history_list and history_list[field.name]:
                    field_name = field.name
                    if action.lower() == "update":
                        original_value = getattr(original_instance, field_name)
                    new_value = getattr(instance, field_name)
                    if isinstance(new_value, (datetime, date)):
                        new_value = new_value.strftime('%d-%m-%Y')  # or '%d-%m-%Y' or with time '%Y-%m-%d %H:%M:%S'
                        if action.lower() == "update":
                            original_value = original_value.strftime('%d-%m-%Y')
                    if action.lower() == "update" and original_value != new_value:
                        if field_name != "modified_by":
                            change_description = f"{history_list[field.name]}: {str(original_value)} -> {str(new_value)}; "
                            history_record.UpdatedState += f"\n{change_description}"
                    elif action.lower() == "add":
                        if field_name != "modified_by":
                            change_description = f"{history_list[field.name]}: {str(new_value)}; "
                            history_record.UpdatedState += f"{change_description}"
        except Exception as e:
            print(e)
        if history_record.UpdatedState is not None and history_record.UpdatedState != "":
            history_record.save()
            instance.history_details.add(history_record)
    return instance


def create_serial_number(conditions):
    errors = ""
    try:
        with transaction.atomic():
            # Retrieve the numbering series based on conditions
            numbering_series = NumberingSeries.objects.filter(**conditions).first()
            success = False

            if numbering_series:
                format_template = numbering_series.formate
                last_serial_history = numbering_series.last_serial_history
                current_value = numbering_series.current_value

                # Split the format into text part and zero count part
                text_format = format_template.split("#")[0]
                zero_count = int(format_template.split("#")[-1])

                if last_serial_history > 0:
                    pos_id = f"{text_format}{int(last_serial_history):0{zero_count}d}"
                else:
                    pos_id = f"{text_format}{current_value:0{zero_count}d}"

                try:
                    linked_instance = NumberingSeriesLinking.objects.create(
                        numbering_Seriel_link=numbering_series,
                        linked_model_id=pos_id
                    )
                    success = True
                    if last_serial_history > 0:
                        numbering_series.last_serial_history += 1
                    else:
                        numbering_series.last_serial_history = current_value + 1
                    numbering_series.current_value = numbering_series.last_serial_history
                    numbering_series.save()
                except Exception as e:
                    print(e)
                    errors = str(e)
                    print("errors---", errors)
                return {'instance': linked_instance, 'success': success, 'errors': errors}

            else:
                return {'instance': None, 'success': False, 'errors': 'NumberingSeries not found'}

    except NumberingSeries.DoesNotExist:
        return {'instance': None, 'success': False, 'errors': 'No matching NumberingSeries found'}
    except Exception as e:
        print("errors---", e)
        return {'instance': None, 'success': False, 'errors': errors}

class FilingSchedule(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    QUARTERLY = 'quarterly', 'Quarterly'

class DeductorType(models.TextChoices):
    COMPANY = "company", "Company"
    INDIVIDUAL = "individual/huf", "Individual/huf"

class BankDetails(models.Model):
    company_master = models.ForeignKey("itemmaster.CompanyMaster", on_delete=models.PROTECT)
    bank_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=30, unique=True)
    ifsc_code = models.CharField(max_length=11)  # IFSC is always 11 chars in India
 
    is_active = models.BooleanField(default=True)  # optional: to soft-disable accounts
    modified_by = models.ForeignKey(User, related_name="bank_detail_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="bank_detail_created", on_delete=models.PROTECT, null=True,
                                blank=True)
 
    class Meta:
        db_table = "bank_details"
        verbose_name = "Bank Detail"
        verbose_name_plural = "Bank Details"
 
    def __str__(self):
        return f"{self.bank_name} ({self.branch_name}) - {self.account_number}"
 

def validate_phone(value):
    pattern = r'^\+?[1-9]\d{6,14}$'
    if not re.match(pattern, value):
        raise ValidationError("Enter a valid phone number (7-15 digits, optional +).")






class CompanyMaster(models.Model):
    company_name = models.CharField(max_length=100)
    address = models.ForeignKey("itemmaster.CompanyAddress",on_delete=models.PROTECT)
    currency = models.ForeignKey("itemmaster.CurrencyExchange", on_delete=models.PROTECT)
    mobile = models.CharField(max_length=15, validators=[validate_phone])
    telephone = models.CharField(max_length=15,null=True,blank=True,validators=[validate_phone])
    whatsapp = models.CharField(max_length=15,null=True,blank=True,validators=[validate_phone])
    email = models.EmailField(null=True, blank=True)
    financial_year_start_from = models.DateField()
    financial_year_end_from = models.DateField()
    gst = models.BooleanField(default=False)
    # gst_state = models.CharField(null=True, blank=True)
    gst_in_type = models.ForeignKey("itemmaster.GstType", on_delete=models.PROTECT, null=True, blank=True)
    gstin = models.CharField(max_length=15, null=True, blank=True)
    gstr1_filing_schedule = models.CharField(max_length=20,
                            choices=FilingSchedule.choices, null=True, blank=True)
    e_way_bill = models.BooleanField(default=False)
    applicable_from = models.DateField(null=True, blank=True)
    threshold_for_intrastate = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    threshold_for_interstate = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    tds = models.BooleanField(default=False)
    tds_tan_no = models.CharField(max_length=50, null=True, blank=True)
    deductor_type = models.CharField(max_length=20, choices=DeductorType.choices,
                                    blank=True,null=True)
    deductor_branch = models.CharField(max_length=50, null=True, blank=True)
    tcs = models.BooleanField(default=False)
    tcs_tan_no = models.CharField(max_length=50, null=True, blank=True)
    collector_type = models.CharField(max_length=20, choices=DeductorType.choices,
                                    blank=True,null=True)
    collector_branch = models.CharField(max_length=50, null=True, blank=True)
    sales_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='sales_account')
    sales_pending_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='sales_pending_account')
    sales_return_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='sales_return_account')
    purchase_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_account')
    purchase_return_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_return_account')
    receivable_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='receivable_account')
    payable_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='payable_account')
    purchase_pending_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_pending_account')
    stock_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='stock_account')
    stock_in_transit_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='stock_in_transit_account')
    work_in_progress_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='work_in_progress_account')
    round_off_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='round_off_account')
    forex_gain_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='forex_gain_account')
    forex_loss_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='forex_loss_account')
    expense_advance_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='expense_advance_account')
    salary_advance_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='salary_advance_account')
    expense_reimbursement_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='expense_reimbursement_account')
    salary_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='salary_account')
    igst_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='igst_account')
    cgst_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='cgst_account')
    sgst_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='sgst_account')
    cess_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='cess_account')
    tds_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='tds_account')
    tcs_account = models.ForeignKey("itemmaster.AccountsMaster", on_delete=models.PROTECT, null=True, blank=True, related_name='tcs_account')

    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="company_master_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="company_master_created", on_delete=models.PROTECT, null=True,
                                blank=True)
    def __str__(self):
        return f'{self.company_name}'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            history_list = {
                "company_name": "Company Name",
                "currency": "Currency",
                "mobile": "Mobile",
                "telephone": "Telephone",
                "whatsapp": "Whatsapp",
                "email": "Email",
                "financial_year_start_from": "Financial Year Start From",
                "financial_year_end_from": "Financial Year End From",
                "gst": "GST",
                "gst_in_type": "GSTIN TYPE",
                "gstr1_filing_schedule" : "GSTR1 filing schedule",
                "e_way_bill": "E Way Bill",
                "applicable_from": "Applicable From",
                "threshold_for_intrastate" : "Threshold for intrastate",
                "threshold_for_interstate":"Threshold for interstate",
                "tds" : "TDS",
                "tds_tan_no" : "TDS TAN No",
                "deductor_type":"Deductor Type",
                "deductor_branch" : "Deductor Branch",
                "tcs" :"TCS",
                "tcs_tan_no":"TCS TAN No",
                "collector_type":"Collector Type",
                "collector_branch":"Collector Branch"

            }
            
            action = "Add" if self._state.adding else "Update"
            if action == "Add":
                super(CompanyMaster, self).save(*args, **kwargs)
            instance = SaveToHistory(self, action, CompanyMaster, history_list)
            if action == "Update":
                super(CompanyMaster, self).save(*args, **kwargs)
            return instance

class ReportTemplate(models.Model):
    report_name = models.CharField(max_length=50, unique=True)
    report_folder = models.CharField(max_length=50)
    primary_model = models.CharField(max_length=50)  # Model associated with the report
    app = models.CharField(max_length=50)  # App where the model belongs
    share_report = models.ManyToManyField(User, blank=True)  # Shared with users
    description = models.CharField(max_length=200, blank=True, null=True)
    grouped_by = models.JSONField(blank=True, null=True)
    select_data = models.JSONField()  # Required field
    filter_conditions = models.JSONField(blank=True, null=True)

    x_axis = models.JSONField(blank=True, null=True)
    y_axis = models.JSONField(blank=True, null=True)
    chart = models.CharField(max_length=50, blank=True, null=True)
    chart_type = models.CharField(max_length=20, blank=True, null=True)
    chart_title = models.CharField(max_length=50, blank=True, null=True)
    chart_date_format = models.CharField(max_length=20, blank=True, null=True)
    data_field = models.JSONField(blank=True, null=True)
    modified_by = models.ForeignKey(User, related_name="modifiedReportTemplate", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createReportTemplate", on_delete=models.PROTECT, null=True,
                                   blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)


class States(models.Model):
    state_name = models.CharField(max_length=50)
    def __str__(self):
        return f'{self.state_name}'


class Districts(models.Model):
    district = models.CharField(max_length=50)
    def __str__(self):
        return f'{self.district}'


class Pincode(models.Model):
    pincode = models.CharField(max_length=6)

    def __str__(self):
        return f'{self.pincode}'


class ManualIdSeries(models.Model):
    name = models.CharField(max_length=20)
    id_series = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, related_name="created_ManualIdSeries", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_ManualIdSeries", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AreaNames(models.Model):
    area_name = models.CharField(max_length=50)


class AddressMaster(models.Model):
    state = models.ForeignKey(States, on_delete=models.PROTECT)
    district = models.ForeignKey(Districts, on_delete=models.PROTECT)
    pincode = models.ForeignKey(Pincode, on_delete=models.PROTECT)
    area_name = models.ForeignKey(AreaNames, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, related_name="created_Address", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_Address", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Imagedata(models.Model):
    image = models.CharField(max_length=2500, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Image", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_Image", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Document(models.Model):
    document_file = models.URLField(max_length=2500, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Doc", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_Doc", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ItemMasterHistory(models.Model):
    Action = models.CharField(choices=Action, max_length=10)
    ColumnName = models.CharField(max_length=250, null=True, blank=True)
    PreviousState = models.CharField(max_length=250, null=True, blank=True)
    UpdatedState = models.TextField(max_length=2500)
    modifiedDate = models.DateTimeField(auto_now_add=True)
    SavedBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class EditListView(models.Model):
    view_name = models.CharField(max_length=50)
    visible_to = models.CharField(max_length=20, choices=visibleTo_, default=1)
    visible_to_user = models.ManyToManyField(User, blank=True)
    default_sort_column = models.CharField(max_length=60, null=True, blank=True)
    default_sort_order = models.CharField(max_length=60, null=True, blank=True)
    filiter_conditions = models.JSONField(null=True, blank=True)
    coloumn_to_display = models.JSONField(null=True, blank=True)
    default_update_date_time = models.DateTimeField(null=True, blank=True)
    is_default = models.BooleanField(default=True)
    table = models.CharField(max_length=50)
    modified_by = models.ForeignKey(User, related_name="ModifiedPOSEditListView", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createPOSTEditListView", on_delete=models.CASCADE, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.table}'


class ResourcePosType(models.Model):
    ReSourceIsPosType = models.CharField(max_length=20, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="ModifiedPOSTYPE", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="createPOSTYPE", on_delete=models.CASCADE, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.ReSourceIsPosType}'


class NumberingSeries(models.Model):
    numbering_series_name = models.CharField(max_length=50, unique=True)
    resource = models.CharField(max_length=50, choices=NumberingResource)
    pos_type = models.ForeignKey(ResourcePosType, on_delete=models.PROTECT, null=True, blank=True)
    department = models.ForeignKey("Department", on_delete=models.PROTECT, null=True, blank=True)
    formate = models.CharField(max_length=50)
    current_value = models.IntegerField()
    last_serial_history = models.IntegerField()
    default = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified", on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="create", on_delete=models.CASCADE, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.numbering_series_name}'

    def save(self, *args, **kwargs):
        self.Name = self.numbering_series_name
        if NumberingSeries.objects.exclude(pk=self.pk).filter(
                numbering_series_name__iexact=self.numbering_series_name).exists():
            raise ValidationError("NumberingSeries Name must be unique.")
        history_list = {
            "numbering_series_name": "Name",
            "resource": "Resource",
            "pos_type": "POS Type",
            "department": "Department",
            "formate": "Formate",
            "default": "Default",
            "active": "Active"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", NumberingSeries, history_list)
            super(NumberingSeries, self).save(*args, **kwargs)
        elif self.pk is None:
            super(NumberingSeries, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", NumberingSeries, history_list)
        return instance

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        NumberingSeriesLinking.objects.filter(numbering_Seriel_link=self).delete()
        super().delete(*args, **kwargs)

class NumberingSeriesLinking(models.Model):
    numbering_Seriel_link = models.ForeignKey(NumberingSeries, on_delete=models.PROTECT)
    linked_model_id = models.CharField(max_length=50)
    def __str__(self):
        return str(self.linked_model_id)


class HsnType(models.Model):
    name = models.CharField(max_length=5)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True, null=True, blank=True)


class GstRate(models.Model):
    rate = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True, null=True, blank=True)


class TaxabilityType(models.TextChoices):
    TAXABLE = 'taxable', 'Taxable'
    NIL_RATE = 'nil rated', 'Nil Rated'
    EXEMPT = 'exempt', 'Exempt'
    NON_GST = 'non-gst', 'Non-GST'

class Hsn(models.Model):
    hsn_types = models.ForeignKey(HsnType, on_delete=models.PROTECT, null=True, blank=True, default=1)
    hsn_code = models.IntegerField(unique=True)
    taxability_type = models.CharField(max_length=20,
                        choices=TaxabilityType.choices, null=True, blank=True)
    description = models.TextField()
    cess_rate = models.IntegerField(null=True, blank=True)
    rcm = models.BooleanField(default=False)
    itc = models.BooleanField(default=False)
    effective_date = models.DateField(null=True, blank=True)
    gst_rates = models.ForeignKey(GstRate, on_delete=models.PROTECT, null=True, blank=True, default=1)
    modified_by = models.ForeignKey(User, related_name="modified_Hsn", on_delete=models.PROTECT, null=True,
                                    blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Hsn", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.hsn_code)

    def save(self, *args, **kwargs):
        history_list = {
            "hsn_types": "HSN Type",
            "hsn_code": "HSN Code",
            "description": "Description",
            "cess_rate": "CESS Rate",
            "rcm": "RCM",
            "itc": "ITC",
            "effective_date": "Effective Date",
            "gst_rates": "Gst Rates"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Hsn, history_list)
            super(Hsn, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Hsn, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Hsn, history_list)
        return instance

    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here

        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
            HsnEffectiveData = HsnEffectiveDate.objects.filter(hsn_id=self.id)
            for hsn_ in HsnEffectiveData:
                hsn_.delete()
        super().delete(*args, **kwargs)

"""On effective_date data will relpace data in hsn -> every day using 
scheduler triger functions update the data"""
class HsnEffectiveDate(models.Model):
    hsn_id = models.ForeignKey(Hsn, on_delete=models.CASCADE)
    # before add Hsn need to check unique  except current hsn
    hsn_code = models.IntegerField()
    taxability_type = models.CharField(max_length=20,
                            choices=TaxabilityType.choices, null=True, blank=True)
    gst_rates = models.ForeignKey(GstRate, on_delete=models.PROTECT, null=True, blank=True, default=1)
    cess_rate = models.IntegerField(null=True, blank=True)
    rcm = models.BooleanField(default=0)
    itc = models.BooleanField(default=0)
    effective_date = models.DateField()
    created_by = models.ForeignKey(User, related_name="created_HsnEffectiveDate", on_delete=models.PROTECT, null=True,
                                blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_HsnEffectiveDate", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True,
                                    blank=True)

    def __str__(self):
        return str(self.hsn_code)


class Item_Groups_Name(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent_group = models.ForeignKey("Item_Groups_Name", null=True, blank=True, on_delete=models.PROTECT)
    hsn = models.ForeignKey(Hsn, null=True, blank=True, on_delete=models.PROTECT)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="IGmodified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="IGcreate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = self.name
        if Item_Groups_Name.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        # super(Item_Groups_Name, self).save(*args, **kwargs)
        history_list = {
            "name": "Name",
            "parent_group": "Parent Group",
            "hsn": "Hsn"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Item_Groups_Name, history_list)
            super(Item_Groups_Name, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Item_Groups_Name, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Item_Groups_Name, history_list)
        return instance

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)


class UserGroup(models.Model):
    group_name = models.CharField(max_length=50, unique=True)
    sub_group_name = models.ForeignKey("UserGroup", null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=50, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="UserGroupmodified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="UserGroupcreate", on_delete=models.PROTECT, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "group_name": "Group Name",
            "sub_group_name": "Sub Group Name",
            "description": "Description"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", UserGroup, history_list)
            super(UserGroup, self).save(*args, **kwargs)
        elif self.pk is None:
            super(UserGroup, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", UserGroup, history_list)

        return instance

    def __str__(self):
        return self.group_name


class UOM(models.Model):
    name = models.CharField(max_length=255, unique=True)
    e_way_bill_uom = models.CharField(choices=e_way_bill, max_length=50, null=True, blank=True)
    description_text = models.TextField(max_length=300, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="ModifiedUOM", on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="createUOM", on_delete=models.CASCADE, null=True,
                                   blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name',)

    def save(self, *args, **kwargs):
        self.name = self.name
        if UOM.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")

            # Save the object after performing necessary operations
        history_list = {
            "name": "Name",
            "e_way_bill_uom": "E Way Bill Uom",
            "description_text": "Description"
        }
        if self.pk is not None:

            instance = SaveToHistory(self, "Update", UOM, history_list)
            super(UOM, self).save(*args, **kwargs)
        elif self.pk is None:
            super(UOM, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", UOM, history_list)
        return instance

    def delete(self, *args, **kwargs):
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(unique=True, max_length=255)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name

        # Check if a record with the same normalized name already exists
        if Category.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")

        # Save the object after performing necessary operations
        super(Category, self).save(*args, **kwargs)

        return self


class AccountsgroupType(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AccountsGroup(models.Model):
    accounts_group_name = models.CharField(unique=True, max_length=50)
    accounts_type = models.ForeignKey(AccountsgroupType, on_delete=models.PROTECT, null=True, blank=True)
    group_active = models.BooleanField(default=True)
    modified_by = models.ForeignKey(User, related_name="modified_AccountsGroups", on_delete=models.PROTECT, null=True,
                                    blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_AccountsGroups", on_delete=models.PROTECT, null=True,blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.accounts_group_name

    def save(self, *args, **kwargs):
        self.accounts_group_name = self.accounts_group_name

        # Check if a record with the same normalized name already exists
        if AccountsGroup.objects.exclude(pk=self.pk).filter(
                accounts_group_name__iexact=self.accounts_group_name).exists():
            raise ValidationError("Accounts_Group_Name must be unique.")
        history_list = {
            "accounts_group_name": "Group Name",
            "accounts_type": "Account Type",
            "group_active": "Group Active"
        }
        # Save the object after performing necessary operations
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", AccountsGroup, history_list)
            super(AccountsGroup, self).save(*args, **kwargs)
        elif self.pk is None:
            super(AccountsGroup, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", AccountsGroup, history_list)
        return instance

    def delete(self, *args, **kwargs):
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class TaxType(models.TextChoices):
    GST = 'gst', 'Gst'
    TDS = 'tds', 'Tds'
    TCS = 'tcs', 'Tcs'
    OTHERS = "others", "Others"

class GstTypeOptions(models.TextChoices):
    IGST = 'igst', 'Igst'
    CGST = 'cgst', 'Cgst'
    SGST = 'sgst', 'Sgst'
    CESS = "cess", "Cess"

class AccountsMaster(models.Model):
    accounts_name = models.CharField(unique=True, max_length=50, )
    accounts_group_name = models.ForeignKey(AccountsGroup, null=True, blank=True, on_delete=models.PROTECT)
    account_type = models.CharField(choices=Accounts_Type, max_length=20, null=True, blank=True)
    accounts_active = models.BooleanField(default=True)
    gst_applicable = models.BooleanField(default=False)
    allow_payment = models.BooleanField(default=False)
    allow_receipt = models.BooleanField(default=False)
    enforce_position_balance = models.BooleanField(default=False)
    # "Tax Data"
    tds_link = models.ForeignKey("itemmaster.TDSMaster", on_delete=models.PROTECT, null=True, blank=True)
    tcs_link = models.ForeignKey("itemmaster.TCSMaster", on_delete=models.PROTECT, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax_type = models.CharField(max_length=20, choices=TaxType.choices, null=True, blank=True)
    other_rate_tax = models.IntegerField(null=True, blank=True)
    gst_type = models.CharField(max_length=20, choices=GstTypeOptions.choices, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="AMcreate", on_delete=models.PROTECT, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="Amcreate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    set_pos_report = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.accounts_name

    def save(self, *args, **kwargs):
        self.accounts_name = self.accounts_name

        # Check if a record with the same normalized name already exists
        if AccountsMaster.objects.exclude(pk=self.pk).filter(accounts_name__iexact=self.accounts_name).exists():
            raise ValidationError("Accounts Name must be unique.")
        # Save the object after performing necessary operations
        history_list = {
            "accounts_name": "Accounts Name",
            "accounts_group_name": "Account Group Name",
            "account_type": "Account Type",
            "accounts_active": "Account Active",
            "gst_applicable": "Gst Applicable",
            "tds": "TDS",
            "allow_payment": "Allow Payments",
            "allow_receipt": "Allow Receipt",
            "enforce_position_balance": "Enforce Position Balance",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", AccountsMaster, history_list)
            super(AccountsMaster, self).save(*args, **kwargs)
        elif self.pk is None:
            super(AccountsMaster, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", AccountsMaster, history_list)
        return instance

    def delete(self, *args, **kwargs):
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        
        if self.tds_link:
            self.tds_link.delete()
        if self.tcs_link:
            self.tcs_link.delete()

        super().delete(*args, **kwargs)


class GSTNatureTransaction(models.Model):
    TRANSACTION_CHOICES = [
        ('Sales', 'Sales'),
        ('Purchase', 'Purchase'),
    ]
    
    PLACE_OF_SUPPLY = [
        ('Interstate', 'Interstate'),
        ('Intrastate', 'Intrastate'),
    ]

    nature_of_transaction = models.CharField(max_length=255)
    applies_to = models.CharField(max_length=20, choices=TRANSACTION_CHOICES)
    # Multiple GSTIN types selection
    gstin_types = models.ManyToManyField("GstType", related_name='transactions')
    gst_nature_type = models.CharField(max_length=20, choices=NATURE_TYPE_CHOICES)

    # only shown if gst_nature_type == 'Specify'
    specify_type = models.CharField(max_length=20,
                            choices=TaxabilityType.choices, null=True, blank=True)

    # if specify_type == "Taxable"
    place_of_supply = models.CharField(max_length=20, choices=PLACE_OF_SUPPLY,null=True,
                                    blank=True)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="GNT_modified", on_delete=models.PROTECT, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="GNT_create", on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.nature_of_transaction
    
    def save(self, *args, **kwargs):
        history_list = {
            "nature_of_transaction":"Nature Of Transaction",
            "applies_to":"Applies To",
            "gst_nature_type":"Gst Nature Type",
            "specify_type":"Specify Type",
            "place_of_supply":"Place Of Supply",
            "igst_rate":"IGST RATE",
            "cgst_rate":"CGST RATE",
            "sgst_rate":"SGST RATE",
            "cess_rate":"CESS RATE"
        }
        try:
            if self.pk is not None:
                instance = SaveToHistory(self, "Update", GSTNatureTransaction, history_list)
                super(GSTNatureTransaction, self).save(*args, **kwargs)
            elif self.pk is None:
                super(GSTNatureTransaction, self).save(*args, **kwargs)
                instance = SaveToHistory(self, "Add", GSTNatureTransaction, history_list)
        except Exception as e:
            print(e, "---")

        return instance

class AccountsGeneralLedger(models.Model):
    date = models.DateField()
    voucher_type = models.CharField(max_length=50)
    payment_voucher_no = models.ForeignKey("userManagement.PaymentVoucher", on_delete=models.PROTECT, null=True, blank=True)
    sales_dc_voucher_no = models.ForeignKey("itemmaster2.SalesOrder_2_DeliveryChallan", on_delete=models.PROTECT, null=True, blank=True)
    sales_invoice_voucher_no = models.ForeignKey("itemmaster2.SalesInvoice", on_delete=models.PROTECT, null=True, blank=True)
    direct_sales_voucher_no = models.ForeignKey("itemmaster2.DirectSalesInvoice", on_delete=models.PROTECT, null=True, blank=True)
    sales_return_voucher_no = models.ForeignKey("itemmaster2.SalesReturn", on_delete=models.PROTECT, null=True, blank=True)
    receipt_voucher_voucher_no = models.ForeignKey("itemmaster2.ReceiptVoucher", on_delete=models.PROTECT, null=True, blank=True)
    credit_note_voucher_no = models.ForeignKey("itemmaster2.CreditNote", on_delete=models.PROTECT, null=True, blank=True)
    goods_receipt_note_no = models.ForeignKey("GoodsReceiptNote", on_delete=models.PROTECT, null=True, blank=True)
    purchase_invoice = models.ForeignKey("PurchaseInvoice", on_delete=models.PROTECT, null=True, blank=True)
    direct_purchase_invoice = models.ForeignKey("DirectPurchaseinvoice", on_delete=models.PROTECT, null=True, blank=True)
    purchase_return_challan = models.ForeignKey("PurchaseReturnChallan", on_delete=models.PROTECT, null=True, blank=True)
    debit_note = models.ForeignKey("DebitNote", on_delete=models.PROTECT, null=True, blank=True)
    account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    credit = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    purchase_account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT, related_name="gl_purchase_account", null=True, blank=True)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    customer_supplier = models.ForeignKey('itemmaster.SupplierFormData',  on_delete=models.PROTECT, null=True, blank=True)
    employee = models.ForeignKey("userManagement.Employee", on_delete=models.PROTECT, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="AccountsGeneralLedger_created", on_delete=models.PROTECT)

    def __str__(self):
        return f"GL Entry {self.id} - {self.voucher_type} on {self.date}"
    
    class Meta:
        ordering = [  '-id']
        verbose_name = "General Ledger Entry"
        verbose_name_plural = "General Ledger Entries"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.debit and self.credit:
            raise ValidationError("Only one of debit or credit should be filled.")
        if not self.debit and not self.credit:
            raise ValidationError("Either debit or credit must be filled.")

class Alternate_unit(models.Model):
    addtional_unit = models.ForeignKey(UOM, on_delete=models.CASCADE)
    conversion_factor = models.DecimalField(max_digits=12, decimal_places=8)
    fixed = models.BooleanField(default=False) 
    modified_by = models.ForeignKey(User, related_name="Aumodified", on_delete=models.SET_NULL,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="Aucreate", on_delete=models.PROTECT,
                                   null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.addtional_unit)


class Store(models.Model):
    store_name = models.CharField(max_length=100)
    store_account = models.ForeignKey(AccountsMaster, null=True, blank=True, on_delete=models.PROTECT)
    store_incharge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    matained = models.BooleanField(default=True)
    action = models.BooleanField(default=True)
    conference = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="Store_modified", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Store_create", on_delete=models.CASCADE, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name + "   " + str(self.id)

    def save(self, *args, **kwargs):
        self.store_name = self.store_name

        # Check if a record with the same normalized name already exists
        if Store.objects.exclude(pk=self.pk).filter(store_name__iexact=self.store_name).exists():
            raise ValidationError("Name must be unique.")
        history_list = {
            "store_name": "Store Name",
            "store_account": "Store Account",
            "store_incharge": "Store Incharge",
            "matained": "Maintained",
            "action": "Action",
            "conference": "Conference",
        }
        # Save the object after performing necessary operations
        try:
            if self.pk is not None:
                instance = SaveToHistory(self, "Update", Store, history_list)
                super(Store, self).save(*args, **kwargs)
            elif self.pk is None:
                super(Store, self).save(*args, **kwargs)
                instance = SaveToHistory(self, "Add", Store, history_list)
        except Exception as e:
            print(e, "---")

        return instance

    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here

        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)


class display_group(models.Model):
    display = models.CharField(max_length=100)
    part_number = models.ForeignKey('ItemMaster', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.display


class Item_Combo(models.Model):
    s_no = models.IntegerField(null=True, blank=True)
    part_number = models.ForeignKey('ItemMaster', on_delete=models.CASCADE)
    item_qty = models.DecimalField(max_digits=10, decimal_places=3)
    item_display = models.ForeignKey(display_group, on_delete=models.CASCADE, null=True, blank=True)
    is_mandatory = models.BooleanField(default=True)
    modified_by = models.ForeignKey(User, related_name="icmodified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="iccreate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{str(self.part_number)}-{str(self.id)}"


class CustomerGroups(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent_group = models.CharField(max_length=50, null=True, blank=True)
    Active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    Saved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        self.name = self.name

        # Check if a record with the same normalized name already exists
        if CustomerGroups.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")

        # Save the object after performing necessary operations
        super(CustomerGroups, self).save(*args, **kwargs)

        return self


class SupplierGroups(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent_group = models.CharField(max_length=50, null=True, blank=True)
    Active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    Saved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.name) + str(self.id)

    def save(self, *args, **kwargs):
        self.name = self.name
        # Check if a record with the same normalized name already exists
        if SupplierGroups.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")

        # Save the object after performing necessary operations
        super(SupplierGroups, self).save(*args, **kwargs)

        return self


class Contact_type(models.Model):
    name = models.CharField(max_length=20)
    modified_by = models.ForeignKey(User, related_name="Contact_type_modified", on_delete=models.CASCADE, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Contact_type_create", on_delete=models.CASCADE, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


class UniquePhoneNumberError(Exception):
    pass


class ContactDetalis(models.Model):
    index = models.IntegerField(null=True, blank=True)
    contact_person_name = models.CharField(max_length=100)
    salutation = models.CharField(choices=salutation, max_length=10, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20,null=True, blank=True)
    default = models.BooleanField(default=False)
    whatsapp_no = models.CharField(null=True, blank=True, max_length=20)
    other_no = models.CharField(null=True, blank=True)
    contact_type = models.ForeignKey(Contact_type, on_delete=models.PROTECT, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="ContactDetalis_modified", on_delete=models.CASCADE, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ContactDetalis_create", on_delete=models.CASCADE, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    """we use this for table view"""

    # supplier = models.ForeignKey("itemmaster.SupplierFormData",null=True, blank=True, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if ContactDetalis.objects.exclude(pk=self.pk).filter(phone_number__iexact=self.phone_number).exists():
            raise ValidationError("Mobile Number Already Exists in Contact.")
        super(ContactDetalis, self).save(*args, **kwargs)

    def __str__(self):
        return self.contact_person_name + "  " + str(self.id)


class CompanyAddress(models.Model):
    address_type = models.CharField(choices=address_types, max_length=30, null=True, blank=True)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100 ,null=True, blank=True)
    pincode = models.IntegerField( null=True, blank=True)
    state = models.CharField(max_length=100 , null=True, blank=True)
    country = models.CharField(max_length=100)
    default = models.BooleanField(default=False)

    def __str__(self):
        return str(self.address_type) + str(self.address_line_1)


class GstType(models.Model):
    gst_type = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.gst_type


class SupplierFormData(models.Model):
    supplier_no = models.CharField(max_length=15, null=True, blank=True, editable=False)
    company_name = models.CharField(max_length=100, unique=True)
    legal_name = models.CharField(max_length=100)
    customer = models.BooleanField()
    supplier = models.BooleanField()
    transporter = models.BooleanField()
    transporter_id = models.CharField(max_length=100, null=True, blank=True)
    gstin_type = models.ForeignKey(GstType, on_delete=models.PROTECT, null=True, blank=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    tcs = models.CharField(choices=tcs, max_length=10, null=True, blank=True)
    tds = models.BooleanField(default=False)
    pan_no = models.CharField(max_length=100, null=True, blank=True)
    currency = models.ForeignKey("CurrencyExchange", on_delete=models.PROTECT, null=True,
                                blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contact = models.ManyToManyField(ContactDetalis)
    address = models.ManyToManyField(CompanyAddress)
    active = models.BooleanField(default=True)
    """customer"""
    customer_group = models.ForeignKey(CustomerGroups, on_delete=models.SET_NULL, null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="salesPerson", null=True, blank=True)
    customer_credited_period = models.IntegerField(null=True, blank=True)
    credited_limit = models.IntegerField(null=True, blank=True)
    """Supplier"""
    supplier_group = models.ForeignKey(SupplierGroups, on_delete=models.CASCADE, null=True, blank=True)
    supplier_credited_period = models.IntegerField(null=True, blank=True)
    """city and state for table view"""
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    is_lead = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="Supplier_modified", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Supplier_create", on_delete=models.CASCADE, null=True,
                                   blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # class Meta:
        # constraints = [
        #     models.UniqueConstraint(
        #         name='unique_pan_no',
        #         fields=['pan_no'],
        #         condition=Q(pan_no__isnull=False)
        #     )
        # ]

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # ID Mandatory - for customers - STC00001 - for suppliers - STS00001
        starting_id = "00001"
        customer_prefix = "STC"
        suppliers_prefix = "STS"

        if self.pk is None:
            if self.customer:
                filter_conditions = "Customer_id"
                current_prefix = customer_prefix
            elif self.supplier:
                filter_conditions = "Supplier_id"
                current_prefix = suppliers_prefix

            last_serial_id_record = ManualIdSeries.objects.filter(
                name__iexact=filter_conditions).first() if filter_conditions else None
            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.supplier_no = f'{current_prefix}{new_serial_id:05}'
            # Save or update the ManualIdSeries record
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name=filter_conditions, id_series=new_serial_id,
                                              created_by=self.created_by)
        history_list = {
            "supplier_no": "Company ID",
            "active": "Active",
            "company_name": "Company Name",
            "legal_name": "Legal Name",
            "gstin_type": "GSTIN Type",
            "gstin": "GSTIN",
            "tcs": "TCS",
            "PAN No": "pan_no",
            "customer_group": "Customer Group",
            "sales_person": "Sales Person",
            "customer_credited_period": "Credit period",
            "credited_limit": "Credit Limit",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", SupplierFormData, history_list)
            super(SupplierFormData, self).save(*args, **kwargs)
        elif self.pk is None:
            super(SupplierFormData, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", SupplierFormData, history_list)
        # super(SupplierFormData, self).save(*args, **kwargs)
        return instance


class SupplierFormGstEffectiveDate(models.Model):
    supplier_form_data_id = models.ForeignKey(SupplierFormData, on_delete=models.CASCADE)
    gstin_type = models.ForeignKey(GstType, on_delete=models.PROTECT)
    gstin = models.CharField(max_length=15)
    effective_date = models.DateField()
    created_by = models.ForeignKey(User, related_name="created_SupplierFormGstEffectiveDate",
                                   on_delete=models.PROTECT,
                                   null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_SupplierFormGstEffectiveDate",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True,
                                      blank=True)

class ItemType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name)

class Item_Indicator(models.Model):
    name = models.CharField(max_length=20)

class TDSMaster(models.Model):
    name = models.CharField(max_length=100, verbose_name="TDS Name")
    section = models.CharField(max_length=50, null=True, blank=True)
    payment_code = models.CharField(max_length=50, null=True, blank=True)
    remittance_code = models.CharField(max_length=50, null=True, blank=True)

    # Percentages
    percent_individual_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Percentage for Individual/HUF with PAN"
    )
    percent_other_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Percentage for Other with PAN"
    )

    # Boolean flag
    zero_rated = models.BooleanField(default=False, verbose_name="Zero Rated")

    # Currency limits
    exemption_limit = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Exemption Limit", null=True, blank=True
    )
    single_transaction_limit = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Single Transaction Limit", null=True, blank=True
    )

    # Date
    effective_date = models.DateField(verbose_name="Effective Date")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TCSMaster(models.Model):
    name = models.CharField(max_length=100, verbose_name="TCS Name")
    section = models.CharField(max_length=50, null=True, blank=True)
    payment_code = models.CharField(max_length=50, null=True, blank=True)
    remittance_code = models.CharField(max_length=50, null=True, blank=True)

    # Percentage for Individual/HUF
    percent_individual_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Individual/HUF with PAN",
    )
    
    # Percentage for Other
    percent_other_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Other with PAN"
    )
    percent_other_without_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Other without PAN"
    )

    # Boolean Flags
    zero_rated = models.BooleanField(default=False, verbose_name="Zero Rated")
    tax_based_on_realization = models.BooleanField(default=False, verbose_name="Tax calculation based on realization")

    # Currency Limits
    exemption_limit = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Exemption Limit",
        null=True, blank=True
    )
    single_transaction_limit = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Single Transaction Limit",
        null=True, blank=True
    )

    # Effective Date
    effective_date = models.DateField(verbose_name="Effective Date")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TdsTcsEffectiveDate(models.Model):
    tds = models.ForeignKey(TDSMaster, on_delete=models.CASCADE, null=True, blank=True)
    tcs = models.ForeignKey(TCSMaster, on_delete=models.CASCADE, null=True, blank=True)
    # Percentage for Individual/HUF
    percent_individual_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Individual/HUF with PAN",
    )
    # Percentage for Other
    percent_other_with_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Other with PAN"
    )
    percent_other_without_pan = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentage for Other without PAN",
        null=True, blank=True
    )
    effective_date = models.DateField(verbose_name="Effective Date", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                    null=True, blank=True)

class ItemMaster(models.Model):
    item_part_code = models.CharField(unique=True, max_length=250, db_index=True)
    item_name = models.CharField(unique=True, max_length=250, db_index=True)
    description = models.TextField(max_length=300, null=True, blank=True)
    item_types = models.ForeignKey(ItemType, on_delete=models.PROTECT, null=True, blank=True)
    item_uom = models.ForeignKey(UOM, related_name="unit", on_delete=models.PROTECT, null=True, blank=True)
    product_image = models.ForeignKey(Imagedata, on_delete=models.SET_NULL, null=True, blank=True)
    product_document = models.ManyToManyField(Document, blank=True)
    item_group = models.ForeignKey(Item_Groups_Name, null=True, related_name="group", blank=True,
                            on_delete=models.PROTECT)
    alternate_uom = models.ManyToManyField(Alternate_unit, blank=True)
    alternate_uom_fixed = models.BooleanField(default=False)
    item_indicators = models.ForeignKey(Item_Indicator, on_delete=models.PROTECT, null=True, blank=True)
    category = models.ForeignKey(Category, related_name="Category", on_delete=models.CASCADE, null=True, blank=True)
    supplier_data = models.ManyToManyField(SupplierFormData, blank=True)
    '''Purchase'''
    purchase_uom = models.ForeignKey(UOM, related_name="uom", on_delete=models.PROTECT, null=True, blank=True)
    item_cost = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_safe_stock = models.IntegerField(null=True, blank=True)
    item_order_qty = models.IntegerField(null=True, blank=True)
    item_lead_time = models.IntegerField(null=True, blank=True)
    total_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    rejected_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    '''sell'''
    item_mrp = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_min_price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_sales_account = models.ForeignKey(AccountsMaster, related_name="Accounts_Master_Sales_Account",
                                        on_delete=models.PROTECT, null=True, blank=True)
    item_purchase_account = models.ForeignKey(AccountsMaster, related_name="Accounts_Master_Purchase_Account",
                                            on_delete=models.PROTECT, null=True, blank=True)
    item_hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    hsn_changed_date = models.DateTimeField(null=True, blank=True)
    keep_stock = models.BooleanField(default=0)
    sell_on_mrp = models.BooleanField(default=False)
    '''serial number'''
    serial = models.BooleanField(default=0)
    serial_auto_gentrate = models.BooleanField(default=False)
    serial_format = models.CharField(max_length=30, null=True, blank=True)
    serial_starting = models.IntegerField(null=True, blank=True)
    '''batch number'''
    batch_number = models.BooleanField(default=False)
    '''Service'''
    service = models.BooleanField(default=False)
    item_warranty_based = models.CharField(choices=Item_Warranty_base_on, null=True, blank=True, max_length=20)
    item_installation = models.BooleanField(default=False)
    invoice_date = models.DateField(null=True, blank=True)
    installation_data = models.DateField(null=True, blank=True)
    item_combo_bool = models.BooleanField(default=False)
    item_combo_data = models.ManyToManyField(Item_Combo, blank=True)
    item_combo_print = models.BooleanField(default=False)
    item_barcode = models.BooleanField(default=False)
    item_active = models.BooleanField(default=True)
    item_qc = models.BooleanField(default=False)
    location = models.CharField(max_length=20, null=True, blank=True)
    notes = models.CharField(max_length=300, null=True, blank=True)
    variation = models.CharField(max_length=50, null=True, blank=True)
    enable_variation = models.BooleanField(default=False)
    is_manufacture = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    stock_ids = models.ManyToManyField("ItemStock", blank=True)
    "Tax Data"
    tds_link = models.ForeignKey(TDSMaster, on_delete=models.PROTECT, null=True, blank=True)
    tcs_link = models.ForeignKey(TCSMaster, on_delete=models.PROTECT, null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="createItemmaster", on_delete=models.CASCADE, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.item_part_code = self.item_part_code
        # Check if a record with the same normalized name already exists
        if ItemMaster.objects.exclude(pk=self.pk).filter(item_part_code__iexact=self.item_part_code).exists():
            raise ValidationError("PartCode must be unique.")
        self.Item_name = self.item_name.title()
        # Check if a record with the same normalized name already exists
        if ItemMaster.objects.exclude(pk=self.pk).filter(item_name__iexact=self.item_name).exists():
            raise ValidationError("Item Name must be unique.")
        # Save the object after performing necessary operations
        history_list = {
            "item_active": "Active",
            "item_part_code": "part code",
            "item_name": "Part Name",
            "description": "Description",
            "item_types": "Product/Service",
            "category": "Category",
            "item_uom": "UOM",
            "item_hsn": "Hsn",
            "keep_stock": "Keep Stock",
            "item_mrp": "Max Selling Price",
            "item_sales_account": "Item Sales Account",
            "item_cost": "Item Cost",
            "purchase_uom": "Purchase UOM",
            "item_purchase_account": "Item Purchase Account",
            "serial": "Serial Number",
            "batch_number": "Batch Number",
            "item_barcode": "Barcode",
            "service": "Serviceable",
            "item_combo_bool": "Item Combo",
            "is_manufacture": "Manufacture",
            "item_qc": "item_qc"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ItemMaster, history_list)
            super(ItemMaster, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ItemMaster, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ItemMaster, history_list)

        return instance

    def __str__(self):
        return f"{self.item_part_code}-{self.item_name}"

    def delete(self, *args, **kwargs):
        # Delete related history details if any
        if self.history_details.exists():
            self.history_details.all().delete()

        # Delete product image if exists
        if self.product_image:
            self.product_image.delete( )

        # Delete product document if exists
        if self.product_document:
            self.product_document.all().delete( )

        # Delete combo items if exists
        if self.item_combo_data.exists():
            self.item_combo_data.all().delete()

        # Delete alternate UOMs
        if self.alternate_uom.exists():
            self.alternate_uom.all().delete()

        # Delete TDS/TCS links if present
        if self.tds_link:
            self.tds_link.delete()

        if self.tcs_link:
            self.tcs_link.delete()

        # Finally, delete the instance
        super().delete(*args, **kwargs)

class CommanHsnEffectiveDate(models.Model):
    table_name = models.CharField(max_length=50)
    hsn_id = models.ForeignKey(Hsn, on_delete=models.PROTECT)
    effective_date = models.DateField()
    created_by = models.ForeignKey(User, related_name="created_CommanHsnEffectiveDate", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

class SerialNumbers(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BatchNumber(models.Model):
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    batch_number_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class StockSerialHistory(models.Model):
    part_no = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    last_serial_history = models.CharField(max_length=50, null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

class ItemStock(models.Model):
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT)
    serial_number = models.ManyToManyField(SerialNumbers, blank=True)
    batch_number = models.ForeignKey(BatchNumber, null=True, blank=True, on_delete=models.SET_NULL)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    conference = models.IntegerField(null=True, blank=True)
    rate = models.DecimalField(max_digits=12, decimal_places=3,null=True, blank=True )
    """only for serialnum to track last serial number"""
    last_serial_history = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{str(self.part_number.item_part_code)}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            # The instance already exists in the database, meaning it's an update
            original_instance = ItemStock.objects.get(pk=self.pk)
            # Compare each field and create a StockHistoryLog for each modified field
            for field in self._meta.fields:
                field_name = field.name
                original_value = getattr(original_instance, field_name)
                new_value = getattr(self, field_name)
                if original_value != new_value:
                    StockHistoryLog.objects.create(
                        action='Update',
                        stock_link=self,
                        part_number=self.part_number,
                        store_link=self.store,
                        column_name=field_name,
                        previous_state=str(original_value),
                        updated_state=str(new_value),
                        modified_date=timezone.now(),
                        saved_by=kwargs.get('user'),
                    )

            # Save the ItemStock instance before dealing with many-to-many relationships
            super().save(*args, **kwargs)

            # Now that the ItemStock instance is saved, create/update many-to-many relationships
            self.serial_number.set(self.serial_number.all())  # Adjust this based on your many-to-many relationships
        else:
            # The instance is new, meaning it's a new row
            super().save(*args, **kwargs)
            if self.current_stock:
                StockHistoryLog.objects.create(
                    action='Add',
                    stock_link=self,
                    part_number=self.part_number,
                    store_link=self.store,
                    column_name="current_stock",
                    previous_state=0,
                    updated_state=str(self.current_stock),
                    modified_date=timezone.now(),
                    saved_by=kwargs.get('user')
                )

class StockHistoryLog(models.Model):
    action = models.CharField(choices=Action, max_length=10)
    stock_link = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    store_link = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True, blank=True)
    column_name = models.CharField(max_length=250)
    previous_state = models.CharField(max_length=250)
    updated_state = models.CharField(max_length=250)
    modified_date = models.DateTimeField(max_length=250)
    saved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class ItemInventoryApproval(models.Model):
    """Stock statement"""
    is_stock_added= models.BooleanField(default=False)
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    qty = models.IntegerField()
    rate = models.DecimalField(max_digits=12, decimal_places=3,null=True, blank=True )
    amount = models.DecimalField(max_digits=12, decimal_places=3,null=True, blank=True )
    serial_number =  models.TextField(null=True, blank=True)
    deletion_serial_number = models.ManyToManyField(SerialNumbers, blank=True)
    batch_number = models.ForeignKey(BatchNumber, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        if (self.batch_number != None):
            return str(self.part_number.item_part_code) + "  qty : " + str(self.qty) + "  batch_number:  " + str(
                self.batch_number) + "  serial_number: " + str(self.serial_number)+" "+ str(self.id)
        else:
            return str(self.part_number.item_part_code) + "  qty : " + str(self.qty) + "  batch_number:  " + str(
                self.batch_number) + "  serial_number: " + str(self.serial_number)+" "+ str(self.id)

class InventoryHandler(models.Model):
    status = models.ForeignKey("itemmaster.CommanStatus", on_delete=models.PROTECT, null=True, blank=True)
    inventory_handler_id = models.CharField(max_length=20, unique=True, editable=False)
    inventory_id = models.ManyToManyField(ItemInventoryApproval)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    saved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_handler", null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="modified_handler", null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    actions = models.CharField(choices=Action, max_length=10)
    conference = models.ForeignKey("EnquriFromapi.conferencedata", null=True, blank=True, on_delete=models.PROTECT,
                                swappable=True)

    def __str__(self):
        return self.inventory_handler_id

    def save(self, *args, **kwargs):
        if not self.inventory_handler_id:
            if self.actions == 'Add':
                iaa_instances = InventoryHandler.objects.filter(inventory_handler_id__startswith='IAA').order_by(
                    '-inventory_handler_id').first()
                last_number = int(iaa_instances.inventory_handler_id.split('-')[1]) if iaa_instances else 0
                new_number = last_number + 1
                self.inventory_handler_id = f'IAA-{new_number:03d}'

            elif self.actions == 'Delete':
                iad_instances = InventoryHandler.objects.filter(inventory_handler_id__startswith='IAD').order_by(
                    '-inventory_handler_id').first()
                last_number = int(iad_instances.inventory_handler_id.split('-')[1]) if iad_instances else 0
                new_number = last_number + 1
                self.inventory_handler_id = f'IAD-{new_number:03d}'

        # Call super().save outside the if conditions
        super().save(*args, **kwargs)



class CurrencyMaster(models.Model):
    name = models.CharField(max_length=50, unique=True)
    currency_symbol = models.CharField(max_length=5)
    active = models.BooleanField(default=True)
    modified_by = models.ForeignKey(User, related_name="modified_CurrencyMaster", on_delete=models.PROTECT, null=True,
                                    blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_CurrencyMaster", on_delete=models.PROTECT, null=True,
                                   blank=True)
    is_Delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name
        if CurrencyMaster.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        history_list = {
            "name": "Name",
            "currency_symbol": "Symbol",
            "formate": "Format",
            "active": "Active"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", CurrencyMaster, history_list)
            super(CurrencyMaster, self).save(*args, **kwargs)
        elif self.pk is None:
            super(CurrencyMaster, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", CurrencyMaster, history_list)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class CurrencyExchange(models.Model):
    Currency = models.ForeignKey(CurrencyMaster, on_delete=models.PROTECT, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_CurrencyExchange", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_CurrencyExchange", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.Currency.name

    def save(self, *args, **kwargs):
        # super(CurrencyExchange, self).save(*args, **kwargs)
        history_list = {
            "Currency": "Currency",
            "rate": "Rate",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", CurrencyExchange, history_list)
            super(CurrencyExchange, self).save(*args, **kwargs)
        elif self.pk is None:
            super(CurrencyExchange, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", CurrencyExchange, history_list)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

# This SalesOrderItemCombo Consider as POSItemCombo
class SalesOrderItemCombo(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    batch = models.ForeignKey(BatchNumber, null=True, blank=True, on_delete=models.SET_NULL)
    stock_reduce = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    Status = models.CharField(choices=PosStatus, max_length=10, null=True, blank=True)
    gst_rate = models.IntegerField(null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, )
    amount = models.DecimalField(max_digits=10, decimal_places=2, )
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_salesorderitemcombos', on_delete=models.SET_NULL,
                                   null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name='modified_salesorderitemcombos', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    display = models.CharField(null=True, blank=True, max_length=250)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "itemmaster_salesorderitemcombo"

# This SalesOrderItem Consider as POSItem
class SalesOrderItem(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    batch = models.ForeignKey(BatchNumber, null=True, blank=True, on_delete=models.SET_NULL)
    stock_reduce = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    Status = models.CharField(choices=PosStatus, max_length=10, null=True, blank=True)
    gst_rate = models.IntegerField(null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, )
    amount = models.DecimalField(max_digits=10, decimal_places=2, )
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    item_combo = models.ManyToManyField(SalesOrderItemCombo, blank=True)
    pos_item_combo_bool = models.BooleanField(default=False)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_SalesOrderItem", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_SalesOrderItem", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class paymentMode(models.Model):
    payby = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    pay_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedpPAy", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="createPay", on_delete=models.PROTECT, null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

class posOtherIncomeCharges(models.Model):
    other_income_charges_id = models.ForeignKey('itemmaster2.OtherIncomeCharges', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.IntegerField(blank=True, null=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    after_discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="POSOtherIncomeCharges_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="POSOtherIncomeCharges_create", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# This SalesOrder Consider as POS
class SalesOrder(models.Model):
    IsPOS = models.BooleanField(default=True)
    posType = models.CharField(choices=Postypes_, max_length=50)
    marketingEvent = models.ForeignKey("EnquriFromapi.conferencedata", null=True, on_delete=models.PROTECT,
                                       swappable=True)
    OrderDate = models.DateField()
    status = models.CharField(choices=PosStatus, max_length=50, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True)
    POS_ID = models.ForeignKey(NumberingSeriesLinking, null=True, blank=True, on_delete=models.PROTECT)
    # Sample
    sample_contact_link = models.ForeignKey(ContactDetalis, null=True, on_delete=models.PROTECT,
                                            related_name="pos_sample_contact_link")
    Mobile = models.CharField(null=True, blank=True, max_length=20)
    WhatsappNumber = models.CharField(null=True, blank=True, max_length=20)
    CosName = models.CharField(max_length=100, null=True, blank=True)
    Email = models.EmailField(null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    State = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.ForeignKey(Pincode, on_delete=models.PROTECT, null=True, blank=True)
    Remarks = models.CharField(max_length=200, null=True, blank=True)
    customerName = models.ForeignKey(SupplierFormData, null=True, blank=True, on_delete=models.PROTECT)
    BillingAddress = models.ForeignKey(CompanyAddress, related_name="BillingAddress", null=True, blank=True,
                                       on_delete=models.PROTECT)
    DeliverAddress = models.ForeignKey(CompanyAddress, related_name="DeliverAddress", null=True, blank=True,
                                       on_delete=models.PROTECT)
    contactPerson = models.ForeignKey(ContactDetalis, null=True, blank=True, on_delete=models.PROTECT,
                                      related_name="pos_contactPerson")
    """Billing Details"""
    Currency = models.ForeignKey(CurrencyMaster, null=True, blank=True, on_delete=models.PROTECT)
    """Item Details"""
    itemDetails = models.ManyToManyField(SalesOrderItem, blank=True)
    OverallDiscountPercentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    OverallDiscountPercentageValue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    OverallDiscountValue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    DiscountFinalTotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    all_stock_reduced = models.BooleanField(default=False)
    "Total amount"
    TotalAmount = models.DecimalField(max_digits=10, decimal_places=2)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    other_income_charge = models.ManyToManyField(posOtherIncomeCharges, blank=True)
    # AmountwithTax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receivedAmount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance_Amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    FinalTotalValue = models.DecimalField(max_digits=10, decimal_places=2)
    SalesPerson = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    isDelivered = models.BooleanField(default=True)
    Pending = models.BooleanField(default=False)
    payment = models.ManyToManyField(paymentMode, blank=True)
    Remarks = models.CharField(max_length=250, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="modifiedpos", on_delete=models.PROTECT, null=True, blank=True)
    createdby = models.ForeignKey(User, related_name="createpos", on_delete=models.PROTECT, null=True, blank=True)
    isDelete = models.BooleanField(default=False)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
 
    def save(self, *args, **kwargs):
        if not self.id:
            try:
                with transaction.atomic():
                    if self.posType in ['Sample', 'Sales']:
                        # Determine conditions based on posType
                        conditions = {'resource': 'Pos', 'pos_type__ReSourceIsPosType': self.posType, 'default': True}
                        getSerialNumber = NumberingSeries.objects.get(**conditions)
                        formate = getSerialNumber.formate
                        LastSerialHistory = getSerialNumber.last_serial_history
                        Current_Value = getSerialNumber.current_value
                        textFromate = str(formate).split("#")[0]
                        ZeroCount = str(formate).split("#")[-1]
                        if LastSerialHistory > 0:
                            posid = f"{textFromate}{int(LastSerialHistory):0{ZeroCount}d}"
                            instance = NumberingSeriesLinking.objects.create(
                                numbering_Seriel_link=getSerialNumber,
                                linked_model_id=posid
                            )
                            self.POS_ID = instance
                            getSerialNumber.last_serial_history = int(LastSerialHistory) + 1
                            getSerialNumber.current_value = int(LastSerialHistory) + 1
                        elif LastSerialHistory == 0:
                            posid = f"{textFromate}{Current_Value:0{ZeroCount}d}"
                            instance = NumberingSeriesLinking.objects.create(
                                numbering_Seriel_link=getSerialNumber,
                                linked_model_id=posid
                            )
                            self.POS_ID = instance
                            getSerialNumber.last_serial_history = int(Current_Value) + 1
                            getSerialNumber.current_value = int(LastSerialHistory) + 1
                        getSerialNumber.save()
            except NumberingSeries.DoesNotExist:
                raise ValidationError("No matching NumberingSeries found.")
            except Exception as e:
                raise ValidationError(e)

        history_list = {
            "POS_ID": "POS ID",
            "status": "Status",
            "OrderDate": "Date",
            "posType": "POS Type",
            "marketingEvent": "Event",
            "store": "Store",
            "customerName": "Customer Name",
            "Mobile": "Mobile",
            "pincode": "Pincode",
            "State": "State",
            "SalesPerson": "Sales Person",
            "TotalAmount": "Total Amount",
            "receivedAmount": "Received",
            "balance_Amount": "Balance",
            "Pending": "Pending",
            "isDelivered": "Delivered",
            "Remarks": "Remarks",
            "FinalTotalValue": "To Pay"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", SalesOrder, history_list)
            super(SalesOrder, self).save(*args, **kwargs)
        elif self.pk is None:
            super(SalesOrder, self).save(*args, **kwargs)
            # instance = SaveToHistory(self, "Add", SalesOrder,history_list)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.itemDetails.exists():
            self.itemDetails.all().delete()
        if self.other_income_charge.exists():
            self.other_income_charge.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        if self.payment.exists():
            self.payment.all().delete()
        super().delete(*args, **kwargs)
 
class BomCostVariation(models.Model):
    is_percentage = models.BooleanField(default=True)
    variation = models.CharField(max_length=50, null=True, blank=True)
    lead_time = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="BCVcreated", on_delete=models.PROTECT, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="BCVmodified", on_delete=models.PROTECT, null=True, blank=True)

class FinishedGoods(models.Model):
    serial_number = models.IntegerField()
    part_no = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    cost_allocation = models.IntegerField()
    labour_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="FGmodified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="FGcreate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RawMaterial(models.Model):
    serial_number = models.IntegerField()
    part_no = models.ForeignKey(ItemMaster, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    raw_qty = models.DecimalField(max_digits=10, decimal_places=3)
    category = models.CharField(max_length=50, null=True, blank=True)
    unit = models.ForeignKey(UOM, on_delete=models.SET_NULL, null=True, blank=True)
    fixed = models.BooleanField(null=True, blank=True, default=False)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="Rmmodified", on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="Rmcreate", on_delete=models.CASCADE, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    item_cost = models.DecimalField(null=True, blank=True, default=0, max_digits=50, decimal_places=3)

class Scrap(models.Model):
    serial_number = models.IntegerField()
    part_no = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    category = models.CharField(max_length=50, null=True, blank=True)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    cost_allocation = models.IntegerField()
    modified_by = models.ForeignKey(User, related_name="Smodified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="Screate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Routing(models.Model):
    serial_number = models.IntegerField(null=True, blank=True)
    route_name = models.CharField(max_length=50)
    modified_by = models.ForeignKey(User, related_name="routingmodified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="routingScreate", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkCenter(models.Model):
    work_center = models.CharField(max_length=500, null=True, blank=True)
    in_charge = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

class BomRouting(models.Model):
    serial_number = models.IntegerField(null=True, blank=True)
    route = models.ForeignKey(Routing, on_delete=models.PROTECT, null=True, blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, null=True, blank=True)
    duration = models.IntegerField(blank=True, null=True)

class BomStatus(models.Model):
    status = models.CharField(max_length=10)

class Bom(models.Model):
    bom_no = models.CharField(blank=True, max_length=50)
    bom_name = models.CharField(max_length=50, unique=True)
    bom_type = models.CharField(max_length=20, default="MANUFACTURE")
    fg_store = models.ForeignKey(Store, related_name="FgStore", on_delete=models.PROTECT, null=True, blank=True)
    scrap_store = models.ForeignKey(Store, related_name="ScrapRejectStore", on_delete=models.PROTECT, null=True,
                                    blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    action = models.BooleanField(default=True)
    default = models.BooleanField(default=True)
    total_raw_material = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(BomStatus, on_delete=models.PROTECT, null=True, blank=True)
    finished_goods = models.ForeignKey(FinishedGoods, on_delete=models.SET_NULL, null=True, blank=True)
    raw_material = models.ManyToManyField(RawMaterial, blank=True)
    scrap = models.ManyToManyField(Scrap, blank=True)
    routes = models.ManyToManyField(BomRouting, blank=True)
    labour_charges = models.JSONField(null=True, blank=True)
    machinery_charges = models.JSONField(null=True, blank=True)
    electricity_charges = models.JSONField(null=True, blank=True)
    other_charges = models.JSONField(null=True, blank=True)
    cost_variation = models.ForeignKey(BomCostVariation, null=True, blank=True, on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="Bom_modified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="Bom_create", on_delete=models.PROTECT, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    supplier = models.ManyToManyField(SupplierFormData, blank=True)
    is_active = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_default:
            with transaction.atomic():
                Bom.objects.filter(finished_goods=self.finished_goods, is_default=True).exclude(pk=self.pk).update(
                    is_default=False)
        if not self.pk:
            last_bom = Bom.objects.filter(bom_type=self.bom_type).order_by('-id').first()
            bom_no_prefix = 'BOMM' if self.bom_type == 'MANUFACTURE' else 'BOMS'
            bom_no_prefix = 'BOMM' if self.bom_type == 'MANUFACTURE' else 'BOMS'
            if last_bom:
                last_bom_no = last_bom.bom_no

                # Extract the numeric part from the last BOM number
                bom_no_numeric_part = int(last_bom_no.split('-')[-1])

                # Increment the numeric part for the new BOM number
                new_bom_no_numeric_part = bom_no_numeric_part + 1
                self.bom_no = f'{bom_no_prefix}-{new_bom_no_numeric_part:05d}'
            else:
                # If no BOM exists yet, start with 1
                self.bom_no = f'{bom_no_prefix}-00001'
        super().save(*args, **kwargs)

class RawMaterialBomLink(models.Model):
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    bom = models.ForeignKey(Bom, on_delete=models.PROTECT)

class StockHistory(models.Model):
    action = models.CharField(max_length=10)
    stock_link = models.ForeignKey(ItemStock, on_delete=models.CASCADE)
    store_link = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT, null=True, blank=True)
    previous_state = models.CharField(max_length=250)
    updated_state = models.CharField(max_length=250)
    added = models.CharField(max_length=250)
    reduced = models.CharField(max_length=250)
    modified_date = models.DateTimeField(auto_now_add=True)
    saved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_module = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.IntegerField(null=True, blank=True)
    display_id = models.CharField(max_length=250, null=True, blank=True)
    display_name = models.CharField(max_length=250, null=True, blank=True)
    item_cost = models.CharField(max_length=10, null=True, blank=True)
    conference = models.IntegerField(default=0)
    is_delete = models.BooleanField(default=False)
    isTransfered = models.BooleanField(default=False)

class Department(models.Model):
    No = models.CharField(unique=True, max_length=20, editable=False)
    name = models.CharField(unique=True, max_length=50)
    department_head_user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="Department_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Department_create", on_delete=models.PROTECT, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        starting_id = "001"
        dep_prefix = "D"
        self.name = self.name

        # Check if a record with the same normalized name already exists
        if Department.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        if self.pk is None:  # Create operation
            last_serial_id_record = ManualIdSeries.objects.filter(name__iexact="Department_no").first()

            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.No = f'{dep_prefix}{new_serial_id:03}'  # Format to ensure leading zeros
            # Save or update the ManualIdSeries record
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name="Department_no", id_series=new_serial_id, created_by=self.created_by)

        history_list = {
            "No": "No",
            "name": "Name",
            "department_head_user_id": "Department Head"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Department, history_list)
            super(Department, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Department, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Department, history_list)

        return instance

    def __str__(self):
        return str(self.name) + str(self.id)

class TermsConditions(models.Model):
    name = models.CharField(max_length=255, unique=True)
    tc = models.TextField()
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    modified_by = models.ForeignKey(User, related_name="TermsConditions_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="TermsConditions_create", on_delete=models.PROTECT, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    module = models.CharField(choices=TermsConditionsModels, max_length=50)

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        # Check if a record with the same normalized name already exists
        if TermsConditions.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        history_list = {
            "name": "name",
            "tc": "tc",
            "module": "module"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", TermsConditions, history_list)
            super(TermsConditions, self).save(*args, **kwargs)
        elif self.pk is None:
            super(TermsConditions, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", TermsConditions, history_list)

        return instance

    def __str__(self):
        return self.name  # Defines the string representation of the model instance

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class OtherExpenses(models.Model):
    name = models.CharField(max_length=20, unique=True)
    account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    HSN = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)

    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    comman_hsn_effective_date = models.ManyToManyField(CommanHsnEffectiveDate, blank=True)
    active = models.BooleanField(default=True)
    modified_by = models.ForeignKey(User, related_name="OtherExpenses_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="OtherExpenses_create", on_delete=models.PROTECT, null=True,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        # Check if a record with the same normalized name already exists
        if OtherExpenses.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError("Name must be unique.")
        history_list = {
            "name": "Name",
            "account": "Account",
            "HSN": "Hsn",
            "active": "Active"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", OtherExpenses, history_list)
            super(OtherExpenses, self).save(*args, **kwargs)
        elif self.pk is None:
            super(OtherExpenses, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", OtherExpenses, history_list)

        return instance

    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here

        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        if self.comman_hsn_effective_date.exists():
            self.comman_hsn_effective_date.all().delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name

class OtherExpensespurchaseOrder(models.Model):
    other_expenses_id = models.ForeignKey(OtherExpenses, on_delete=models.PROTECT)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True,blank=True, related_name='child_income_charges')
    modified_by = models.ForeignKey(User, related_name="OtherExpensespurchaseOrder_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="OtherExpensespurchaseOrder_create", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class purchaseOrderItemDetails(models.Model):
    item_master_id = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.TextField(max_length=250, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    hsn_id = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    uom = models.ForeignKey(UOM, related_name="base_uom",  on_delete=models.PROTECT)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    po_qty = models.DecimalField(max_digits=15, decimal_places=3)
    po_uom = models.ForeignKey(UOM,  related_name ="po_uom", on_delete=models.PROTECT, null=True, blank=True)
    po_rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    conversion_factor = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    fixed = models.BooleanField(default=False)
    tax = models.IntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    po_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    rework_received = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    rework_retun_qty = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    invoiced_qty = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    received = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    accepted_qty = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="purchaseOrderItem_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="purchaseOrderItem_create", on_delete=models.PROTECT, null=True,
                                blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class purchaseOrder(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT, null=True, blank=True)
    purchaseOrder_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True)
    po_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES, null=True, blank=True)
    supplier_id = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT)
    credit_period = models.IntegerField()
    payment_terms = models.CharField(max_length=50, null=True, blank=True)
    supplier_ref = models.CharField(max_length=50, null=True, blank=True)
    due_date = models.DateField()
    receiving_store_id = models.ForeignKey(Store, related_name="receiving_store_id", on_delete=models.PROTECT,
                                        null=True, blank=True)
    scrap_reject_store_id = models.ForeignKey(Store, related_name="scrap_reject_store_id", on_delete=models.PROTECT,
                                            null=True, blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    """Supplier details"""
    gstin_type = models.CharField(max_length=50, null=True, blank=True)
    gstin = models.CharField(max_length=15, null=True, blank=True)
    contact = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT)
    address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT)
    place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    """item details"""
    item_details = models.ManyToManyField(purchaseOrderItemDetails, blank=True)
    other_expenses = models.ManyToManyField(OtherExpensespurchaseOrder, blank=True)
    inward_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) 
    invoice_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) 
    """amount details"""
    igst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cess_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    round_off = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    active = models.BooleanField(default=False)
    parent_order = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='child_orders')
    child_count = models.IntegerField(null=True, blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    gin = models.ManyToManyField("GoodsInwardNote", blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    "Activities"
    note = models.ManyToManyField("itemmaster2.Notes", blank=True)
    email = models.EmailField(null=True, blank=True)
    email_record = models.ManyToManyField("itemmaster2.EmailRecord", blank=True)
    
    modified_by = models.ForeignKey(User, related_name="purchaseOrder_modified", on_delete=models.PROTECT, null=True,
                                blank=True)
    created_by = models.ForeignKey(User, related_name="purchaseOrder_create", on_delete=models.PROTECT, null=True,
                                blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id: 
            if not self.parent_order:
                conditions = {'resource': 'Purchase Order', 'default': True}
                response = create_serial_number(conditions)
                if response['success']:
                    self.purchaseOrder_no = response['instance']
                    self.active = True
                else:
                    raise ValidationError(response['errors'])
            else:
                old_numbering_series = self.parent_order.purchaseOrder_no.numbering_Seriel_link
                old_numbering_series_id = self.parent_order.purchaseOrder_no.linked_model_id
                if self.parent_order.child_count is None:
                    self.child_count = 1
                else:
                    self.child_count = self.parent_order.child_count + 1
                if (self.child_count or 0) > 1:
                    old_numbering_series_id = str(old_numbering_series_id).rsplit("-", 1)[0]
                self.active = True
                try:
                    instance = NumberingSeriesLinking.objects.create(
                        numbering_Seriel_link=old_numbering_series,
                        linked_model_id=f"{old_numbering_series_id}-{self.child_count}"
                    )
                    self.purchaseOrder_no = instance
                     
                except Exception as e:
                    raise ValidationError(f"unexpected error occurred :{e}")
                try:
                    # Fetch parent order and update its active status
                    parent_order = purchaseOrder.objects.get(id=self.parent_order.id)
                    parent_order.active = False
                    parent_order.save()
                    # grn_data = GoodsReceiptNote.objects.filter(purchase_order_id=parent_order.id)
                    # for goods_receipt_note in grn_data:
                    #     goods_receipt_note.purchase_order_id = self
                    #     goods_receipt_note.save()
                except purchaseOrder.DoesNotExist:
                    raise ValidationError(f"Parent order with ID {self.parent_order.id} does not exist")
                except Exception as e:
                    raise ValidationError(f"Error updating parent order: {e}")

        history_list = {
                "status": "Status",
                "purchaseOrder_no": "Purchase Order No",
                "po_date": "PO Date",
                "currency": "Currency",
                "gst_nature_transaction": "GST Nature Transaction",
                "gst_nature_type": "GST Nature Type",
                "supplier_id": "Supplier",
                "credit_period": "Credit Period",
                "payment_terms": "Payment Terms",
                "supplier_ref": "Supplier Reference",
                "due_date": "Due Date",
                "receiving_store_id": "Receiving Store",
                "scrap_reject_store_id": "Scrap/Reject Store",
                "remarks": "Remarks",
                "department": "Department",
                "gstin_type": "GSTIN Type",
                "gstin": "GSTIN",
                "contact": "Contact Person",
                "address": "Address",
                "place_of_supply": "Place of Supply",
                "overall_discount_percentage": "Overall Discount (%)",
                "overall_discount_value": "Overall Discount Value",
                "discount_final_total": "Discount Final Total",
                "tax_total": "Tax Total",
                "round_off": "Round Off",
                "net_amount": "Net Amount",
            }

        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(purchaseOrder, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, purchaseOrder, history_list)
        if action == "Update":
            super(purchaseOrder, self).save(*args, **kwargs)
        return instance
    
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_details.exists():
            self.item_details.all().delete()
        if self.other_expenses.exists():
            self.other_expenses.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        parent_order = self.parent_order
        super().delete(*args, **kwargs)
        if parent_order:
            parent_order.delete()

class GoodsInwardNoteItemDetails(models.Model):
    item_master = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    received = models.DecimalField(max_digits=10, decimal_places=3)
    qc = models.BooleanField(default=False)
    purchase_order_parent = models.ForeignKey(purchaseOrderItemDetails, on_delete=models.PROTECT, null=True, blank=True)
    reword_delivery_challan_item = models.ForeignKey("ReworkDeliveryChallanItemDetails", on_delete=models.PROTECT,
                                                    null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="GoodsInwardNoteItemDetails_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="GoodsInwardNoteItemDetails_create", on_delete=models.PROTECT,
                                null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GoodsInwardNote(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT, null=True, blank=True)
    gin_no = models.ForeignKey(NumberingSeriesLinking, related_name="gin", on_delete=models.PROTECT, null=True,
                                blank=True)
    gin_date = models.DateField(null=True)
    remark = models.TextField(null=True, blank=True)
    purchase_order_id = models.ForeignKey(purchaseOrder, on_delete=models.PROTECT, null=True,
                                        blank=True)
    quality_inspection_report_id = models.ForeignKey("QualityInspectionReport", on_delete=models.SET_NULL, null=True,
                                                    blank=True)
    rework_delivery_challan = models.ForeignKey("ReworkDeliveryChallan", on_delete=models.PROTECT, null=True,
                                        blank=True)
    goods_receipt_note_item_details_id = models.ManyToManyField(GoodsInwardNoteItemDetails)
    grn = models.ForeignKey("GoodsReceiptNote", on_delete=models.SET_NULL, null=True,
                                                    blank=True)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    modified_by = models.ForeignKey(User, related_name="Gin_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="Gin_create", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            conditions = {'resource': 'Goods Inward Note', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.gin_no = response['instance'] 
            else:
                raise ValidationError(f"Error creating serial number: {response['errors']}")
                
        history_list = {
            "status": "Status",
            "remark": "Remark",
            "gin_date": "Date",
        }
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(GoodsInwardNote, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, GoodsInwardNote, history_list)
        if action == "Update":
            super(GoodsInwardNote, self).save(*args, **kwargs)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.goods_receipt_note_item_details_id.exists():
            self.goods_receipt_note_item_details_id.all().delete() 
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class QualityInspectionsReportItemDetails(models.Model):
    goods_inward_note_item = models.ForeignKey(GoodsInwardNoteItemDetails, on_delete=models.PROTECT)
    accepted = models.DecimalField(max_digits=11, decimal_places=4)
    rejected = models.DecimalField(max_digits=11, decimal_places=4)
    rework = models.DecimalField(max_digits=11, decimal_places=4)
    checked_by = models.ForeignKey(User, related_name="checked_by", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="QualityInspectionsReportItemDetails_modified",
                                    on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="QualityInspectionsReportItemDetails_create",
                                on_delete=models.PROTECT, null=True, blank=True)
    reject_stock_is_added = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QualityInspectionReport(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT, null=True, blank=True)
    qir_no = models.ForeignKey(NumberingSeriesLinking, related_name="qir", on_delete=models.PROTECT, null=True,
                                blank=True)
    qir_date = models.DateField(null=True)
    remarks = models.TextField(blank=True, null=True)
    reject_last_serial = models.IntegerField(default=0)
    quality_inspections_report_item_detail_id = models.ManyToManyField(QualityInspectionsReportItemDetails)
    goods_inward_note = models.ForeignKey(GoodsInwardNote, on_delete=models.PROTECT, null=True, blank=True)
    rework_received = models.ForeignKey("ReworkDeliveryChallan", on_delete=models.SET_NULL, null=True, blank=True)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    modified_by = models.ForeignKey(User, related_name="QualityInspectionReport_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="QualityInspectionReport_create", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            conditions = {'resource': 'Quality Inspection Report', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.qir_no = response['instance']
                self.qir_date = datetime.now().date() 
            else:
                raise ValidationError(response['errors']) 

        history_list = {
                "status": "Status",
                "qir_no":"Qir No",
                "qir_date":"Qir Date",
                "remarks":"Remarks",
                "modified_by":"Modified By",
                "created_by":"Created By",
                "created_at":"Created At",
                "updated_at":"Updated At"
            }

        
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(QualityInspectionReport, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, QualityInspectionReport, history_list)
        if action == "Update":
            super(QualityInspectionReport, self).save(*args, **kwargs)
        return instance
    
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.quality_inspections_report_item_detail_id.exists():
            self.quality_inspections_report_item_detail_id.all().delete() 
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class GoodsReceiptNoteItemDetails(models.Model):
    gin = models.ForeignKey(GoodsInwardNoteItemDetails, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    base_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    stock_added = models.BooleanField(default=False)
    conversion_factor = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    purchase_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    serial_number = models.TextField(null=True, blank=True) 
    batch_number = models.CharField(max_length=20, null=True, blank=True)
    purchase_invoice_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    purchase_return_qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    is_submited_purchase_invoice = models.BooleanField(default=False)
    is_draft_purchase_invoice = models.BooleanField(default=False)
    modified_by = models.ForeignKey(User, related_name="GoodsReceiptNoteItemDetails_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="GoodsReceiptNoteItemDetails_create", on_delete=models.PROTECT,
                                null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GoodsReceiptNote(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT, null=True, blank=True)
    grn_no = models.ForeignKey(NumberingSeriesLinking, related_name="grn", on_delete=models.PROTECT, null=True,
                            blank=True)
    grn_date = models.DateField(null=True, blank=True)
    e_way_bill = models.CharField(max_length=50, null=True, blank=True)
    e_way_bill_date = models.DateField(null=True, blank=True)
    goods_receipt_note_item_details = models.ManyToManyField(GoodsReceiptNoteItemDetails)
    remarks = models.TextField(null=True, blank=True)
    goods_inward_note = models.ForeignKey(GoodsInwardNote, on_delete=models.PROTECT, null=True, blank=True)
    all_stock_added = models.BooleanField(default=False)
    purchase_invoice = models.ManyToManyField("PurchaseInvoice", blank=True)
    purchase_retun = models.ManyToManyField("PurchaseReturnChallan", blank=True)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    modified_by = models.ForeignKey(User, related_name="GRN_modified", on_delete=models.PROTECT,
                                        null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="GRN_create", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit':[],
            "credits" : {}

        }
        if not self.id:
            conditions = {'resource': 'Goods Receipt Note', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.grn_no = response['instance']
                # super().save(*args, **kwargs)
            else:
                raise ValidationError(f"Error creating serial number: {response['errors']}")
        history_list = {
            "status": "Status",
            "remark": "Remark",
            "grn_date": "Date",
        }
        
        
        if self.status.name == "Received" and not self.is_account_general_ledger_upated and self.goods_inward_note.purchase_order_id:
            from itemmaster.Utils.CommanUtils import company_info, CommonError
            from itemmaster.services.grn_services import grn_general_update
            credits = []
            company_master = company_info()
            pending_account = company_master.purchase_pending_account #Goods Received Not Invoiced
            stock_account = company_master.stock_account #Stock in Hand
            if not pending_account:
                raise CommonError(["Pending account not found in company master."])
            if not stock_account:
                raise CommonError(["Stock account not found in company master."])
            total_amount= 0
            
            for item in self.goods_receipt_note_item_details.all(): 
                item_amount = (item.gin.purchase_order_parent.po_rate or 0) * (item.qty or 0)
                total_amount+=item_amount
                credits.append({
                    "date": self.grn_date,
                    "voucher_type": "GRN",
                    "goods_receipt_note_no": self.id,
                    "account": pending_account.id,
                    "credit": item_amount.quantize(Decimal('0.000'), rounding=ROUND_HALF_UP),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            account_general_ledger["credits"] = credits
            account_general_ledger["debit"] =  {
                    "date": self.grn_date,
                    "voucher_type": "GRN",
                    "goods_receipt_note_no": self.id,
                    "account": stock_account.id,
                    "debit": total_amount.quantize(Decimal('0.000'), rounding=ROUND_HALF_UP),
                    "remark": "",
                    "created_by": self.created_by.pk,
                }
            result = grn_general_update(account_general_ledger)
            if not result['success']:
                raise CommonError(result['errors'])
            else:
                self.is_account_general_ledger_upated = True
        
        if self.status.name == "Canceled" and self.is_account_general_ledger_upated and self.goods_inward_note.purchase_order_id:
            agl_qs = AccountsGeneralLedger.objects.filter(goods_receipt_note_no=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()
            
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(GoodsReceiptNote, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, GoodsReceiptNote, history_list)
        if action == "Update":
            super(GoodsReceiptNote, self).save(*args, **kwargs)
        return instance
    
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.goods_receipt_note_item_details.exists():
            self.goods_receipt_note_item_details.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class ReworkDeliveryChallanItemDetails(models.Model):
    purchase_item = models.ForeignKey(purchaseOrderItemDetails, on_delete=models.PROTECT, null=True, blank=True)
    qc_item = models.ForeignKey(QualityInspectionsReportItemDetails, on_delete=models.PROTECT, null=True, blank=True)
    rework_qty = models.DecimalField(max_digits=10, decimal_places=2)
    received_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_invoice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ReworkDeliveryChallanItemDetails_modified",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReworkDeliveryChallanItemDetails_created",
                                on_delete=models.PROTECT, null=True, blank=True)

class ReworkDeliveryChallan(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT)
    dc_no = models.ForeignKey(NumberingSeriesLinking, related_name="RDC", on_delete=models.PROTECT, null=True,
                            blank=True)
    dc_date = models.DateField(null=True, blank=True)
    address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT, null=True,
                            blank=True)
    e_way_bill = models.CharField(max_length=50, null=True, blank=True)
    e_way_bill_date = models.DateField(null=True, blank=True)
    purchase_order_no = models.ForeignKey(purchaseOrder, on_delete=models.PROTECT, null=True, blank=True)
    rework_percentage = models.IntegerField(null=True, blank=True)
    qc = models.ForeignKey(QualityInspectionReport,  on_delete=models.PROTECT, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    rework_delivery_challan_item_details = models.ManyToManyField(ReworkDeliveryChallanItemDetails,
                                                                blank=True)
    """amount details"""
    befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3)
    round_off = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    # own_vehicle--  Vehicle No & Driver Name
    vehicle_no = models.CharField(max_length=20, null=True, blank=True)
    driver_name = models.CharField(max_length=20, null=True, blank=True)
    # Transporter Vehicle No & Transporter Name
    transport = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="transport_id",
                                    null=True, blank=True)
    #courier -- Docket No & Docket Date
    docket_no = models.CharField(max_length=30, null=True, blank=True)
    docket_date = models.DateField(null=True, blank=True)
    other_model = models.TextField(null=True, blank=True)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ReworkDeliveryChallan_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="ReworkDeliveryChallan_created", on_delete=models.PROTECT,
                                null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            conditions = {'resource': 'Rework Delivery Challan', 'default': True}
            response = create_serial_number(conditions)
            if response['success']: 
                self.dc_no = response['instance'] 
            else:
                raise ValidationError(response['errors'])
        history_list = {
                "status": "Status", 
                "dc_date": "DC Date",
                "remarks": "Remarks",
                "gst_nature_transaction": "GST Nature Transaction",
                "place_of_supply": "Place Of Supply",
                "befor_tax": "Befor Tax",
                "tax_total": "Tax total",
                "net_amount": "Net Amount",
                "vehicle_no": "Vehicle No",
                "driver_name": "Driver Name",
                "transport": "Transport",
                "docket_no": "Docket No",
                "docket_date": "Docket Date",
                "other_model": "Other Model",
            }
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(ReworkDeliveryChallan, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, ReworkDeliveryChallan, history_list)
        if action == "Update":
            super(ReworkDeliveryChallan, self).save(*args, **kwargs)
        return instance
        
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.rework_delivery_challan_item_details.exists():
            self.rework_delivery_challan_item_details.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class PurchaseInvoiceItemDetails(models.Model):
    grn_item = models.ManyToManyField(GoodsReceiptNoteItemDetails, blank=True)
    po_item = models.ForeignKey(purchaseOrderItemDetails, null=True, blank=True, on_delete=models.PROTECT)
    po_rate = models.DecimalField(max_digits=10, decimal_places=3)
    po_qty = models.DecimalField(max_digits=10, decimal_places=3)
    conversion_factor = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
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
    po_amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_PurchaseInvoiceItemDetails",
                                    on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_PurchaseInvoiceItemDetails",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PurchaseInvoice(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT)
    purchase_invoice_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT)
    purchase_invoice_date = models.DateField()
    payment_terms = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    due_date = models.DateField()
    
    """Supplier details"""
    credit = models.IntegerField()
    credit_date = models.DateField(null=True, blank=True) 
    place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    """item details"""
    item_detail = models.ManyToManyField(PurchaseInvoiceItemDetails)
    other_expence_charge = models.ManyToManyField(OtherExpensespurchaseOrder , blank=True)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT, null=True, blank=True)
    terms_conditions_text = models.TextField(null=True, blank=True)
    """amount details"""
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
    item_total_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    other_charges_befor_tax = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    purchase_retun = models.ManyToManyField("PurchaseReturnChallan", blank=True)
    created_by = models.ForeignKey(User, related_name="created_purchase_invoice", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_purchase_invoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        
        account_general_ledger= {
            'debits':[],
            "credit" : {}
        }
        if not self.id:
            conditions = {'resource': 'Purchase Invoice', 'default': True}
            response = create_serial_number(conditions)
            if response['success']: 
                self.purchase_invoice_no = response['instance']
            else:
                raise ValidationError(response['errors'])
        history_list = {
                "status": "Status", 
                "purchase_invoice_date": "Date",
                "payment_terms" : "Payment Terms",
                "supplier_ref" : "Supplier Ref",
                "remarks": "Remarks",
                "due_date" : "Due Date",
                "department__name" : "Department",
                "place_of_supply" : "Place Of Supply",
                "e_way_bill" : "E Way Bill",
                "e_way_bill Date" : "e_way_bill_date",
                "item_total_befor_tax" : "Item Total Befor Tax",
                "other_charges_befor_tax" : "Other Charges Befor Tax",
                "taxable_value" : "Taxable Value",
                "tax_total" : "Tax Total",
                "net_amount" : "Net Amount",
            }
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster.Utils.CommanUtils import company_info, CommonError
            from itemmaster.services.purchase_invoice_services import purchase_invoice_general_update
            grn = self.goodsreceiptnote_set.first()
            supplier = grn.goods_inward_note.purchase_order_id.supplier_id
            if not supplier:
                raise CommonError(["supplier not found."])
            debits=[]
            company_master = company_info()
            pending_account = company_master.purchase_pending_account #Goods Received Not Invoiced
            
            if not pending_account:
                raise CommonError(["Pending account not found in company master."])
            purchase_account = company_info().purchase_account
            if not purchase_account:
                raise CommonError("Purchase account not found in company master.")
            
            item_details = self.item_detail.all()
            other_expence_charge = self.other_expence_charge.all()
            purchase_amount = 0
            for item in item_details:
                grn = item.grn_item.exists()
                if grn:
                    purchase_amount += (item.po_amount or 0)
                else:
                    item_master = item.po_item.item_master_id
                    if not item_master:
                        raise CommonError(f" {item.id} item master link not found.")
                    
                    item_account = item_master.item_purchase_account
                    if not item_account:
                        raise CommonError(f"{item_master} account not found in item master.")
                    
                    debits.append({
                        "date": self.purchase_invoice_date,
                        "voucher_type": "Purchase Invoice",
                        "purchase_invoice": self.id,
                        "account":  item_account.id,
                        "debit":  item.po_amount,
                        "purchase_account" : None ,
                        "purchase_amount" : Decimal(0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if purchase_amount > 0:
                debits.append({
                        "date": self.purchase_invoice_date,
                        "voucher_type": "Purchase Invoice",
                        "purchase_invoice": self.id,
                        "account": pending_account.id,
                        "debit": purchase_amount,
                        "purchase_account" : purchase_account.id,
                        "purchase_amount" : purchase_amount,
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            for charge in other_expence_charge:
                account_id = charge.other_expenses_id.account.id if charge.other_expenses_id else None
                if not account_id:
                    raise CommonError(f"{charge.other_expenses_id.name} account not found.")
                
                debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": account_id,
                    "debit": (charge.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.igst_value and Decimal(self.igst_value) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in company master."])
                else: 
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": igst_account.id,
                    "debit": (self.igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst_value and  Decimal(self.sgst_value) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in company master."])
                else:
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": sgst_account.id,
                    "debit": (self.sgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cgst_value and  Decimal(self.cgst_value) > 0:
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in company master."])
                else: 
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": cgst_account.id,
                    "debit": (self.cgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cess_value and  Decimal(self.cess_value) > 0:
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in company master."])
                else:
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": cess_account.id,
                    "debit": (self.cess_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in company master."])
                else:
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
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
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": tds_account.id,
                    "debit": (self.tds_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.round_off is not None and self.round_off !=0 and self.round_off != "" :
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in company master."])
                else:
                    debits.append({
                    "date": self.purchase_invoice_date,
                    "voucher_type": "Purchase Invoice",
                    "purchase_invoice": self.id,
                    "account": round_off_account.id,
                    "debit": self.round_off,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
                    
            payable_account = company_info().payable_account
            if not payable_account:
                raise CommonError(["Payable Account not found in company master."])
            else:
                account_general_ledger["credit"] = {
                "date": self.purchase_invoice_date,
                "voucher_type": "Purchase Invoice",
                "purchase_invoice": self.id,
                "account": payable_account.id,
                "credit": (self.net_amount or 0),
                "customer_supplier" : supplier.id,
                "remark": "",
                "created_by": self.created_by.pk,
            }
            account_general_ledger["debits"] = debits 
            if not self.is_account_general_ledger_upated:
                result = purchase_invoice_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True

        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(PurchaseInvoice, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, PurchaseInvoice, history_list)
        if action == "Update":
            super(PurchaseInvoice, self).save(*args, **kwargs)
        return instance
        
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.item_detail.exists():
            self.item_detail.all().delete()
        if self.other_expence_charge.exists():
            self.other_expence_charge.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete() 

        super().delete(*args, **kwargs)

class PurchaseInvoiceImport(models.Model):
    purchase_invoice = models.OneToOneField(PurchaseInvoice, on_delete=models.CASCADE,related_name="import_details")
    bill_of_entry_no = models.CharField(max_length=50, null=True, blank=True)
    bill_of_entry_date = models.DateField(null=True, blank=True)
    port_code = models.CharField(max_length=10, null=True, blank=True)
    total_duty = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

class PurchaseInvoiceImportLine(models.Model):
    import_header = models.ForeignKey(PurchaseInvoiceImport, on_delete=models.CASCADE, related_name="line_items")
    item = models.ForeignKey(PurchaseInvoiceItemDetails, on_delete=models.CASCADE)
    assessable_hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    assessable_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    igst = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

class PurchaseRetunBatch(models.Model):
    """batch -> link GoodsReceiptNoteItemDetails to track batch and qty"""
    batch = models.ForeignKey(GoodsReceiptNoteItemDetails, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    is_stock_reduce = models.BooleanField(default=False)

class PurchaseRetunNobatchNoserial(models.Model):
    """NobatchNoserial -> link GoodsReceiptNoteItemDetails to track NobatchNoserial and qty"""
    nobatch_noserial = models.ForeignKey(GoodsReceiptNoteItemDetails, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    is_stock_reduce = models.BooleanField(default=False)

class PurchaseReturnChallanItemDetails(models.Model):
    purchase_invoice_item = models.ForeignKey(PurchaseInvoiceItemDetails, on_delete=models.PROTECT, null=True, blank=True)
    grn_item = models.ManyToManyField(GoodsReceiptNoteItemDetails, blank=True)
    serial = models.ManyToManyField(SerialNumbers, blank=True)
    batch = models.ManyToManyField(PurchaseRetunBatch, blank=True)
    nobatch_noserial= models.ManyToManyField(PurchaseRetunNobatchNoserial, blank=True)
    po_return_qty = models.DecimalField(max_digits=10, decimal_places=3)
    base_return_qty = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    po_amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_stock_reduce = models.BooleanField(default=False)
    modified_by = models.ForeignKey(User, related_name="PurchaseReturnChallanItemDetails_modified",
                                on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="PurchaseReturnChallanItemDetails_create",
                                on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.serial.exists():
            self.serial.all().delete()
        if self.batch.exists():
            self.batch.all().delete()
        if self.nobatch_noserial.exists():
            self.nobatch_noserial.all().delete()
        super().delete(*args, **kwargs)

class PurchaseReturnChallan(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT)
    purchase_return_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True)
    purchase_return_date = models.DateField()
    purchase_order = models.ForeignKey(purchaseOrder, on_delete=models.PROTECT, null=True, blank=True)
    eway_bill_no = models.CharField(max_length=50, null=True, blank=True)
    eway_bill_date = models.DateField(null=True, blank=True)
    remarks = models.TextField( null=True, blank=True)
    purchase_return_challan_item_Details = models.ManyToManyField(PurchaseReturnChallanItemDetails)
    terms_conditions = models.ForeignKey(TermsConditions, on_delete=models.PROTECT)
    terms_conditions_text = models.TextField()
    # own_vehicle--  Vehicle No & Driver Name
    vehicle_no = models.CharField(max_length=20, null=True, blank=True)
    driver_name = models.CharField(max_length=20, null=True, blank=True)
    # # Transporter -- Vehicle No & Transporter Name
    transport = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT,
                                    related_name="PurchaseReturnChallan_transport_id",
                                    null=True, blank=True)
    #courier -- Docket No & Docket Date
    docket_no = models.CharField(max_length=30, null=True, blank=True)
    docket_date = models.DateField(null=True, blank=True)
    # Other mode
    other_model = models.TextField(null=True, blank=True)
    """amount details"""
    igst = models.JSONField(null=True, blank=True)
    sgst = models.JSONField(null=True, blank=True)
    cgst = models.JSONField(null=True, blank=True)
    cess = models.JSONField(null=True, blank=True)
    befor_tax = models.DecimalField(max_digits=15, decimal_places=3)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    modified_by = models.ForeignKey(User, related_name="PurchaseReturnChallan_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="PurchaseReturnChallan_create", on_delete=models.PROTECT,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debits': [],
            "credit" : {}
        }
        debits= []
        
        if not self.id:
            conditions = {'resource': 'Purchase Return Challan', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.purchase_return_no = response['instance'] 
                
            else:
                raise ValidationError(response['errors'])
        # purchase_return_challan

        
        history_list = {
            "status": "Status",
            "remark": "Remark",
            "purchase_return_date": "Date",
            "eway_bill_no" : "E Way Bill No",
            "eway_bill_date" : "E Way Bill Date",
            "vehicle_no" : "Vehicle no",
            "driver_name": "Driver Name",
            "docket_no" : "Docket No",
            "docket_date" : "Docket Date",
            "other_model": "other Model",
            "net_amount" : "Net Amount"
        }
        action = "Add" if self._state.adding else "Update"
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster.Utils.CommanUtils import company_info, CommonError, cal_total_dic_value
            from itemmaster.services.purchase_return_services import purchase_return_general_update
            purchase_account = company_info().purchase_account
            if not purchase_account:
                raise CommonError("Purchase account not found in company master.")
            stock_account = company_info().stock_account
            if not stock_account:
                raise CommonError("Stock account not found in company master.")
            purchase_amount =  0
            for item in self.purchase_return_challan_item_Details.all():
                if item.purchase_invoice_item:
                    grn_item = item.purchase_invoice_item.grn_item.first()
                else:
                    grn_item = item.grn_item.first()
                if grn_item is None :
                    pass
                if grn_item.gin.item_master.item_types == "Product":
                    purchase_amount+=(item.po_amount or 0)
                else:
                    item_purchase_account = grn_item.gin.item_master.item_purchase_account
                    if not item_purchase_account:
                        raise CommonError(f"{grn_item.gin.item_master} purchase account not found.")
                    debits.append({
                        "date": self.purchase_return_date,
                        "voucher_type": "Purchase Return Invoice",
                        "purchase_return_challan": self.id,
                        "account": item_purchase_account.id,
                        "debit": (item.po_amount or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
    
            if self.igst and  cal_total_dic_value(self.igst) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in account."])
                else: 
                    igst_value = cal_total_dic_value(self.igst)
                    debits.append({
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": igst_account.id,
                    "debit": (igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst and cal_total_dic_value(self.sgst) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in account."])
                else:
                    sgst_value = cal_total_dic_value(self.sgst)
                    debits.append({
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": sgst_account.id,
                    "debit": (sgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cgst and  cal_total_dic_value(self.cgst) > 0 :
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in account."])
                else: 
                    cgst_value = cal_total_dic_value(self.cgst)
                    debits.append({
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": cgst_account.id,
                    "debit": (cgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cess and  cal_total_dic_value(self.cess) > 0 :
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in account."])
                else:
                    cess_value = cal_total_dic_value(self.cess)
                    debits.append({
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": cess_account.id,
                    "debit": (cess_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.round_off is not None and self.round_off != 0  and  self.round_off !="":
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in account."])
                else: 
                    debits.append({
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": round_off_account.id,
                    "debit": (self.round_off or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if purchase_amount > 0:
                debits.append(
                    {
                        "date": self.purchase_return_date,
                        "voucher_type": "Purchase Return Invoice",
                        "purchase_return_challan": self.id,
                        "account": purchase_account.id,
                        "debit": (purchase_amount or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    }
                )

            account_general_ledger["debits"] = debits
            account_general_ledger["credit"] = {
                    "date": self.purchase_return_date,
                    "voucher_type": "Purchase Return Invoice",
                    "purchase_return_challan": self.id,
                    "account": stock_account.id,
                    "credit": (self.net_amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                }
 
            if not self.is_account_general_ledger_upated:
                result = purchase_return_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True
            
        if self.status.name == "Canceled" and self.is_account_general_ledger_upated:
            agl_qs = AccountsGeneralLedger.objects.filter(purchase_return_challan=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()
        if action == "Add":
            super(PurchaseReturnChallan, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, PurchaseReturnChallan, history_list)
        if action == "Update":
            super(PurchaseReturnChallan, self).save(*args, **kwargs)
        return instance

    def delete(self, *args, **kwargs):
        "delete the releted datas"
        if self.purchase_return_challan_item_Details.exists():
            self.purchase_return_challan_item_Details.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class DirectPurchaseInvoiceItemDetails(models.Model):
    index = models.IntegerField(null=True, blank=True)
    itemmaster = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.TextField(max_length=250)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=3)
    after_discount_value_for_per_item = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT)
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
    created_by = models.ForeignKey(User, related_name="created_Direct_purchse_Invoice", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_Direct_purchse_Invoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DirectPurchaseInvoiceAccount(models.Model):
    index = models.IntegerField(null=True, blank=True)
    direct_purchase_invoice = models.ForeignKey("DirectPurchaseinvoice", on_delete=models.CASCADE, null=True, blank=True)
    account_master = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    description = models.CharField(max_length=100, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    igst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    sgst_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    cess_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tcs_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tds_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tcs_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_by = models.ForeignKey(User, related_name="created_direct_purchase_invoice_account", on_delete=models.PROTECT,)
    modified_by = models.ForeignKey(User, related_name="modified_direct_purchase_invoice_account", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DirectPurchaseinvoice(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT)
    direct_purchase_invoice_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT,  
                                editable=True, null=True, blank=True)
    direct_purchase_invoice_date = models.DateField()
    due_date = models.DateField()
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    supplier = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, related_name="Direct_purchase_invoice_supplier")
    supplier_address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT,
                                    related_name="Direct_purchase_invoice_supplier_address")
    supplier_contact_person = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT,
                                    related_name="Direct_purchase_invoice_supplier_contact_person")
    supplier_gstin_type = models.CharField(max_length=50)
    supplier_gstin = models.CharField(max_length=15, null=True, blank=True)
    supplier_state = models.CharField(max_length=20)
    supplier_place_of_supply = models.CharField(max_length=50)
    supplier_ref = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    creadit_period = models.IntegerField()
    creadit_date = models.DateField(null=True, blank=True)
    payment_term = models.TextField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    item_detail = models.ManyToManyField(DirectPurchaseInvoiceItemDetails, blank=True)
    other_expence_charge = models.ManyToManyField(OtherExpensespurchaseOrder , blank=True)
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
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3,)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Direct_purchase_invoice", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_Direct_purchase_invoice", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debits':[],
            "credit" : {}
        }
        if not self.id:
            conditions = {'resource': 'Direct Purchase Invoice', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.direct_purchase_invoice_no = response['instance'] 
                
            else:
                raise ValidationError(response['errors'])

        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster.Utils.CommanUtils import company_info, CommonError
            from itemmaster.services.purchase_direct_invoice import purchase_direct_invoice_general_update

            supplier = self.supplier
            if not supplier:
                raise CommonError(["supplier not found."])
            debits=[]

            other_expence_charge = self.other_expence_charge.all()
            item_details = self.item_detail.all()
            purchase_invoice_accounts = self.directpurchaseinvoiceaccount_set.all()

            purchase_account = company_info().purchase_account
            if not purchase_account:
                raise CommonError("Purchase account not found in company master.")
            for item in item_details:
                account = None
                if item.itemmaster.item_types != "Product":
                    itemmater = item.itemmaster
                    account = itemmater.item_purchase_account
                    if not account:
                        raise CommonError(f"Purchase account not found in {itemmater.item_part_code}-{itemmater.item_name}.")
                else:
                    account = purchase_account
                debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": account.id,
                    "debit": (item.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            for purchase_invoice_account in purchase_invoice_accounts:
                account = purchase_invoice_account.account_master
                if not account:
                    raise CommonError(f"Purchase account not found in accounts.")
                debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": account.id,
                    "debit": (purchase_invoice_account.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
                
            for charge in other_expence_charge:
 
                account_id = charge.other_expenses_id.account if charge.other_expenses_id else None
                if not account_id:
                    raise CommonError(f"{charge.other_expenses_id.name} account not found.")
                
                debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": account_id.id,
                    "debit": (charge.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                }) 

            if self.igst_value and Decimal(self.igst_value) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in company master."])
                else: 
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": igst_account.id,
                    "debit": (self.igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst_value and  Decimal(self.sgst_value) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in company master."])
                else:
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": sgst_account.id,
                    "debit": (self.sgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cgst_value and  Decimal(self.cgst_value) > 0:
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in company master."])
                else: 
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": cgst_account.id,
                    "debit": (self.cgst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.cess_value and  Decimal(self.cess_value) > 0:
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in company master."])
                else:
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": cess_account.id,
                    "debit": (self.cess_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in company master."])
                else:
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
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
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": tcs_account.id,
                    "debit": (self.tds_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            if self.round_off is not None and self.round_off !=0 and self.round_off != "" :
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in company master."])
                else:
                    debits.append({
                    "date": self.direct_purchase_invoice_date,
                    "voucher_type": "Direct Purchase Invoice",
                    "direct_purchase_invoice": self.id,
                    "account": round_off_account.id,
                    "debit": self.round_off,
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
            
            payable_account = company_info().payable_account
            if not payable_account:
                raise CommonError(["Payable Account not found in company master."])
            else:
                account_general_ledger["credit"] = {
                "date": self.direct_purchase_invoice_date,
                "voucher_type": "Direct Purchase Invoice",
                "direct_purchase_invoice": self.id,
                "account": payable_account.id,
                "credit": (self.net_amount or 0),
                "customer_supplier" : supplier.id,
                "remark": "",
                "created_by": self.created_by.pk,
            }
            account_general_ledger["debits"] = debits
            print("account_general_ledger", account_general_ledger)
            if not self.is_account_general_ledger_upated:
                result = purchase_direct_invoice_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True




        history_list = {
                "status": "Status", 
                "direct_purchase_invoice_date": "Date",
                "payment_term" : "Payment Terms",
                "supplier_ref" : "Supplier Ref",
                "remarks": "Remarks",
                "due_date" : "Due Date",
                "department__name" : "Department",
                "place_of_supply" : "Place Of Supply",
                "e_way_bill" : "E Way Bill",
                "e_way_bill Date" : "e_way_bill_date",
                "item_total_befor_tax" : "Item Total Befor Tax", 
                "taxable_value" : "Taxable Value",
                "tax_total" : "Tax Total",
                "net_amount" : "Net Amount",
            }
        action = "Add" if self._state.adding else "Update"
        if action == "Add":
            super(DirectPurchaseinvoice, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, DirectPurchaseinvoice, history_list)
        if action == "Update":
            super(DirectPurchaseinvoice, self).save(*args, **kwargs)
        return instance

class DebitNoteOtherIncomeCharge(models.Model):
    debit_note = models.ForeignKey("DebitNote", on_delete=models.CASCADE, null=True, blank=True)
    other_income_charges = models.ForeignKey("itemmaster2.OtherIncomeCharges", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="debit_note_other_income_charges_create", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="debit_note_other_income_charges_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DebitNoteItemDetail(models.Model):
    index = models.IntegerField(null=True, blank=True)
    debit_note = models.ForeignKey("DebitNote", on_delete=models.CASCADE, null=True, blank=True)
    item_master = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    description = models.CharField(max_length=100, null=True, blank=True)
    purchase_return_item = models.ForeignKey(PurchaseReturnChallanItemDetails, 
                                            on_delete=models.PROTECT, null=True, blank=True)
    qty = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    uom = models.ForeignKey(UOM, related_name="debit_note_base_uom",  on_delete=models.PROTECT, null=True, blank=True)
    rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    po_qty = models.DecimalField(max_digits=15, decimal_places=3)
    po_uom = models.ForeignKey(UOM,  related_name ="debit_note_po_uom", on_delete=models.PROTECT, null=True, blank=True)
    po_rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    conversion_factor = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT)
    tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    tds_percentage = models.IntegerField(null=True, blank=True)
    tcs_percentage = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3,null=True, blank=True)
    po_amount = models.DecimalField(max_digits=10, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="created_debit_note_item_detail", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_debit_note_item_detail", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DebitNoteAccount(models.Model):
    index = models.IntegerField(null=True, blank=True)
    debit_note = models.ForeignKey("DebitNote", on_delete=models.CASCADE, null=True, blank=True)
    account_master = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    description = models.CharField(max_length=100, null=True, blank=True)
    hsn = models.ForeignKey(Hsn, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cgst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    igst = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cess = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    tcs_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_by = models.ForeignKey(User, related_name="created_debit_note_account", on_delete=models.PROTECT,
                                null=True, blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_debit_note_account", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DebitNote(models.Model):
    status = models.ForeignKey("CommanStatus", on_delete=models.PROTECT)
    debit_note_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, blank=True, null=True,)
    debit_note_date = models.DateField()
    note_no = models.CharField(max_length=16, blank=True, null=True)
    note_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT)
    supplier_ref = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    purchase_order_no = models.ForeignKey(purchaseOrder, on_delete=models.PROTECT, null=True, blank=True )
    return_invoice = models.ForeignKey(PurchaseReturnChallan, on_delete=models.PROTECT, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    gstin_type = models.CharField(max_length=50, null=True, blank=True)
    gstin = models.CharField(max_length=15, null=True, blank=True)
    gst_nature_transaction= models.ForeignKey(GSTNatureTransaction, on_delete=models.PROTECT, null=True, blank=True)
    gst_nature_type = models.CharField(max_length=50, choices=NATURE_TYPE_CHOICES, null=True, blank=True)
    place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    e_way_bill = models.CharField(max_length=50, null=True, blank=True)
    e_way_bill_date = models.DateField(null=True, blank=True)
    contact = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT)
    address = models.ForeignKey(CompanyAddress, on_delete=models.PROTECT)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
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
    taxable_value = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    tax_total = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    round_off = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    round_off_method = models.CharField(max_length=10, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_account_general_ledger_upated = models.BooleanField(default=False)
    history_details = models.ManyToManyField("ItemMasterHistory", blank=True)
    created_by = models.ForeignKey(User, related_name="created_debit_note", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modified_debit_note", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit': [],
            "credits" : {}
        }
        credits = []
        if not self.id:
            conditions = {'resource': 'Debit Note', 'default': True}
            response = create_serial_number(conditions)
            if response['success']:
                self.debit_note_no = response['instance'] 
            else:
                raise ValidationError(response['errors'])
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_upated:
            from itemmaster.Utils.CommanUtils import company_info, CommonError, cal_total_dic_value
            from itemmaster.services.debit_note import debit_note_general_update

            other_income_charge = self.debitnoteotherincomecharge_set.all()
            item_details = self.debitnoteitemdetail_set.all()
            accounts = self.debitnoteaccount_set.all()
            supplier = self.supplier
            if not supplier:
                raise CommonError(["supplier not found."])
            purchase_account = company_info().purchase_account
            if not purchase_account:
                raise CommonError("Purchase account not found in company master.")
            
            for item in item_details:
                item_account =None
                item_type =  item.item_master.item_types.name
                if item_type != "Product":
                    itemmater = item.item_master
                    item_account = itemmater.item_purchase_account
                    if not item_account:
                        raise CommonError(f"Purchase account not found in {itemmater.item_part_code}-{itemmater.item_name}.")
                else:
                    item_account = purchase_account
                item_credit =  {
                "date": self.debit_note_date,
                "voucher_type": "Debit Note",
                "debit_note": self.id,
                "account": item_account.id if item_account else None,
                "credit": (item.po_amount or 0),
                "purchase_account" : item_account.id if self.return_invoice   else None,
                "purchase_amount" : item.po_amount if self.return_invoice   else Decimal(0),
                "remark": "",
                "created_by": self.created_by.pk,
                }
                credits.append(item_credit)
            
            for account in accounts:
                account_master = account.account_master
                if not account_master:
                    raise CommonError(f"{account.description} not found in company master.")
                credits.append({
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": account_master.id,
                    "credit": (account.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            for charge in other_income_charge:
                other_income_charge = charge.other_income_charges
                if not other_income_charge:
                    raise CommonError(f"{charge.id} Other income charge not found.")
                charge_account = other_income_charge.account
                if not charge_account:
                    raise CommonError(f"{other_income_charge.name} account not found.")
                
                credits.append({
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": charge_account.id,
                    "credit": (charge.amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.igst and  Decimal(cal_total_dic_value(self.igst)) > 0:
                igst_account = company_info().igst_account
                if not igst_account:
                    raise CommonError(["IGST not found in account."])
                else: 
                    igst_value =  cal_total_dic_value(self.igst)
                    credits.append({
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": igst_account.id,
                    "credit": (igst_value or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })

            if self.sgst and cal_total_dic_value(self.sgst) > 0:
                sgst_account = company_info().sgst_account
                if not sgst_account:
                    raise CommonError(["SGST not found in account."])
                else:
                    sgst_value = cal_total_dic_value(self.sgst)
                    credits.append({
                        "date": self.debit_note_date,
                        "voucher_type": "Debit Note",
                        "debit_note": self.id,
                        "account": sgst_account.id,
                        "credit": (sgst_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.cgst and cal_total_dic_value(self.cgst) > 0 :
                cgst_account = company_info().cgst_account
                if not cgst_account:
                    raise CommonError(["CGST not found in account."])
                else: 
                    cgst_value = cal_total_dic_value(self.cgst)
                    credits.append({
                        "date": self.debit_note_date,
                        "voucher_type": "Debit Note",
                        "debit_note": self.id,
                        "account": cgst_account.id,
                        "credit": (cgst_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.cess and cal_total_dic_value(self.cess) > 0 :
                cess_account = company_info().cess_account
                if not cess_account:
                    raise CommonError(["CESS not found in account."])
                else:
                    cess_value = cal_total_dic_value(self.cess)
                    credits.append({
                        "date": self.debit_note_date,
                        "voucher_type": "Debit Note",
                        "debit_note": self.id,
                        "account": cess_account.id,
                        "credit": (cess_value or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            
            if self.tcs_total and  Decimal(self.tcs_total) > 0:
                tcs_account = company_info().tcs_account
                if not tcs_account:
                    raise CommonError(["TCS not found in company master."])
                else:
                    credits.append({
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": tcs_account.id,
                    "credit": (self.tcs_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })
                    
            if self.tds_total and  Decimal(self.tds_total) > 0:
                tds_account = company_info().tds_account
                if not tds_account:
                    raise CommonError(["TDS not found in company master."])
                else:
                    credits.append({
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": tds_account.id,
                    "credit": (self.tds_total or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                })


            if self.round_off is not None and self.round_off != 0  and  self.round_off !="":
                round_off_account = company_info().round_off_account
                if not round_off_account:
                    raise CommonError(["Round Off not found in account."])
                else: 
                    credits.append({
                        "date": self.debit_note_date,
                        "voucher_type": "Debit Note",
                        "debit_note": self.id,
                        "account": round_off_account.id,
                        "credit": (self.round_off or 0),
                        "remark": "",
                        "created_by": self.created_by.pk,
                    })
            


            account_general_ledger["credits"] = credits
            payable_account = company_info().payable_account
            if not payable_account:
                raise CommonError(["Payable Account not found in company master."])
            else:
                account_general_ledger["debit"] = {
                    "date": self.debit_note_date,
                    "voucher_type": "Debit Note",
                    "debit_note": self.id,
                    "account": payable_account.id,
                    "debit": (self.net_amount or 0),
                    "remark": "",
                    "created_by": self.created_by.pk,
                    } 
            if not self.is_account_general_ledger_upated:
                result = debit_note_general_update(account_general_ledger)
                if not result['success']:
                    raise CommonError(result['errors'])
                else:
                    self.is_account_general_ledger_upated = True
        
        if self.status.name == "Canceled" and self.is_account_general_ledger_upated:
            agl_qs = AccountsGeneralLedger.objects.filter(debit_note=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()

        history_list = {
            "status": "Status",
            "debit_note_date": "Debit Note Date",
            "supplier": "Supplier",
            "supplier_ref" : "Supplier Ref",
            "remarks" : "Remarks",
            "department" : "Department",
            "gstin_type": "GST TYPE",
            "gst_nature_type" : "GST Nature Type",
            "place_of_supply": "Place Of Supply",
            "e_way_bill" : "E Way Bill",
            "e_way_bill_date" : "E way Bill Date",
            "net_amount" : "Net Amount",
            "created_by" : "Created By",
            "modified_by" : "Modified By",
        }
        action = "Add" if self._state.adding else "Update"
        
        if action == "Add":
            super(DebitNote, self).save(*args, **kwargs)
        instance = SaveToHistory(self, action, DebitNote, history_list)
        if action == "Update":
            super(DebitNote, self).save(*args, **kwargs)
        return instance
    
    def delete(self, *args, **kwargs):
        "delete the releted datas" 
         
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class PurchasePaidDetails(models.Model):
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE)
    payment_voucher = models.ForeignKey("userManagement.PaymentVoucher", on_delete=models.CASCADE, 
                                        null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    created_by = models.ForeignKey(User, related_name="PurchasePaidDetails_created", on_delete=models.PROTECT)


class MrpSourceType(models.Model):
    name = models.CharField(max_length=50)

class MrpItem(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    bom = models.ForeignKey(Bom, on_delete=models.PROTECT, blank=True, null=True, default='')
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    source_type = models.ForeignKey(MrpSourceType, on_delete=models.PROTECT)
    cost = models.CharField(max_length=15, default='0', blank=True, null=True)
    supplier = models.ManyToManyField(SupplierFormData, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="mrp_item_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="mrp_item_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

class MrpMaster(models.Model):
    is_sales_order = models.BooleanField(default=False)
    is_production_order = models.BooleanField(default=False)
    is_item_group = models.BooleanField(default=False)
    item_group = models.ManyToManyField(Item_Groups_Name)
    mrp_item = models.ManyToManyField(MrpItem)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="mrp_modified", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="mrp_created", on_delete=models.PROTECT, null=True, blank=True)

class ProductionOrderStatus(models.Model):
    name = models.CharField(max_length=50)
    table = models.CharField(max_length=30, default='ProductionOrderItemDetail')

class ProductionOrderSerialNumbers(models.Model):
    name = models.CharField(max_length=30)
    last_serial = models.CharField(max_length=50)
    last_sub_production_order_serial = models.CharField(max_length=50)

class ProductionOrderItem(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    bom = models.ForeignKey(Bom, on_delete=models.PROTECT, blank=True, null=True, default='')
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    source_type = models.ForeignKey(MrpSourceType, on_delete=models.PROTECT)
    cost = models.CharField(max_length=15, default='0', blank=True, null=True)
    supplier = models.ManyToManyField(SupplierFormData, blank=True)
    is_combo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="production_order_item_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="production_order_item_created", on_delete=models.PROTECT,
                                   null=True, blank=True)

class ProductionOrderMaster(models.Model):
    order_no = models.CharField(max_length=100, blank=True, null=True)
    order_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    status = models.ForeignKey(ProductionOrderStatus, on_delete=models.PROTECT, default=6)
    is_combo = models.BooleanField(default=False)
    is_multi_level_manufacture = models.BooleanField(default=False)
    is_sub_production_order = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_master_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_master_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                if self.is_sub_production_order == True:
                    # last_serial_record = ProductionOrderSerialNumbers.objects.select_for_update().filter(name='ProductionOrderMasterSub').first()
                    # if last_serial_record:
                    #     new_serial = int(last_serial_record.last_serial) + 1
                    #     self.order_no = f"-{new_serial}"
                    #     last_serial_record.last_serial = new_serial
                    #     last_serial_record.save()
                    # else:
                    #     self.order_no = f"-1"
                    #     ProductionOrderSerialNumbers.objects.create(name='ProductionOrderMasterSub', last_serial='1')
                    self.order_no = ''
                else:
                    last_serial_record = ProductionOrderSerialNumbers.objects.select_for_update().filter(
                        name='ProductionOrderMaster').first()
                    if last_serial_record:
                        new_serial = int(last_serial_record.last_serial) + 1
                        self.order_no = f"MO{str(new_serial).zfill(4)}"
                        last_serial_record.last_serial = new_serial
                        last_serial_record.save()
                    else:
                        self.order_no = "MO0001"
                        ProductionOrderSerialNumbers.objects.create(name='ProductionOrderMaster', last_serial='1')
        super(ProductionOrderMaster, self).save(*args, **kwargs)

class SubProductionOrders(models.Model):
    order_no = models.CharField(max_length=100, blank=True, null=True)
    status = models.ForeignKey(ProductionOrderStatus, on_delete=models.PROTECT, default=1)
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    production_qty = models.DecimalField(max_digits=10, decimal_places=3)
    completed_qty = models.DecimalField(max_digits=10, decimal_places=3)
    pending_qty = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    po_master = models.ForeignKey(ProductionOrderMaster, on_delete=models.PROTECT, null=True, blank=True)
    bom_type = models.ForeignKey(MrpSourceType, blank=True, null=True, default=1, on_delete=models.PROTECT)
    is_combo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="sub_po_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="sub_po_created", on_delete=models.PROTECT, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                last_serial_record = ProductionOrderSerialNumbers.objects.select_for_update().filter(
                    name='SubProductionOrders').first()
                if last_serial_record:
                    new_serial = int(last_serial_record.last_serial) + 1
                    self.order_no = f"{new_serial}"
                    last_serial_record.last_serial = new_serial
                    last_serial_record.save()
                else:
                    self.order_no = "1"
                    ProductionOrderSerialNumbers.objects.create(name='SubProductionOrders', last_serial='1')
        super(SubProductionOrders, self).save(*args, **kwargs)

class ProductionOrderFinishedGoods(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True)
    production_qty = models.DecimalField(max_digits=10, decimal_places=3)
    completed_qty = models.DecimalField(max_digits=10, decimal_places=3)
    accepted_qty = models.DecimalField(max_digits=10, decimal_places=3)
    rework_qty = models.DecimalField(max_digits=10, decimal_places=3)
    rejected_qty = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    remarks = models.CharField(max_length=1200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_fg_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_fg_created", on_delete=models.PROTECT, null=True, blank=True)

class ProductionOrderRawMaterials(models.Model):
    serial_number = models.CharField(max_length=30)
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True)
    parent_bom = models.ForeignKey(Bom, related_name="parent_bom", on_delete=models.PROTECT, null=True, blank=True)
    bom = models.ForeignKey(Bom, on_delete=models.PROTECT, null=True, blank=True)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    fixed = models.BooleanField(default=False)
    actual_qty = models.DecimalField(max_digits=10, decimal_places=3)
    issued_qty = models.DecimalField(max_digits=10, decimal_places=3)
    used_qty = models.DecimalField(max_digits=10, decimal_places=3)
    store = models.ForeignKey(Store, related_name="po_rm_store", on_delete=models.PROTECT)
    is_combo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_rm_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_rm_created", on_delete=models.PROTECT, null=True, blank=True)

class ProductionOrderScrap(models.Model):
    part_code = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True)
    unit = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    actual_qty = models.DecimalField(max_digits=10, decimal_places=3)
    store = models.ForeignKey(Store, related_name="po_scrap_store", on_delete=models.PROTECT)
    cost_allocation = models.DecimalField(max_digits=10, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_scrap_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_scrap_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

class ProductionOrderProcessRoute(models.Model):
    serial_number = models.IntegerField(null=True, blank=True)
    route = models.ForeignKey(Routing, on_delete=models.PROTECT, null=True, blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, null=True, blank=True)
    duration = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    actual_duration = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_pr_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_pr_created", on_delete=models.PROTECT, null=True, blank=True)

class ProductionOrderOtherCharges(models.Model):
    description = models.CharField(max_length=100, blank=True, null=True)
    bom_amount = models.DecimalField(max_digits=10, decimal_places=3)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=3)
    remarks = models.CharField(max_length=1200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_other_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_other_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

class ProductionOrderItemDetail(models.Model):
    due_date = models.DateField(null=True, blank=True)
    status = models.ForeignKey(ProductionOrderStatus, on_delete=models.PROTECT)
    remarks = models.CharField(max_length=1200, blank=True, null=True)
    sub_production_orders = models.ManyToManyField(SubProductionOrders, blank=True)
    finished_goods = models.ForeignKey(ProductionOrderFinishedGoods, on_delete=models.PROTECT, null=True, blank=True)
    raw_material = models.ManyToManyField(ProductionOrderRawMaterials, blank=True)
    scrap = models.ManyToManyField(ProductionOrderScrap, blank=True)
    other_charges = models.ManyToManyField(ProductionOrderOtherCharges, blank=True)
    routes = models.ManyToManyField(ProductionOrderProcessRoute, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="po_id_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="po_id_created", on_delete=models.PROTECT, null=True, blank=True)

class ProductionOrderLinkingTable(models.Model):
    po_master = models.ForeignKey(ProductionOrderMaster, on_delete=models.PROTECT)
    po_item = models.ForeignKey(ProductionOrderItem, on_delete=models.PROTECT)
    po_item_detail = models.ForeignKey(ProductionOrderItemDetail, on_delete=models.PROTECT, null=True, blank=True)
    is_sub_production_order = models.BooleanField(default=False)

class CommanStatus(models.Model):
    name = models.CharField(max_length=50)
    table = models.CharField(max_length=30)

    def __str__(self):
        return self.name + " , " + self.table

class MaterialRequestFor(models.Model):
    name = models.CharField(max_length=50)

class MaterialRequestItemDetails(models.Model):
    part_number = models.ForeignKey(ItemMaster, on_delete=models.PROTECT)
    hsn_code = models.ForeignKey(Hsn, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    po_raw_material = models.ForeignKey(ProductionOrderRawMaterials, on_delete=models.PROTECT, blank=True)
    issued_qty = models.DecimalField(max_digits=10, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="mr_item_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="mr_item_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

class MaterialRequestMaster(models.Model):
    request_no = models.CharField(max_length=100, blank=True, null=True)
    status = models.ForeignKey(ProductionOrderStatus, on_delete=models.PROTECT, default=8)
    request_for = models.ForeignKey(MaterialRequestFor, on_delete=models.PROTECT)
    request_date = models.DateField()
    production_order = models.ForeignKey(ProductionOrderMaster, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    remarks = models.CharField(max_length=1200, blank=True, null=True)
    issuing_store = models.ForeignKey(Store, on_delete=models.PROTECT)
    item_details = models.ManyToManyField(MaterialRequestItemDetails, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="mr_master_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="mr_master_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                last_serial_record = ProductionOrderSerialNumbers.objects.select_for_update().filter(
                    name='MaterialRequestMaster').first()
                if last_serial_record:
                    new_serial = int(last_serial_record.last_serial) + 1
                    self.request_no = f"MR{str(new_serial).zfill(4)}"
                    last_serial_record.last_serial = new_serial
                    last_serial_record.save()
                else:
                    self.request_no = "MR0001"
                    ProductionOrderSerialNumbers.objects.create(name='MaterialRequestMaster', last_serial='1')
        super(MaterialRequestMaster, self).save(*args, **kwargs)

 
