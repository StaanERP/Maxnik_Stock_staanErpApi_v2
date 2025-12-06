from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from itemmaster.models import *
from Validations.userDataValidations import *
from itemmaster.Utils.CommanUtils import *

"""PermissionOptions and PermissionModel user update from admin page """

leave_type = (('Paid', 'Paid'),
              ('Lop', 'Lop'))

leave_day_type = (('Half Day', 'Half Day'),
                  ('Full Day', 'Full Day'))

employee_education_details = (("Unskilled Labour", "Unskilled Labour"),
                              ("Skilled Labour", "Skilled Labour"),
                              ("10th", "10th"),
                              ("12th", "12th"),
                              ("ITI", "ITI"),
                              ("Diploma", "Diploma"),
                              ("Graduates", "Graduates"),
                              ("Masters", "Masters"),)
transfer_via = (
    ("UPI", "UPI"),
    ("Neft/RTGS", "Neft/RTGS"),
    ("Cheque", "Cheque"),
    )

permission_parent_model = (
    ("Other", "Other"),
   ("Dashboard", "Dashboard"),
   ("General", "General"),
   ("Stock", "Stock"),
   ("Purchase", "Purchase"),
    ("Sales", "Sales"),
    ("Target", "Target"),
    ("Report", "Report"),
    ("Conference", "Conference"),
    ("Accounts", "Accounts"),
    ("Service", "Service"),
    ("Manufacturing", "Manufacturing"),
    ("HR", "HR"),
    ("Table", "Table"),
)

PAY_BY = [
        ('Supplier & Customer', 'Supplier & Customer'),
        ('Employee', 'Employee')
    ]

PAY_MODE = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank')
    ]

# user model and Expense models handle in this models file
class PermissionOptions(models.Model):
    options_name = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="permission_options_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="permission_options_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def __str__(self):
        return self.options_name + str(self.id)


class PermissionModel(models.Model):
    model_name = models.CharField(max_length=50)
    permission_options = models.ManyToManyField(PermissionOptions, related_name='permission_models')
    permission_parent_model = models.CharField(max_length=50, null=True, choices=permission_parent_model,default="Other")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="permission_Model_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="permission_Model_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def __str__(self):
        return self.model_name


class AllowedPermission(models.Model):
    model_name = models.CharField(max_length=50)
    permission_model = models.ForeignKey(PermissionModel, on_delete=models.PROTECT, null=True, blank=True)
    permission_options = models.ManyToManyField(PermissionOptions, related_name='allowed_permission_models')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="allowed_Model_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="allowed_Model_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def __str__(self):
        return self.model_name + str(self.id)


class Profile(models.Model):
    profile_name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    allowed_permission = models.ManyToManyField(AllowedPermission, related_name='allowed_permission')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="profile_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="profile_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def __str__(self):
        return self.profile_name

    def delete(self, *args, **kwargs):
        # Optionally handle custom delete logic here

        # Explicitly delete related AllowedPermission instances if needed
        if self.allowed_permission.exists():
            self.allowed_permission.all().delete()
        super().delete(*args, **kwargs)

