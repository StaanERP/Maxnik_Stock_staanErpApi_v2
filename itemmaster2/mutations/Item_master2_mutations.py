import base64
from num2words import num2words
import graphene
from _decimal import ROUND_DOWN
import datetime
from ..schema.item_master2_schema import *
from ..models import *
from django.db.models import ProtectedError
from ..Serializer import *
from EnquriFromapi.models import *
from itemmaster.Utils.CommanUtils import *
from itemmaster2.PDF.Quotations.QuotationsPDF import *
from itemmaster.mutations.Item_master_mutations import *
from userManagement.models import *
from django.apps import apps
import re
from bs4 import BeautifulSoup
from itemmaster2.services.salesorder_delivery_challan_service import  *
from itemmaster2.services.sales_invoice_services import *
from itemmaster2.services.quotation_serives import *
from docx import Document as Documentpdf
import platform
from itemmaster2.services.salesorder_serives import *
from itemmaster2.services.direct_sales_invoice_services import *
from itemmaster2.services.sales_return_serives import *
from itemmaster2.services.serivece_class import *


def add_contact_into_supplier(enquiry, customer):
    # add enquiry contact into CUSTOMER
    enquiry_data = enquiryDatas.objects.filter(
        id=enquiry).first()  # Use .first() to get a single object
    if enquiry_data:
        contact_link_id = enquiry_data.link_contact_detalis

        if contact_link_id:
            supplier_data = SupplierFormData.objects.filter(id=customer).first()  # Get the supplier data
            if supplier_data:
                # Check if contact_link_id exists in the supplier's contacts
                contacts = supplier_data.contact.all()  # Get all contacts
                supplier_data.contact.add(contact_link_id)
            else:
                return "Supplier data not found"


from django.core.exceptions import ObjectDoesNotExist

from decimal import Decimal, ROUND_DOWN


def getItemCombo(itemmaster_id, amount, qty):
    """use to get item combo data"""
    isItemCombo = False
    itemCombo_list = []

    try:
        itemMaster = ItemMaster.objects.get(id=itemmaster_id)
    except ObjectDoesNotExist:
        return isItemCombo, itemCombo_list
    try:
        if itemMaster.item_combo_bool:
            isItemCombo = True

            # Calculate total value of mandatory items
            mandatory_items = [
                item for item in itemMaster.item_combo_data.all() if item.is_mandatory
            ] 
            total_value = sum(
                Decimal(item.part_number.item_mrp) * Decimal(item.item_qty)
                for item in mandatory_items
            )
            # for item in mandatory_items:
            #     print(item,item.part_number.item_mrp, item.item_qty )
            rounded_final_total = round(Decimal(amount), 2) / qty
            # if total_value == 0:
            #     return isItemCombo, itemCombo_list
            # Calculate total discount needed
            total_discount_needed = total_value - rounded_final_total

            # Calculate contributions and ratios
            item_contributions = [
                Decimal(item.part_number.item_mrp) * item.item_qty for item in mandatory_items
            ]
        
            ratios = [contribution / total_value for contribution in item_contributions]

            # Calculate the discount for each item
            discounts = [total_discount_needed * ratio for ratio in ratios] 
            try:
                for item in itemMaster.item_combo_data.all():
                    original_price = Decimal(item.part_number.item_mrp) * item.item_qty
                    changed_qty = item.item_qty * qty

                    data = {
                        "parent":{
                            "id":item.id
                        },
                        'itemmaster': {
                            "id": item.part_number.id,
                            'itemPartCode': item.part_number.item_part_code,
                            'itemName': item.part_number.item_name,
                        },
                        "rate": str(original_price.quantize(Decimal('0.000'))),
                        "qty": str(changed_qty),
                        'uom': {
                            "id": item.part_number.item_uom.id,
                            "name": item.part_number.item_uom.name
                        },
                        'display': item.item_display.display if item.item_display else None,
                        'isMandatory': item.is_mandatory,
                    }
                    if item.is_mandatory:
                        index = mandatory_items.index(item)  # Find the index of the current item in mandatory_items
                        discounted_amount = original_price - discounts[index]
                        discounted_amount = max(discounted_amount, Decimal('0.00')).quantize(Decimal('0.000'),
                                                                                            rounding=ROUND_DOWN)
                        after_discount_value_for_per_item = (discounted_amount / item.item_qty).quantize(Decimal('0.000'),
                                                                                                        rounding=ROUND_DOWN)
                        changed_amount = (discounted_amount / item.item_qty) * changed_qty
                        data["afterDiscountValueForPerItem"] = str(after_discount_value_for_per_item)
                        data['amount'] = str(changed_amount)
                    else:
                        data["afterDiscountValueForPerItem"] = 0
                        data['amount'] = str(0)

                    itemCombo_list.append(data)

                # Ensure the total of the amounts matches the original parameter amount
                total_calculated_amount = sum(Decimal(data['amount']) for data in itemCombo_list)
                if total_calculated_amount != rounded_final_total:
                    print(
                        f"Warning: The total calculated amount {total_calculated_amount} does not match the parameter amount {amount}.")
                return isItemCombo, itemCombo_list, ""
            except Exception as e:
                return False, [], f"{str(e)}"
    except Exception as e:
        return e
    return False, [], f"{str(e)}"


"""Activities start"""

class NoteCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        note = graphene.String()
        modal_id = graphene.Int()
        created_by = graphene.Int()
        modified_by = graphene.Int()
        app_name = graphene.String()
        modal_name = graphene.String()

    notes_instance = graphene.Field(Notes_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        notes_instance = None
        success = False
        errors = []

        # Check if updating an existing call log
        if 'id' in kwargs and kwargs['id']:
            try:
                notes_instance = Notes.objects.get(id=kwargs['id'])
                serializer = NotesSerializer(notes_instance, data=kwargs, partial=True)
            except Notes.DoesNotExist:
                errors.append("CallLog not found.")
                return NoteCreateMutation(success=success, errors=errors, notes_instance=notes_instance)
        else:
            serializer = NotesSerializer(data=kwargs)

        if serializer.is_valid():
            try:
                instance = serializer.save()
                notes_instance = instance
                success = True
                try:
                    app_name = kwargs.get('app_name')
                    modal_name = kwargs.get('modal_name')
                    modal_id = kwargs.get('modal_id')
                    if app_name and modal_name and modal_id:
                        ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                        query = ModelClass.objects.get(id=modal_id)
                        try:
                            existing_notes = list(query.note.all())
                            existing_notes.append(notes_instance)
                            query.note.set(existing_notes)
                            query.save()
                            success = True
                        except Exception as e:
                            print(e, "e----")
                    else:
                        success = False
                except Exception as e:
                    errors.append(str(e))

            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return NoteCreateMutation(success=success, errors=errors, notes_instance=notes_instance)

class NoteDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            notes_instance = Notes.objects.get(id=id)
            notes_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return NoteDeleteMutation(success=success, errors=errors)

class ActivityTypeCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        time_tracking = graphene.Boolean()
        due_date = graphene.Boolean()
        geotagging = graphene.Boolean()
        participants = graphene.Boolean()
        remainder_mail = graphene.Boolean()
        status = graphene.Boolean()
        active = graphene.Boolean()
        icon = graphene.String()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    activity_type_instance = graphene.Field(ActivityType_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Activites", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        # Access the request object from the context
        result = commanSaveAllModel(ActivityType, kwargs, ActivityTypeSerializer, "Activity Type")
        if result['success']:
            return ActivityTypeCreateMutation(success=result['success'],
                                              errors=result['errors'],
                                              activity_type_instance=result['instance'])
        else:
            return ActivityTypeCreateMutation(success=result['success'],
                                              errors=result['errors'],
                                              activity_type_instance=result['instance'])

class ActivityTypeDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Activites", create_action="Save", edit_action="Edit")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            activity_instance = ActivityType.objects.get(id=id)
            activity_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ActivityTypeDeleteMutation(success=success, errors=errors)

def get_meeting_activity_count(activity_queryset):
    """
    Filters meeting activities based on status and relevant date fields.
    Returns the count of unique activities that qualify as meetings.
    Returns 0 if any database error occurs.
    """
    try:
        return activity_queryset.filter(
            status__isnull=False
        ).filter(
            Q(planned_start_date_time__isnull=False) |
            Q(planned_end_date_time__isnull=False) |
            Q(actual_start_date_time__isnull=False) |
            Q(actual_end_date_time__isnull=False) |
            Q(due_date_time__isnull=False)
        ).distinct().count()

    except Exception as e:
        return 0
    
def update_follow_up_and_status_enquiry(instance,status_instance,operation="Edit"):
    """
    Update follow_up, last_activity, and over_due for Enquiry and Leads models
    based on related activities.
    """
    current_date = datetime.today().date()
    next_follow_up = None
    try:
        if isinstance(instance, enquiryDatas):
            activitys = instance.activity.all()

            # Handle deletion: exclude the activity being deleted
            if operation == "Delete":
                activitys = activitys.exclude(id=status_instance.id)

            filtered_activities = [activity for activity in activitys if
                                activity.pass_wanted_date() and activity.pass_wanted_date() >= current_date]
            if filtered_activities:
                next_follow_up = min(activity.pass_wanted_date() for activity in filtered_activities)
                instance.follow_up = next_follow_up
            else:
                instance.follow_up = None
            if operation == "Edit" and status_instance.status and status_instance.status.name == "Completed":
                instance.last_activity = timezone.now()
            instance.over_due = any(activity.over_due for activity in activitys)

            if operation == "Delete":
                 return {"instance": instance, "next_follow_up": next_follow_up}
            return instance
            

    except Exception as e:
        print(f"[ERROR] Updating follow_up and status: {e}")

def update_follow_up_and_status_leads(instance, enquiry, activity_instance, operation="Edit"):
    """
    Update rext_follow_up, last_activity, and over_due for Leads model
    based on related activities and associated Enquiry (if exists).
    """
    current_date = datetime.today().date()
    next_follow_up = None
    try:
        if isinstance(instance, Leads):
            # Start with lead's own activities
            activitys = list(instance.activity.all())
            # Merge enquiry's activities if related
            if instance.Enquiry and enquiry and instance.Enquiry.id == enquiry.id:
                activitys += list(enquiry.activity.all())

            # Remove duplicates
            activitys = list({act.id: act for act in activitys}.values())
            # Exclude deleted activity if operation is "Delete"
            if operation == "Delete":
                activitys = [act for act in activitys if act.id != activity_instance.id]

            # Filter for valid future/ongoing activities
            filtered_activities = [
                activity for activity in activitys
                if activity.pass_wanted_date() and activity.pass_wanted_date() >= current_date
            ]
            next_follow_up = min(
                (activity.pass_wanted_date() for activity in filtered_activities),
                default=None
            )
            # Update rext_follow_up
            instance.rext_follow_up = next_follow_up

            # Update overdue always (not just on Edit)
            instance.over_due = any(activity.over_due for activity in activitys)

            # Update last_activity only on Edit with completed status
            if operation == "Edit" and activity_instance.status and activity_instance.status.name == "Completed":
                instance.last_activity = timezone.now()

            if operation == "Delete":
                 return {"instance": instance, "next_follow_up": next_follow_up}
            
            return instance

    except Exception as e:
        print("Error in update_follow_up_and_status_leads:", e)
        return instance



class ActivityCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        activity_type = graphene.Int()
        status = graphene.String()
        subject = graphene.String()
        outcome = graphene.String()
        assigned = graphene.Int()
        planned_start_date_time = graphene.DateTime()
        planned_end_date_time = graphene.DateTime()
        actual_start_date_time = graphene.DateTime()
        actual_end_date_time = graphene.DateTime()
        due_date_time = graphene.DateTime()
        user_participants = graphene.List(graphene.Int)
        customer_participants = graphene.List(graphene.Int)
        Contact = graphene.Int()
        customer = graphene.Int()
        remainder_mail = graphene.Boolean()
        email_templete = graphene.Int()
        actual_email = graphene.JSONString()
        created_by = graphene.Int()
        modified_by = graphene.Int()
        app_name = graphene.String()
        modal_name = graphene.String()
        modal_id = graphene.String()

    Activity_instance = graphene.Field(Activity_Type)
    enquiry_instatce = graphene.Field(EnquiryDataType)
    leads_instatce = graphene.Field(Leads_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Activites", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        request = info.context
        access_token = str(request.headers.get('Authorization')).replace("JWT ", "")
        enquiry_instatce = None
        leads_instatce = None
        success = False
        errors = []
        instance_ = None
        serializer_ = None
        start_time = None
        end_time = None
        kwargs["over_due"] = False
        if "status" in kwargs and kwargs['status']:
            try:
                status = CommanStatus.objects.filter(name=kwargs['status'], table="Activites").first()
                kwargs['status'] = status.id
            except ObjectDoesNotExist:
                return ActivityCreateMutation(success=False,
                                              errors=["status Does Not Exist"],
                                              Activity_instance=None)
        if "id" in kwargs and kwargs.get('id'):
            try:
                model_instance = Activites.objects.get(id=kwargs['id'])
                serializer_ = ActivitySerializer(model_instance, data=kwargs, partial=True)
                start_time = model_instance.planned_start_date_time
                end_time = model_instance.planned_end_date_time
            except Activites.DoesNotExist:
                errors.append(f"Activites with id {kwargs['id']} not found.")
                return ActivityCreateMutation(success=success,
                                              errors=errors,
                                              Activity_instance=instance_)
        else:
            serializer_ = ActivitySerializer(data=kwargs)
        if serializer_.is_valid():
            try:
                instance_ = serializer_.save()
                success = True
                app_name = kwargs.get('app_name', None)
                modal_name = kwargs.get('modal_name', None)
                modal_id = kwargs.get('modal_id', None)
                if app_name and modal_name and modal_id:
                    ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                    query = ModelClass.objects.get(id=modal_id)
                    try:
                        existing_activity = list(query.activity.all())
                        existing_activity.append(instance_)
                        query.activity.set(existing_activity)
                        query.save()
                        # Fetch "Completed" status for filtering
                        completed_status = CommanStatus.objects.filter(name="Completed", table="Activites").first()
                        if modal_name == "enquiryDatas" and app_name == "EnquriFromapi":
                            try:
                                enquiry_instance = enquiryDatas.objects.get(id=modal_id)
                                enquiry_activities = list(enquiry_instance.activity.all())

                                if not completed_status:
                                    errors.append("Status 'Completed' not found in CommanStatus table.")
                                else:
                                    # Initialize new counts
                                    new_meeting_count = 0
                                    new_call_count = 0
                                    new_task_count = 0
                                    # Iterate through all activities
                                    for activity in enquiry_activities:
                                        if activity.activity_type:
                                            if activity.activity_type.name == "Meeting" and activity.status == completed_status:
                                                new_meeting_count += 1
                                            elif activity.activity_type.name == "Task" and activity.status == completed_status:
                                                new_task_count += 1
                                            elif activity.activity_type.name == "Call Log":  # No status condition for Call Log
                                                new_call_count += 1

                                    # Update enquiry instance with filtered counts
                                    enquiry_instance.meeting_count = new_meeting_count
                                    enquiry_instance.call_count = new_call_count
                                    enquiry_instance.task_count = new_task_count
                                    enquiry_instance.save()

                            except enquiryDatas.DoesNotExist:
                                errors.append(f"Enquiry with id {modal_id} not found.")
                            except Exception as e:
                                errors.append(str(e))

                        if modal_name == "Leads" and app_name == "itemmaster2":
                            try:
                                leads_Datas = Leads.objects.get(id=modal_id)
                                unique_activities = set()
                                if leads_Datas.Enquiry:
                                    enquiry_activities = list(leads_Datas.Enquiry.activity.all())
                                    unique_activities.update(enquiry_activities)
                                lead_activities = list(leads_Datas.activity.all())
                                unique_activities.update(lead_activities)
                                unique_activities_queryset = Activites.objects.filter(
                                    id__in=[a.id for a in unique_activities])
                                new_meeting_count = 0
                                new_call_count = 0
                                new_task_count = 0
                                # Iterate through all activities
                                for activity in unique_activities_queryset:
                                    if activity.activity_type:
                                        if activity.activity_type.name == "Meeting" and activity.status == completed_status:
                                            new_meeting_count += 1
                                        elif activity.activity_type.name == "Task" and activity.status == completed_status:
                                            new_task_count += 1
                                        elif activity.activity_type.name == "Call Log":  # No status condition for Call Log
                                            new_call_count += 1
                                leads_Datas.meeting_count = new_meeting_count
                                leads_Datas.call_count = new_call_count
                                leads_Datas.task_count = new_task_count
                                leads_Datas.save()

                            except Leads.DoesNotExist:
                                errors.append(f"Lead with id {modal_id} not found.")
                            except Exception as e:
                                errors.append(str(e))
                        success = True
                    except Exception as e:
                        print("e",e)
                        success = False
                        errors.append(e)
                else:
                    success = True
                try:
                    if kwargs['id'] is None or instance_.status.name in ["Completed", "Canceled"]:
                        current_date = datetime.today().date()  # Simulating today's date

                        # Process Enquiry
                        enquiry = enquiryDatas.objects.filter(activity__id=instance_.id).first()
                        if enquiry:
                            enq_instance = update_follow_up_and_status_enquiry(enquiry,instance_)
                            # activitys = enquiry.activity.all()

                            # # Filter and get the minimum follow-up date
                            # filtered_activities = [activity for activity in activitys if
                            #                        activity.pass_wanted_date() and activity.pass_wanted_date() >= current_date]

                            # if filtered_activities:
                            #     enquiry.follow_up = min(activity.pass_wanted_date() for activity in filtered_activities)
                            # else:
                            #     enquiry.follow_up = None
                            # if instance_.status and instance_.status.name == "Completed":
                            #     enquiry.last_activity = timezone.now()
                            # enquiry.over_due = any(activity.over_due for activity in activitys)
                            if enq_instance:
                                enq_instance.save()
                                enquiry_instatce = enq_instance

                        # Process Leads
                        leads_Datas = Leads.objects.filter(activity__id=instance_.id).first()
                        if leads_Datas:
                            lead_ins = update_follow_up_and_status_leads(leads_Datas,enquiry,instance_)
                            # activitys = leads_Datas.activity.all()

                            # # If leads_Datas has an Enquiry linked, merge activities
                            # if leads_Datas.Enquiry and enquiry and leads_Datas.Enquiry.id == enquiry.id:
                            #     activitys = activitys | enquiry.activity.all()  # Merge two QuerySets efficiently

                            # # Filter and get the minimum follow-up date
                            # filtered_activities = [activity for activity in activitys if
                            #                        activity.pass_wanted_date() and activity.pass_wanted_date() >= current_date]
                            # if filtered_activities:
                            #     leads_Datas.rext_follow_up = min(
                            #         activity.pass_wanted_date() for activity in filtered_activities)

                            # if instance_.status and instance_.status.name == "Completed":
                            #     leads_Datas.over_due = any(activity.over_due for activity in activitys)
                            #     leads_Datas.last_activity = timezone.now()
                            if lead_ins:
                                lead_ins.save()
                                leads_instatce = lead_ins
                except Exception as e:
                    print(f"Error updating enquiry and leads: {e}")  # Better error handling
                if kwargs["id"] is None and instance_.activity_type.remainder_mail:
                    to = [user.email for user in instance_.user_participants.all()]
                    bcc = [contact.email for contact in instance_.customer_participants.all()]
                    email_body = f"""
                        Activity Scheduled {instance_.activity_type.name} for {query.name if modal_name == "enquiryDatas"
                    else query.lead_name} on ({instance_.due_date_time if instance_.due_date_time else instance_.planned_start_date_time}).
                        For more information login www.maxnikerp.com."""

                    SendMail(access_token, to, "Activity Scheduled",
                             email_body, [], bcc, "HTML", None)

                elif kwargs["id"] and instance_.activity_type.remainder_mail and (
                        (start_time != instance_.planned_start_date_time)
                        or (end_time != instance_.planned_end_date_time)):
                    to = [user.email for user in instance_.user_participants.all()]
                    bcc = [contact.email for contact in instance_.customer_participants.all()]
                    SendMail(access_token, to, instance_.email_templete.subject,
                             instance_.email_templete.email_body,
                             [], bcc, "HTML", None)

                return ActivityCreateMutation(success=success,
                                              errors=errors,
                                              Activity_instance=instance_, 
                                              enquiry_instatce=enquiry_instatce,
                                              leads_instatce=leads_instatce)
            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer_.errors.items()]

        return ActivityCreateMutation(success=success,
                                      errors=errors,
                                      Activity_instance=instance_)

class ActivityDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)


    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    enquiry_instatce = graphene.Field(EnquiryDataType)
    leads_instatce = graphene.Field(Leads_type)
    next_follow_up = graphene.Date()

    def mutate(self, info, id):
        success = False
        errors = []
        enquiry_instatce = None
        leads_instatce = None
        next_follow_up = None

        try:
            activity_instance = Activites.objects.get(id=id)

            enquiry = enquiryDatas.objects.filter(activity__id=id).first()
            lead = Leads.objects.filter(activity__id=id).first()

            # Update related enquiry before deleting the activity
            if enquiry:
                updated_enquiry_data = update_follow_up_and_status_enquiry(enquiry, activity_instance, operation="Delete")
                if updated_enquiry_data:
                    updated_enquiry_data["instance"].save()
                    enquiry_instatce = updated_enquiry_data["instance"]
                    next_follow_up = updated_enquiry_data["next_follow_up"]

            # Update related lead before deleting the activity
            if lead:
                updated_lead_data = update_follow_up_and_status_leads(lead, enquiry, activity_instance, operation="Delete")
                if updated_lead_data:
                    updated_lead_data["instance"].save()
                    leads_instatce = updated_lead_data["instance"]
                    # Only override next_follow_up if it wasn’t already set by enquiry
                    if not next_follow_up:
                        next_follow_up = updated_lead_data["next_follow_up"]

            # Delete the activity
            activity_instance.delete()
            success = True

        except ProtectedError:
            errors.append('This data is linked with other modules and cannot be deleted.')
        except Activites.DoesNotExist:
            errors.append('Activity does not exist.')
        except Exception as e:
            errors.append(str(e))

        return ActivityDeleteMutation(
            success=success,
            errors=errors,
            enquiry_instatce=enquiry_instatce,
            leads_instatce=leads_instatce,
            next_follow_up=next_follow_up
        )

class ActivityCalenderMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        activity_type = graphene.Int()
        start_date_time = graphene.String()
        end_date_time = graphene.String()
        user_id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    Activity_instance = graphene.Field(Activity_Type)
    @mutation_permission("Activites", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        activity_instance = None

        try:
            # 1. Fetch the activity
            activity_instance = Activites.objects.get(id=kwargs["id"])

            # 2. Check if status is completed or canceled
            current_status = activity_instance.status.name.lower()
            if current_status in ["completed", "canceled"]:
                return ActivityCalenderMutation(
                    success=False,
                    errors=["You cannot modify a completed or canceled activity."],
                    Activity_instance=None
                )

            # 3. Fetch the activity type
            activity_type = activity_instance.activity_type
            # 4. Update times based on activity type flags
            if activity_type:
                if activity_type.time_tracking:
                    activity_instance.planned_start_date_time = kwargs.get("start_date_time")
                    activity_instance.planned_end_date_time = kwargs.get("end_date_time")
                elif activity_type.due_date:
                    activity_instance.due_date_time = kwargs.get("start_date_time")

            # 5. Set modified_by
            try:
                user = User.objects.get(id=kwargs["user_id"])
                activity_instance.modified_by = user
            except User.DoesNotExist:
                errors.append("User not found.")

            activity_instance.save()
            success = True

        except Activites.DoesNotExist:
            errors.append("Activity not found.")

        return ActivityCalenderMutation(
            success=success,
            errors=errors,
            Activity_instance=activity_instance if success else None
        )


class EmailTempleteCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        title = graphene.String()
        resource = graphene.Int()
        active = graphene.Boolean()
        subject = graphene.String()
        email_body = graphene.String()
        mail_template = graphene.Boolean()
        whats_app_template = graphene.Boolean()
        created_by = graphene.Int(required = True)
        modified_by = graphene.Int()

    EmailTemplete_instance = graphene.Field(EmailTemplete_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    # @mutation_permission("Email_Template", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        result = commanSaveAllModel(EmailTemplete, kwargs, EmailTempleteSerializer, "EmailTemplete")
        if result['success']:
            return EmailTempleteCreateMutation(success=result['success'],
                                               errors=result['errors'],
                                               EmailTemplete_instance=result['instance'])
        else:
            return EmailTempleteCreateMutation(success=result['success'],
                                               errors=result['errors'],
                                               EmailTemplete_instance=result['instance'])


class EmailTempleteDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    # @mutation_permission("Email_Template", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            EmailTemplete_instance = EmailTemplete.objects.get(id=id)
            EmailTemplete_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return EmailTempleteDeleteMutation(success=success, errors=errors)


class ReplaceEmailTempleTags(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        app = graphene.String(required=True)
        module = graphene.String(required=True)
        template_id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    subject = graphene.String()
    body = graphene.String()

    def mutate(self, info, **kwargs):
        try:
            ModelClass = apps.get_model(app_label=kwargs['app'], model_name=kwargs['module'])
            template = EmailTemplete.objects.get(id=kwargs["template_id"])
            template_tags = template.resource.email_tags
        except Exception as e:
            return ReplaceEmailTempleTags(success=False, errors=[str(e)], subject=None, body=None)

        # Extract placeholders from email body and subject
        matches_email_body = re.findall(r"\{([a-zA-Z\s]+)\}", template.email_body)
        matches_subject = re.findall(r"\{([a-zA-Z\s]+)\}", template.subject)

        if matches_email_body or matches_subject:
            # Create a mapping of placeholders to database field names
            match_dict = {tag['label'].strip(): tag['value'] for tag in template_tags}

            # Identify which fields need to be fetched
            needed_fields = list(match_dict.values())

            if kwargs['id']: 
                # Fetch data from the model
                model_data = ModelClass.objects.filter(id=kwargs['id']).values(*needed_fields)
            else:
                 return ReplaceEmailTempleTags(success=False, errors=["No data found"], subject=None, body=None)

            if not model_data:
                return ReplaceEmailTempleTags(success=False, errors=["No data found"], subject=None, body=None)

            model_data = model_data[0]  # Extract the first (and only) dictionary

            # Replace placeholders in email body and subject
            updated_body = template.email_body
            updated_subject = template.subject

            for placeholder, field_name in match_dict.items():
                if field_name in model_data:
                    replacement_value = str(model_data[field_name])
                    updated_body = updated_body.replace(f"{{{placeholder}}}", replacement_value)
                    updated_subject = updated_subject.replace(f"{{{placeholder}}}", replacement_value)

            return ReplaceEmailTempleTags(success=True, errors=[], subject=updated_subject, body=updated_body)

        return ReplaceEmailTempleTags(success=True, errors=[], subject=template.subject, body=template.email_body)


class EmailRecordCreateMutation(graphene.Mutation):
    class Arguments:
        sent_to = graphene.List(graphene.String)
        cc = graphene.List(graphene.String)
        bcc = graphene.List(graphene.String)
        subject = graphene.String()
        email_body = graphene.String()
        modal_id = graphene.Int()
        app_name = graphene.String()
        modal_name = graphene.String()
        created_by = graphene.Int()
        files = graphene.String()

    mail_instance = graphene.Field(EmailRecord_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        mail_instance = None
        success = False
        errors = []
        request = info.context
        mail_instance = None
        access_token = str(request.headers.get('Authorization')).replace("JWT ", "")
        sent_to_list = json.loads(json.dumps(kwargs.get('sent_to', [])))
        cc_list = json.loads(json.dumps(kwargs.get('cc', [])))
        bcc_list = json.loads(json.dumps(kwargs.get('bcc', [])))
        sent_to_list_ = []
        cc_list_ = []
        bcc_list_ = []
        if sent_to_list and isinstance(sent_to_list[0], str):
            sent_to_list_ = json.loads(sent_to_list[0])
        if cc_list and isinstance(cc_list[0], str):
            cc_list_ = json.loads(cc_list[0])
        if bcc_list and isinstance(bcc_list[0], str):
            bcc_list_ = json.loads(bcc_list[0])

        # Decode the Email Body which was send as base64 format 
        try:
            decoded_email_body = base64.b64decode(kwargs['email_body']).decode("utf-8")
        except Exception as e:
            errors.append(f"Failed to decode email body: {str(e)}")
            return EmailRecordCreateMutation(success=False, errors=errors)

        # Remove the HTML Tag From the Email body to store in the database
        soup = BeautifulSoup(decoded_email_body, "html.parser")
        # Remove the Image From the Email body to store in the database
        for img in soup.find_all("img"):
            img.decompose()

        plain_text_email_body = soup.get_text(separator=" ", strip=True)

        uploaded_files_json = kwargs.get("files", "[]")
        attachments = []

        try:
            uploaded_files = json.loads(uploaded_files_json)  # Convert JSON string to list of objects
        except json.JSONDecodeError:
            errors.append("Invalid JSON format for files.")
            return EmailRecordCreateMutation(success=False, errors=errors)
        if uploaded_files and isinstance(uploaded_files, list):
            for file_obj in uploaded_files:
                try:
                    base64_content = file_obj.get("base64")
                    file_name = file_obj.get("name", "default_file")
                    file_type = file_obj.get("type", "application/octet-stream")

                    if not base64_content:
                        continue  # Skip empty files

                    if file_type == "text/html":
                        try:
                            decoded_file_content = base64.b64decode(base64_content).decode("utf-8")
                        except Exception as e:
                            errors.append(f"Invalid base64 encoding for {file_name}: {str(e)}")
                            continue
                        decoded_email_body += f"\n\n{decoded_file_content}"

                    else:
                        attachments.append({
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": file_name,
                            "contentBytes": base64_content,  # Base64 content sent directly
                            "contentType": file_type,
                            "IsInline": False  # Change to True if inline attachment
                        })
                except Exception as e:
                    errors.append(f"Error processing file {file_name}: {str(e)}")
        # Send Mail
        result = SendMail(access_token, sent_to_list_, kwargs['subject'], decoded_email_body, cc_list_, bcc_list_,
                          "HTML",
                          attachments)
        serializer = EmailRecordSerializer(data=kwargs)
        if result['success']:
            try:
                # Store send to cc bcc and email body in test format
                kwargs["sent_to"] = ", ".join(sent_to_list) if sent_to_list else ""
                kwargs["cc"] = ", ".join(cc_list) if cc_list else ""
                kwargs["bcc"] = ", ".join(bcc_list) if bcc_list else ""
                kwargs["email_body"] = plain_text_email_body
                if serializer.is_valid():
                    mail_instance = serializer.save()
                    success = True
                    try:
                        app_name = kwargs.get('app_name')
                        modal_name = kwargs.get('modal_name')
                        modal_id = kwargs.get('modal_id')
                        if app_name and modal_name and modal_id:
                            ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                            query = ModelClass.objects.get(id=modal_id)
                            try:
                                existing_mail = list(query.email_record.all())
                                existing_mail.append(mail_instance)
                                query.email_record.set(existing_mail)
                                query.save()
                                completed_status = CommanStatus.objects.filter(name="Completed",
                                                                               table="Activites").first()
                                if not completed_status:
                                    errors.append("Status 'Completed' not found in CommanStatus table.")
                                if modal_name == "enquiryDatas" and app_name == "EnquriFromapi":
                                    try:
                                        enquiry_instance = enquiryDatas.objects.get(id=modal_id)
                                        # Increment mail_count by 1 (handle if it's None)
                                        enquiry_instance.mail_count = (enquiry_instance.mail_count or 0) + 1
                                        # Save the updated instance
                                        enquiry_instance.save(update_fields=['mail_count'])

                                    except enquiryDatas.DoesNotExist:
                                        errors.append(f"Enquiry with id {modal_id} not found.")
                                    except Exception as e:
                                        errors.append(str(e))
                                if modal_name == "Leads" and app_name == "itemmaster2":
                                    try:
                                        leads_Datas = Leads.objects.get(id=modal_id)

                                        if leads_Datas.Enquiry:  # Check if Enquiry exists
                                            enquiry_mail_count = leads_Datas.Enquiry.mail_count or 0
                                        else:
                                            enquiry_mail_count = 0  # Default to 0 if no Enquiry is linked
                                        lead_mail_count = leads_Datas.mail_count or 0
                                        # total_mail_count = lead_mail_count + enquiry_mail_count + 1  # Adding 1 as per your requirement
                                        total_mail_count = lead_mail_count + 1  # Adding 1 as per your requirement

                                        leads_Datas.mail_count = total_mail_count
                                        leads_Datas.save(update_fields=['mail_count'])

                                    except Leads.DoesNotExist:
                                        errors.append(e)
                                    except Exception as e:
                                        errors.append(e)
                            except Exception as e:
                                errors.append(e)
                        else:
                            success = False
                    except Exception as e:
                        errors.append(e)
            except Exception as e:
                errors.append(e)
                return EmailRecordCreateMutation(success=success, errors=errors)
        else:
            errors = result['error']
        return EmailRecordCreateMutation(success=success, errors=errors, mail_instance=mail_instance)


class BulkEmailCreateMutation(graphene.Mutation):
    class Arguments:
        sent_to = graphene.List(graphene.String)
        cc = graphene.List(graphene.String)
        bcc = graphene.List(graphene.String)
        subject = graphene.String()
        email_body = graphene.String()
        id_list = graphene.List(graphene.Int)
        app_name = graphene.String()
        modal_name = graphene.String()
        created_by = graphene.Int()
        files = graphene.String()

    mail_instance = graphene.Field(EmailRecord_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        request = info.context
        mail_instance = None
        access_token = str(request.headers.get('Authorization')).replace("JWT ", "")
        sent_to_list = json.loads(json.dumps(kwargs.get('sent_to', [])))
        cc_list = json.loads(json.dumps(kwargs.get('cc', [])))
        bcc_list = json.loads(json.dumps(kwargs.get('bcc', [])))
        sent_to_list_ = []
        cc_list_ = []
        bcc_list_ = []
        if sent_to_list and isinstance(sent_to_list[0], str):
            sent_to_list_ = json.loads(sent_to_list[0])
        if cc_list and isinstance(cc_list[0], str):
            cc_list_ = json.loads(cc_list[0])
        if bcc_list and isinstance(bcc_list[0], str):
            bcc_list_ = json.loads(bcc_list[0])

        try:
            decoded_email_body = base64.b64decode(kwargs['email_body']).decode("utf-8")
        except Exception as e:
            errors.append(f"Failed to decode email body: {str(e)}")
            return EmailRecordCreateMutation(success=False, errors=errors)
        soup = BeautifulSoup(decoded_email_body, "html.parser")
        for img in soup.find_all("img"):
            img.decompose()

        plain_text_email_body = soup.get_text(separator=" ", strip=True)

        uploaded_files_json = kwargs.get("files", "[]")
        attachments = []

        try:
            uploaded_files = json.loads(uploaded_files_json)  # Convert JSON string to list of objects
        except json.JSONDecodeError:
            errors.append("Invalid JSON format for files.")
            return EmailRecordCreateMutation(success=False, errors=errors)

        if uploaded_files and isinstance(uploaded_files, list):
            for file_obj in uploaded_files:
                try:
                    base64_content = file_obj.get("base64")
                    file_name = file_obj.get("name", "default_file")
                    file_type = file_obj.get("type", "application/octet-stream")

                    if not base64_content:
                        continue  # Skip empty files

                    if file_type == "text/html":
                        try:
                            decoded_file_content = base64.b64decode(base64_content).decode("utf-8")
                        except Exception as e:
                            errors.append(f"Invalid base64 encoding for {file_name}: {str(e)}")
                            continue
                        decoded_email_body += f"\n\n{decoded_file_content}"

                    else:
                        attachments.append({
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": file_name,
                            "contentBytes": base64_content,  # Base64 content sent directly
                            "contentType": file_type,
                            "IsInline": False  # Change to True if inline attachment
                        })
                except Exception as e:
                    errors.append(f"Error processing file {file_name}: {str(e)}")
        result = SendMail(access_token, sent_to_list_, kwargs['subject'], decoded_email_body, cc_list_, bcc_list_,
                          "HTML",
                          attachments)
        serializer = EmailRecordSerializer(data=kwargs)
        if result['success']:
            try:
                kwargs["sent_to"] = ", ".join(sent_to_list) if sent_to_list else ""
                kwargs["cc"] = ", ".join(cc_list) if cc_list else ""
                kwargs["bcc"] = ", ".join(bcc_list) if bcc_list else ""
                kwargs["email_body"] = plain_text_email_body
                if serializer.is_valid():
                    mail_instance = serializer.save()
                    success = True
                    try:
                        app_name = kwargs.get("app_name")
                        modal_name = kwargs.get("modal_name")
                        id_list = kwargs.get("id_list", [])
                        if app_name and modal_name and id_list:
                            ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                            try:
                                records = ModelClass.objects.filter(id__in=id_list)
                                for record in records:
                                    existing_mail = list(record.email_record.all())
                                    existing_mail.append(mail_instance)
                                    record.email_record.set(existing_mail)
                                    if modal_name == "enquiryDatas" and app_name == "EnquriFromapi":
                                        try:
                                            record.mail_count = (record.mail_count or 0) + 1
                                            record.save(update_fields=['mail_count'])
                                        except Exception as e:
                                            errors.append(f"Error updating Enquiry mail_count: {str(e)}")
                                    elif modal_name == "Leads" and app_name == "itemmaster2":
                                        try:
                                            # Get the existing mail count for Lead (ignore Enquiry mail count)
                                            lead_mail_count = record.mail_count or 0

                                            # Increment only the Lead's mail count
                                            total_mail_count = lead_mail_count + 1

                                            # Update the Lead's mail_count
                                            record.mail_count = total_mail_count
                                            record.save(update_fields=['mail_count'])
                                        except Exception as e:
                                            errors.append(f"Error updating Lead mail_count: {str(e)}")

                                    record.save()
                            except Exception as e:
                                errors.append(f"Error updating email records: {str(e)}")
                    except Exception as e:
                        errors.append(e)
            except Exception as e:
                errors.append(e)
                return BulkEmailCreateMutation(success=success, errors=errors)
        else:
            errors.append(result["error"][0])
        return BulkEmailCreateMutation(success=success, errors=errors, mail_instance=mail_instance)


class LeadsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        lead_name = graphene.String()
        customer = graphene.Int()
        contact = graphene.Int()
        requirement = graphene.String()
        rext_follow_up = graphene.Date()
        lead_currency = graphene.Int()
        lead_value = graphene.String()
        expected_closing_date = graphene.Date()
        Enquiry = graphene.Int()
        priority = graphene.Int()
        lead_reason = graphene.String()
        lead_reason_dec = graphene.String()
        sales_person = graphene.Int()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    Leads_instance = graphene.Field(Leads_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("Lead", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        Leads_instance = None
        success = False
        errors = []

        if kwargs['status']:
            status = CommanStatus.objects.filter(name=kwargs['status'], table="Leads").first()
            if status:
                kwargs['status'] = status.id
            else:
                errors.append(f"Ask Admin To Add The {kwargs['status']}")
                return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)
        # Check if updating an existing call log
        if 'id' in kwargs and kwargs['id']:
            try:
                Leads_instance = Leads.objects.get(id=kwargs['id'])
                if Leads_instance.Enquiry:
                    add_contact_into_supplier(Leads_instance.Enquiry.id, Leads_instance.customer.id)
                if Leads_instance.status.name == "Won":
                    errors.append("You can't change the status of Won Lead.")
                    return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)
                if Leads_instance.status.name == "Lost":
                    errors.append("You can't change the status of Lost Lead.")
                    return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)
                if status.name == "Won" or status.name == "Lost":
                    result = any(
                        getattr(lead.status, "name", None) == "Planned" for lead in Leads_instance.activity.all())
                    enquiry_result = False
                    if Leads_instance.Enquiry:
                        enquiry_result = any(
                            getattr(Enquiry.status, "name", None) == "Planned" for Enquiry in
                            Leads_instance.Enquiry.activity.all())
                    if result or enquiry_result:
                        errors.append("Some activity status is Planned make change completed or canceled .")
                        return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)
                serializer = LeadsSerializer(Leads_instance, data=kwargs, partial=True)
            except Notes.DoesNotExist:
                errors.append("Leads not found.")
                return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)
        else:
            serializer = LeadsSerializer(data=kwargs)
            if kwargs['Enquiry']:
                add_contact_into_supplier(kwargs['Enquiry'], kwargs['customer'])
        if serializer.is_valid():
            try:
                instance = serializer.save()
                Leads_instance = instance
                if kwargs['id'] is None and kwargs['Enquiry']:
                    if instance.Enquiry:
                        enquiry = instance.Enquiry
                        # Aggregate counts from Enquiry (handling None values)
                        instance.mail_count = (enquiry.mail_count or 0)
                        instance.meeting_count = (enquiry.meeting_count or 0)
                        instance.task_count = (enquiry.task_count or 0)
                        instance.call_count = (enquiry.call_count or 0)
                        # Update note & email_record from Enquiry to Lead
                        instance.note.set(enquiry.note.all())
                        instance.email_record.set(enquiry.email_record.all())
                        instance.activity.set(enquiry.activity.all())
                        instance.rext_follow_up = enquiry.follow_up or None
                        instance.save(update_fields=['mail_count', 'meeting_count', 'task_count', 'call_count','rext_follow_up'])

                        #  After copying, now REMOVE data from the Enquiry
                        enquiry.mail_count = 0
                        enquiry.meeting_count = 0
                        enquiry.task_count = 0
                        enquiry.call_count = 0
                        enquiry.note.clear()
                        enquiry.email_record.clear()
                        enquiry.activity.clear()
                        enquiry.follow_up = None

                        enquiry.save(update_fields=['mail_count', 'meeting_count', 'task_count', 'call_count', 'follow_up'])
                        
                success = True
                # CalculateTheTarget("Leads", kwargs.get("sales_person"), instance, instance.lead_currency, instance.created_at)
            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return LeadsCreateMutation(success=success, errors=errors, Leads_instance=Leads_instance)


class LeadSalesPersonUpdateMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)
        sales_person = graphene.Int()

    enquiry_data = graphene.Field(Leads_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id_list=None, sales_person=None):
        success = False
        errors = []
        try:
            sales_person_instance = User.objects.get(id=sales_person)
        except:
            sales_person_instance = None
        if id_list and sales_person_instance:
            unique_id = set(id_list)
            try:
                Leads_instance = Leads.objects.filter(id__in=list(unique_id))
                for item in Leads_instance:
                    try:
                        if item.status.name != "Won" and item.status.name != "Lost":
                            item.sales_person = sales_person_instance
                    except Exception as e:
                        print(e)

                Leads.objects.bulk_update(Leads_instance, ['sales_person'])
                success = True
            except Exception as e:
                success = False
                errors = [e]
        else:
            errors = ["Given data doesn't exists"]
        return LeadSalesPersonUpdateMutation(success=success, errors=errors)


def LeadPrevalidation(leadDatalists):
    errors = []
    modifiedDatas = []
    serializer_list = []
    status = None
    try:
        status = CommanStatus.objects.get(name="Qualified", table="Leads")
    except Exception as e:
        errors.append({"modifiedRowIndex": 0, "errors": e})
        return {"success": False, "error": errors, "serializer_list": []}

    for index, leadDatalist in enumerate(leadDatalists):
        leadDatalist['status'] = status.id
        if leadDatalist['customer']:
            try:
                supplierData = SupplierFormData.objects.get(supplier_no=leadDatalist['customer'])
                if supplierData:
                    leadDatalist['customer'] = supplierData.id
            except Exception as e:
                errors.append({"modifiedRowIndex": index, "errors": f"Customer ID {e}"})
        else:
            errors.append({"modifiedRowIndex": index, "errors": "Customer ID is required"})
        if leadDatalist['lead_currency']:
            try:
                currency = CurrencyExchange.objects.get(Currency__name=leadDatalist['lead_currency'])
                if currency:
                    leadDatalist['lead_currency'] = currency.id
            except Exception as e:
                errors.append({"modifiedRowIndex": index, "errors": f"currency not match"})

        else:
            errors.append({"modifiedRowIndex": index, "errors": "Lead Currency  is required"})
        if leadDatalist['sales_person']:
            try:
                user = User.objects.get(username=leadDatalist['sales_person'])
                if user:
                    leadDatalist['sales_person'] = user.id
            except Exception as e:
                errors.append({"modifiedRowIndex": index, "errors": f"Sales Person ${e}"})
        else:
            errors.append({"modifiedRowIndex": index, "errors": "Sales Person  is required"})
        modifiedDatas.append(leadDatalist)
        # Now, we will merge errors by `modifiedRowIndex`
        merged_errors = {}
        for error in errors:
            index = error['modifiedRowIndex']
            error_message = error['errors']

            if index not in merged_errors:
                merged_errors[index] = error_message
            else:
                merged_errors[index] += f", {error_message}"
    # Convert merged_errors back into the desired format
    final_errors = [{"modifiedRowIndex": index, "errors": message} for index, message in merged_errors.items()]

    if len(final_errors) == 0 and len(modifiedDatas) > 0:
        for index, modifiedData in enumerate(modifiedDatas):
            serializer = LeadsSerializer(data=modifiedData)
            if serializer.is_valid():
                serializer_list.append(serializer)
            else:
                field_errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in
                                serializer.errors.items()]
                final_errors.append({"modifiedRowIndex": index, "errors": field_errors})
    return {"success": len(final_errors) == 0, "error": final_errors, "serializer_list": serializer_list}


class LeadDataInput(graphene.InputObjectType):
    lead_name = graphene.String()
    customer = graphene.String()
    lead_currency = graphene.String()
    lead_value = graphene.String()
    priority = graphene.Int()
    expected_closing_date = graphene.Date()
    sales_person = graphene.String()
    requirement = graphene.String()
    next_follow_up = graphene.Date()
    created_by = graphene.Int()


class LeadDataImportMutations(graphene.Mutation):
    class Arguments:
        leadDatalist = graphene.List(LeadDataInput)

    success = graphene.Boolean()
    errors = graphene.List(graphene.JSONString)

    def mutate(self, info, leadDatalist):
        success = False
        errors = []
        result = LeadPrevalidation(leadDatalist)
        if result["success"]:
            for serializer_data in result['serializer_list']:
                serializer_data.save()
            success = True
        else:
            errors = result["error"]

        return LeadDataImportMutations(success=success, errors=errors)


class LeadsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Lead", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            leads_instance = Leads.objects.get(id=id)
            leads_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules.')
        except Exception as e:
            errors.append(str(e))
        return LeadsDeleteMutation(success=success, errors=errors)


"""Leads end"""

"""OtherIncomeCharges start"""


class OtherIncomeChargesCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        account = graphene.Int()
        hsn = graphene.Int()
        active = graphene.Boolean()
        effective_date = graphene.Date()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    other_income_charges = graphene.Field(OtherIncomeCharges_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Other_Income", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        other_income_charges = None
        success = False
        errors = []
        commanHsnEffectiveDate_instance = None
        if 'id' in kwargs and kwargs['id']:
            # Update operation
            other_income_charges_instance = OtherIncomeCharges.objects.filter(id=kwargs['id']).first()
            if not other_income_charges_instance:
                errors.append("Other Income Charges Not Found.")
                return OtherIncomeChargesCreateMutation(other_income_charges=other_income_charges, success=success,
                                                        errors=errors)
            hsn = Hsn.objects.get(id=kwargs['hsn'])
            if kwargs['effective_date'] == datetime.now().date():
                kwargs['hsn'] = hsn.id
            else:
                kwargs['hsn'] = other_income_charges_instance.hsn.id
            serializer = OtherIncomeChargesSerializer(other_income_charges_instance, data=kwargs, partial=True)
        
            created_by = User.objects.get(id=kwargs['created_by'])
            if other_income_charges_instance.hsn.hsn_code == hsn.hsn_code:
                pass  # No change needed if the hsn codes match
            else:
                if kwargs['effective_date']:
                    # Create commanHsnEffectiveDate if needed
                    commanHsnEffectiveDate_instance = CommanHsnEffectiveDate(
                        None, "other_income_charges", hsn.id, kwargs['effective_date'],
                        created_by.id
                    )
                    commanHsnEffectiveDate_instance.save()
                else:
                    errors.append('Effective date is required')
                    return OtherIncomeChargesCreateMutation(other_income_charges=other_income_charges, success=success,
                                                            errors=errors)
        else:
            serializer = OtherIncomeChargesSerializer(data=kwargs)
        
        if serializer.is_valid():
            serializer.save()
            other_income_charges = serializer.instance
            if commanHsnEffectiveDate_instance:
                other_income_charges.comman_hsn_effective_date.add(commanHsnEffectiveDate_instance)
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return OtherIncomeChargesCreateMutation(other_income_charges=other_income_charges, success=success,
                                                errors=errors)


class OtherIncomeChargesDeleteMutation(graphene.Mutation):
    """OtherIncomeCharges Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Other_Income", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            OtherIncomeCharges_instance = OtherIncomeCharges.objects.get(id=id)
            OtherIncomeCharges_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return OtherIncomeChargesDeleteMutation(success=success, errors=errors)


"""OtherIncomeCharges end"""

"""use to get item combo data"""


class getItemComboItemDetails(graphene.Mutation):
    class Arguments:
        itemmaster = graphene.ID(required=True)
        amount = graphene.Decimal(required=True)
        qty = graphene.Decimal(required=True)

    item_combo = graphene.Boolean()
    item_combo_data = graphene.List(graphene.JSONString)
    error = graphene.String()

    def mutate(self, info, **kwargs):
        item_combo = True
        item_combo_data = []

        item_combo, item_combo_data, error = getItemCombo(kwargs['itemmaster'], kwargs['amount'], kwargs['qty'])

        return getItemComboItemDetails(item_combo=item_combo, item_combo_data=item_combo_data, error=error)


"""Quotations Start"""

class QuotationsItemComboItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    itemmaster = graphene.Int()
    parent = graphene.Int()
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    display = graphene.String()
    is_mandatory = graphene.Boolean()
    after_discount_value_for_per_item = graphene.Decimal()
    amount = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class QuotationItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    parent = graphene.Int()
    itemmaster = graphene.Int(required=True)
    qty = graphene.Decimal(required=True)
    rate = graphene.Decimal(required=True)
    hsn = graphene.Int()
    
    description = graphene.String(required=True)
    item_combo_item_details = graphene.List(QuotationsItemComboItemDetailsInput)
    item_combo_total_amount = graphene.Decimal()
    item_combo = graphene.Boolean()
    after_discount_value_for_per_item = graphene.Decimal()
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    final_value = graphene.Decimal()
    uom = graphene.Int(required=True)
    tax = graphene.Decimal(required=True)
    igst = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    cess = graphene.Decimal()
    states = graphene.String(required=True)
    amount = graphene.Decimal(required=True)
    modified_by = graphene.Int()
    created_by = graphene.Int()


class OtherIncomechargeInput(graphene.InputObjectType):
    id = graphene.ID()
    other_income_charges_id = graphene.Int(required=True)
    tax = graphene.Decimal(required=True)
    discount_value = graphene.Decimal()
    after_discount_value = graphene.Decimal()
    amount = graphene.Decimal(required=True)
    igst = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    cess = graphene.Decimal()
    states = graphene.String(required=True)
    modified_by = graphene.Int()
    created_by = graphene.Int()

class QuotationsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String(required=True)
        quotation_date = graphene.Date()
        customer_id = graphene.Int(required=True)
        customer_address = graphene.Int(required=True)
        customer_contact_person = graphene.Int(required=True)
        gstin_type = graphene.String()
        currency = graphene.Int(required=True)
        exchange_rate = graphene.String(required=True)
        sales_person = graphene.Int(required=True)
        lead_no = graphene.Int()
        department = graphene.Int(required=True)
        remarks = graphene.String()
        itemDetails = graphene.List(QuotationItemDetailsInput)
        other_income_charge = graphene.List(OtherIncomechargeInput)
        overall_discount_percentage = graphene.Decimal()
        overall_discount_value = graphene.Decimal()
        discount_final_total = graphene.Decimal()
        terms_conditions = graphene.Int(required=True)
        terms_conditions_text = graphene.String(required=True)
        item_total_befor_tax = graphene.Decimal()
        other_charges_befor_tax = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        gst_nature_transaction = graphene.Int()
        parent_order = graphene.Int()
        child_count = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    quotations = graphene.Field(Quotations_type)
    version = graphene.Field(versionListType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    outOfRangeErrors = graphene.List(graphene.String)
    item_details = graphene.JSONString()
    other_income_charges = graphene.JSONString()

    @mutation_permission("Quotation", create_action="Draft", edit_action="Edit")
    def mutate(self, info, **kwargs):
        quotations = None
        success = False
        errors = []
        version = []
        out_of_range_errors = []
        
        quotation_service = QuotationService(data=kwargs, status=kwargs["status"], info=info)
        response = quotation_service.process()
        if response["success"]:
            success = response["success"]
            quotations = response["quotation"]
            version = response["version"]
        else:
            errors= response["errors"]
            out_of_range_errors = response["outOfRangeErrors"]
        return QuotationsCreateMutation(quotations=quotations, success=success,
                                        errors=errors, version=version,
                                        outOfRangeErrors=out_of_range_errors,
                                        item_details= json.dumps(response.get("item_details") , cls=DecimalEncoder) if response.get("item_details") else None
                                        , other_income_charges= json.dumps(response.get("other_income_charges"), cls=DecimalEncoder) if response.get("other_income_charges") else None)
    
class QuotationsCanceledMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    quotations = graphene.Field(Quotations_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Quotation", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        quotations_instance = None
        success = False
        errors = []

        try:
            quotations_instance = Quotations.objects.get(id=id)
        except Quotations.DoesNotExist:
            errors.append("Quotation not found.")
            return QuotationsCanceledMutation(quotations=quotations_instance, success=success, errors=errors)

        status_object = CommanStatus.objects.filter(name="Canceled", table="Quotations").first()
        if not status_object:
            errors.append("Ask Admin to add 'Canceled' status for Quotations.")
            return QuotationsCanceledMutation(quotations=quotations_instance, success=success, errors=errors)

        try:
            quotations_instance.status = status_object
            quotations_instance.save()
            success = True
        except Exception as e:
            errors.append(str(e))

        return QuotationsCanceledMutation(quotations=quotations_instance, success=success, errors=errors)


class QuotationsDeleteMutation(graphene.Mutation):
    """Quotations Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @mutation_permission("Quotation", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            Quotations_instance = Quotations.objects.get(id=id)
            if Quotations_instance.status.name == "Canceled":
                Quotations_instance.delete()
                success = True
            else:
                errors.append("After make canceled after only can delete.")
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return QuotationsDeleteMutation(success=success, errors=errors)

class GeneratePdfForQuotationNew(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id):
        success = False
        errors = []
        pdf_base64 = None 
        def remove_number(data):
            if data:
                value = float(data)
                return int(value) if value.is_integer() else value
            else:
                return ""

        try:
            quotation_instance = Quotations.objects.get(id=id)
            discount_percentage = lambda d: d.discount_percentage or 0
            discount_value = lambda d: d.discount_value or 0
            html = quotation_instance.terms_conditions_text
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            bank_data = company_bank_info()
            
            is_discount_applied = any(
                (item.discount_percentage or 0) > 0 or 
                (item.discount_value or 0) > 0 or 
                (item.final_value or 0) > 0
                for item in quotation_instance.itemDetails.all()
            )

            # Final tax list  
            list_tax = createPdfHsnTableContent(quotation_instance.itemDetails,quotation_instance.other_income_charge, quotation_instance.currency.Currency.currency_symbol)
            print(quotation_instance.customer_address.address_line_2,type(quotation_instance.customer_address.address_line_2))
            quotation_data = {
                "customerId": quotation_instance.customer_id.supplier_no,
                "customerName": quotation_instance.customer_id.company_name,
                "customerAddress": f"{quotation_instance.customer_address.address_line_1},\n"
                                f"{quotation_instance.customer_address.address_line_2},\n"
                                f"{quotation_instance.customer_address.city} - {quotation_instance.customer_address.pincode},\n"
                                f"{quotation_instance.customer_address.state}, {quotation_instance.customer_address.country}." if quotation_instance.customer_address.address_line_2 else
                                f"{quotation_instance.customer_address.address_line_1},\n"
                                f"{quotation_instance.customer_address.city} - {quotation_instance.customer_address.pincode},\n"
                                f"{quotation_instance.customer_address.state}, {quotation_instance.customer_address.country}.",
                "contactPerson": f"{quotation_instance.customer_contact_person.salutation} {quotation_instance.customer_contact_person.contact_person_name}",
                "phoneNumber":quotation_instance.customer_contact_person.phone_number,
                "mail":quotation_instance.customer_contact_person.email,
                "quotationNo": quotation_instance.quotation_no.linked_model_id,
                "quotationDate": str(quotation_instance.quotation_date.strftime('%d/%m/%Y')),
                "salesPerson": quotation_instance.sales_person.username,
                "buyerGstIn": quotation_instance.customer_id.gstin,

                "Table Name": ['SI', "HSNTABLE", "OtherIncome"],
                "Other Table": ["OtherIncome"],

                "OtherIncome_Datas": [
                    {
                        "account": other_charges.other_income_charges_id.name,
                        # "%": other_charges.discount_value if  other_charges.discount_value else "",
                        # "tax": f"{other_charges.tax}.00",
                        "Total": format_currency(other_charges.after_discount_value, quotation_instance.currency.Currency.currency_symbol) if other_charges.after_discount_value and other_charges.after_discount_value != 0.00 else format_currency(other_charges.amount, quotation_instance.currency.Currency.currency_symbol, False)
                    }
                    for other_charges in quotation_instance.other_income_charge.all()
                ],
                "OtherIncome_Style":{
                    "account":"right",
                    "%":"right",
                    "tax":"right",
                    "Total":"right"
                },
                "SI_Columns": {
                    "S.No": "No",
                    "Description": "Description",
                    "HSN": "Item's HSN Code (Text)",
                    "Qty": "Quantity",
                    # "UOM": "UOM's Name",
                    "Rate": "Rate",
                    "Disc": "Disc",
                    "%": "%",
                    "Amount": "Amount",
                    "Total": "Total"
                },
                "SI_Datas":[
                    {
                        "No": f"{str(index + 1)}",
                        "Description": (
                            f"{itemdetail.description}" +
                            (
                                lambda: (
                                    # Group by display (non-empty)
                                    "".join(
                                        f"\n \n  • {display}" + "\n    " + "\n    ".join([
                                            f"{i2.itemmaster.description}"
                                            for i2 in itemdetail.item_combo_item_details.all()
                                            if i2.display and i2.display.strip() == display
                                        ])
                                        for display in (set(
                                            i.display.strip()
                                            for i in itemdetail.item_combo_item_details.all()
                                            if i.display and i.display.strip()
                                        ))
                                    )
                                    +
                                    (
                                        "\n \n • No DisPlay\n    " + "\n    ".join([
                                            f"{i.itemmaster.description}"
                                            for i in itemdetail.item_combo_item_details.all()
                                            if not i.display or not i.display.strip()
                                        ])
                                        if any(
                                            not i.display or not i.display.strip()
                                            for i in itemdetail.item_combo_item_details.all()
                                        )
                                        else ""
                                    )
                                )
                            )()
                        ),
                        "Item's HSN Code (Text)": f"{itemdetail.hsn.hsn_code}",
                        "Quantity": f"{itemdetail.qty:.0f} {itemdetail.uom.name}",
                        "Rate": f"{itemdetail.rate:.2f}",
                        "Disc": (
                                (
                                    f"{remove_number(discount_percentage(itemdetail))}%"
                                    if discount_percentage(itemdetail) and discount_percentage(itemdetail) > 0
                                    else remove_number(discount_value(itemdetail))
                                    if discount_value(itemdetail) and discount_value(itemdetail) > 0
                                    else remove_number(itemdetail.final_value)
                                    if itemdetail.final_value
                                    else ""
                                )
                            ),
                        "%": f"{int(itemdetail.tax)}" if str(itemdetail.tax).endswith(".00") else f"{str(float(itemdetail.tax))}",
                        "Amount": f"{round((itemdetail.tax * itemdetail.amount) / 100, 2)}",
                        "Total": f"{itemdetail.amount:.2f}"
                    }
                    for index, itemdetail in enumerate(quotation_instance.itemDetails.all())
                ],
                
                "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "HSN": "center",
                    "Qty": "center",
                    "UOM": "center",
                    "Rate": "right",
                    "Disc": "right",
                    "%": "right",
                    "Amount": "right",
                    "Total": "right"
                }
                ,
                "HSNTABLE_Columns": {
                    "S.No[S.No]": "S.No",
                    "HSN/SAC[HSN/SAC]": "HSN/SAC",
                    "Taxable Value[Taxable Value]": "Taxable Value",
                    "CGST[%]": "cgst %",
                    "CGST[Amount]": "cgst Amount",
                    "SGST[%]": "sgst %",
                    "SGST[Amount]": "sgst Amount",
                    "IGST[%]": "igst %",
                    "IGST[Amount]": "igst Amount"
                },
                "HSNTABLE_Columns_Style":{
                    "S.No[S.No]": "center",
                    "HSN/SAC[HSN/SAC]": "center",
                    "Taxable Value[Taxable Value]": "right",
                    "CGST[%]": "center",
                    "CGST[Amount]": "right",
                    "SGST[%]": "center",
                    "SGST[Amount]": "right",
                    "IGST[%]": "center",
                    "IGST[Amount]": "right"
                },
                "HSNTABLE_Datas":[ taxdata for taxdata in list_tax],
                "totalAmoutInWords": num2words(int(float(quotation_instance.net_amount)), lang='en_IN' if quotation_instance.currency.Currency.currency_symbol == '₹' else 'en').title() + " Only",
                "termsandcondition": tc,
                "departmentName": quotation_instance.department.name,
                "AfterTax": format_currency(quotation_instance.net_amount, quotation_instance.currency.Currency.currency_symbol, False),
                "gst": format_currency(str(float(quotation_instance.tax_total,)), quotation_instance.currency.Currency.currency_symbol, False),
                "totalTax": format_currency(str(float(quotation_instance.taxable_value)), quotation_instance.currency.Currency.currency_symbol, False),
                "bankName":bank_data.bank_name if bank_data else "",
                "ifsc":bank_data.ifsc_code if bank_data else "",
                "accountNo":bank_data.account_number if bank_data else "",
                "branch":bank_data.branch_name if bank_data else ""
            }
            status = quotation_instance.status.name
            # print("quotation_data",quotation_data) 
            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\QuotationNew1.docx".format(BASE_DIR)
                if is_discount_applied:
                    if status == "Draft":
                        print(1)
                        doc_path = r"{}\static\PDF_TEMP\Quotation_v01_Draft.docx".format(BASE_DIR)
                    else:
                        print(2)
                        doc_path = r"{}\static\PDF_TEMP\Quotation_v01_Submit.docx".format(BASE_DIR)
                else:
                    if status == "Draft":
                        print(3)
                        doc_path = r"{}\static\PDF_TEMP\Quotation_ND_v01_Draft.docx".format(BASE_DIR)
                    else:
                        print(4)
                        doc_path = r"{}\static\PDF_TEMP\Quotation_ND_v01_Submit.docx".format(BASE_DIR)
            else:
                output_docx = r"{}/static/PDF_OUTPUT/QuotationNew1.docx".format(BASE_DIR)
                if is_discount_applied:
                    if status == "Draft":
                        doc_path =  r"{}/static/PDF_TEMP/Quotation_v01_Draft.docx".format(BASE_DIR)
                    else:
                        doc_path =  r"{}/static/PDF_TEMP/Quotation_v01_Submit.docx".format(BASE_DIR)
                else:
                    if status == "Draft":
                        doc_path =  r"{}/static/PDF_TEMP/Quotation_ND_v01_Draft.docx".format(BASE_DIR)
                    else:
                        doc_path =  r"{}/static/PDF_TEMP/Quotation_ND_v01_Submit.docx".format(BASE_DIR)
                    
            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, quotation_data)
            doc.save(output_docx)
            pdf_path = convert_docx_to_pdf(output_docx)
            
            # Generate the PDF
            # Read the generated DOCX into memory and encode it
            with open(pdf_path, 'rb') as docx_file:
                docx_data = docx_file.read()
                pdf_base64 = base64.b64encode(docx_data).decode('utf-8')
                
            # Clean up the temporary file (uncomment this line if needed)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(output_docx):
                os.remove(output_docx)

            success = True 
        except Exception as e:
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForQuotationNew(pdf_data =pdf_base64, success=success, errors=errors)


"""Quotations end"""

"""SaleOrder 2 Start"""


class SalesOrder_2_ItemComboItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    itemmaster = graphene.Int()
    parent = graphene.Int()
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    display = graphene.String()
    is_mandatory = graphene.Boolean()
    after_discount_value_for_per_item = graphene.Decimal()
    amount = graphene.Decimal()
    parent_itemDetail_id = graphene.ID()
    modified_by = graphene.Int()
    created_by = graphene.Int()
 

class SalesOrder_2ItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    itemmaster = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    description = graphene.String(required=True)
    hsn = graphene.Int()
    tax = graphene.Decimal()
    after_discount_value_for_per_item = graphene.Decimal()
    item_combo = graphene.Boolean()
    item_combo_item_details = graphene.List(SalesOrder_2_ItemComboItemDetailsInput)
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    final_value = graphene.Decimal()
    uom = graphene.Int()
    igst = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    cess = graphene.Decimal() 
    states = graphene.String(required=True)
    amount = graphene.Decimal()
    modified_by = graphene.Int() 
    parent_itemDetail_id = graphene.Int()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class SalesOrder_2_otherIncomeChargesInput(graphene.InputObjectType):
    id = graphene.ID()
    other_income_charges_id = graphene.Int() 
    tax = graphene.Decimal()
    amount = graphene.Decimal()
    states = graphene.String(required=True)
    discount_value = graphene.Decimal()
    after_discount_value = graphene.Decimal()
    parent_other_income_id = graphene.Int()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class SalesOrder_2CreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        sales_order_date = graphene.Date()
        gst_nature_transaction = graphene.Int()
        sales_person = graphene.Int()
        due_date = graphene.Date()
        credit_period = graphene.Int()
        payment_terms = graphene.String()
        customer_po_no = graphene.String()
        customer_po_date = graphene.Date()
        lead_no = graphene.Int()
        quotations = graphene.Int()
        department = graphene.Int()
        remarks = graphene.String()
        currency = graphene.Int()
        exchange_rate = graphene.String()
        buyer = graphene.Int()
        buyer_address = graphene.Int()
        buyer_contact_person = graphene.Int()
        buyer_gstin_type = graphene.String()
        buyer_gstin = graphene.String()
        buyer_state = graphene.String()
        buyer_place_of_supply = graphene.String()
        consignee = graphene.Int()
        consignee_address = graphene.Int()
        consignee_contact_person = graphene.Int()
        consignee_gstin_type = graphene.String()
        consignee_gstin = graphene.String()
        consignee_state = graphene.String()
        consignee_place_of_supply = graphene.String()
        item_details = graphene.List(SalesOrder_2ItemDetailsInput)
        other_income_charge = graphene.List(SalesOrder_2_otherIncomeChargesInput)
        overall_discount_percentage = graphene.Decimal()
        overall_discount_value = graphene.Decimal()
        discount_final_total = graphene.Decimal()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        item_total_befor_tax = graphene.Decimal()
        other_charges_befor_tax = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        conformation_to_submit = graphene.Boolean()
        parent_order = graphene.Int()
        child_count = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    SalesOrder_2 = graphene.Field(SalesOrder_2_type)
    version = graphene.Field(versionListType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    outOfRangeErrors = graphene.List(graphene.String)
    waring = graphene.JSONString()
    get_conformation_to_submit = graphene.Boolean()
    valueIsHight = graphene.Boolean()
    item_details = graphene.JSONString()
    other_income_charges = graphene.JSONString()
    
    @status_mutation_permission("SalesOrder_2")
    def mutate(self, info, **kwargs):
        sales_order_service = SalesOrderService(data=kwargs, status=kwargs['status'], info=info)
        sales_result = sales_order_service.execute()
    
        return SalesOrder_2CreateMutation(SalesOrder_2=sales_result.get("salesorder"), success=sales_result.get("success"),
                                        errors=sales_result.get("errors"), outOfRangeErrors=sales_result.get("outOfRangeErrors"),
                                        waring=sales_result.get("warning"),get_conformation_to_submit=sales_result.get("get_conformation_to_submit"),
                                        valueIsHight= sales_result.get("valueIsHight"),version=sales_result.get("version"),
                                        item_details= json.dumps(sales_result.get("item_details") , cls=DecimalEncoder) if sales_result.get("item_details") else None
                                        , other_income_charges= json.dumps(sales_result.get("other_income_charges"), cls=DecimalEncoder) if sales_result.get("other_income_charges") else None)


class SalesOrder_2CanceledMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    salesOrder_2 = graphene.Field(SalesOrder_2_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("SalesOrder_2", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        salesOrder_2_instance = None
        success = False
        errors = []
        try:
            salesOrder_2_instance = SalesOrder_2.objects.get(id=id)
        except salesOrder_2_instance.DoesNotExist:
            errors.append("SalesOrder not found.")
            return SalesOrder_2CanceledMutation(salesOrder_2=salesOrder_2_instance, success=success, errors=errors)
        status_object = CommanStatus.objects.filter(name="Canceled", table="SalesOrder_2").first()
        if not status_object:
            errors.append("Ask Admin to add 'Canceled' status for Sales order.")
            return SalesOrder_2CanceledMutation(salesOrder_2=salesOrder_2_instance, success=success, errors=errors)

        if salesOrder_2_instance.dc_links.exists():
            for dc in salesOrder_2_instance.dc_links.all():
                if dc.status.name != "Canceled":
                    errors.append("Befor Cancel Sales Order need to cancel all child DC.")
                    return SalesOrder_2CanceledMutation(salesOrder_2=salesOrder_2_instance, success=success, errors=errors)
        try:
            salesOrder_2_instance.status = status_object
            salesOrder_2_instance.save()
            success = True
        except Exception as e:
            errors.append(str(e))
        return SalesOrder_2CanceledMutation(salesOrder_2=salesOrder_2_instance, success=success, errors=errors)


class SalesOrder_2DeleteMutation(graphene.Mutation):
    """SalesOrder_2 Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("SalesOrder_2", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            SalesOrder_2_instance = SalesOrder_2.objects.get(id=id)
            if SalesOrder_2_instance.dc_links.exists():
                errors.append("Befor Delete Need to delete the linked sales dc.")
            if SalesOrder_2_instance.status.name == "Canceled":
                SalesOrder_2_instance.delete()
                success = True
            else:
                errors.append("After make canceled after only can delete.")
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SalesOrder_2DeleteMutation(success=success, errors=errors)
"""SaleOrder 2 End"""

"""Deliver Challen Start"""
class SalesOrder_2_RetunBatchInput(graphene.InputObjectType):
    id = graphene.ID()
    batch_str =  graphene.String(required=True)
    batch = graphene.Int(required=True)
    qty = graphene.Decimal(required=True)

class DeliveryChallanItemComboInput(graphene.InputObjectType):
    id = graphene.ID()
    item_combo = graphene.Int(required=True)
    serial = graphene.List(graphene.Int)
    batch = graphene.List(SalesOrder_2_RetunBatchInput)
    store  =  graphene.Int(required=True)
    qty = graphene.Decimal(required=True)

class DeliveryChallanItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    sales_order_item_detail = graphene.Int(required=True)
    qty = graphene.Decimal(required=True)
    store = graphene.Int()
    amount = graphene.Decimal(required=True)
    item_combo_item_details = graphene.List(DeliveryChallanItemComboInput)
    serial = graphene.List(graphene.Int)
    batch = graphene.List(SalesOrder_2_RetunBatchInput)


def Sales_SO_2_DC_ItemDetails(data, info):
    updatedItemDetails = []
    for item in data:
        if "item_combo_item_details" in item and item.get('item_combo_item_details') and len(item.get('item_combo_item_details')) > 0:
            itemcombo_before_save = []
            for itemcombo_item in item.get('item_combo_item_details', []):
                if not itemcombo_item['serial']:
                    itemcombo_item['serial'] = []
                itemcombo_before_save.append(itemcombo_item)

            savedItemCombo = save_items(itemcombo_before_save, SalesOrder_2_DeliverChallanItemCombo,
                                        SalesOrder_2_DeliverChallanItemComboSerializer, "Item Combo", info.context)
            if not savedItemCombo['success']:
                return {"ids": [], "success": False, "error": savedItemCombo['error']}
            item['item_combo_itemdetails'] = savedItemCombo['ids']
            updatedItemDetails.append(item)
        else:
            updatedItemDetails.append(item)
        if item['serial'] is None:
                item['serial'] = [] 
    return save_items(data, SalesOrder_2_DeliveryChallanItemDetails,
                    SalesOrder_2_DeliveryChallanItemDetailsSerializer,"Item Detail", info.context)


class SalesOrder_2_DeliverChallenCretedMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        dc_date = graphene.Date()
        e_way_bill = graphene.String()
        e_way_bill_date = graphene.String()
        sales_order = graphene.Int()
        item_details = graphene.List(DeliveryChallanItemDetailsInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        comman_store = graphene.Int()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        before_tax = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        nett_amount = graphene.Decimal()
        vehicle_no = graphene.String()
        driver_name = graphene.String()
        transportation_mode = graphene.String()
        transport = graphene.Int()
        docket_no = graphene.String()
        docket_date = graphene.Date()
        other_model = graphene.String()

    DeliveryChallan = graphene.Field(salesOrder_2_DeliveryChallan_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    needstock = graphene.String()

    @status_mutation_permission("Sales Delivery Challan")
    def mutate(self, info, **kwargs): 
        status = kwargs["status"]
        
        service =  DeliverChallanService(kwargs, status, info)
        result = service.Process()

        return SalesOrder_2_DeliverChallenCretedMutations(DeliveryChallan=result.get("soDeliveryChallan"),
                                                            success= result.get("success"),
                                                            errors=result.get("errors"),
                                                            needstock=json.dumps(result.get("needStock"), default=str))


class SalesOrder_2_DeliverChallenCanceleMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)


    @mutation_permission("Sales Delivery Challan", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        status = None
        soDeliveryChallan = None
        with transaction.atomic():
            statusObjects = CommanStatus.objects.filter(name='Canceled', table="SalesOrderDeliveryChallan").first()
            if statusObjects:
                status = statusObjects
            else:
                status = 'Canceled' # Provide a default value if 'status' is not in kwargs
                errors.append(f"Ask devopole to add ${status}")
                return SalesOrder_2_DeliverChallenCanceleMutations(success=success, errors=errors)
            
            try:
                soDeliveryChallan = SalesOrder_2_DeliveryChallan.objects.get(id=id)
                
                if soDeliveryChallan.status.name == "Canceled":
                    errors.append("Delivery Challan already Cancel.")
                    return SalesInvoiceCancelMutation(success=False, errors=errors)
                if soDeliveryChallan.status.name == "Dispatch":
                    errors.append("Delivery challan is dispatched so can't cancel.")
                    return SalesInvoiceCancelMutation(success=False, errors=errors)
            except Exception as e:
                errors.append("Sales Order DC Not Found.")
                return SalesOrder_2_DeliverChallenCanceleMutations( success=success,
                                                errors=errors)
            if soDeliveryChallan.sales_invoice:
                sales_invoice = soDeliveryChallan.sales_invoice
                if sales_invoice.status.name != "Canceled":
                    errors.append("The Sales Invoice must be cancelled before you can cancel the Delivery Challan.")
                    return SalesOrder_2_DeliverChallenCanceleMutations( success=success,
                                            errors=errors)

            """update the item count"""
            try:
                if soDeliveryChallan.status.name == "Draft":
                    for itemdetail in  soDeliveryChallan.item_details.all():
                        so_dc_instance= itemdetail.sales_order_item_detail
                        if so_dc_instance:
                            has_draft = any(
                                    linked_dc.salesorder_2_deliverychallan.first() and 
                                    linked_dc.salesorder_2_deliverychallan.first().status.name == "Draft"
                                    for linked_dc in so_dc_instance.salesorder_2_deliverychallanitemdetails_set.all()
                                )
                            so_dc_instance.is_have_draft = has_draft
                            so_dc_instance.save()
                        if so_dc_instance and so_dc_instance.item_combo and itemdetail.item_combo_itemdetails.exists():
                            for combo_item in itemdetail.item_combo_itemdetails.all():
                                salesorder_combo = combo_item.item_combo
                                if not salesorder_combo:
                                    continue

                                # Check if any linked combo DC items belong to a Draft DC
                                has_draft = any(
                                    (linked_combo.salesorder_2_deliverychallanitemdetails_set.first() and
                                    linked_combo.salesorder_2_deliverychallanitemdetails_set.first().salesorder_2_deliverychallan_set.first() and
                                    linked_combo.salesorder_2_deliverychallanitemdetails_set.first().salesorder_2_deliverychallan_set.first().status.name == "Draft")
                                    for linked_combo in salesorder_combo.salesorder_2_deliverchallanitemcombo_set.all()
                                )

                                salesorder_combo.is_have_draft = has_draft
                                salesorder_combo.save()
                    soDeliveryChallan.status = statusObjects
                    soDeliveryChallan.save()
                    success = True

                elif soDeliveryChallan.status.name == "Submit":
                    result_error = SalesOrderDcOnCancelAddTheStock(soDeliveryChallan)
                    if len(result_error) == 0:
                        soDeliveryChallan.status = statusObjects
                        soDeliveryChallan.all_stock_reduce = False
                        soDeliveryChallan.save()
                        success = True
                    sales_dc_general_ledger  = AccountsGeneralLedger.objects.filter(sales_dc_voucher_no=soDeliveryChallan.id)
                    for general_ledger in sales_dc_general_ledger:
                        general_ledger.delete()
                
            except Exception as e:
                errors.append(f'An exception occurred {e}')
        
        return SalesOrder_2_DeliverChallenCanceleMutations( success=success,
                                        errors=errors)


class SalesOrder_2_Deliver_ChallanDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Sales Delivery Challan", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []

        try:
            so_delivery_challan = SalesOrder_2_DeliveryChallan.objects.get(id=id)
        except SalesOrder_2_DeliveryChallan.DoesNotExist:
            errors.append("Sales Order DC not found.")
            return SalesOrder_2_Deliver_ChallanDeleteMutation(success=success, errors=errors)
 
        if so_delivery_challan.salesinvoice_set.exists():
            errors.append("Before deleting Sales DC, delete the linked sales invoice(s).")
            return SalesOrder_2_Deliver_ChallanDeleteMutation(success=success, errors=errors)

        # only allow delete if canceled
        if so_delivery_challan.status and so_delivery_challan.status.name == "Canceled":
            so_delivery_challan.delete()
            success = True
        else:
            errors.append("Only canceled Sales Order DCs can be deleted.")

        return SalesOrder_2_Deliver_ChallanDeleteMutation(success=success, errors=errors)


class TaxValidationBeforSalesOrder_DC(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    def mutate(self, info, id):
        
        errors = []
        soDeliveryChallan = None

        salesorder = SalesOrder_2.objects.get(id=id)
        item_details = salesorder.item_details.all()
        gst_transaction = salesorder.gst_nature_transaction
        if gst_transaction.gst_nature_type == "Specify" and gst_transaction.specify_type == "taxable":
            for item in item_details:
                if gst_transaction.place_of_supply == "Intrastate":
                    if (
                        item.sgst!= gst_transaction.sgst_rate or
                        item.cgst!= gst_transaction.cgst_rate or
                        item.cess != gst_transaction.cess_rate
                    ):
                        errors.append("There is a tax mismatch; please amend the sales order accordingly.")
                        
                elif gst_transaction.place_of_supply == "Interstate":
                    if (
                        item.igst != gst_transaction.igst_rate or
                        item.cess != gst_transaction.cess_rate
                    ):
                        errors.append("There is a tax mismatch; please amend the sales order accordingly.")

        elif gst_transaction.gst_nature_type == "As per HSN":
            for item in item_details:
                if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != item.hsn.gst_rates.rate or (item.cess or 0) !=(item.hsn.cess_rate or 0):
                    errors.append("There is a tax mismatch; please amend the sales order accordingly.")


        else:
            # Fallback check — if all 4 rates are present, reject
            for item in item_details:
                if item.sgst or item.cgst or item.igst or item.cess:
                    errors.append("There is a tax mismatch; please amend the sales order accordingly.")
        success = len(errors) == 0
        return TaxValidationBeforSalesOrder_DC(success=success, errors=errors)

class GeneratePdfForSalesOrderNew(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id):
        success = False
        errors = []
        def remove_number(data):
            if data:
                value = float(data)
                return int(value) if value.is_integer() else value
            else:
                return ""
        try:
            sales_instance = SalesOrder_2.objects.get(id=id) 
            discount_percentage = lambda d: d.discount_percentage or 0
            discount_value = lambda d: d.discount_value or 0
            html = sales_instance.terms_conditions_text
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            # Final tax list
            list_tax = createPdfHsnTableContent(sales_instance.item_details,sales_instance.other_income_charge)
            status = sales_instance.status.name
            is_discount_applied = any(
                    (item.discount_percentage or 0) > 0 or 
                    (item.discount_value or 0) > 0 or 
                    (item.final_value or 0) > 0
                    for item in sales_instance.item_details.all()
                    )
            bank_data = company_bank_info()
            try:
               sales_order_data = { 
                "customerName": sales_instance.buyer.company_name,
                "customerAddress": f"{sales_instance.buyer_address.address_line_1},\n"
                                f"{sales_instance.buyer_address.address_line_2},\n"
                                f"{sales_instance.buyer_address.city} - {sales_instance.buyer_address.pincode},\n"
                                f"{sales_instance.buyer_address.state}, {sales_instance.buyer_address.country}." if sales_instance.buyer_address.address_line_2 else
                                f"{sales_instance.buyer_address.address_line_1},\n "
                                f"{sales_instance.buyer_address.city} - {sales_instance.buyer_address.pincode},\n"
                                f"{sales_instance.buyer_address.state}, {sales_instance.buyer_address.country}.",
                "consignee_name": sales_instance.consignee.company_name,
                "consignee_address": f"{sales_instance.consignee_address.address_line_1},\n"
                                f"{sales_instance.consignee_address.address_line_2},\n"
                                f"{sales_instance.consignee_address.city} - {sales_instance.consignee_address.pincode},\n"
                                f"{sales_instance.consignee_address.state}, {sales_instance.consignee_address.country}." if sales_instance.consignee_address.address_line_2 else
                                f"{sales_instance.consignee_address.address_line_1},\n "
                                f"{sales_instance.consignee_address.city} - {sales_instance.consignee_address.pincode},\n"
                                f"{sales_instance.consignee_address.state}, {sales_instance.consignee_address.country}.",
                "contactPerson": sales_instance.buyer_contact_person.contact_person_name,
                "phoneNumber" : sales_instance.buyer_contact_person.phone_number,
                "sales_order_no": sales_instance.sales_order_no.linked_model_id,
                "so_date": str(sales_instance.sales_order_date.strftime('%d/%m/%Y')),
                "sales_person": sales_instance.sales_person.username,
                "customer_po_no": sales_instance.customer_po_no,
                "customer_due_date": str(sales_instance.due_date.strftime('%d/%m/%Y')),
                "credit_period" : str(sales_instance.credit_period),
                "mail":sales_instance.buyer_contact_person.email,
                "payment_terms" : sales_instance.payment_terms,
                "Table Name": ['SI', "HSNTABLE", "OtherIncome"],
                "Other Table": ["OtherIncome"],
                "OtherIncome_Datas": [
                    {
                        "account": other_charges.other_income_charges_id.name,
                        # "%": other_charges.discount_value if  other_charges.discount_value else "",
                        # "tax": other_charges.tax,
                        "Total": format_currency(other_charges.after_discount_value, sales_instance.currency.Currency.currency_symbol,False) 
                        if other_charges.after_discount_value and other_charges.after_discount_value != 0.00 else format_currency(other_charges.amount, 
                                            sales_instance.currency.Currency.currency_symbol, False)
                    }
                    for other_charges in sales_instance.other_income_charge.all()
                ],
                "OtherIncome_Style":{
                    "account":"right",
                    "%":"right",
                    "tax":"right",
                    "Total":"right"
                },
                "SI_Columns": {
                    "S.No": "No",
                    "Description": "Description",
                    "HSN": "Item's HSN Code (Text)",
                    "Qty": "Quantity",
                    # "UOM": "UOM's Name",
                    "Rate": "Rate",
                    "Disc": "Disc",
                    "%": "%",
                    "Amount": "Amount",
                    "Total": "Total"
                },
                "SI_Datas":[
                    {
                        "No": f"{str(index + 1)}",
                        "Description": (
                            f"{itemdetail.description}" +
                            (
                                lambda: (
                                    # Group by display (non-empty)
                                    "".join(
                                        f"\n \n  • {display}" + "\n    " + "\n    ".join([
                                            f"{i2.itemmaster.description}"
                                            for i2 in itemdetail.item_combo_item_details.all()
                                            if i2.display and i2.display.strip() == display
                                        ])
                                        for display in (set(
                                            i.display.strip()
                                            for i in itemdetail.item_combo_item_details.all()
                                            if i.display and i.display.strip()
                                        ))
                                    )
                                    +
                                    (
                                        "\n \n • No DisPlay\n    " + "\n    ".join([
                                            f"{i.itemmaster.description}"
                                            for i in itemdetail.item_combo_item_details.all()
                                            if not i.display or not i.display.strip()
                                        ])
                                        if any(
                                            not i.display or not i.display.strip()
                                            for i in itemdetail.item_combo_item_details.all()
                                        )
                                        else ""
                                    )
                                )
                            )()
                        ),
                        "Item's HSN Code (Text)": f"{itemdetail.hsn.hsn_code}",
                        "Quantity": f"{itemdetail.qty:.0f} {itemdetail.uom.name}",
                        "Rate": f"{itemdetail.rate:.2f}",
                        "Disc": (
                                (
                                    f"{remove_number(discount_percentage(itemdetail))}%"
                                    if discount_percentage(itemdetail) and discount_percentage(itemdetail) > 0
                                    else remove_number(discount_value(itemdetail))
                                    if discount_value(itemdetail) and discount_value(itemdetail) > 0
                                    else remove_number(itemdetail.final_value)
                                    if itemdetail.final_value
                                    else ""
                                )
                            ),
                        "%": str(int(itemdetail.tax)) if float(itemdetail.tax).is_integer() else str(float(itemdetail.tax)),
                        "Amount": f"{round((itemdetail.tax * itemdetail.amount) / 100, 2)}",
                        "Total": f"{itemdetail.amount:.2f}"
                    }
                    for index, itemdetail in enumerate(sales_instance.item_details.all())
                ],
                "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "HSN": "center",
                    "Qty": "center",
                    "UOM": "center",
                    "Rate": "right",
                    "Disc": "right",
                    "%": "right",
                    "Amount": "right",
                    "Total": "right"
                },
                "HSNTABLE_Columns": {
                    "S.No[S.No]": "S.No",
                    "HSN/SAC[HSN/SAC]": "HSN/SAC",
                    "Taxable Value[Taxable Value]": "Taxable Value",
                    "CGST[%]": "cgst %",
                    "CGST[Amount]": "cgst Amount",
                    "SGST[%]": "sgst %",
                    "SGST[Amount]": "sgst Amount",
                    "IGST[%]": "igst %",
                    "IGST[Amount]": "igst Amount"
                },
                "HSNTABLE_Datas": [ taxdata for taxdata in list_tax],
                "totalAmoutInWords": num2words(sales_instance.net_amount, lang='en').title() + " Only",
                "termsandcondition": tc,
                "departmentName": sales_instance.department.name,
                "AfterTax": format_currency(sales_instance.net_amount, sales_instance.currency.Currency.currency_symbol,False),
                "gst": format_currency(float(sales_instance.tax_total),  sales_instance.currency.Currency.currency_symbol, False),
                "totalTax": format_currency(str(float(sales_instance.taxable_value)), sales_instance.currency.Currency.currency_symbol, False),
                "bankName":bank_data.bank_name if bank_data else "",
                "ifsc":bank_data.ifsc_code if bank_data else "",
                "accountNo":bank_data.account_number if bank_data else "",
                "branch":bank_data.branch_name if bank_data else ""
                } 
            except Exception  as e:
              print('An exception occurred',e)
            


            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\SalesOrderNewView2.docx".format(BASE_DIR)
                if not is_discount_applied:
                    if status == "Draft":
                        print(1)
                        doc_path = r"{}\static\PDF_TEMP\SO Template_ND_V03 - Draft.docx".format(BASE_DIR)
                    else:
                        print(2)
                        doc_path = r"{}\static\PDF_TEMP\SO Template_ND_V03 - Submit.docx".format(BASE_DIR)
                else:
                    if status == "Draft":
                        print(3)
                        doc_path = r"{}\static\PDF_TEMP\SO Template_V03 - Draft.docx".format(BASE_DIR)
                    else:
                        print(4)
                        doc_path = r"{}\static\PDF_TEMP\SO Template_V03 - Submit.docx".format(BASE_DIR)
                    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/SalesOrderNew.docx".format(BASE_DIR)
                if not is_discount_applied:
                    if status == "Draft":
                        doc_path = r"{}/static/PDF_TEMP/SO Template_ND_V03 - Draft.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}/static/PDF_TEMP/SO Template_ND_V03 - Submit.docx".format(BASE_DIR)
                else:
                    if status == "Draft":
                        doc_path = r"{}/static/PDF_TEMP/SO Template_V03 - Draft.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}/static/PDF_TEMP/SO Template_V03 - Submit.docx".format(BASE_DIR)
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, sales_order_data)
            doc.save(output_docx)
            pdf_path = convert_docx_to_pdf(output_docx)
            pdf_base64 = None
            # Generate the PDF
            # Read the generated DOCX into memory and encode it
            with open(pdf_path, 'rb') as docx_file:
                docx_data = docx_file.read()
                pdf_base64 = base64.b64encode(docx_data).decode('utf-8')

            # Clean up the temporary file (uncomment this line if needed)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(output_docx):
                os.remove(output_docx)

            success = True 
        except Exception as e:
            print(e)
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForSalesOrderNew(pdf_data =pdf_base64, success=success, errors=errors)

"""Target start"""
def targetPreValidations(kwargs):
    required_fields = [
        "target_name", "financial_year_start", "financial_year_end",
        "target_module", "target_field", "currency",
        "total_target_value", "created_by","target_mode"
    ]

    # Validate required fields
    errors = [f"{field.replace('_', ' ').title()} is required" for field in required_fields if not kwargs.get(field)]
    # Validate Achievement value already exist
    if "id" in kwargs and kwargs['id']:
        Target_instance = Target.objects.get(id=kwargs['id'])
        target_achievement_data = Target_instance.get_target_achievement_exists()
        if target_achievement_data["status"]:
            sales_person = target_achievement_data["sales_person"]
            achievement_value = target_achievement_data["target_achievement"]
            errors.append(f'Some Achievement Is Already Exist for {sales_person} with a target value of {achievement_value}. So We Cannot Edit This Target.')
            
    # Extract only valid sales persons from input
    salesPersonList = [person["sales_person"] for person in kwargs.get("target_sales_person", []) if
                       "sales_person" in person]
    if not errors and Target.objects.filter(target_name__iexact=kwargs.get("target_name")
                                            ).exclude(id=kwargs.get("id")).exists():
        errors.append("Target name must be unique")
    if not errors and salesPersonList:
        # Get existing salespersons with targets (excluding current target if updating)
        existing_targets = Target.objects.filter(
            financial_year_start=kwargs["financial_year_start"],
            financial_year_end=kwargs["financial_year_end"],
            target_sales_person__sales_person__in=salesPersonList
        ).exclude(id=kwargs.get("id")).values_list(
            "target_sales_person__sales_person__id", "target_sales_person__sales_person__username"
        ).distinct()

        # Filter only those that are in salesPersonList
        existing_salespersons = {sp_id: sp_name for sp_id, sp_name in existing_targets if sp_id in salesPersonList}

        if existing_salespersons:
            salesperson_names = ", ".join(existing_salespersons.values())
            errors.append(f"Target already exists for: {salesperson_names}")

    # Validate modified_by if ID exists
    if "id" in kwargs and kwargs.get("id") and not kwargs.get("modified_by"):
        errors.append("Modified By is required")

    # Validate target_sales_person
    target_sales_persons = kwargs.get("target_sales_person", [])
    if not target_sales_persons:
        errors.append("Target Sales Person List is required")
    else:
        for person in target_sales_persons:
            sales_person_id = person.get("sales_person")
            if not sales_person_id:
                errors.append("Sales Person is required")
                continue

            role = Roles.objects.filter(id=person.get("role")).first()
            if not role:
                errors.append("Role is required")
                continue

            user = User.objects.get(id=sales_person_id)

            if person.get("is_head") or person.get("target_months"):
                for month in person.get("target_months", []):
                    if "month" not in month or not (1 <= month["month"] <= 12):
                        errors.append(f"{user.username}: Invalid Month")

                    if "target_value" not in month or month["target_value"] < 0:
                        errors.append(f"{user.username}: Invalid Target Value")
            else:
                errors.append(f"{user.username}: Target Months are required")
    success = len(errors) == 0
    return {"success": success, "error": errors}

def saveSalesPersonTarget(target_sales_person):
    errors = []
    target_sales_person_instance_ids = []  # Store IDs instead of instances

    try:
        for person in target_sales_person:
            sales_person_id = person.get("sales_person")
            user = User.objects.get(id=sales_person_id)
            role = Roles.objects.filter(id=person.get("role")).first()

            # Check if TargetSalesperson exists
            if person.get("id"):
                target_sales_person_instance = TargetSalesperson.objects.get(id=person["id"])
                target_sales_person_instance.is_head = person.get("is_head", False)
                target_sales_person_instance.save()
            else:
                target_sales_person_instance = TargetSalesperson.objects.create(
                    sales_person=user, is_head=person.get("is_head", False), role=role
                )

            # Process target months
            target_month_list = []
            for month in person.get("target_months", []):
                if month.get("id"):
                    target_month = TargetMonth.objects.get(id=month["id"])
                    target_month.month = month.get("month", target_month.month)
                    target_month.target_value = month.get("target_value", target_month.target_value)
                    target_month.save()
                else:
                    target_month = TargetMonth.objects.create(
                        month=month.get("month", 0),
                        target_value=month.get("target_value", 0)
                    )
                target_month_list.append(target_month)

            # Update ManyToMany relation
            target_sales_person_instance.target_months.set(target_month_list)
            target_sales_person_instance_ids.append(target_sales_person_instance.id)  # Append ID

    except Exception as e:
        errors.append(str(e))

    return {"success": not errors, "target_sales_person_ids": target_sales_person_instance_ids, "error": errors}

class TargetMonthInput(graphene.InputObjectType):
    id = graphene.ID()
    month = graphene.Int()
    target_value = graphene.Decimal()

class Target_Sales_personInput(graphene.InputObjectType):
    id = graphene.ID()
    is_head = graphene.Boolean()
    role = graphene.Int()
    sales_person = graphene.Int()
    target_months = graphene.List(TargetMonthInput)

class TargetCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        target_name = graphene.String()
        financial_year_start = graphene.Date()
        financial_year_end = graphene.Date()
        target_module = graphene.String()
        target_field = graphene.String()
        target_mode = graphene.String()
        currency = graphene.Int()
        total_target_value = graphene.Decimal()
        target_sales_person = graphene.List(Target_Sales_personInput)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("Target", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        # Pre-validation
        validation_result = targetPreValidations(kwargs)
        if not validation_result["success"]:
            return TargetCreateMutation(success=False, errors=validation_result["error"])

        # Process target sales persons if provided
        person_target_result = {"success": False, "target_sales_person_ids": []}
        if kwargs.get("target_sales_person"):
            person_target_result = saveSalesPersonTarget(kwargs["target_sales_person"])

        if not person_target_result["success"]:
            return TargetCreateMutation(success=False, errors=person_target_result["error"])

        # Update kwargs with sales person IDs
        kwargs["target_sales_person"] = person_target_result["target_sales_person_ids"]
        # Save Target
        result = commanSaveAllModel(Target, kwargs, TargetSerializer, Target)
        return TargetCreateMutation(success=result["success"], errors=result["errors"])

class TargetDeleteMutation(graphene.Mutation):
    """Target Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Target", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            Target_instance = Target.objects.get(id=id)
            target_achievement_data = Target_instance.get_target_achievement_exists()
            if target_achievement_data["status"]:
                sales_person = target_achievement_data["sales_person"]
                achievement_value = target_achievement_data["target_achievement"]
                
                errors.append(f'Some Achievement Is Already Exist for {sales_person} with a target value of {achievement_value}. So We Cannot Delete This Target.')
            else:
                Target_instance.delete()
                success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return TargetDeleteMutation(success=success, errors=errors)

"""Target End"""


"""Deliver Challen end"""

class SalesInvoice_otherIncomeChargesInput(graphene.InputObjectType):
    id = graphene.ID()
    parent = graphene.Int()
    other_income_charges_id = graphene.Int()
    tax = graphene.Decimal()
    amount = graphene.Decimal()
    discount_value = graphene.Decimal()
    after_discount_value = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()

class SalesInvoice_itemcombo(graphene.InputObjectType):
    id = graphene.ID()
    item_combo = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    after_discount_value_for_per_item = graphene.Decimal()
    amount = graphene.Decimal()

class SalesInvoice_ItemDetailInput(graphene.InputObjectType):
    id = graphene.ID()
    item = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    amount = graphene.Decimal()
    item_combo = graphene.List(SalesInvoice_itemcombo)
    after_discount_value_for_per_item = graphene.Decimal()
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    final_value = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()
    tax = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    tds_value = graphene.Decimal()
    tcs_value = graphene.Decimal()

def SaveSalesInvoiceItemDetails(data):
    ItemDetails_id = []
    errors = []

    for item in data:
        combo_items = item.get("item_combo", [])
        combo_ids = []
        if combo_items:
            for combo in combo_items:
                serialize_combo = SalesInvoiceItemComboSerialzer(data=combo)
                if serialize_combo.is_valid():
                    serialize_combo.save()
                    combo_ids.append(serialize_combo.instance.id)
                else:
                    error_list = [f"{field}: {', '.join(errs)}" for field, errs in serialize_combo.errors.items()]
                    return {"ids": [], "success": False, "error": error_list}
        item['item_combo_item_details'] = combo_ids

        item_detail_list = item.get("item_detail", [])
        for itemdetail in item_detail_list:
            serialize_itemdetils = SalesInvoiceItemDetailSerialzer(data=itemdetail)
            if serialize_itemdetils.is_valid():
                serialize_itemdetils.save()
                ItemDetails_id.append(serialize_itemdetils.instance)
            else:
                for field, errs in serialize_itemdetils.errors.items():
                    errors.append(f"{field}: {', '.join(errs)}")

    return {"ids": ItemDetails_id, "success": len(errors) == 0, "error": errors}

"""Sales invoice start"""
class SalesInvoiceCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        sales_invoice_date = graphene.Date()
        sales_dc = graphene.List(graphene.Int)
        due_date = graphene.Date()
        exchange_rate = graphene.String()
        buyer = graphene.Int(required=True)
        buyer_address = graphene.Int(required=True)
        buyer_contact_person = graphene.Int(required=True)
        buyer_gstin_type = graphene.String(required=True)
        buyer_gstin = graphene.String(required=True)
        buyer_state = graphene.String(required=True)
        buyer_place_of_supply = graphene.String(required=True)
        consignee = graphene.Int(required=True)
        consignee_address = graphene.Int(required=True) 
        consignee_contact_person = graphene.Int(required=True)
        consignee_gstin_type = graphene.String(required=True)
        consignee_gstin = graphene.String(required=True)
        consignee_state = graphene.String(required=True)
        consignee_place_of_supply = graphene.String(required=True)
        remarks = graphene.String()
        creadit_period = graphene.Int()
        sales_person = graphene.String()
        payment_term = graphene.String()
        customer_po = graphene.String()
        customer_po_date = graphene.Date()
        department = graphene.Int()
        item_detail = graphene.List(SalesInvoice_ItemDetailInput)
        other_income_charge = graphene.List(SalesInvoice_otherIncomeChargesInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        igst_value = graphene.JSONString()
        sgst_value = graphene.JSONString()
        cgst_value = graphene.JSONString()
        cess_value = graphene.JSONString()
        tds_bool = graphene.Boolean()
        tcs_bool = graphene.Boolean()
        tds_total = graphene.Decimal()
        tcs_total = graphene.Decimal()
        overall_discount_percentage = graphene.Decimal()
        overall_discount_value = graphene.Decimal()
        discount_final_total = graphene.Decimal()
        item_total_befor_tax = graphene.String()
        other_charges_befor_tax = graphene.String()
        taxable_value = graphene.String()
        tax_total = graphene.String()
        round_off = graphene.String()
        round_off_method = graphene.String()
        net_amount = graphene.String()
    
    SalesInvoice = graphene.Field(SalesInvoice_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString()
    other_income_charges = graphene.JSONString()
    sales_account_ledger = graphene.JSONString()

    @status_mutation_permission("Sales Invoice")
    def mutate(self, info, **kwargs):
        success = True
        status = kwargs.get('status')

        """Validation Class"""
        service =  SalesInvoiceService(kwargs, status, info)
        validations_result = service.process()     
        if not validations_result['success']:
            return SalesInvoiceCreateMutations(SalesInvoice=None,
                                    success= False,
                                    errors=validations_result['errors'],
                                    item_details= json.dumps(validations_result.get("item_detail") , cls=DecimalEncoder) if validations_result.get("item_detail") else None
                        , other_income_charges= json.dumps(validations_result.get("other_income_charges"), cls=DecimalEncoder) if validations_result.get("other_income_charges") else None,
                        sales_account_ledger= json.dumps(validations_result.get("sales_account_ledger"), cls=DecimalEncoder) if validations_result.get("sales_account_ledger") else None)
        
        return SalesInvoiceCreateMutations(
            SalesInvoice=validations_result['SalesInvoice'],
            success= True ,
            errors=validations_result["errors"],
            )

class SalesInvoiceCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Sales Invoice", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        sales_invoice = None
        with transaction.atomic():
            # Get 'Canceled' status for Sales Invoice
            status_obj = CommanStatus.objects.filter(name='Canceled', table="Sales Invoice").first()
            if not status_obj:
                errors.append("Ask developer to add 'Canceled' status for 'Sales Invoice' in CommanStatus table.")
                return SalesInvoiceCancelMutation(success=False, errors=errors)

            # Try fetching Sales Invoice
            try:
                sales_invoice = SalesInvoice.objects.get(id=id)

                if sales_invoice.status.name == "Canceled":
                    errors.append("Sales Invoice already Cancel.")
                    return SalesInvoiceCancelMutation(success=False, errors=errors)
            except SalesInvoice.DoesNotExist:
                errors.append("Sales Invoice Not Found.")
                return SalesInvoiceCancelMutation(success=False, errors=errors)
            except Exception as e:
                errors.append("Unexpected error occurred while fetching Sales Invoice.")
                return SalesInvoiceCancelMutation(success=False, errors=errors)

            # Attempt to cancel the sales invoice
            try:
                # Unlink other income charges
                for other_charge in sales_invoice.other_income_charge.all():
                    other_charge.parent = None
                    other_charge.save()
                    
                prev_status = sales_invoice.status.name
                print("satra")
                for itemdetail in sales_invoice.item_detail.all():
                    sales_dc = itemdetail.item
                    if sales_dc.sales_order_item_detail.item_combo and sales_dc.item_combo_itemdetails.exists():
                        for combo in itemdetail.item_combo.all():
                            dc_combo = combo.item_combo
                            if prev_status == "Draft" and (dc_combo.invoice_draft_count or 0) >= (combo.qty or 0):
                                dc_combo.invoice_draft_count  =  (dc_combo.invoice_draft_count or 0) - (combo.qty or 0)
                            elif prev_status == "Submit" and (dc_combo.invoice_submit_count or 0) >= (combo.qty or 0):
                                dc_combo.invoice_submit_count = (dc_combo.invoice_submit_count or 0) - (combo.qty or 0)
                            dc_combo.save()

                    if sales_dc:
                        if prev_status == "Draft":
                            if (sales_dc.invoice_draft_count or 0) >= (itemdetail.qty or 0):
                                sales_dc.invoice_draft_count = (sales_dc.invoice_draft_count or 0) - (itemdetail.qty or 0)
                            else:
                                sales_dc.invoice_draft_count = 0

                        elif prev_status == "Submit":
                            if (sales_dc.invoice_submit_count or 0) >= (itemdetail.qty or 0):
                                sales_dc.invoice_submit_count = (sales_dc.invoice_submit_count or 0) - (itemdetail.qty or 0)
                            else:
                                sales_dc.invoice_submit_count = 0

                        sales_dc.save()
                print("end")
                sales_invoice.status = status_obj
                sales_invoice.save()
                success = True
                if prev_status == "Submit":
                    sales_invoice_general_ledger  = AccountsGeneralLedger.objects.filter(sales_invoice_voucher_no=sales_invoice.id)
                    if sales_invoice_general_ledger.exists():
                        for general_ledger in sales_invoice_general_ledger:
                            general_ledger.delete()

            except Exception as e:
                errors.append(f"Unexpected error occurred while updating Sales Invoice: {e}")

        return SalesInvoiceCancelMutation(success=success, errors=errors)

class SalesInvoiceDeleteMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @mutation_permission("Sales Invoice", create_action="Draft", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        sales_invoice = None
        try:
            sales_invoice = SalesInvoice.objects.get(id=id)
        except Exception as e:
            errors.append("Sales Invoice Not Found.")
            return SalesInvoiceDeleteMutations(success=success,
                                            errors=errors)
        if sales_invoice and sales_invoice.status and  sales_invoice.status.name == "Canceled":
            sales_invoice.delete()
            return SalesInvoiceDeleteMutations( success=True,
                                            errors=errors)
        else:
            errors.append("Can't Delete This Sales Invoice.")
            return SalesInvoiceDeleteMutations( success=success, errors=errors)

class GeneratePdfForSalesOrderDeliverChallan(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id):
        success = False
        errors = []
        def remove_number(data):
            if data:
                value = float(data)
                return int(value) if value.is_integer() else value
            else:
                return ""
        pdf_base64 = None
        try:
            sales_order_dc_instance = SalesOrder_2_DeliveryChallan.objects.get(id=id)
            # discount_percentage = lambda d: d.discount_percentage or 0
            # discount_value = lambda d: d.discount_value or 0
            
            html = sales_order_dc_instance.terms_conditions_text
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            aggregated_data = {}
            def safe_float(value):
                return float(value) if value not in [None, "null"] else 0.0

                # Aggregate item details
            for item in sales_order_dc_instance.item_details.all():
                hsn = item.sales_order_item_detail.hsn.hsn_code
                rate = safe_float(item.sales_order_item_detail.after_discount_value_for_per_item) \
                    if item.sales_order_item_detail.after_discount_value_for_per_item else safe_float(item.sales_order_item_detail.rate)
                qty = safe_float(item.qty)
                 
                taxable_value = (rate * qty)

                cgst = safe_float(item.sales_order_item_detail.cgst)
                sgst = safe_float(item.sales_order_item_detail.sgst)
                igst = safe_float(item.sales_order_item_detail.igst)

                if hsn not in aggregated_data:
                    aggregated_data[hsn] = {
                        "taxable": 0.0,
                        "cgst": cgst,
                        "sgst": sgst,
                        "igst": igst
                    }

                aggregated_data[hsn]["taxable"] += taxable_value

                # Final tax list
                list_tax = []

                for i, (hsn, data) in enumerate(aggregated_data.items(), start=1):
                    taxable = data["taxable"]
                    cgst = data["cgst"]
                    sgst = data["sgst"]
                    igst = data["igst"]

                    list_tax.append({
                                "S.No": str(i),
                                "HSN/SAC": str(hsn),
                                "Taxable Value": f"{taxable:.2f}",
                                "cgst %": f"{cgst:.2f}%" if cgst else "-",
                                "cgst Amount": f"{(cgst * taxable / 100):.2f}" if cgst else "-",
                                "sgst %": f"{sgst:.2f}%" if sgst else "-",
                                "sgst Amount": f"{(sgst * taxable / 100):.2f}" if sgst else "-",
                                "igst %": f"{igst:.2f}%" if igst else "-",
                                "igst Amount": f"{(igst * taxable / 100):.2f}" if igst else "-"
                            })
            print("Due Date",sales_order_dc_instance.sales_order.due_date)
            sales_order_data = {
                "customerName": sales_order_dc_instance.sales_order.consignee.company_name,
                "customerAddress":f"{sales_order_dc_instance.sales_order.consignee_address.address_line_1},\n"
                                f"{sales_order_dc_instance.sales_order.consignee_address.address_line_2},"
                                f"{sales_order_dc_instance.sales_order.consignee_address.city} - {sales_order_dc_instance.sales_order.consignee_address.pincode},\n"
                                f"{sales_order_dc_instance.sales_order.consignee_address.state}, {sales_order_dc_instance.sales_order.consignee_address.country}." if sales_order_dc_instance.sales_order.consignee_address.address_line_2 and sales_order_dc_instance.sales_order.consignee_address.address_line_2 != None else
                                f"{sales_order_dc_instance.sales_order.consignee_address.address_line_1},\n"
                                f"{sales_order_dc_instance.sales_order.consignee_address.city} - {sales_order_dc_instance.sales_order.consignee_address.pincode},\n"
                                f"{sales_order_dc_instance.sales_order.consignee_address.state}, {sales_order_dc_instance.sales_order.consignee_address.country}.",
                # "customerAddress": f"{sales_order_dc_instance.sales_order.consignee_address.address_line_1} {sales_order_dc_instance.sales_order.consignee_address.address_line_2},"
                #                 f"{sales_order_dc_instance.sales_order.consignee_address.city} {sales_order_dc_instance.sales_order.consignee_address.state},"
                #                 f"{sales_order_dc_instance.sales_order.consignee_address.country} {sales_order_dc_instance.sales_order.consignee_address.pincode}.",
                "salesOrder":sales_order_dc_instance.sales_order.sales_order_no.linked_model_id,
                "customerPO":sales_order_dc_instance.sales_order.customer_po_no,
                "dueDate":str(sales_order_dc_instance.sales_order.due_date.strftime('%d/%m/%Y')),
                "eWay":sales_order_dc_instance.e_way_bill if sales_order_dc_instance.e_way_bill else "-",
                "contactPerson": sales_order_dc_instance.sales_order.consignee_contact_person.contact_person_name,
                "phoneNumber": sales_order_dc_instance.sales_order.consignee_contact_person.phone_number,
                "mail": sales_order_dc_instance.sales_order.consignee_contact_person.email,
                "dcNo": sales_order_dc_instance.dc_no.linked_model_id,
                "dcDate": str(sales_order_dc_instance.dc_date.strftime('%d/%m/%Y')),
                "salesPerson": sales_order_dc_instance.sales_order.sales_person.username,
                "buyerGstIn": sales_order_dc_instance.sales_order.consignee_gstin,
                "Table Name": ['SI', "HSNTABLE"],
                "SI_Columns": {
                    "S.No": "No",
                    "Description": "Description",
                    "HSN": "Item's HSN Code (Text)",
                    "Qty": "Quantity",
                    "UOM": "UOM's Name",
                    "Rate": "Rate",
                    "Disc": "Disc",
                    "%": "%",
                    "Amount": "Amount",
                    "Total": "Total"
                },
                "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "HSN": "center",
                    "Qty": "center", 
                    "Rate": "right",
                    "Disc": "right",
                    "%": "right",
                    "Amount": "right",
                    "Total": "right"
                },
                "SI_Datas":[
                        {
                            "No": str(index + 1),
                            "Description": (
                                f"{itemdetail.sales_order_item_detail.description}" +
                                (
                                    lambda: (
                                        # Group by display (non-empty)
                                        "".join(
                                            f"\n \n  • {display}" + "\n    " + "\n    ".join([
                                                f"{i2.item_combo.itemmaster.description}"
                                                for i2 in itemdetail.item_combo_itemdetails.all()
                                                if i2.item_combo.display and i2.item_combo.display.strip() == display
                                            ])
                                            for display in sorted(set(
                                                i.item_combo.display.strip()
                                                for i in itemdetail.item_combo_itemdetails.all()
                                                if i.item_combo.display and i.item_combo.display.strip()
                                            ))
                                        )
                                        +
                                        (
                                            "\n \n • No DisPlay\n    " + "\n    ".join([
                                                f"{i.item_combo.itemmaster.description}"
                                                for i in itemdetail.item_combo_itemdetails.all()
                                                if not i.item_combo.display or not i.item_combo.display.strip()
                                            ])
                                            if any(
                                                not i.item_combo.display or not i.item_combo.display.strip()
                                                for i in itemdetail.item_combo_itemdetails.all()
                                            )
                                            else ""
                                        )
                                    )
                                )() 
                            ),
                            "Item's HSN Code (Text)": itemdetail.sales_order_item_detail.hsn.hsn_code,
                            "Quantity": f"{itemdetail.qty:.0f} {itemdetail.sales_order_item_detail.uom.name}",
                            "Rate": f"{itemdetail.sales_order_item_detail.rate:.2f}",
                            # "Disc":  (
                            #     (
                            #         f"{remove_number(discount_percentage(itemdetail))}%"
                            #         if discount_percentage(itemdetail) and discount_percentage(itemdetail) > 0
                            #         else remove_number(discount_value(itemdetail))
                            #         if discount_value(itemdetail) and discount_value(itemdetail) > 0
                            #         else remove_number(itemdetail.final_value)
                            #         if itemdetail.final_value
                            #         else ""
                            #     )
                            # ),
                            # "%": itemdetail.sales_order_item_detail.tax,
                            "%": str(int(itemdetail.sales_order_item_detail.tax)) if float(itemdetail.sales_order_item_detail.tax).is_integer() else str(float(itemdetail.sales_order_item_detail.tax)),
                            "Amount": round((itemdetail.sales_order_item_detail.tax * itemdetail.amount) / 100, 2),
                            "Total": f"{itemdetail.amount:.2f}"
                        }
                        for index, itemdetail in enumerate(sales_order_dc_instance.item_details.all())
                    ]
                ,
                "HSNTABLE_Columns": {
                    "S.No[S.No]": "S.No",
                    "HSN/SAC[HSN/SAC]": "HSN/SAC",
                    "Taxable Value[Taxable Value]": "Taxable Value",
                    "CGST[%]": "cgst %",
                    "CGST[Amount]": "cgst Amount",
                    "SGST[%]": "sgst %",
                    "SGST[Amount]": "sgst Amount",
                    "IGST[%]": "igst %",
                    "IGST[Amount]": "igst Amount"
                },

                "HSNTABLE_Datas": [ taxdata for taxdata in list_tax],

                "totalAmoutInWords": num2words(sales_order_dc_instance.nett_amount, lang='en').title() + " Only",
                "termsandcondition": tc,
                "departmentName": sales_order_dc_instance.sales_order.department.name, 
                "AfterTax": format_currency(sales_order_dc_instance.nett_amount, sales_order_dc_instance.sales_order.currency.Currency.currency_symbol,False),
                "gst": format_currency(float(sales_order_dc_instance.tax_total),  sales_order_dc_instance.sales_order.currency.Currency.currency_symbol, False),
                "totalTax": format_currency(str(float(sales_order_dc_instance.before_tax)), sales_order_dc_instance.sales_order.currency.Currency.currency_symbol, False)
            }
         
            current_os = platform.system().lower()
            if current_os == 'windows':
                if sales_order_dc_instance.status.name == "Draft":
                    doc_path = r"{}\static\PDF_TEMP\Sales_Dc_ND_v03-Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}\static\PDF_TEMP\Sales_Dc_ND_v03-Submit.docx".format(BASE_DIR)
                output_docx = r"{}\static\PDF_OUTPUT\SalesOrderDCNew.docx".format(BASE_DIR)
            else:
                if sales_order_dc_instance.status.name == "Draft":
                    doc_path = r"{}/static/PDF_TEMP/Sales_Dc_ND_v03-Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}/static/PDF_TEMP/Sales_Dc_ND_v03-Submit.docx".format(BASE_DIR)
                
                output_docx = r"{}/static/PDF_OUTPUT/SalesOrderDCNew.docx".format(BASE_DIR)

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, sales_order_data)
            doc.save(output_docx)
            pdf_path = convert_docx_to_pdf(output_docx)
            
            # Generate the PDF
            # Read the generated DOCX into memory and encode it
            with open(pdf_path, 'rb') as docx_file:
                docx_data = docx_file.read()
                pdf_base64 = base64.b64encode(docx_data).decode('utf-8')
            # Clean up the temporary file (uncomment this line if needed)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(output_docx):
                os.remove(output_docx)
            success = True
        except Exception as e: 
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForSalesOrderDeliverChallan(pdf_data =pdf_base64, success=success, errors=errors)

"""Sales invoice end"""

"""Direct Sales invoice Start"""

class SalesAccountLedgerInput(graphene.InputObjectType):
    id = graphene.ID()
    account_master = graphene.Int()
    hsn = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    amount = graphene.Decimal()
    after_discount_value_for_per_item = graphene.Decimal()
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    final_value = graphene.Decimal()
    igst = graphene.Decimal()
    cgst = graphene.Decimal()
    sgst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    tds_value = graphene.Decimal()
    tcs_value = graphene.Decimal()

class DirectSalesInvoiceItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    itemmaster = graphene.Int()
    description = graphene.String()
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    after_discount_value_for_per_item = graphene.Decimal()
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    final_value = graphene.Decimal()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    igst = graphene.Decimal()
    cgst = graphene.Decimal()
    sgst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    tds_value = graphene.Decimal()
    tcs_value = graphene.Decimal()
    amount = graphene.Decimal()

class DirectSalesInvoiceCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        direct_sales_invoice_date = graphene.Date()
        due_date = graphene.Date()
        gst_nature_transaction = graphene.Int()
        buyer = graphene.Int(required=True)
        buyer_address = graphene.Int(required=True)
        buyer_contact_person = graphene.Int(required=True)
        buyer_gstin_type = graphene.String(required=True)
        buyer_gstin = graphene.String(required=True)
        buyer_state = graphene.String(required=True)
        buyer_place_of_supply = graphene.String(required=True)
        consignee = graphene.Int(required=True)
        consignee_address = graphene.Int(required=True) 
        consignee_contact_person = graphene.Int(required=True)
        consignee_gstin_type = graphene.String(required=True)
        consignee_gstin = graphene.String(required=True)
        consignee_state = graphene.String(required=True)
        consignee_place_of_supply = graphene.String(required=True)
        currency = graphene.Int(required=True)
        remarks = graphene.String()
        creadit_period = graphene.Int()
        sales_person = graphene.String()
        payment_term = graphene.String()
        customer_po = graphene.String()
        customer_po_date = graphene.Date()
        department = graphene.Int()
        item_detail = graphene.List(DirectSalesInvoiceItemDetailsInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        igst_value = graphene.JSONString()
        sgst_value = graphene.JSONString()
        cgst_value = graphene.JSONString()
        cess_value = graphene.JSONString()
        tds_bool = graphene.Boolean()
        tcs_bool = graphene.Boolean()
        tds_total = graphene.Decimal()
        tcs_total = graphene.Decimal()
        overall_discount_percentage = graphene.Decimal()
        overall_discount_value = graphene.Decimal()
        discount_final_total = graphene.Decimal()
        item_total_befor_tax = graphene.String()
        other_charges_befor_tax = graphene.String()
        taxable_value = graphene.String()
        tax_total = graphene.String()
        round_off = graphene.String()
        round_off_method = graphene.String()
        net_amount = graphene.String()
    
    DirectSalesInvoice = graphene.Field(DirectSalesInvoice_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString()
    sales_account_ledger = graphene.JSONString()

    @status_mutation_permission("Direct Sales Invoice")
    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        """Validation Class"""
        service =  DirectSalesInvoiceService(kwargs, status, info)
        validations_result = service.process()
        if not validations_result['success']:
            return DirectSalesInvoiceCreateMutations(DirectSalesInvoice=None,
                                    success= False,
                                    errors=validations_result['errors'],
                                    item_details= json.dumps(validations_result.get("item_detail") , cls=DecimalEncoder) if validations_result.get("item_detail") else None,)
        return DirectSalesInvoiceCreateMutations(
            DirectSalesInvoice=validations_result.get("direct_sales_invoice_obj"),
            success= True ,
            errors=validations_result["errors"],
            item_details= json.dumps(validations_result.get("item_detail") , cls=DecimalEncoder) if validations_result.get("item_detail") else None)

class DirectSalesInvoiceCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Direct Sales Invoice", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        sales_invoice = None
        # Get 'Canceled' status for Sales Invoice
        status_obj = CommanStatus.objects.filter(name='Canceled', table="Sales Invoice").first()
        if not status_obj:
            errors.append("Ask developer to add 'Canceled' status for 'Direct Sales Invoice' in CommanStatus table.")
            return DirectSalesInvoiceCancelMutation(success=False, errors=errors)

        # Try fetching Sales Invoice
        try:
            sales_invoice = DirectSalesInvoice.objects.get(id=id)

            if sales_invoice.status.name == "Canceled":
                errors.append("Direct Sales Invoice already Cancel.")
                return DirectSalesInvoiceCancelMutation(success=False, errors=errors)
        except SalesInvoice.DoesNotExist:
            errors.append("Direct Sales Invoice Not Found.")
            return DirectSalesInvoiceCancelMutation(success=False, errors=errors)
        except Exception as e:
            errors.append("Unexpected error occurred while fetching Sales Invoice.")
            return DirectSalesInvoiceCancelMutation(success=False, errors=errors)

        # Attempt to cancel the sales invoice
        sales_invoice.status = status_obj
        sales_invoice.save()
        success = True
        direct_sales_invoice_general_ledger  = AccountsGeneralLedger.objects.filter(direct_sales_voucher_no=sales_invoice.id)
        if direct_sales_invoice_general_ledger.exists():
            for general_ledger in direct_sales_invoice_general_ledger:
                general_ledger.delete() 

        return DirectSalesInvoiceCancelMutation(success=success, errors=errors)

class DirectSalesInvoiceDeleteMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @mutation_permission("Direct Sales Invoice", create_action="Draft", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        sales_invoice = None
        try:
            sales_invoice = DirectSalesInvoice.objects.get(id=id)
        except Exception as e:
            errors.append("Sales Invoice Not Found.")
            return DirectSalesInvoiceDeleteMutations(success=success,
                                            errors=errors)
        if sales_invoice and sales_invoice.status and  sales_invoice.status.name == "Canceled":
            sales_invoice.delete()
            return DirectSalesInvoiceDeleteMutations( success=True,
                                            errors=errors)
        else:
            errors.append("Can't Delete This Sales Invoice.")
            return DirectSalesInvoiceDeleteMutations( success=success, errors=errors)


"""Direct Sales invoice end"""

"""sales return start"""
 

class SalesReturnBatch_item(graphene.InputObjectType):
    id = graphene.ID()
    batch_str = graphene.String()
    batch = graphene.Int()
    qty = graphene.Int()
    
class SalesRetun_ItemCombo(graphene.InputObjectType):
    id = graphene.ID() 
    itemmaster = graphene.Int()
    item_detail = graphene.Int()
    dc_item_combo = graphene.Int()
    sales_invoice_item_combo = graphene.Int()
    serial = graphene.List(graphene.Int)
    store = graphene.Int()
    batch_link = graphene.List(SalesReturnBatch_item)
    qty = graphene.Decimal()
    allowed_qty = graphene.Decimal()
    amount = graphene.Decimal()

class SalesReturn_ItemDetailInput(graphene.InputObjectType):
    id = graphene.ID() 
    itemmaster = graphene.Int()
    sales_return = graphene.Int()
    dc_item_detail = graphene.Int()
    sales_invoice_item_detail = graphene.Int()
    item_combo = graphene.List(SalesRetun_ItemCombo)
    batch_link = graphene.List(SalesReturnBatch_item)
    serial = graphene.List(graphene.Int)
    store = graphene.Int()
    qty = graphene.Decimal()
    allowed_qty = graphene.Decimal()
    amount = graphene.Decimal()
    igst = graphene.Decimal()
    cgst = graphene.Decimal()
    sgst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cess_value = graphene.Decimal() 
 
class SalesReturnCretedMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        sr_date = graphene.Date()
        sales_order= graphene.Int()
        e_way_bill = graphene.String()
        e_way_bill_date = graphene.Date()
        comman_store = graphene.Int()
        reason = graphene.String()
        item_details = graphene.List(SalesReturn_ItemDetailInput)
        sales_dc_ids = graphene.List(graphene.Int)
        sales_invoice_ids = graphene.List(graphene.Int)
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        igst_value = graphene.Decimal()
        sgst_value = graphene.Decimal()
        cgst_value = graphene.Decimal()
        cess_value = graphene.Decimal() 
        item_total_befor_tax = graphene.Decimal() 
        tax_total = graphene.Decimal()
        taxable_value = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
    
    salesReturn = graphene.Field(salesReturn_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @status_mutation_permission("Purchase Return")
    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        salesReturn = SalesReturnService(kwargs, status, info)
        service_result = salesReturn.process()
        
        return SalesReturnCretedMutations(
                salesReturn=service_result.get("sales_return"),
                success=service_result.get("success"),
                errors=service_result.get("errors"))

class SalesReturnCancelMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
    
    salesReturn = graphene.Field(salesReturn_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    need_stock = graphene.List(graphene.JSONString)

    @mutation_permission("Purchase Return", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id): 
        salesReturn = SalesReturnCancelService(id)
        service_result = salesReturn.process() 
        print("service_result", service_result)
        return SalesReturnCancelMutations(
                salesReturn=service_result.get("sales_return"),
                success=service_result.get("success"),
                errors=service_result.get("errors"),
                need_stock = service_result.get("need_stock"))

class SalesReturnDeleteMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
     
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase Return", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        errors = []
        try:
            sales_return_instance = SalesReturn.objects.filter(id=id).first()
            
            if not sales_return_instance:
                return SalesReturnDeleteMutations(success=success, errors=errors)
            
            if sales_return_instance:
                if sales_return_instance.status.name in ['Canceled']:
                    sales_return_instance.delete()
            
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules.')
        except Exception as e:
            errors.append(str(e))
        return SalesReturnDeleteMutations(success=success, errors=errors)

class GeneratePdfForSalesReturn(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            sales_return = SalesReturn.objects.get(id=id)
            if not sales_return:
                return GraphQLError("Sales return not found") 
            html = sales_return.terms_conditions_text
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            status = sales_return.status.name 
            dc = sales_return.salesorder_2_deliverychallan_set.first() 
            sales_order = dc.sales_order
            
            def find_batch_serial(itemdetail):
                if itemdetail.serial.exists():
                    return ", ".join( serial.serial_number for serial in  itemdetail.serial.all())
                elif itemdetail.batch.salesreturnbatch_item_set.exists():
                         
                    return ", ".join( batch.batch.batch_number_name for batch in itemdetail.batch.salesreturnbatch_item_set.all())

                return ""
            try:
                sales_return = {
                    "salesRetunNo":str(sales_return.sr_no.linked_model_id),
                    "salesReturnDate":str(sales_return.sr_date.strftime('%d/%m/%Y')),
                    "buyerName":sales_order.buyer.company_name ,
                    "buyerAddress":f"{sales_order.buyer_address.address_line_1},\n"
                                f"{sales_order.buyer_address.address_line_2},"
                                f"{sales_order.buyer_address.city} - {sales_order.buyer_address.pincode},\n"
                                f"{sales_order.buyer_address.state}, {sales_order.buyer_address.country}." if sales_order.buyer_address.address_line_2 and sales_order.buyer_address.address_line_2 != None else
                                f"{sales_order.buyer_address.address_line_1},\n"
                                f"{sales_order.buyer_address.city} - {sales_order.buyer_address.pincode},\n"
                                f"{sales_order.buyer_address.state}, {sales_order.buyer_address.country}.",
                    "gstIn":sales_order.buyer_gstin if sales_order.buyer_gstin else "",
                    "contactPerson":sales_order.buyer_contact_person.contact_person_name if sales_order.buyer_contact_person else "",
                    "phoneNumber":sales_order.buyer_contact_person.phone_number if sales_order.buyer_contact_person else "",
                    "mail":sales_order.buyer_contact_person.email if sales_order.buyer_contact_person else "",

                    "consigneeName":sales_order.consignee.company_name ,
                    "consigneeAddress":f"{sales_order.consignee_address.address_line_1},\n"
                                f"{sales_order.consignee_address.address_line_2},"
                                f"{sales_order.consignee_address.city} - {sales_order.consignee_address.pincode},\n"
                                f"{sales_order.consignee_address.state}, {sales_order.consignee_address.country}." if sales_order.consignee_address.address_line_2 and sales_order.consignee_address.address_line_2 != None else
                                f"{sales_order.consignee_address.address_line_1},\n"
                                f"{sales_order.consignee_address.city} - {sales_order.consignee_address.pincode},\n"
                                f"{sales_order.consignee_address.state}, {sales_order.consignee_address.country}.",
                    "consigneegstIn":sales_order.consignee_gstin if sales_order.consignee_gstin else "",
                    "consigneecontactPerson":sales_order.consignee_contact_person.contact_person_name if sales_order.consignee_contact_person else "",
                    "consigneephoneNumber":sales_order.consignee_contact_person.phone_number if sales_order.consignee_contact_person else "",
                    "consigneemail":sales_order.consignee_contact_person.email if sales_order.consignee_contact_person else "",


                    "salesOrderNo":sales_order.sales_order_no.linked_model_id,
                    "dcNo":dc.dc_no.linked_model_id if dc else  "",
                    "dueDate":str(sales_order.due_date.strftime('%d/%m/%Y')) if sales_order.due_date else "",
                    "ewayBill":sales_return.e_way_bill if sales_return.e_way_bill else "",
                    "Table Name": ['SI'],
                    "SI_Columns": {
                      "S.No": "No",
                      "Description": "Description",
                      "HSN": "Item's HSN Code (Text)",
                      "Qty": "Quantity",
                      "Batch / Serial":"BatchSerial",
                      "Rate": "Rate", 
                      "Total": "Total"
                  },
                  "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "HSN": "center",
                    "Qty": "center",
                    "BatchSerial":"center",
                    "Rate":"right", 
                    "Total": "right"
                },
                "SI_Datas": [
                    {
                    "No": str(index+1) ,
                    "Description": itemdetail.purchase_invoice_item.grn_item.first().gin.item_master.description  if itemdetail.purchase_invoice_item else itemdetail.grn_item.first().gin.item_master.description,
                    "Item's HSN Code (Text)":  itemdetail.purchase_invoice_item.grn_item.first().gin.purchase_order_parent.hsn_id.hsn_code  if itemdetail.purchase_invoice_item else itemdetail.grn_item.first().gin.purchase_order_parent.hsn_id.hsn_code,
                    "Quantity":  f"{itemdetail.po_return_qty} ({itemdetail.base_return_qty})",
                    "BatchSerial": find_batch_serial(itemdetail),

                    "Rate":   (itemdetail.purchase_invoice_item.po_rate or 0)   if itemdetail.purchase_invoice_item else (itemdetail.grn_item.first().gin.purchase_order_parent.po_rate or 0),
                    "Total":  (itemdetail.purchase_invoice_item.po_rate or 0) * (itemdetail.po_return_qty)  if itemdetail.purchase_invoice_item else ((itemdetail.grn_item.first().gin.purchase_order_parent.po_rate or 0) * itemdetail.po_return_qty)
                }
                  for index, itemdetail in enumerate(sales_return.salesreturnitemdetails_set.all())
                ],
                "taxTotal":format_currency(sales_return.net_amount, sales_order.currency.Currency.currency_symbol),
                "totalQty": f"{sum(itemdetail.qty for itemdetail in sales_return.salesreturnitemdetails_set.all()):.3f}",
                "termsandcondition":tc
                } 
            except Exception  as e:
               print("Exception in pdf",e)
               pass
            
            current_os = platform.system().lower()

            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\SalesReturn.docx".format(BASE_DIR)

                if status == "Draft":
                    doc_path = r"{}\static\PDF_TEMP\Sales Return - Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}\static\PDF_TEMP\Sales Return - Submit.docx".format(BASE_DIR)
    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/SalesReturn.docx".format(BASE_DIR)
                if status == "Draft":
                    doc_path = r"{}/static/PDF_TEMP/Sales Return - Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}/static/PDF_TEMP/Sales Return - Submit.docx".format(BASE_DIR)
                
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, sales_return)
            doc.save(output_docx)
            pdf_path = convert_docx_to_pdf(output_docx)
            pdf_base64 = None
            # Generate the PDF
            # Read the generated DOCX into memory and encode it
            with open(pdf_path, 'rb') as docx_file:
                docx_data = docx_file.read()
                pdf_base64 = base64.b64encode(docx_data).decode('utf-8')

            # Clean up the temporary file (uncomment this line if needed)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(output_docx):
                os.remove(output_docx)

            success = True 

        except Exception as e: 
            print("eeee",e)
            errors.append(f'An exception occurred in PDF creation -{str(e)}')  

        return GeneratePdfForSalesReturn(pdf_data =pdf_base64, success=success, errors=errors)


class ReceiptVoucherAdvanceInput(graphene.InputObjectType):
    id= graphene.ID()
    adv_remark = graphene.String(required=True)
    amount = graphene.Decimal(required=True)


class ReceiptVoucherAgainstInvoiceInput(graphene.InputObjectType):
    id= graphene.ID()
    salesInvoiceNo = graphene.String(required=True)
    sales_invoice = graphene.ID(required=True)
    adjusted = graphene.Decimal(required=True)
    remarks = graphene.String()

class ReceiptVoucherLineInput(graphene.InputObjectType):
    id = graphene.ID()
    account_name = graphene.String()
    account = graphene.Int()
    employee_name = graphene.String()
    employee = graphene.Int()
    pay_for = graphene.Int()
    cus_sup_name = graphene.String()
    cus_sup = graphene.Int()
    amount = graphene.Decimal()
    advance_details = graphene.List(ReceiptVoucherAdvanceInput)
    against_invoice_details = graphene.List(ReceiptVoucherAgainstInvoiceInput)

class ReceiptVoucherCreateMutataions(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        rv_date = graphene.Date(required=True)
        pay_by = graphene.String(required=True)
        pay_mode = graphene.String(required=True)
        currency = graphene.ID()
        exchange_rate = graphene.Decimal(required=True)
        against_invoice = graphene.Boolean()
        advance = graphene.Boolean()
        bank = graphene.ID()
        transfer_via = graphene.String()
        chq_ref_no = graphene.String()
        chq_date = graphene.Date() 
        receipt_voucher_lines = graphene.List(ReceiptVoucherLineInput)
        

    receipt_voucher = graphene.Field(ReceiptVoucher_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("Receipt Voucher")
    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        receipt_voucher = ReceiptVoucherService(kwargs, status, info)
        receipt_voucher_result = receipt_voucher.process()
        
        return ReceiptVoucherCreateMutataions(
                receipt_voucher=receipt_voucher_result.get("receipt_voucher"),
                success=receipt_voucher_result.get("success"),
                errors=receipt_voucher_result.get("errors"))

class ReceiptVoucherCancelMutataions(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    receipt_voucher = graphene.Field(ReceiptVoucher_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Receipt Voucher", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        receipt_voucher = None
        success = False
        errors = []
        try:
            if not id:
                errors.append("id is required.")
                return ReceiptVoucherCancelMutataions(
                    receipt_voucher=receipt_voucher,
                    success=success,
                    errors=errors)
            
            status = CommanStatus.objects.filter(table="Receipt Voucher", name="Canceled").first()
            
            if not status:
                errors.append("Cancel status is not found.")
            
            rv = ReceiptVoucher.objects.filter(id=id).first()
            
            if rv.status.name == "Canceled":
                errors.append("Already Receipt Voucher canceled.")
                return ReceiptVoucherCancelMutataions(
                receipt_voucher=receipt_voucher,
                success=success,
                errors=errors)

            
            if not rv:
                errors.append("Receipt Voucher is not found.")

            rv.status = status
            rv.save()
            receipt_voucher= rv
            
        except Exception as e:
            print("e", e)
            errors.append(f"Unexpeted error : {str(e)}")
        success = True
        return ReceiptVoucherCancelMutataions(
                receipt_voucher=receipt_voucher,
                success=success,
                errors=errors)

class ReceiptVoucherDeleteMutataions(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Receipt Voucher", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            if not id:
                errors.append("id is required.")
                return ReceiptVoucherCancelMutataions(
                    success=success,
                    errors=errors)
            
            rv = ReceiptVoucher.objects.filter(id=id).first()
            if rv.status.name != "Canceled":
                errors.append('Befor delete need to make it cancel.')
                return ReceiptVoucherCancelMutataions(
                    success=success,
                    errors=errors)

            if not rv:
                errors.append("Receipt Voucher is not found.")
                return ReceiptVoucherCancelMutataions(
                    success=success,
                    errors=errors)

            rv.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(f"Unexpeted error : {str(e)}")

        return ReceiptVoucherCancelMutataions(
                success=success,
                errors=errors)

class CreditNoteOtherIncomeChargesInput(graphene.InputObjectType):
    id = graphene.ID()
    other_income_charges = graphene.Int()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    amount = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()

class CreditNoteAccountInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int() 
    account_master = graphene.Int()
    description = graphene.String()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()

class CreditNoteItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    itemmaster = graphene.Int()
    sales_return_item = graphene.Int()
    description = graphene.String()
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()

class CreditNoteComboItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    itemmaster = graphene.Int()
    credit_note_item = graphene.Int()
    sales_return_combo_item = graphene.Int()
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    display = graphene.String()
    is_mandatory = graphene.String()
    amount = graphene.Decimal()

class CreditNoteItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    itemmaster = graphene.Int()
    sales_return_item = graphene.Int()
    description = graphene.String()
    combo_details = graphene.List(CreditNoteComboItemDetailsInput)
    uom = graphene.Int()
    qty = graphene.Decimal()
    rate = graphene.Decimal()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()

class CreditNoteCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        cn_date = graphene.Date()
        sales_return = graphene.Int()
        sales_person = graphene.Int()
        reason = graphene.String()
        remarks = graphene.String()
        currency = graphene.Int(required=True)
        exchange_rate = graphene.Decimal(required=True)
        department = graphene.Int()
        e_way_bill_no = graphene.String()
        e_way_bill_date = graphene.Date()
        gst_nature_type = graphene.String()
        gst_nature_transaction = graphene.Int()
        buyer = graphene.Int(required=True)
        buyer_address = graphene.Int(required=True)
        buyer_contact_person = graphene.Int(required=True)
        buyer_gstin_type = graphene.String(required=True)
        buyer_gstin = graphene.String(required=True)
        buyer_state = graphene.String(required=True)
        buyer_place_of_supply = graphene.String(required=True)

        consignee = graphene.Int(required=True)
        consignee_address = graphene.Int(required=True)
        consignee_contact_person = graphene.Int(required=True)
        consignee_gstin_type = graphene.String(required=True)
        consignee_gstin = graphene.String(required=True)
        consignee_state = graphene.String(required=True)
        consignee_place_of_supply = graphene.String(required=True)
        
        item_details = graphene.List(CreditNoteItemDetailsInput)
        other_income_charge = graphene.List(CreditNoteOtherIncomeChargesInput)
        accounts = graphene.List(CreditNoteAccountInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        tds_bool = graphene.Boolean()
        tcs_bool = graphene.Boolean()
        tds_total = graphene.Decimal()
        tcs_total = graphene.Decimal()
        item_total_befor_tax = graphene.Decimal()
        other_charges_befor_tax = graphene.Decimal()
        taxable_value = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
    
    credit_note = graphene.Field(credit_note_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString()
    other_incomes = graphene.JSONString()

    # @status_mutation_permission("Credit Note")
    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        service = CreditNoteService(kwargs, status, info)
        service_result = service.process()
        print(service_result)
        return CreditNoteCreateMutations(
            credit_note=service_result.get("credit_note_invoice"),
            success= service_result.get("success") ,
            errors=service_result.get("errors"),
            item_details= service_result.get("item_details") if service_result.get("item_details") else None,
            other_incomes = service_result.get("other_income") if service_result.get("other_income") else None,
            # accounts = service_result.get("accounts") if service_result.get("accounts") else None
        )

class CreditNoteCancelMutataions(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    credit_note = graphene.Field(credit_note_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    # @mutation_permission("Credit Note", create_action="Save", edit_action="Cancel")
    def mutate(self, info, id):
        credit_note = None
        success = False
        errors = []
        try:
            if not id:
                errors.append("id is required.")
                return CreditNoteCancelMutataions(
                    credit_note=credit_note,
                    success=success,
                    errors=errors)
            
            status = CommanStatus.objects.filter(table="Credit Note", name="Canceled").first()
            if not status:
                errors.append("Cancel status is not found.")
            cn = CreditNote.objects.filter(id=id).first()
            if not cn:
                errors.append("Credit Note is not found.")
            if cn.status.name == "Canceled":
                return CreditNoteCancelMutataions( credit_note=credit_note, success=success, errors=["This credit note is already cancelled can't be cancelled again"])
            cn.status = status
            cn.save()
            credit_note= cn
            success = True
        except Exception as e:
            print("e---",e)
            self.errors.append(f"Unexpeted error : {str(e)}")

        return CreditNoteCancelMutataions(
                credit_note=credit_note,
                success=success,
                errors=errors)

class CreditNoteDeleteMutataions(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    # @mutation_permission("Credit Note", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            if not id:
                errors.append("id is required.")
                return CreditNoteDeleteMutataions(
                    success=success,
                    errors=errors)
            
            cn = CreditNote.objects.filter(id=id).first()
            if not cn:
                errors.append("Credit Note is not found.")
                return CreditNoteDeleteMutataions(
                success=success,
                errors=errors)
            if cn.status.name != "Canceled": 
                errors.append("Before delete need to cancel.")
            else:
                cn.delete()
                success = True
        except ProtectedError as e:
            print(e)
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(f"Unexpeted error : {str(e)}")

        return CreditNoteDeleteMutataions(
                success=success,
                errors=errors)


class Mutation(graphene.ObjectType):
    note_create_mutation = NoteCreateMutation.Field()
    note_delete_mutation = NoteDeleteMutation.Field()

    activity_type_create_mutation = ActivityTypeCreateMutation.Field()
    activity_type_delete_mutation = ActivityTypeDeleteMutation.Field()

    activity_create_mutation = ActivityCreateMutation.Field()
    activity_delete_mutation = ActivityDeleteMutation.Field()
    activity_calender_mutation = ActivityCalenderMutation.Field()

    email_templete_create_mutation = EmailTempleteCreateMutation.Field()
    email_templete_delete_mutation = EmailTempleteDeleteMutation.Field()

    replace_email_temple_tags = ReplaceEmailTempleTags.Field()

    email_record_create_mutation = EmailRecordCreateMutation.Field()
    bulk_email_create_mutation = BulkEmailCreateMutation.Field()

    leads_create_mutation = LeadsCreateMutation.Field()
    lead_sales_person_update_mutation = LeadSalesPersonUpdateMutation.Field()
    lead_data_import_mutations = LeadDataImportMutations.Field()
    leads_delete_mutation = LeadsDeleteMutation.Field()

    other_income_charges_create_mutation = OtherIncomeChargesCreateMutation.Field()
    other_income_charges_delete_mutation = OtherIncomeChargesDeleteMutation.Field()

    get_item_combo_item_details = getItemComboItemDetails.Field()

    quotations_create_mutation = QuotationsCreateMutation.Field()
    quotations_delete_mutation = QuotationsDeleteMutation.Field()
    quotations_canceled_mutation = QuotationsCanceledMutation.Field()
    generate_pdf_for_quotation_new = GeneratePdfForQuotationNew.Field()

    salesOrder_2_create_mutation = SalesOrder_2CreateMutation.Field()
    salesOrder_2_canceled_mutation = SalesOrder_2CanceledMutation.Field()
    salesOrder_2_delete_mutation = SalesOrder_2DeleteMutation.Field()
    generate_pdf_for_sales_order_new = GeneratePdfForSalesOrderNew.Field()

    target_create_mutation = TargetCreateMutation.Field()
    target_delete_mutation = TargetDeleteMutation.Field()

    salesOrder_2__deliver_challen_creted_mutations = SalesOrder_2_DeliverChallenCretedMutations.Field()
    salesOrder_2_deliver_challen_cancele_mutations = SalesOrder_2_DeliverChallenCanceleMutations.Field()
    salesOrder_2__deliver_challen_delete_mutations = SalesOrder_2_Deliver_ChallanDeleteMutation.Field()
    
    tax_validation_befor_sales_order_DC = TaxValidationBeforSalesOrder_DC.Field()
    generate_pdf_for_sales_order_deliver_challan = GeneratePdfForSalesOrderDeliverChallan.Field()

    

    sales_invoice_create_mutations = SalesInvoiceCreateMutations.Field()
    sales_invoice_cancel_mutation = SalesInvoiceCancelMutation.Field()
    sales_invoice_delete_mutations = SalesInvoiceDeleteMutations.Field()

    direct_sales_invoice_create_mutations =  DirectSalesInvoiceCreateMutations.Field()
    direct_sales_invoice_cancel_mutation = DirectSalesInvoiceCancelMutation.Field()
    direct_sales_invoice_delete_mutations = DirectSalesInvoiceDeleteMutations.Field()

    sales_return_create_mutations = SalesReturnCretedMutations.Field()
    sales_return_cancel_mutations = SalesReturnCancelMutations.Field()
    sales_return_delete_mutations = SalesReturnDeleteMutations.Field()
    generate_pdf_for_sales_return = GeneratePdfForSalesReturn.Field()

    receipt_voucher_create_mutataions = ReceiptVoucherCreateMutataions.Field()
    receipt_voucher_cancel_mutataions = ReceiptVoucherCancelMutataions.Field()
    receipt_voucher_delete_mutataions = ReceiptVoucherDeleteMutataions.Field()

    credit_note_create_mutations = CreditNoteCreateMutations.Field()
    credit_note_delete_mutataions = CreditNoteDeleteMutataions.Field()
    credit_note_cancel_mutataions = CreditNoteCancelMutataions.Field()