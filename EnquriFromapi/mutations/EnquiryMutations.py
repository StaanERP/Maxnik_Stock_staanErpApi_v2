import graphene
from EnquriFromapi.models import *
from django.db.models import ProtectedError
from EnquriFromapi.Schema import *
from EnquriFromapi.serializers import *
from pathlib import Path
import requests
from EnquriFromapi.views import send_email
from itemmaster.models import SalesOrder, ContactDetalis, SupplierFormData, Contact_type
from itemmaster.schema import ContactDetalisType, SupplierFormDataType
from itemmaster.Utils.CommanUtils import *
from EnquriFromapi.views import  sendWhatsApp

# def sendWhatsApp(name, number, templeName):
#     url = f"https://live-mt-server.wati.io/330840/api/v1/sendTemplateMessage?whatsappNumber={number}"

#     payload = "{\"parameters\":[{\"name\":\"name\",\"value\":\"" + name + "\"}],\"template_name\":\"" + templeName + "\",\"broadcast_name\":\"" + templeName + "\"}"
#     # payload = "{ \"template_name\":\""+templeName+"\",\"broadcast_name\":\""+templeName+"\"}"
#     headers = {
#         "content-type": "application/json-patch+json",
#         "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2OTM1NTgzOS1kMWJlLTQ4NjEtYmJjMC03OWNlZDg1NjQ5YTkiLCJ1bmlxdWVfbmFtZSI6ImFudG9ueUBzdGFhbi5pbiIsIm5hbWVpZCI6ImFudG9ueUBzdGFhbi5pbiIsImVtYWlsIjoiYW50b255QHN0YWFuLmluIiwiYXV0aF90aW1lIjoiMDcvMjkvMjAyNCAwOTowODoyMSIsImRiX25hbWUiOiJtdC1wcm9kLVRlbmFudHMiLCJ0ZW5hbnRfaWQiOiIzMzA4NDAiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.NxLCWxfKtmvclbXLLpLO20ZlvahCosCi6epqmubHBBU"
#     }
#     response = requests.post(url, data=payload, headers=headers)
#     print(response)


class EnquiryDataCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        organization_name = graphene.String()
        email = graphene.String()
        alternate_mobile_number = graphene.String()
        other_number = graphene.String()
        link_contact_detalis = graphene.Int()
        mobile_number = graphene.String()
        location = graphene.String()
        message = graphene.String()
        interests = graphene.List(graphene.String)
        conference_data = graphene.Int()
        sales_person = graphene.Int()
        remarks = graphene.String()
        follow_up = graphene.String()
        status = graphene.String()
        pincode = graphene.Int()
        district = graphene.Int()
        state = graphene.Int()
        counter = graphene.String()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    enquiry_data = graphene.Field(EnquiryDataType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Enquiry", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        enquiry_data_item = None
        success = False
        errors = []
        created_by = User.objects.get(id=kwargs['created_by'])
        conference = None
        if not kwargs.get('conference_data'):
            default_conference = Conferencedata.objects.filter(name="Direct").first()
             
            if default_conference:
                kwargs['conference_data'] = default_conference.id
            else:
                errors.append("Default conference data not found.")
        else:
            conference = Conferencedata.objects.filter(id=kwargs.get('conference_data')).first()
        if 'id' in kwargs:
            enquiry_data_item = enquiryDatas.objects.filter(id=kwargs['id']).first()
            if "link_contact_detalis" in kwargs and kwargs['link_contact_detalis']:
                try:
                    # Retrieve the existing contact details
                    contact = ContactDetalis.objects.get(id=kwargs['link_contact_detalis'])
                    # Compare the old contact details with the new values
                    if contact.contact_person_name != kwargs.get('name', contact.contact_person_name) or \
                            contact.email != kwargs.get('email', contact.email) or \
                            contact.phone_number != kwargs.get('mobile_number', contact.phone_number) or \
                            contact.whatsapp_no != kwargs.get('alternate_mobile_number', contact.whatsapp_no):
                        # Update the contact details
                        contact.contact_person_name = kwargs.get('name', contact.contact_person_name)
                        contact.email = kwargs.get('email', contact.email)
                        contact.phone_number = kwargs.get('mobile_number', contact.phone_number)
                        contact.whatsapp_no = kwargs.get('alternate_mobile_number', contact.whatsapp_no)
                        contact.modified_by = created_by
                        contact.save()

                except ContactDetalis.DoesNotExist:
                    errors.append("The provided contact details ID does not exist.")
                    return EnquiryDataCreateMutation(success=success, errors=errors)
            if not enquiry_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = EnquirySerializers(enquiry_data_item, data=kwargs, partial=True)
        else:
            serializer = EnquirySerializers(data=kwargs)

            if not kwargs['link_contact_detalis']:
                contact_type = Contact_type.objects.get(name="Enquiry")
                if contact_type:
                    if ContactDetalis.objects.filter(
                            phone_number__iexact=kwargs['mobile_number']).exists():
                        errors.append("Alredy Mobile Number in Contact.")
                        return EnquiryDataCreateMutation(enquiry_data=enquiry_data_item, success=success,
                                                         errors=errors)
                    else:
                        try:

                            contact = ContactDetalis.objects.create(contact_person_name=kwargs['name'],
                                                                    email=kwargs['email'],
                                                                    phone_number=kwargs['mobile_number'],
                                                                    whatsapp_no=kwargs.get("alternate_mobile_number",
                                                                                           ""),
                                                                    contact_type=contact_type, created_by=created_by)
                            kwargs['link_contact_detalis'] = contact.id
                        except Exception as e:
                            errors.append(e)
                            return EnquiryDataCreateMutation(enquiry_data=enquiry_data_item, success=success,
                                                             errors=errors)
                else:
                    errors.append("Ask admin to add enquiry Type in Contact.")
                    return EnquiryDataCreateMutation(enquiry_data=enquiry_data_item, success=success,
                                                     errors=errors)
            elif "link_contact_detalis" in kwargs and kwargs['link_contact_detalis']:
                try:
                    # Retrieve the existing contact details
                    contact = ContactDetalis.objects.get(id=kwargs['link_contact_detalis'])

                    # Compare the old contact details with the new values
                    if contact.contact_person_name != kwargs.get('name', contact.contact_person_name) or \
                            contact.email != kwargs.get('email', contact.email) or \
                            contact.phone_number != kwargs.get('mobile_number', contact.phone_number) or \
                            contact.whatsapp_no != kwargs.get('alternate_mobile_number', contact.whatsapp_no):
                        # Update the contact details
                        contact.contact_person_name = kwargs.get('name', contact.contact_person_name)
                        contact.email = kwargs.get('email', contact.email)
                        contact.phone_number = kwargs.get('mobile_number', contact.phone_number)
                        contact.whatsapp_no = kwargs.get('alternate_mobile_number', contact.whatsapp_no)
                        contact.save()

                except ContactDetalis.DoesNotExist:
                    errors.append("The provided contact details ID does not exist.")
                    return EnquiryDataCreateMutation(success=success, errors=errors)

        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:
                print(e, "error---->")
            if 'id' not in kwargs:
                email_value = kwargs['email']
                intrested = kwargs['interests']

                BASE_DIR = Path(__file__).resolve().parent.parent.parent
                pdf_path = BASE_DIR / "PDF"
                intrested_list = [] 
                for data in (intrested):
                    product_name = product.objects.filter(id=data).first()
                    intrested_list.append(pdf_path / str(str(product_name.Name) + ".pdf"))
                    
                if 'alternate_mobile_number' in kwargs and kwargs['alternate_mobile_number'] and kwargs[
                    'name']:
                    pass
                    sendWhatsApp(kwargs['name'], kwargs['alternate_mobile_number'], conference.name if conference and conference.name else "Conference")
                try:
                    if email_value:
                        send_email(email_value, intrested_list)
                except Exception as e:
                    pass
            enquiry_data_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return EnquiryDataCreateMutation(enquiry_data=enquiry_data_item, success=success,
                                         errors=errors)


def EnquiryPrevalidation(enquirydatas):
    errors = []
    modifiedDatas = []
    serializer_list = []

    for index, enquirydata in enumerate(enquirydatas):
        enquirydata['status'] = "Not Contacted"
        enquirydata['alternate_mobile_number'] = enquirydata['alternate_mobile_number'] \
            if enquirydata['alternate_mobile_number'] not in ["", None] else None
        enquirydata['other_number'] = enquirydata['other_number'] \
            if enquirydata['other_number'] not in ["", None] else None
        contact_type = Contact_type.objects.get(name="Enquiry")
        if ContactDetalis.objects.filter(phone_number__iexact=enquirydata['mobile_number']).exists():
            oldContact = ContactDetalis.objects.filter(phone_number__iexact=enquirydata['mobile_number']).first()
            enquirydata['link_contact_detalis'] = oldContact.id
        else:
            try:
                contact = ContactDetalis.objects.create(
                    contact_person_name=enquirydata['name'],
                    email=enquirydata['email'],
                    phone_number=enquirydata['mobile_number'],
                    whatsapp_no=enquirydata.get("alternate_mobile_number", ""),
                    contact_type=contact_type
                )
                enquirydata['link_contact_detalis'] = contact.id
            except Exception as e:
                errors.append({"modifiedRowIndex": index, "errors": str(e)})
        pincode = Pincode.objects.filter(pincode=enquirydata['pincode']).first()
        if pincode:
            address = AddressMaster.objects.filter(pincode=pincode.id).first()
            if address:
                enquirydata['pincode'] = address.pincode.id
                enquirydata['district'] = address.district.id
                enquirydata['state'] = address.state.id
            else:
                errors.append({"modifiedRowIndex": index, "errors": "Pincode not in list"})
        else:
            errors.append({"modifiedRowIndex": index, "errors": "Pincode not in list"})
        conference_data = Conferencedata.objects.filter(name=str(enquirydata['conference_data']).strip()).first()
        if conference_data:
            enquirydata['conference_data'] = conference_data.id
        else:
            errors.append({"modifiedRowIndex": index, "errors": f"{enquirydata['conference_data']} not found."})

        if "interests" in enquirydata and enquirydata['interests']:
            interest_list_ = str(enquirydata['interests'][0]).split(",")
            interest_list = [interest_list_i.strip() for interest_list_i in interest_list_]
            product_name = product.objects.filter(Name__in=interest_list)
            enquirydata['interests'] = [pro.id for pro in product_name]
        else:
            enquirydata['interests'] = []
        modifiedDatas.append(enquirydata)

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
            serializer = EnquirySerializers(data=modifiedData)
            if serializer.is_valid():
                serializer_list.append(serializer)
            else:
                field_errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in
                                serializer.errors.items()]
                final_errors.append({"modifiedRowIndex": index, "errors": field_errors})

    return {"success": len(final_errors) == 0, "error": final_errors, "serializer_list": serializer_list}