class Roles(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    report_to = models.ForeignKey(User, related_name="Role_report_to", on_delete=models.PROTECT, blank=True, null=True)
    descriptions = models.TextField(null=True, blank=True)
    share_data_with = models.ManyToManyField(User, related_name="share_data_with", blank=True)
    parent_role = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="Roles_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Roles_created", on_delete=models.PROTECT, null=True,
                                blank=True)

    def save(self, *args, **kwargs):
        self.role_name = self.role_name
        # Check if a record with the same normalized name already exists
        if Roles.objects.exclude(pk=self.pk).filter(role_name__iexact=self.role_name).exists():
            raise ValidationError("Role name must be unique.")
        history_list = {
            "role_name": "Role Name",
            "report_to": "Report To",
            "descriptions": "Descriptions"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Roles, history_list)
            super(Roles, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Roles, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Roles, history_list)
        return instance

    def __str__(self,):
        return self.role_name

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class UserManagement(models.Model):
    user = models.ForeignKey(User, related_name="userManagement_user", on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    role = models.ForeignKey(Roles, related_name="role_one", on_delete=models.PROTECT, null=True, blank=True)
    role_2 = models.ForeignKey(Roles, related_name="role_two", on_delete=models.PROTECT, null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.PROTECT, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.PROTECT, null=True, blank=True)
    is_staan_user = models.BooleanField(default=False)
    is_microsoft_user = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)
    sales_person = models.BooleanField(default=False)
    service = models.BooleanField(default=False)
    sales_executive = models.BooleanField(default=False)
    service_executive = models.BooleanField(default=False)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="userManagement_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="userManagement_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        history_list = {
            "user": "User",
            "department": "Department",
            "role": "Role",
            "profile": "Profile",
            "user_group": "User Group",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", UserManagement, history_list)
            super(UserManagement, self).save(*args, **kwargs)
        elif self.pk is None:
            super(UserManagement, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", UserManagement, history_list)
        return instance

class Employee(models.Model):
    employee_id = models.CharField(max_length=50, editable=False, unique=True, null=True, blank=True)
    employee_name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    user_profile = models.ForeignKey(Imagedata, on_delete=models.SET_NULL, null=True, blank=True)
    document = models.ManyToManyField(Document, blank=True)
    user = models.ForeignKey(UserManagement, on_delete=models.PROTECT, null=True, blank=True,
                            related_name="Employee_user_id")
    education_qualification = models.CharField(max_length=50, null=True, blank=True)
    designation = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=16, validators=[phone_Validator], null=True, blank=True)
    alt_mobile = models.CharField(max_length=16, validators=[phone_Validator], null=True, blank=True)
    aadhaar_no = models.CharField(
        max_length=12,
        validators=[aadhaar_validator],
        null=True, blank=True
    )
    pan_no = models.CharField(
        max_length=10,
        validators=[pan_validator],
        null=True, blank=True
    )
    work_start_time = models.TimeField(null=True, blank=True)
    work_end_time = models.TimeField(null=True, blank=True)
    working_hours = models.FloatField(null=True, blank=True)
    week_off_days = models.CharField(max_length=100, null=True, blank=True)
    uan_no = models.CharField(max_length=50, null=True, blank=True)
    esi_no = models.CharField(max_length=15, validators=[esi_validator], null=True, blank=True)
    employee_education = models.CharField(max_length=100, null=True, blank=True)
    experience_year = models.IntegerField(null=True, blank=True)
    experience_months = models.IntegerField(null=True, blank=True)
    training = models.CharField(max_length=250, null=True, blank=True)
    present_address = models.ForeignKey(CompanyAddress, on_delete=models.CASCADE, null=True, blank=True)
    permanent_address = models.ForeignKey(CompanyAddress, on_delete=models.CASCADE,
                                          null=True, blank=True, related_name='premanent_address')
    remark = models.CharField(max_length=50, null=True, blank=True)
    bank_account_no = models.CharField(max_length=25, null=True, blank=True)
    ifsc_code = models.CharField(max_length=25, null=True, blank=True)
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    branch = models.CharField(max_length=50, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="Employee_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="Employee_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        if self.aadhaar_no and Employee.objects.exclude(pk=self.pk).filter(aadhaar_no__iexact=self.aadhaar_no).exists():
            raise ValidationError("Aadhaar no must be unique.")
        if self.pan_no and Employee.objects.exclude(pk=self.pk).filter(pan_no__iexact=self.pan_no).exists():
            raise ValidationError("Pan No must be unique.")
        if self.employee_name and Employee.objects.exclude(pk=self.pk).filter(
                employee_name__iexact=self.employee_name).exists():
            raise ValidationError("Employee Name must be unique.")
        if self.email and Employee.objects.exclude(pk=self.pk).filter(email__iexact=self.email).exists():
            raise ValidationError("Email must be unique.")
        if self.uan_no and Employee.objects.exclude(pk=self.pk).filter(uan_no__iexact=self.uan_no).exists():
            raise ValidationError("UAN NO must be unique.")
        if self.esi_no and Employee.objects.exclude(pk=self.pk).filter(esi_no__iexact=self.esi_no).exists():
            raise ValidationError("ESI NO must be unique.")

        if self.id is None:
            starting_id = "00001"
            employee_prefix = "STEMP"
            filter_conditions = "employee"
            last_serial_id_record = ManualIdSeries.objects.filter(
                name__iexact=filter_conditions).first()
            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.employee_id = f'{employee_prefix}{new_serial_id:04}'
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name=filter_conditions, id_series=new_serial_id,
                                              created_by=self.created_by)
        history_list = {
            "employee_id": "Employee Id",
            "employee_name": "Employee Name",
            "department": "Department",
            "education_qualification": "Education Qualification",
            "designation": "Designation",
            "email": "Email",
            "mobile": "Mobile",
            "alt_mobile": "Alternate Number",
            "aadhaar_no": "Aadhaar Number",
            "pan_no": "Pan Number",
            "present_address": "Present Address",
            "permanent_address": "Premanent Address",
            "remark": "Remark",
            "bank_account_no": "Bank Account Number",
            "ifsc_code": "IFSC",
            "bank_name": "Bank Name",
            "branch": "Branch"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Employee, history_list)
            super(Employee, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Employee, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Employee, history_list)

        return instance

    def delete(self, *args, **kwargs):
        # Ensure documents are deleted before the Employee object is deleted
        if self.document.exists():
            self.document.all().delete()
        if self.history_details.exists():
            self.history_details.all().delete()
        if self.present_address:
            self.present_address.delete()
        if self.permanent_address:
            self.permanent_address.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.employee_id

class ExpenseRequest(models.Model):
    expense_request_no = models.CharField(max_length=30, null=True,
                                        blank=True)
    expense_request_date = models.DateField()
    employee_name = models.ForeignKey(Employee, on_delete=models.PROTECT)
    request_amount = models.DecimalField(max_digits=10, decimal_places=3)
    expense_for = models.TextField(null=True, blank=True)
    is_cancel = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, related_name="ExpenseRequest_approved_by", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    pay_by = models.ForeignKey(User, related_name="ExpenseRequest_pay_by", on_delete=models.PROTECT, null=True,
                            blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ExpenseRequest_modified", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ExpenseRequest_created", on_delete=models.PROTECT, null=True,
                                blank=True)

    def save(self, *args, **kwargs):
        if self.id is None:
            starting_id = "00001"
            employee_prefix = "ESTRQ"
            filter_conditions = "ExpenseRequest"
            last_serial_id_record = ManualIdSeries.objects.filter(
                name__iexact=filter_conditions).first()
            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.expense_request_no = f'{employee_prefix}{new_serial_id:04}'
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name=filter_conditions, id_series=new_serial_id,
                                              created_by=self.created_by)
        history_list = {
            "expense_request_no": "Expense Request No",
            "expense_request_date": "Expense Request Date",
            "request_amount": "Request Amount",
            "expense_for": "Expense For",
            "is_cancel": "Is Cancel",
            "approved_by": "Approved By",
            "pay_by": "Pay By",
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ExpenseRequest, history_list)
            super(ExpenseRequest, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ExpenseRequest, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ExpenseRequest, history_list)
        return instance

