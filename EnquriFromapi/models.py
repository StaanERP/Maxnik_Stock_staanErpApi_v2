from django.db import models
from itemmaster2.models import *
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from itemmaster.models import ContactDetalis, SaveToHistory, Districts, Pincode, States, Store

from django.contrib.auth.models import AbstractUser
from importlib import import_module

from itemmaster2.models import Activites, EmailRecord, Notes

status_ = (
    ("Not Contacted", "Not Contacted"),
    ("Converted To Lead", "Converted To Lead"),
    ('Junk', "Junk"),
    ('Inprogress', "Inprogress"),
)
class Conferencedata(models.Model):
    name = models.CharField(max_length=50)
    in_charge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="incharge")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=True)
    additional_in_charges = models.ManyToManyField(User, blank=True)
    default_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, swappable=True)
    currency = models.ForeignKey(CurrencyExchange , on_delete=models.SET_NULL, null=True, blank=True, swappable=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_Conferencedata")
    modified_by = models.ForeignKey(User, related_name="modified_Conferencedata", on_delete=models.PROTECT, null=True,
                                    blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = self.name
        history_list={
           "name":"Name",
           "in_charge":"In Charge",
           "start_date":"Start Date",
           "end_date":"End Date",
           "status":"Status",
           "default_store":"Default Store",
           "currency":"Currency"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", Conferencedata,history_list)
            super(Conferencedata, self).save(*args, **kwargs)
        elif self.pk is None:
            super(Conferencedata, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", Conferencedata,history_list)
        return  self
    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Explicitly delete related AllowedPermission instances if needed
        if self.history_details.exists():
            self.history_details.all().delete()
        super().delete(*args, **kwargs)



class product(models.Model):
    Name = models.CharField(max_length=50)
    whatsapps_template = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.Name


class enquiryDatas(models.Model):
    name = models.CharField(max_length=50)
    organization_name = models.CharField(max_length=200, null=True, blank=True)
    link_contact_detalis = models.ForeignKey(ContactDetalis, on_delete=models.PROTECT, null=True, blank=True)
    activity = models.ManyToManyField(Activites,blank=True)
    call_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    task_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    meeting_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    mail_count = models.DecimalField(max_digits=10, decimal_places=0,null=True, blank=True)
    note=models.ManyToManyField(Notes,blank=True)
    email = models.EmailField(null=True, blank=True)
    email_record=models.ManyToManyField(EmailRecord,blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?9?1?\s?-?\d{1,}-?\s?\d{1,}',
        message="Phone number must be entered in the format: '+91-1234567890' or '091 1234 567890'. Up to 15 digits "
                "allowed."
    )
    alternate_mobile_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?9?1?\s?-?\d{1,}-?\s?\d{1,}',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        null=True,
        blank=True
    )
    status = models.CharField(max_length=50, choices=status_)
    mobile_number = models.CharField(validators=[phone_regex], max_length=17)
    other_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    message = models.CharField(max_length=500, blank=True)
    interests = models.ManyToManyField(product, blank=True)
    conference_data = models.ForeignKey(Conferencedata, on_delete=models.SET_NULL, null=True, blank=True)
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    pincode = models.ForeignKey(Pincode , null=True, blank=True, on_delete=models.CASCADE)
    district = models.ForeignKey(Districts, null=True, blank=True, on_delete=models.CASCADE)
    state = models.ForeignKey(States, null=True, blank=True, on_delete=models.CASCADE)
    over_due = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    counter = models.CharField(null=True, blank=True, max_length=50)
    follow_up = models.DateField(null=True, blank=True)
    history_details = models.ManyToManyField(ItemMasterHistory, blank=True)
    created_by = models.ForeignKey(User, related_name="created_Enquiry", on_delete=models.PROTECT, null=True,
                                   blank=True)
    modified_by = models.ForeignKey(User, related_name="modified_Enquiry", on_delete=models.PROTECT, null=True,
                                    blank=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Name: " + self.name + " , " + "Organization : " + self.organization_name
    
    def save(self, *args, **kwargs):
        # super(CurrencyExchange, self).save(*args, **kwargs)
        history_list={
           "name":"Name",
           "organization_name":"Hospital/Company",
           "email":"Email",
           "mobile_number":"Mobile Number",
           "alternate_mobile_number":"Whatsapp Number",
           "other_number":"Other Number",
           "pincode":"Pincode",
           "district":"District",
           "state":"State",
           "counter":"Country",
           "interests":"Interests",
           "sales_person":"Sales Person",
           "follow_up":"Next Follow up",
           "conference_data":"Source",
           "message":"Requirements",
           "remarks":"Remarks"
        }
        if self.pk is not None:
            instance = SaveToHistory(self, "Update", enquiryDatas,history_list)
            super(enquiryDatas, self).save(*args, **kwargs)
        elif self.pk is None:
            super(enquiryDatas, self).save(*args, **kwargs)
            instance = SaveToHistory(self, "Add", enquiryDatas,history_list)
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


class UserPermission(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_sales_person = models.BooleanField(default=False)
    is_admin_person = models.BooleanField(default=False)
    is_enquiry_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user_id.username + "____" + str(self.id) + ",   " + str(self.user_id.id)