class EnquiryDataInput(graphene.InputObjectType):
    name = graphene.String()
    organization_name = graphene.String()
    email = graphene.String()
    alternate_mobile_number = graphene.String()
    other_number = graphene.String()
    mobile_number = graphene.String()
    message = graphene.String()
    interests = graphene.List(graphene.String)
    conference_data = graphene.String()
    pincode = graphene.Int()
    counter = graphene.String()
    created_by = graphene.Int()


# conference_data interests
class EnquiryDataImportMutations(graphene.Mutation):
    class Arguments:
        enquiryDatalist = graphene.List(EnquiryDataInput)

    success = graphene.Boolean()
    errors = graphene.List(graphene.JSONString)

    def mutate(self, info, enquiryDatalist):
        success = False
        errors = []
        result = EnquiryPrevalidation(enquiryDatalist)

        if result["success"]:
            for serializer_data in result['serializer_list']:
                serializer_data.save()
            success = True
        else:
            errors = result["error"]

        return EnquiryDataImportMutations(success=success, errors=errors)


class EnquiryDataDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.Int)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Enquiry", create_action="Create", edit_action="Delete")
    def mutate(self, info, id=None, id_list=None):
        success = False
        errors = []
        try:
            enquiry_data_instance = None
            if id:
                enquiry_data_instance = enquiryDatas.objects.get(pk=id)
            if id_list:
                enquiry_data_instance = enquiryDatas.objects.filter(pk__in=id_list)
            if enquiry_data_instance:
                enquiry_data_instance.delete()
                success = True
            else:
                errors.append('This data not found')
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return EnquiryDataDeleteMutation(success=success, errors=errors)


class EnquiryDataSalesPersonMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)
        sales_person = graphene.Int()

    enquiry_data = graphene.Field(EnquiryDataType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id_list=None, sales_person=None):
        success = False
        errors = []
        items = []
        try:
            sales_person_instance = User.objects.get(id=sales_person)
        except:
            sales_person_instance = None
        if id_list and sales_person_instance:
            try:
                items = enquiryDatas.objects.filter(id__in=id_list)
                for item in items:
                    item.sales_person = sales_person_instance
                enquiryDatas.objects.bulk_update(items, ['sales_person'])
                success = True
            except Exception as e:
                success = False
                errors = [e]
        else:
            errors = ["Given data doesn't exists"]
        return EnquiryDataSalesPersonMutation(success=success, errors=errors)


class ConferenceDataCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        in_charge = graphene.Int()
        start_date = graphene.String()
        end_date = graphene.String()
        status = graphene.Boolean()
        created_by = graphene.Int(required = True)
        modified_by = graphene.Int()
        default_store = graphene.Int()
        currency = graphene.Int()
        additional_in_charges = graphene.List(graphene.Int)

    conference_data_item = graphene.Field(ConferencedataType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Conference", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        conference_data_item = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id'] is not None:
            conference_data_item = Conferencedata.objects.filter(id=kwargs['id']).first()
            if not conference_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = ConferenceSerializers(conference_data_item, data=kwargs, partial=True)
        else:
            serializer = ConferenceSerializers(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            conference_data_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ConferenceDataCreateMutation(conference_data_item=conference_data_item, success=success, errors=errors)


def checkConferenceLinkWithOtheTable(id):
    SalesOrder_id = SalesOrder.objects.filter(marketingEvent=id).first()
    if SalesOrder_id:
        return False
    else:
        return True


class ConferenceDataDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.Int)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Conference", create_action="Save", edit_action="Delete")
    def mutate(self, info, id=None, id_list=None):
        success = False
        errors = []
        try:
            enquiry_data_instance = None
            if id:
                enquiry_data_instance = Conferencedata.objects.get(id=id)
            if id_list:
                enquiry_data_instance = Conferencedata.objects.filter(id__in=id_list)
            checkLink = checkConferenceLinkWithOtheTable(id)
            if checkLink:
                if enquiry_data_instance:
                    enquiry_data_instance.delete()
                    success = True
                else:
                    errors.append('This data not found')
            else:
                errors.append('This data Linked with other modules.')
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ConferenceDataDeleteMutation(success=success, errors=errors)


class GetContactDetails(graphene.Mutation):
    class Arguments:
        contact_number = graphene.String(required=True)  # Corrected argument name to follow Python conventions

    contact = graphene.Field(ContactDetalisType)  # Define the return type as a Field
    company_name = graphene.String()
    pincode = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, contact_number):
        company_name = ""
        pincode = ""
        supplier_instanc = ""
        try:
            contact = ContactDetalis.objects.filter(phone_number=contact_number).first()
            if contact:
                supplier_instanc = SupplierFormData.objects.filter(contact=contact.id).first()
            if supplier_instanc:
                for address in supplier_instanc.address.all():
                    if address.default:
                        pincode = address.pincode
                company_name = supplier_instanc.company_name


        except ContactDetalis.DoesNotExist:
            contact = None

        return GetContactDetails(contact=contact, company_name=company_name, pincode=pincode)


# class sendEmail(graphene.Mutation):
#     class Arguments:
#         to = graphene.String(required=True)
#         cc = graphene.List(graphene.String)
#         bcc = graphene.List(graphene.String)
#         errors = graphene.List(graphene.String)
#         subject = graphene.String()
#         body = graphene.String()
#
#     def mutate(self, info):
#         request = info.context
#         access_token = str(request.headers.get('Authorization')).replace("JWT ", "")


class Mutation(graphene.ObjectType):
    enquiry_data_create_mutation = EnquiryDataCreateMutation.Field()
    enquiry_data_import_mutations = EnquiryDataImportMutations.Field()
    # send_email_in_q
    enquiry_data_delete_mutation = EnquiryDataDeleteMutation.Field()
    enquiry_data_sales_person_mutation = EnquiryDataSalesPersonMutation.Field()

    conference_data_create_mutation = ConferenceDataCreateMutation.Field()
    conference_data_delete_mutation = ConferenceDataDeleteMutation.Field()

    get_contact_details = GetContactDetails.Field()