class ExpenseCategories(models.Model):
    expense_category_name = models.CharField(max_length=50)
    account_name = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ExpenseCategories_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ExpenseCategories_created", on_delete=models.PROTECT, null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        # super(CurrencyExchange, self).save(*args, **kwargs)
        history_list = {
            "expense_category_name": "Category Name",
            "account_name": "Account Name",
            "active": "Active"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ExpenseCategories, history_list)
            super(ExpenseCategories, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ExpenseCategories, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ExpenseCategories, history_list)
        return instance

 

class PaymentVoucherAgainstInvoice(models.Model):
    payment_voucher_line = models.ForeignKey("PaymentVoucherLine", on_delete=models.CASCADE, null=True, blank=True)
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT)
    adjusted = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="PaymentVoucherAgainstInvoice_modified",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="PaymentVoucherAgainstInvoice_created", on_delete=models.PROTECT)

class PaymentVoucherAdvanceDetails(models.Model):
    payment_voucher_line = models.ForeignKey("PaymentVoucherLine", on_delete=models.CASCADE, null=True, blank=True)
    adv_remark = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    remaining = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="PaymentVoucherAdvanceDetails_modified",
                                    on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="PaymentVoucherAdvanceDetails_created", on_delete=models.PROTECT, null=True,
                                blank=True)

class PaymentVoucherLine(models.Model):
    payment_voucher = models.ForeignKey("PaymentVoucher", on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(AccountsMaster, on_delete=models.PROTECT, null=True, blank=True)
    cus_sup = models.ForeignKey(SupplierFormData, on_delete=models.PROTECT, null=True, blank=True)
    employee = models.ForeignKey("userManagement.Employee", on_delete=models.PROTECT,null=True, blank=True)
    blance_emp_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    pay_for = models.ForeignKey(AccountsMaster, related_name="PaymentVoucherLine_pay_for", on_delete=models.PROTECT,
                                null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    is_claim = models.BooleanField(default=False)
    modified_by = models.ForeignKey(User, related_name="PaymentVoucherLine_modified", on_delete=models.PROTECT,
                                    null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="PaymentVoucherLine_created", on_delete=models.PROTECT)


class PaymentVoucher(models.Model):
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    payment_voucher_no = models.ForeignKey(NumberingSeriesLinking, on_delete=models.PROTECT, null=True, blank=True)
    date = models.DateField()
    expense_request_id = models.ForeignKey(ExpenseRequest, on_delete=models.PROTECT, null=True, blank=True)
    remaining = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    pay_by = models.CharField(max_length=20, choices=PAY_BY, null=True, blank=True)
    pay_mode = models.CharField(max_length=20, choices=PAY_MODE, null=True, blank=True)
    currency = models.ForeignKey(CurrencyExchange, on_delete=models.PROTECT, 
                            null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    against_invoice = models.BooleanField(default=False)
    advance = models.BooleanField(default=False)
    bank = models.ForeignKey(AccountsMaster, related_name="PaymentVoucher_bank", on_delete=models.PROTECT, null=True,
                                blank=True)
    transfer_via = models.CharField(choices=transfer_via, null=True, blank=True)
    chq_ref_no = models.CharField(max_length=50, null=True, blank=True)
    chq_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    is_account_general_ledger_updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="PaymentVoucher_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="PaymentVoucher_created", on_delete=models.PROTECT, null=True,
                                blank=True)

    def save(self, *args, **kwargs):
        account_general_ledger= {
            'debit':{},
            "credits" : []
        }
        if not self.id:
            conditions = {'resource': 'Payment Voucher', 'default': True, }
            response = create_serial_number(conditions)
            if response['success']:
                self.payment_voucher_no = response['instance'] 
            else:
                raise CommonError(response['errors'])
 
        
        history_list = {
            "status": "Status",
            "payment_voucher_no__linked_model_id": "Payment Voucher Number",
            "Voucher Date": "Date",
            "is_claim": "Is Claim",
            "pay_to": "Pay To",
            "expense_request_id": "Expense Request",
            "remaining": "Remaining Amount",
            "pay_mode": "Payment Mode",
            "employee_id": "Employee",
            "pay_for": "Pay For",
            "emp_amount": "Employee Amount",
            "blance_emp_amount": "Balance Employee Amount",
            "cus_sup_id": "Customer/Supplier",
            "cus_sup_amount": "Customer/Supplier Amount",
            "against_invoice": "Against Invoice",
            "advance": "Advance",
            "bank": "Bank",
            "transfer_via": "Transfer Via",
            "chq_ref_no": "Cheque Reference Number",
            "chq_date": "Cheque Date",
            "modified_by": "Modified By",
            "created_by": "Created By",
            "created_at": "Created At",
            "updated_at": "Updated At"
        }
        
        if self.status.name == "Submit" and not self.is_account_general_ledger_updated:
            from userManagement.services.serivece_class import payment_voucher_genral_update
            from itemmaster.models import PurchasePaidDetails
            receivable_account = None
            if self.pay_by == "Supplier & Customer":
                receivable_account = company_info().receivable_account
                if not receivable_account:
                    raise CommonError(["Receivable account not found in company master."])
            credits = []
            for pv_line in self.paymentvoucherline_set.all():
                if self.pay_by == "Supplier & Customer":
                    credits.append({
                    "date": self.date,
                    "voucher_type": "Payment Voucher",
                    "payment_voucher_no": self.id,
                    "account": receivable_account.id ,
                    "credit": (pv_line.amount or 0),
                    "customer_supplier" : pv_line.cus_sup.id,
                    "purchase_account" :  None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
                elif self.pay_by == "Employee":
                    credits.append({
                    "date": self.date,
                    "voucher_type": "Payment Voucher",
                    "payment_voucher_no": self.id,
                    "account": pv_line.pay_for.id,
                    "credit": (pv_line.amount or 0),
                    "employee":pv_line.employee.id,
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
                else:
                    credits.append({
                    "date": self.date,
                    "voucher_type": "Payment Voucher",
                    "payment_voucher_no": self.id,
                    "account": pv_line.account.id ,
                    "credit": (pv_line.amount or 0),
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": "",
                    "created_by": self.created_by.pk,
                    })
            account_general_ledger['credits'] = credits
            account_general_ledger['debit'] = {
                    "date": self.date,
                    "voucher_type": "Payment Voucher",
                    "payment_voucher_no": self.id,
                    "account": self.bank.id ,
                    "debit": (self.total_amount or 0),
                    "purchase_account" : None,
                    "purchase_amount" :0,
                    "remark": self.remark,
                    "created_by": self.created_by.pk,
                    }
            result = payment_voucher_genral_update(account_general_ledger)
            if not result['success']:
                raise CommonError(result['errors'])
            else:
                self.is_account_general_ledger_updated = True
        
        if self.status.name == "Canceled" and self.is_account_general_ledger_updated:
            agl_qs = AccountsGeneralLedger.objects.filter(payment_voucher_no=self.id)
            if agl_qs.exists():
                # bulk delete
                agl_qs.delete()

            sales_paid = PurchasePaidDetails.objects.filter(payment_voucher=self.id)
            if sales_paid.exists():
                sales_paid.delete()
        
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", PaymentVoucher, history_list)
            super(PaymentVoucher, self).save(*args, **kwargs)
        elif self.pk is None:
            super(PaymentVoucher, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", PaymentVoucher, history_list)
        return instance
    

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)

class ExpenseReconciliationDetails(models.Model):
    paymentVoucher_id = models.ForeignKey(PaymentVoucher, on_delete=models.PROTECT, null=True, blank=True)
    adjusted_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ExpenseReconciliationDetails_modified",
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ExpenseReconciliationDetails_created", on_delete=models.PROTECT,
    null=True,
    blank=True)

class ExpenseClaimDetails(models.Model):
    date_of_exp = models.DateField()
    expense_categories = models.ForeignKey(ExpenseCategories, on_delete=models.PROTECT)
    descriptions = models.CharField(max_length=50)
    claim_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    gst_in = models.BooleanField(default=False)
    pdf_url = models.ManyToManyField(Document, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ExpenseClaimDetails_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ExpenseClaimDetails_created", on_delete=models.PROTECT,
                                   null=True,
                                   blank=True)

class ExpenseClaim(models.Model):
    expense_claim_no = models.CharField(max_length=50, null=True, blank=True)
    expense_claim_date = models.DateField()
    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT)
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    expense_claim_details = models.ManyToManyField(ExpenseClaimDetails)
    expense_reconciliation_details = models.ManyToManyField(ExpenseReconciliationDetails, blank=True)
    total_approved_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reimburse_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name="ExpenseClaim_modified", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_by = models.ForeignKey(User, related_name="ExpenseClaim_created", on_delete=models.PROTECT,
                                   null=True,
                                   blank=True)

    def save(self, *args, **kwargs):
        if self.id is None:
            starting_id = "00001"
            ExpenseClaimDetails_prefix = "ESTEC"
            filter_conditions = "ExpenseClaimDetails"
            last_serial_id_record = ManualIdSeries.objects.filter(
                name__iexact=filter_conditions).first()
            if last_serial_id_record:
                last_serial_id = last_serial_id_record.id_series
                new_serial_id = int(last_serial_id) + 1
            else:
                new_serial_id = int(starting_id)
            self.expense_claim_no = f'{ExpenseClaimDetails_prefix}{new_serial_id:04}'
            if last_serial_id_record:
                last_serial_id_record.id_series = new_serial_id
                last_serial_id_record.save()
            else:
                ManualIdSeries.objects.create(name=filter_conditions, id_series=new_serial_id,
                                              created_by=self.created_by)
        history_list = {
            "status": "Status",
            "expense_claim_no":"Expense Claim No",
            "expense_claim_date":"Expense Claim Date",
            "employee_id__employee_id":"Employee Id",
            "total_approved_amount":"Total Approved Amount",
            "reimburse_amount":"Reimburse Amount",
            "balance_amount":"Balance Amount",
            "modified_by": "Modified By",
            "created_by": "Created By",
            "created_at": "Created At",
            "updated_at": "Updated At"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", ExpenseClaim, history_list)
            super(ExpenseClaim, self).save(*args, **kwargs)
        elif self.pk is None:
            super(ExpenseClaim, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", ExpenseClaim, history_list)
        return instance
    

    def delete(self, *args, **kwargs):
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)
        super(ExpenseClaim, self).save(*args, **kwargs)
        return self

class Holidays(models.Model):
    name = models.CharField(max_length=50)
    no_of_days = models.DecimalField(max_digits=5, decimal_places=0)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="createdHolidays", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modifiedHolidays", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "name": 'Name',
            "no_of_days": "Number Of Days",
            "from_date": "From Date",
            "to_date": "To Date"
        }
        print("self.pk", self.pk)
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Holidays, history_list)
            super(Holidays, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Holidays, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Holidays, history_list)
        return instance

    def __str__(self):
        return f"{self.name}"

class LeaveType(models.Model):
    name = models.CharField(max_length=50)
    leave_type = models.CharField(choices=leave_type, max_length=20)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="createdLeaveType", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modifiedLeaveType", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "name": "Name",
            "leave_type": "Leave Type"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", LeaveType, history_list)
            super(LeaveType, self).save(*args, **kwargs)
        elif self.pk is None:
            super(LeaveType, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", LeaveType, history_list)
        return instance

    def __str__(self):
        return self.name

class LeaveAlloted(models.Model):
    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    allotted_days = models.DecimalField(max_digits=5, decimal_places=0)
    taken_leave = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="createdLeaveAlloted", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modifiedLeaveAlloted", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        print("self.pk", self)
        history_list = {
            "employee_id": "Employee Id",
            "leave_type": "Leave Type",
            "from_date": "From Date",
            "to_date": "To Date",
            "allotted_days": "Number of Days",
            "taken_leave": "Taken Leave"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", LeaveAlloted, history_list)
            super(LeaveAlloted, self).save(*args, **kwargs)
        elif self.pk is None:
            super(LeaveAlloted, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", LeaveAlloted, history_list)
        return instance

class Leave(models.Model):
    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True)
    leave_day_type = models.CharField(choices=leave_day_type, max_length=10)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    applied_days = models.DecimalField(max_digits=5, decimal_places=0, null=True)
    reason = models.CharField(max_length=250)
    approved_days = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True)
    leave_alloted = models.ForeignKey(LeaveAlloted, on_delete=models.PROTECT, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=5, decimal_places=0, null=True)
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="createdLeave", on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, related_name="modifiedLeave", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "employee_id": "Employee Id",
            "leave_day_type": "Half / Full Day",
            "from_date": "From Date",
            "to_date": "To Date",
            "applied_days": "Applied Days",
            "reason": "Reason",
            "approved_days": "Approved Days",
            "leave_alloted": "Leave Alloted",
            "current_balance": "Current Balance",
            "status": "Status"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Leave, history_list)
            super(Leave, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Leave, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Leave, history_list)
        return instance

class AttendanceRegister(models.Model):
    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    work_hours = models.TimeField(null=True, blank=True)
    over_time_hours = models.TimeField(null=True, blank=True)
    break_hours = models.TimeField(null=True, blank=True)
    late_in_hours = models.TimeField(null=True, blank=True)
    late_out_hours = models.TimeField(null=True, blank=True)
    break_intervals = models.JSONField(null=True, blank=True)
    # check_in_location = models.CharField(max_length=100, null=True, blank=True)
    # check_out_location = models.CharField(max_length=100, null=True, blank=True)
    status = models.ForeignKey(CommanStatus, on_delete=models.PROTECT)
    leave = models.ForeignKey(Leave, on_delete=models.PROTECT, null=True, blank=True)
    holidays = models.ForeignKey(Holidays, on_delete=models.PROTECT, null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    # created_by = models.ForeignKey(User, related_name="createdAttendanceRegister", on_delete=models.PROTECT, )
    modified_by = models.ForeignKey(User, related_name="modifiedAttendanceRegister", on_delete=models.PROTECT,
                                    null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        history_list = {
            "employee_id": "Employee Id",
            "date": "Date",
            "check_in": "Check In",
            "check_out": "Check Out",
            "work_hours": "Work Hours",
            "break_hours": "Break Hours",
            "over_time_hours": "Over Time Hours",
            "late_in_hours": "Late In Hours",
            "late_out_hours": "Late Out Hours",
            # "check_in_location":"Check In Location",
            # "check_out_location":"Check Out Location",
            "status": "Status",
            "leave": "Leave",
            "holidays": "Holidays"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", AttendanceRegister, history_list)
            super(AttendanceRegister, self).save(*args, **kwargs)
        elif self.pk is None:
            super(AttendanceRegister, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", AttendanceRegister, history_list)
        return instance

# from django.core.cache import cache
#
# def get_all_subordinates(user):
#     cache_key = f"subordinates_of_user_{user.id}"
#     cached_data = cache.get(cache_key)
#     if cached_data is not None:
#         return cached_data
#
#     visited = set()
#     result = set()
#
#     def recurse(current_user):
#         if current_user.id in visited:
#             return
#         visited.add(current_user.id)
#         try:
#             role_entry = RoleWiseHierarchical.objects.select_related('user').prefetch_related('blow_workers').get(user=current_user)
#         except RoleWiseHierarchical.DoesNotExist:
#             return
#         subordinates = role_entry.blow_workers.all()
#         for subordinate in subordinates:
#             result.add(subordinate.user)
#             recurse(subordinate.user)
#
#     recurse(user)
#     result_list = list(result)
#     cache.set(cache_key, result_list, timeout=21600)  # 6 hours = 21600 seconds
#     return result_list
#
# from django.db.models.signals import post_save, m2m_changed
# from django.dispatch import receiver
#
# @receiver(post_save, sender=RoleWiseHierarchical)
# def clear_hierarchy_cache_on_save(sender, instance, **kwargs):
#     cache_key = f"subordinates_of_user_{instance.user.id}"
#     cache.delete(cache_key)
#
# @receiver(m2m_changed, sender=RoleWiseHierarchical.blow_workers.through)
# def clear_hierarchy_cache_on_m2m_change(sender, instance, **kwargs):
#     cache_key = f"subordinates_of_user_{instance.user.id}"
#     cache.delete(cache_key)
