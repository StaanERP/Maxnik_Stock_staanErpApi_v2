import graphene
from django.shortcuts import get_list_or_404
from django.db.models import ProtectedError
from Staanenquiryfromwithazure.settings import BASE_DIR
from itemmaster.schema import *
from itemmaster.serializer import *
from itemmaster.Utils.stockAddtinons import *
from itemmaster2.PDF.Quotations.QuotationsPDF import convert_docx_to_pdf
from itemmaster2.models import OtherIncomeCharges
from ..Utils.CommanUtils import *
from itemmaster.models import *
from itemmaster.services.itemmaster_master_services import *
from itemmaster.services.stock_addtions_serivices import *
from itemmaster.services.purchase_services import *
from itemmaster.services.stock_deletetions_services import *
from itemmaster.services.gin_services import *
from itemmaster.services.quality_inspection_report import *
from itemmaster.services.grn_services import *
from itemmaster.services.purchase_return_services import *
from itemmaster.services.purchase_dc_return import *
from itemmaster.services.purchase_invoice_services import *
from itemmaster.services.purchase_direct_invoice import *
from itemmaster.services.debit_note import *
from bs4 import BeautifulSoup
import platform
from django.db.models import F
from num2words import num2words


preDefinedError = "Error creating serial number: No matching NumberingSeries found"
from itemmaster.Utils.bom import *
from datetime import datetime

current_date = datetime.now().date()

class CompanyAddressInput(graphene.InputObjectType):
    id = graphene.ID()
    address_type = graphene.String()
    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String()
    pincode = graphene.String()
    state = graphene.String()
    country = graphene.String()
    default = graphene.Boolean()

def validate_address_details(address_data, gst_type_name):
    errors = []
    if len(address_data) == 0:
        errors.append("At least one address is required.")
    else:
        gst_type = gst_type_name
        print(gst_type)
        for address in address_data:
            if gst_type != "Export/Import":
                for field in ['address_type',"address_line_1", "city","pincode", "state","country"]:
                    if address.get(field) is None or address.get(field) == "":
                        errors.append(f"{field} is required.")
                if errors:
                    continue
                
            if 'id' in address and address['id']:
                company_address_item = CompanyAddress.objects.filter(id=address['id']).first()
                if not company_address_item:
                    errors.append(f"Address with ID {address['address_type']} not found.")
                    continue
                else:
                    serializer = ItemAddressSerializer(company_address_item, data=address, partial=True)
            else:
                serializer = ItemAddressSerializer(data=address)

            if not serializer.is_valid():
                for field, error_list in serializer.errors.items():
                    errors.append(
                        f"{address.get('address_type', 'Unknown')} - {field}: {'; '.join([str(e) for e in error_list])}")
                continue
    return errors


def validate_bank_details(bank_details):
    errors = []

    if not bank_details or len(bank_details) == 0:
        errors.append("At least one bank is required.")
        return errors  # no point checking further

    default_count = 0

    for idx, bank in enumerate(bank_details, start=1):
        if not bank.get("bank_name"):
            errors.append(f"Bank Name is required.")
        if not bank.get("branch_name"):
            errors.append(f"Branch Name is required.")
        if not bank.get("account_number"):
            errors.append(f"Account Number is required.")
        if not bank.get("ifsc_code"):
            errors.append(f"IFSC Code is required.")

        if bank.get("is_active"):
            default_count += 1

    if default_count == 0:
        errors.append("At least one bank must be marked as default.")
    elif default_count > 1:
        errors.append("Only one bank can be marked as default.")

    return errors
             


def SaveAddress(data):
    return save_items(data, CompanyAddress, ItemAddressSerializer, "Address")


def SaveBank(bank_details, company_id):
    updated_banks = []

    for bank in bank_details:
        bank['company_master'] = company_id
        updated_banks.append(bank)    

    return save_items(updated_banks,BankDetails,BankSerializer,"Bank Details")

def company_validation_result(kwargs):
    errors = []
    serializer = CompanyMasterSerializer(data=kwargs)
    if not serializer.is_valid():
        for field, error_list in serializer.errors.items():
                    errors.append(f"{field}: {'; '.join([str(e) for e in error_list])}")
        return errors
    return

class BankInput(graphene.InputObjectType):
    id = graphene.ID()
    bank_name = graphene.String()
    branch_name = graphene.String()
    account_number = graphene.String()
    ifsc_code = graphene.String()
    is_active = graphene.Boolean()

class CompanyMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        company_name = graphene.String()
        address = graphene.List(CompanyAddressInput)
        currency = graphene.Int()
        mobile = graphene.String()
        telephone = graphene.String()
        whatsapp = graphene.String()
        email = graphene.String()
        financial_year_start_from = graphene.Date()
        financial_year_end_from = graphene.Date()
        gst = graphene.Boolean()
        gst_in_type = graphene.Int()
        gstin = graphene.String()
        gstr1_filing_schedule = graphene.String()
        e_way_bill = graphene.Boolean()
        applicable_from = graphene.Date()
        threshold_for_intrastate = graphene.String()
        threshold_for_interstate = graphene.String()
        tds = graphene.Boolean()
        tds_tan_no = graphene.String()
        deductor_type = graphene.String()
        deductor_branch = graphene.String()
        tcs = graphene.Boolean()
        tcs_tan_no = graphene.String()
        collector_type = graphene.String()
        collector_branch = graphene.String()

        # Account Mapping Fields (ForeignKeys to AccountsMaster)
        sales_account = graphene.Int()
        sales_pending_account = graphene.Int()
        sales_return_account = graphene.Int()
        purchase_account = graphene.Int()
        purchase_return_account = graphene.Int()
        receivable_account = graphene.Int()
        payable_account = graphene.Int()
        purchase_pending_account = graphene.Int()
        stock_account = graphene.Int()
        stock_in_transit_account = graphene.Int()
        work_in_progress_account = graphene.Int()
        round_off_account = graphene.Int()
        forex_gain_account = graphene.Int()
        forex_loss_account = graphene.Int()
        expense_advance_account = graphene.Int()
        salary_advance_account = graphene.Int()
        expense_reimbursement_account = graphene.Int()
        salary_account = graphene.Int()
        igst_account = graphene.Int()
        cgst_account = graphene.Int()
        sgst_account = graphene.Int()
        cess_account = graphene.Int()
        tds_account = graphene.Int()
        tcs_account = graphene.Int()
        bank_details = graphene.List(BankInput)


    companyMaster = graphene.Field(company_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Company Master", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        
        companyMaster_ = None
        success = False
        errors = []

        try:
            with transaction.atomic():
                main_required_fields = [
                    "company_name", "currency", "mobile",
                    "financial_year_start_from", "financial_year_end_from"
                ]
                gst_required_fields = ['gst_in_type', "gstin", "gstr1_filing_schedule"]
                e_way_bill_required_fields = ['gst_in_type', "gstin", "gstr1_filing_schedule"]
                tdc_required_fields = ['tds_tan_no', "deductor_type"]
                tsc_required_fields = ['tcs_tan_no', "collector_type"]
                old_bank_id = []

                for field in main_required_fields:
                    if not kwargs.get(field):
                        errors.append(f"{field} is required")

                if kwargs.get("gst"):
                    for field in gst_required_fields:
                        if not kwargs.get(field):
                            errors.append(f"{field} is required because GST is enabled")

                if kwargs.get("e_way_bill"):
                    for field in e_way_bill_required_fields:
                        if not kwargs.get(field):
                            errors.append(f"{field} is required because E-Way Bill is enabled")
                if kwargs.get("tds"):
                    for field in tdc_required_fields:
                        if not kwargs.get(field):
                            errors.append(f"{field} is required because TDC is enabled")

                if kwargs.get("tcs"):
                    for field in tsc_required_fields:
                        if not kwargs.get(field):
                            errors.append(f"{field} is required because TSC is enabled") 
                address_errors = validate_address_details(kwargs.get('address'), kwargs)
                errors.extend(address_errors)

                bank_error = validate_bank_details(kwargs.get('bank_details'))
                errors.extend(bank_error) 

                company_validate = company_validation_result(kwargs) 
                if company_validate:
                    errors.extend(company_validate)
                if errors:
                    return CompanyMasterCreateMutation(success=False, errors=errors, )
                

                address_result = SaveAddress(kwargs.get('address')) 
                if not address_result['success']:
                    return CompanyMasterCreateMutation(success=False, errors=address_result["error"]) 
                
                if kwargs.get('id'):
                    try:
                        kwargs['address'] = address_result['instance_list'][0] 
                        companyMaster_ = CompanyMaster.objects.get(id=kwargs['id'])
                        serializer = CompanyMasterSerializer(companyMaster_, data=kwargs, partial=True, context={'request': info.context, "address":kwargs['address']},)
                        bank_ids = BankDetails.objects.filter(company_master__id=kwargs.get('id'))
                        old_bank_id = [bank.id for bank in bank_ids] 

                    except ObjectDoesNotExist:
                        return CompanyMasterCreateMutation(success=False, errors=["Company does not exist"])
                    except Exception as e:
                        return CompanyMasterCreateMutation(success=False, errors=[str(e)])
                else:
                    kwargs['address'] = address_result['ids'][0] 
                    serializer = CompanyMasterSerializer(data=kwargs, context={'request': info.context, "address":kwargs['address']})

                if serializer.is_valid(): 
                    serializer.save() 
                    companyMaster_ = serializer.instance 
                    bank_result = SaveBank(kwargs.get('bank_details'),companyMaster_.id) 
                    deleteCommanLinkedTable(old_bank_id, bank_result['ids'], BankDetails) 

                    if not bank_result['success']:
                        errors.extend(bank_result["error"])
                        raise ValidationError(errors)
                        
                    
                    success = True
                else:
                    errors = [f"{field}: {'; '.join(map(str, errs))}" for field, errs in serializer.errors.items()]
        except Exception as e:
            
            errors.append(f"Exception occurred: {str(e)}")

        return CompanyMasterCreateMutation(
            success=success,
            errors=errors,
            companyMaster=companyMaster_
        )





class ReportTempletedCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        report_name = graphene.String()
        report_folder = graphene.String()
        primary_model = graphene.String()
        app = graphene.String()
        share_report = graphene.List(graphene.Int)
        description = graphene.String()
        grouped_by = graphene.JSONString()
        calculation_by = graphene.JSONString()
        select_data = graphene.JSONString()
        filter_conditions = graphene.JSONString()
        chart = graphene.String()
        chart_type = graphene.String()
        chart_title = graphene.String()
        chart_date_format = graphene.String()
        x_axis = graphene.JSONString()
        y_axis = graphene.JSONString()
        group_by = graphene.JSONString()
        data_field = graphene.JSONString()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    report_template_data = graphene.Field(ReportTemplateType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("ReportTemplate", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        report_template_data = None
        success = False
        errors = []
        if "id" in kwargs and kwargs['id'] is not None:
            # Update operation
            report_template_data = ReportTemplate.objects.filter(id=kwargs['id']).first()
            if not report_template_data:
                errors.append("Report Template_data not found.")
                return ReportTempletedCreateMutation(report_template_data=report_template_data, success=success,
                                                     errors=errors)
            else:
                serializer = ReportTempletedSerializer(report_template_data, data=kwargs, partial=True)
        else:
            serializer = ReportTempletedSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                report_template_data = serializer.instance
                success = True
            except ValidationError as e:
                errors = [str(detail) for detail in e.detail]
            except Exception as e:
                errors = [str(error) for error in e]


        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return ReportTempletedCreateMutation(report_template_data=report_template_data, success=success, errors=errors)


class ReportTempletedDeleteMutation(graphene.Mutation):
    """ReportTempleted Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("ReportTemplate", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            report_template_instance = ReportTemplate.objects.get(id=id)
            report_template_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ReportTempletedDeleteMutation(success=success, errors=errors)


class UserGroupCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        group_name = graphene.String()
        sub_group_name = graphene.String()
        description = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    user_group_data = graphene.Field(UserGroupType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("UserGroup", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        user_group_data = None
        success = False
        errors = []
        if "id" in kwargs and kwargs['id'] is not None:
            # Update operation
            user_group_data = UserGroup.objects.filter(id=kwargs['id']).first()
            if not user_group_data:
                errors.append("User Group not found.")
                return UserGroupCreateMutation(user_group_data=user_group_data, success=success, errors=errors)
            elif kwargs['id'] == kwargs['sub_group_name']:
                errors.append("Invalid Sub Group")
                return UserGroupCreateMutation(user_group_data=user_group_data, success=success, errors=errors)
            else:
                serializer = UserGroupSerializer(user_group_data, data=kwargs, partial=True)
        else:
            serializer = UserGroupSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                user_group_data = serializer.instance
                success = True
            except ValidationError as e:
                errors = [str(detail) for detail in e.detail]
            except Exception as e:
                errors = [str(error) for error in e]
        else:
            errors = [f"{field}: {', '.join(errors_list)}" for field, errors_list in serializer.errors.items()]

        return UserGroupCreateMutation(user_group_data=user_group_data, success=success, errors=errors)


class UserGroupDeleteMutation(graphene.Mutation):
    """UserGroup Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("UserGroup", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            user_group_instance = UserGroup.objects.get(id=id)
            user_group_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ReportTempletedDeleteMutation(success=success, errors=errors)


def CheckItIsConnectWithAnyOtherModel(serial_instance):
    check_it_linked = ItemStock.objects.filter(serial_number=serial_instance)
    if check_it_linked:
        return True
    else:
        return False
 
 
 


class TdsMasterInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    section = graphene.String()
    payment_code = graphene.String()
    remittance_code = graphene.String()
    percent_individual_with_pan = graphene.Decimal()
    percent_other_with_pan = graphene.Decimal()
    zero_rated = graphene.Boolean()
    exemption_limit = graphene.Decimal()
    single_transaction_limit = graphene.Decimal()
    effective_date = graphene.Date()

class TcsMasterInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    section = graphene.String()
    payment_code = graphene.String()
    remittance_code = graphene.String()
    percent_individual_with_pan = graphene.Decimal()
    percent_other_with_pan = graphene.Decimal()
    percent_other_without_pan = graphene.Decimal()
    zero_rated = graphene.Boolean()
    tax_based_on_realization = graphene.Boolean()
    exemption_limit = graphene.Decimal()
    single_transaction_limit = graphene.Decimal()
    effective_date = graphene.Date()

class AlternateUnitInput(graphene.InputObjectType):
    id = graphene.ID()
    addtional_unit = graphene.Int()
    conversion_factor = graphene.Decimal()
    fixed = graphene.Boolean()
    variation = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class itemComboInput(graphene.InputObjectType):
    id = graphene.ID()
    s_no = graphene.Int()
    part_number = graphene.Int()
    item_qty = graphene.Decimal()
    item_display = graphene.Int()
    item_display_text = graphene.String()
    is_mandatory = graphene.Boolean()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class ItemMasterCreateMutation(graphene.Mutation):
    """ItemMaster Create and update"""

    # after Optimizations we did not add the  effectiveDate for hsn
    class Arguments:
        id = graphene.ID()
        item_part_code = graphene.String()
        item_name = graphene.String()
        description = graphene.String()
        item_types = graphene.Int()
        product_image = graphene.Int()
        product_document = graphene.List(graphene.Int)
        item_uom = graphene.Int()
        item_group = graphene.Int()
        alternate_uom = graphene.List(AlternateUnitInput)
        item_indicators = graphene.Int()
        category = graphene.Int()
        supplier_data = graphene.List(graphene.Int)
        purchase_uom = graphene.Int()
        item_cost = graphene.Decimal()
        item_safe_stock = graphene.Int()
        item_order_qty = graphene.Int()
        item_lead_time = graphene.Int()
        total_stock = graphene.Decimal()
        rejected_stock = graphene.Decimal()
        item_mrp = graphene.Decimal()
        item_min_price = graphene.Decimal()
        item_sales_account = graphene.Int()
        item_purchase_account = graphene.Int()
        item_hsn = graphene.Int()
        keep_stock = graphene.Boolean()
        sell_on_mrp = graphene.Boolean()
        serial = graphene.Boolean()
        location = graphene.String()
        notes = graphene.String()
        variation = graphene.String()
        enable_variation = graphene.Boolean()
        is_manufacture = graphene.Boolean()
        serial_auto_gentrate = graphene.Boolean()
        serial_format = graphene.String()
        serial_starting = graphene.Int()
        batch_number = graphene.Boolean()
        service = graphene.Boolean()
        item_warranty_based = graphene.String()
        item_installation = graphene.Boolean()
        invoice_date = graphene.Date()
        installation_data = graphene.Date()
        item_combo_bool = graphene.Boolean()
        item_combo_data = graphene.List(itemComboInput)
        item_barcode = graphene.Boolean()
        item_active = graphene.Boolean()
        item_qc = graphene.Boolean()
        tds = graphene.List(TdsMasterInput)
        tcs = graphene.List(TcsMasterInput)
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.Date()
        updated_at = graphene.Date()
        item_combo_print = graphene.Boolean()
        alternate_uom_fixed = graphene.Boolean()

    item_master = graphene.Field(ItemMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Item_Master", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs): 
        serivce =  ItemMasterService(kwargs=kwargs,info=info)
        validations_result = serivce.run_validations() 
        if not validations_result.get("success"):
            return ItemMasterCreateMutation(item_master=validations_result['item_master'], 
                                            success=validations_result['success'],
                                            errors=validations_result['errors'])
        
        return ItemMasterCreateMutation(item_master=validations_result['item_master'],
                                        success=validations_result['success'],
                                        errors=validations_result['errors'])


class ItemMasterDeleteMutation(graphene.Mutation):
    """ItemMaster Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Item_Master", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = ItemMaster.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e: 
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ItemMasterDeleteMutation(success=success, errors=errors)


class ItemGroupsNameCreateMutation(graphene.Mutation):
    """ItemGroupsName Create and update"""

    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        parent_group = graphene.Int()
        hsn = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    Item_groups_name = graphene.Field(ItemGroupsNameType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Item_Group", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        item_groups_name = None
        success = False
        errors = []
        if kwargs['id'] != None:
            # Update operation
            item_groups_name_instance = Item_Groups_Name.objects.filter(id=kwargs['id']).first()
            if not item_groups_name_instance:
                errors.append("item groups not found.")
            else:
                serializer = ItemGroupSerializer(item_groups_name_instance, data=kwargs, partial=True)
        else:
            serializer = ItemGroupSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                item_groups_name = serializer.instance
                success = True
            except ValidationError as e:
                errors = [str(detail) for detail in e.detail]
            except Exception as e:
                errors = [str(error) for error in e]


        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
            # errors_dict = {field: '; '.join([str(e) for e in error]) for field, error in serializer.errors.items()}

        return ItemGroupsNameCreateMutation(Item_groups_name=item_groups_name, success=success, errors=errors)


class ItemGroupNameDeleteMutation(graphene.Mutation):
    """ItemGroupName Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Item_Group", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_groups_name_instance = Item_Groups_Name.objects.get(id=id)
            item_groups_name_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ItemGroupNameDeleteMutation(success=success, errors=errors)


class UomCreateMutation(graphene.Mutation):
    """Uom Create and update"""

    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        e_way_bill_uom = graphene.String()
        description_text = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    Uom = graphene.Field(UOMType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("UOM", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        uom = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id'] != None:
            # Update operation
            uom_instance = UOM.objects.filter(id=kwargs['id']).first()
            
            if not uom_instance:
                errors.append("Uom not found.")

            if "e_way_bill_uom" in kwargs:
                new_value = kwargs.get("e_way_bill_uom")
                if uom_instance.e_way_bill_uom and uom_instance.e_way_bill_uom != new_value:
                    errors.append("E Way Bill UOM cannot be modified once assigned.")
                    return UomCreateMutation(Uom=None, success=False, errors=errors)

            serializer = UOMSerializer(uom_instance, data=kwargs, partial=True)
        else:
            serializer = UOMSerializer(data=kwargs)

        if serializer.is_valid():
            serializer.save()
            uom = serializer.instance
            success = True

        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return UomCreateMutation(Uom=uom, success=success, errors=errors)


class UomDeleteMutation(graphene.Mutation):
    """uom Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("UOM", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            uom_instance = UOM.objects.get(id=id)
            uom_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return UomDeleteMutation(success=success, errors=errors)

class ContactDeleteMutation(graphene.Mutation):
    """Contact Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Contact", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            contact_instance = ContactDetalis.objects.get(id=id)
            contact_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ContactDeleteMutation(success=success, errors=errors)

class HsnEffectiveDateCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        hsn_id = graphene.ID()
        hsn_code = graphene.Int()
        taxability_type = graphene.String()
        description = graphene.String()
        cess_rate = graphene.Int()
        rcm = graphene.Boolean()
        itc = graphene.Boolean()
        effective_date = graphene.String()
        gst_rates = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    effective_date = graphene.Date()
    current_date = graphene.Date()
    date_result = graphene.Boolean()

    @mutation_permission("HSN", create_action="Edit", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        success = False
        errors = []
        effective_date = None
        current_date_ = None
        date_result = None
        main_required_fields = ["hsn_id","hsn_code",'taxability_type']
        remove_field = ['cess_rate','rcm','itc','gst_rates']
        for field in main_required_fields:
            if not kwargs.get(field):
                errors.append(f"{field} is required.")
        if kwargs.get('taxability_type') != "taxable":
            for field in remove_field:
                if kwargs.get(field):
                    errors.append(f"{field} is not required.")
        if len(errors) > 0:
            return HsnEffectiveDateCreateMutation(success=success, errors=errors)

        if Hsn.objects.exclude(pk=kwargs['hsn_id']).filter(hsn_code=kwargs['hsn_code']).exists():
            errors.append(f"HSN code must be unique.")
            return HsnEffectiveDateCreateMutation(success=success, errors=errors)
        
        if 'id' in kwargs:
            # Update operation
            HsnEffectiveDate_instance = HsnEffectiveDate.objects.filter(id=kwargs['id']).first()
            if not HsnEffectiveDate_instance:
                errors.append("HsnEffectiveDate not found.")
            else:
                serializer = HsnEffectiveDateSerializer(HsnEffectiveDate_instance, data=kwargs, partial=True)
        
        else:
            serializer = HsnEffectiveDateSerializer(data=kwargs)
        if serializer.is_valid():
            current_instance = serializer.save()
            effective_date = datetime.strptime(kwargs['effective_date'], '%Y-%m-%d').date()

            current_date_str = current_date.strftime('%Y-%m-%d')
            current_date_ = datetime.strptime(current_date_str, '%Y-%m-%d').date()
            date_result  = effective_date == datetime.strptime(current_date_str, '%Y-%m-%d').date()
            if effective_date == datetime.strptime(current_date_str, '%Y-%m-%d').date():
                hsn_instance = Hsn.objects.get(id=kwargs['hsn_id'])
                hsn_instance.hsn_code = current_instance.hsn_code
                hsn_instance.gst_rates = current_instance.gst_rates
                hsn_instance.taxability_type = current_instance.taxability_type
                hsn_instance.cess_rate = current_instance.cess_rate
                hsn_instance.rcm = current_instance.rcm
                hsn_instance.itc = current_instance.itc
                hsn_instance.effective_date = current_instance.effective_date
                hsn_instance.modified_by = current_instance.modified_by
                hsn_instance.save()
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in
                    serializer.errors.items()]
        return HsnEffectiveDateCreateMutation(success=success, errors=errors, effective_date = effective_date,
                                            current_date = current_date_,  date_result = date_result)


class HsnCreateMutation(graphene.Mutation):
    """hsn Create and update"""

    class Arguments:
        id = graphene.ID()
        hsn_types = graphene.Int()
        hsn_code = graphene.Int()
        taxability_type = graphene.String()
        description = graphene.String()
        cess_rate = graphene.Int()
        rcm = graphene.Boolean()
        itc = graphene.Boolean()
        gst_rates = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    hsn = graphene.Field(Hsn_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("HSN", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        hsn = None
        success = False
        errors = []
        main_required_fields = ["hsn_types","hsn_code",'taxability_type']
        remove_field = ['cess_rate','rcm','itc','gst_rates']
        for field in main_required_fields:
            if not kwargs.get(field):
                errors.append(f"{field} is required.")
        if kwargs.get('taxability_type') != "taxable":
            for field in remove_field:
                if kwargs.get(field):
                    errors.append(f"{field} is not required.")
        if len(errors) > 0:
            return HsnCreateMutation(hsn=hsn, success=success, errors=errors)

        
        if 'id' in kwargs:
            # Update operation
            hsn_instance = Hsn.objects.filter(id=kwargs['id']).first()
            if not hsn_instance:
                errors.append("HSN not found.")
                return HsnCreateMutation(hsn=hsn, success=success, errors=errors)
            else:
                serializer = HsnSerializer(hsn_instance, data=kwargs, partial=True)
        else:
            serializer = HsnSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            hsn = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return HsnCreateMutation(hsn=hsn, success=success, errors=errors)


class HsnDeleteMutation(graphene.Mutation):
    """hsn Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("HSN", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            hsn_instance = Hsn.objects.get(id=id)
            hsn_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return HsnDeleteMutation(success=success, errors=errors)


class AccountsGroupCreateMutation(graphene.Mutation):
    """AccountsGroup Create and update"""

    class Arguments:
        id = graphene.ID()
        accounts_group_name = graphene.String()
        accounts_type = graphene.Int()
        group_active = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    accounts_groups = graphene.Field(AccountsGroupsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Account_Group", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        accounts_group = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            accounts_group_instance = AccountsGroup.objects.filter(id=kwargs['id']).first()
            
            if not accounts_group_instance:
                errors.append("Accounts Group not found.")
            else:
                if AccountsMaster.objects.filter(accounts_group_name=accounts_group_instance.id).exists() and accounts_group_instance.accounts_type.id != kwargs['accounts_type']:
                    errors.append("You cannot change the type because this group is already linked to an Account Master.")
                serializer = AccountsGroupSerializer(accounts_group_instance, data=kwargs, partial=True)
        else:
            serializer = AccountsGroupSerializer(data=kwargs)
        if len(errors) > 0:
            return AccountsGroupCreateMutation(accounts_groups=accounts_group, success=success, errors=errors)

        if serializer.is_valid():
            serializer.save()
            accounts_group = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return AccountsGroupCreateMutation(accounts_groups=accounts_group, success=success, errors=errors)


class AccountsGroupDeleteMutation(graphene.Mutation):
    """Accounts Group Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Account_Group", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            AccountsGroup_instance = AccountsGroup.objects.get(id=id)
            AccountsGroup_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return AccountsGroupDeleteMutation(success=success, errors=errors)

def AccountsMasterPrevValidation(kwargs, new_group):
    errors = []
    tds_serializer = None
    tcs_serializer = None
    if AccountsMaster.objects.exclude(pk=kwargs.get("id")).filter(accounts_name__iexact=kwargs.get('accounts_name')).exists():
            errors.append("Accounts Name must be unique.")
    TDS_REQUIRED_FIELDS = ['name', "percent_individual_with_pan", "percent_other_with_pan", "effective_date"]
    TCS_REQUIRED_FIELDS = ['name', "percent_individual_with_pan", 
                            "percent_other_with_pan", "effective_date", "percent_other_without_pan"]
    if kwargs.get("gst_applicable") and not kwargs.get("hsn"):
            errors.append("HSN is required when GST is applicable.")
    
    group_type = new_group.accounts_type.name

    if kwargs.get("gst_applicable") and group_type not in ["Expenses", "Income","Asset"]:
        errors.append("GST can only be applied to Expenses or Income accounts.")

    if len(kwargs.get("tds_link", [])) > 0 and group_type not in ["Expenses", "Income"]:
        errors.append("TDS can only be linked with Expenses or Income accounts.")

    if len(kwargs.get("tcs_link", [])) > 0 and group_type != "Income":
        errors.append("TCS can only be linked with Income accounts.")
    
    if kwargs.get("tds_link"):
        tds_data = kwargs["tds_link"][0]
        for field in TDS_REQUIRED_FIELDS:
            if tds_data.get(field) is None:
                errors.append(f"{field} is required.")

        if "id" in tds_data and tds_data["id"] and not errors:
            tds_instance = TDSMaster.objects.filter(id=tds_data["id"]).first()
            if tds_instance:
                tds_serializer = TDSMasterSerializer(tds_instance, data=tds_data, partial=True)
            else:
                errors.append("TDS not found.")
                tds_serializer = None
        elif not errors:
            tds_serializer = TDSMasterSerializer(data=tds_data)

        if tds_serializer and not tds_serializer.is_valid():
            errors.extend([f"TDS - {k}: {'; '.join(map(str, v))}" for k, v in tds_serializer.errors.items()])

    if kwargs.get("tcs_link"):
        tcs_data = kwargs["tcs_link"][0]
        for field in TCS_REQUIRED_FIELDS:
            if tcs_data.get(field) is None:
                errors.append(f"{field} is required.")

        if "id" in tcs_data and tcs_data["id"] and not errors:
            tcs_instance = TCSMaster.objects.filter(id=tcs_data["id"]).first()
            if tcs_instance:
                tcs_serializer = TCSMasterSerializer(tcs_instance, data=tcs_data, partial=True)
            else:
                errors.append("TCS not found.")
                tcs_serializer = None
        elif not errors:
            tcs_serializer = TCSMasterSerializer(data=tcs_data)

        if tcs_serializer and not tcs_serializer.is_valid():
            errors.extend([f"TCS - {k}: {'; '.join(map(str, v))}" for k, v in tcs_serializer.errors.items()])
        
    if kwargs['account_type'] == "Tax":
        if new_group.accounts_type.name in ['Liabilities', "Asset"]:
            if kwargs.get("tax_type") != "gst" and kwargs.get('gst_type'):
                errors.append("GST Type is only allowed when Tax Type is set to GST.")
        else:
            errors.append("Account group type must be Liabilities or Assets.")

    return {"success": len(errors) == 0, "errors": errors}

def save_tdc(kwargs):
    errors = []
    tds_link = None
    if kwargs.get("tds_link"):
        tds_data = kwargs["tds_link"][0]
        tds_instance = TDSMaster.objects.filter(id=tds_data.get("id")).first() if tds_data.get("id") else None
        tds_link = tds_data.get("id")
        if tds_instance:
            if (tds_instance.percent_individual_with_pan != tds_data.get("percent_individual_with_pan")\
                    or  tds_instance.percent_other_with_pan != tds_data.get("percent_other_with_pan"))\
                    and date.today() != tds_data.get("effective_date"):
                    effective_result = SaveTdsTcsEffective_date(tds_instance, None,tds_data.get("effective_date"),
                        tds_data.get("percent_individual_with_pan"), tds_data.get("percent_other_with_pan"),
                         None, kwargs.get("modified_by"))
                    if effective_result.get("success"):
                      
                        return {"success": len(errors) == 0, "errors": errors, "tds_link": tds_link}
                    else:
                        return {"success": len(errors) == 0, "errors": errors, "tds_link": tds_link}
        tds_serializer = TDSMasterSerializer(tds_instance, data=tds_data, partial=bool(tds_instance))
        if tds_serializer.is_valid():
            tds_serializer.save()
            tds_link = tds_serializer.instance.id
        else:
            errors.extend([f"TDS - {k}: {'; '.join(map(str, v))}" for k, v in tds_serializer.errors.items()])
    return {"success": len(errors) == 0, "errors": errors, "tds_link": tds_link}

def save_tcs(kwargs):
    errors = []
    tcs_link = None

    if kwargs.get("tcs_link"):
        tcs_data = kwargs["tcs_link"][0]
        tcs_instance = TCSMaster.objects.filter(id=tcs_data.get("id")).first() if tcs_data.get("id") else None
        tcs_link = tcs_data.get("id")
        if tcs_instance:
            if (tcs_instance.percent_individual_with_pan != tcs_data.get("percent_individual_with_pan")\
                            or  tcs_instance.percent_other_with_pan != tcs_data.get("percent_other_with_pan")
                            or tcs_instance.percent_individual_without_pan != tcs_data.get("percent_individual_without_pan")
                            or tcs_instance.percent_other_without_pan != tcs_data.get("percent_other_without_pan")
                            )\
                            and date.today() != tcs_data.get("effective_date"):
                    effective_result = SaveTdsTcsEffective_date(None, tcs_instance,tcs_data.get("effective_date"),
                        tcs_data.get("percent_individual_with_pan"), tcs_data.get("percent_other_with_pan"),
                        tcs_data.get("percent_individual_without_pan"), tcs_data.get("percent_other_without_pan"),
                        kwargs.get("modified_by")) 
                    if effective_result.get("success"):
                        return {"success": len(errors) == 0, "errors": errors, "tcs_link": tcs_link}
                    else:
                        return {"success": len(errors) == 0, "errors": errors, "tcs_link": tcs_link}
        tcs_serializer = TCSMasterSerializer(tcs_instance, data=tcs_data, partial=bool(tcs_instance))
        if tcs_serializer.is_valid():
            tcs_serializer.save()
            tcs_link = tcs_serializer.instance.id
        else:
            errors.extend([f"TCS - {k}: {'; '.join(map(str, v))}" for k, v in tcs_serializer.errors.items()])

    return {"success": len(errors) == 0, "errors": errors, "tcs_link": tcs_link}

class AccountsMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        accounts_name = graphene.String(required=True)
        accounts_group_name = graphene.Int(required=True)
        account_type = graphene.String()
        accounts_active = graphene.Boolean()
        gst_applicable = graphene.Boolean()
        tds_link = graphene.List(TdsMasterInput)
        tcs_link = graphene.List(TcsMasterInput)
        hsn = graphene.Int()
        tax_type = graphene.String()
        gst_type = graphene.String()
        other_rate_tax = graphene.Int()
        allow_payment = graphene.Boolean()
        allow_receipt = graphene.Boolean()
        enforce_position_balance = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int(required=True)

    accounts_master = graphene.Field(AccountsMaster_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Accounts_Master", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        errors = []
        accounts_master = None
        prve_tds_id = None
        prve_tcs_id = None

        kwargs.setdefault("tds_link", [])
        kwargs.setdefault("tcs_link", [])

        new_group = AccountsGroup.objects.filter(id=kwargs['accounts_group_name']).first()
        if not new_group:
            return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=["Account group not found."])

        validation_result = AccountsMasterPrevValidation(kwargs, new_group)
        if not validation_result["success"]:
            return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=validation_result['errors'])

        tds_result = save_tdc(kwargs)
        if not tds_result['success']:
            return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=tds_result['errors'])
        kwargs['tds_link'] = tds_result.get("tds_link")

        tcs_result = save_tcs(kwargs)
        if not tcs_result['success']:
            return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=tcs_result['errors'])

        
        kwargs['tcs_link'] = tcs_result.get("tcs_link")
        if kwargs.get('id'):
            accounts_master_instance = AccountsMaster.objects.filter(id=kwargs['id']).first()
            prve_tds_id = accounts_master_instance.tds_link.id if accounts_master_instance.tds_link  else None
            prve_tcs_id = accounts_master_instance.tcs_link.id if accounts_master_instance.tcs_link else None
            if not accounts_master_instance:
                return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=["Accounts Master not found."])

            if accounts_master_instance.accounts_group_name.accounts_type.id != new_group.accounts_type.id:
                return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=["The selected account group type must match the previous group type."])

            serializer = AccountsMasterSerializer(accounts_master_instance, data=kwargs, partial=True)
        else:
            serializer = AccountsMasterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            instance = serializer.instance
            if instance.hsn:
                OtherIncomeCharges.objects.filter(account=instance).update(hsn=instance.hsn)
                OtherExpenses.objects.filter(account=instance).update(HSN=instance.hsn)
            if prve_tds_id and not instance.tds_link:
                TDSMaster.objects.filter(id=prve_tds_id).first().delete()
            if prve_tcs_id and not instance.tcs_link:
                TCSMaster.objects.filter(id=prve_tcs_id).first().delete()
            return AccountsMasterCreateMutation(accounts_master=serializer.instance, success=True, errors=[])
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
            return AccountsMasterCreateMutation(accounts_master=None, success=False, errors=errors)



class AccountsMasterDeleteMutation(graphene.Mutation):
    """AccountsMaster   Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Accounts_Master", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            accounts_master_instance = AccountsMaster.objects.get(id=id)
            accounts_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return AccountsMasterDeleteMutation(success=success, errors=errors)


class GSTNatureTransactioncreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        nature_of_transaction = graphene.String()
        applies_to = graphene.String()
        gstin_types = graphene.List(graphene.String)
        gst_nature_type = graphene.String()
        specify_type = graphene.String()
        place_of_supply = graphene.String()
        igst_rate = graphene.Decimal()
        cgst_rate = graphene.Decimal()
        sgst_rate = graphene.Decimal()
        cess_rate = graphene.Decimal()

    gst_nature = graphene.Field(GSTNatureTransactionType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GST Nature Transaction", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        gst_nature = None
        success = False
        errors = []
        exclude_filter = {}
        filter_ = {}

        try:
            # Prepare exclusion filter if updating
            if kwargs.get("id"):
                exclude_filter["id"] = kwargs.get("id")
            # Get gst_type_name list from IDs
            gst_type_name = list(GstType.objects.filter(id__in=kwargs.get("gstin_types", [])).values_list("gst_type", flat=True))

            # Validate special types
            if "REGULAR-DEEMED EXPORTER" in gst_type_name:
                if len(gst_type_name) != 1:
                    errors.append("Please note: Only one item can be added when 'REGULAR-DEEMED EXPORTER' is selected.")
                else:
                    if not kwargs.get('gst_nature_type'):
                        errors.append("GST Nature Type is required.")
                    elif kwargs.get('gst_nature_type') != "Specify":
                        errors.append("Only 'Specify' is allowed when 'REGULAR-DEEMED EXPORTER' is selected.")
                    elif not kwargs.get("specify_type"):
                        errors.append("Specify Type is required.")
                    elif kwargs.get("specify_type") == "Taxable" and not kwargs.get("place_of_supply"):
                        errors.append("Place of Supply is required.")
                    else:
                        filter_["place_of_supply"] = kwargs.get("place_of_supply")
                        filter_['gstin_types__gst_type'] = "REGULAR-DEEMED EXPORTER"

            elif "Export/Import" in gst_type_name:
                if len(gst_type_name) != 1:
                    errors.append("Please note: Only one item can be added when 'Export/Import' is selected.")

            # Required fields validation
            required_fields = ["nature_of_transaction", "applies_to", "gst_nature_type"]
            for field in required_fields:
                if not kwargs.get(field):
                    errors.append(f"{field.replace('_', ' ').capitalize()} is required.")

            # GSTIN type check
            gstin_types = [int(i) for i in kwargs.get("gstin_types", [])]
            if not gstin_types:
                errors.append("GSTIN Type is required.")

            
            filter_['applies_to'] = kwargs.get("applies_to", "")
            # Validate Specify Type
            if kwargs.get("gst_nature_type") == "Specify":
                if kwargs.get("specify_type") == "taxable":
                    if not kwargs.get("place_of_supply"):
                        errors.append("Place of Supply is required.")

                    if kwargs.get("place_of_supply") == "Intrastate":
                        if not kwargs.get("cgst_rate") or not kwargs.get("sgst_rate"):
                            errors.append("CGST Rate and SGST Rate are required.")
                        if kwargs.get("igst_rate"):
                            errors.append("IGST Rate should not be provided for Intrastate.")

                    elif kwargs.get("place_of_supply") == "Interstate":
                        if not kwargs.get("igst_rate"):
                            errors.append("IGST Rate is required.")
                        if kwargs.get("cgst_rate") or kwargs.get("sgst_rate"):
                            errors.append("CGST and SGST Rates should not be provided for Interstate.")

            elif kwargs.get("gst_nature_type") == "Import Purchase":
                if kwargs.get("applies_to", "") != "Purchase":
                    errors.append("import Purchase is only allowed to Purchase.")


            # Duplicate GSTIN type validation
            existing_records = GSTNatureTransaction.objects.exclude(**exclude_filter).filter(
                **filter_
            ).values_list("gstin_types", flat=True) 
            used_types = {record for record in existing_records if record}
            duplicates = set(gstin_types).intersection(used_types)

            if duplicates:
                duplicate_labels = GstType.objects.filter(id__in=duplicates).values_list("gst_type", flat=True)
                errors.append(
                    f"The following GSTIN types are already used in another transaction: {', '.join(duplicate_labels)}"
                )

            # Stop here if validation failed
            if errors:
                return GSTNatureTransactioncreateMutation(gst_nature=None, success=False, errors=errors)

            # Create or update record
            if kwargs.get("id"):
                gst_nature_instance = GSTNatureTransaction.objects.filter(id=kwargs.get("id")).first()
                if not gst_nature_instance:
                    errors.append(f"{kwargs.get('nature_of_transaction', 'Record')} not found.")
                    return GSTNatureTransactioncreateMutation(gst_nature=None, success=False, errors=errors)

                serializer = GSTNatureTransactionSerializer(
                    gst_nature_instance, data=kwargs, partial=True, context={"request": info.context}
                )
            else:
                serializer = GSTNatureTransactionSerializer(data=kwargs, context={"request": info.context})
             
            if serializer.is_valid():
                serializer.save()
                gst_nature = serializer.instance
                success = True
            else:
                errors = [
                    f"{field}: {'; '.join(map(str, e))}" for field, e in serializer.errors.items()
                ]

        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")

        return GSTNatureTransactioncreateMutation(
            gst_nature=gst_nature, success=success, errors=errors
        )


class GSTNatureTransactionDeleteMutation(graphene.Mutation):
    """GSTNatureTransaction   Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GST Nature Transaction", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            gst_nature_instance = GSTNatureTransaction.objects.get(id=id)
            gst_nature_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return GSTNatureTransactionDeleteMutation(success=success, errors=errors)


class AlternateUnitCreateMutation(graphene.Mutation):
    """AlternateUnit Create and update"""

    class Arguments:
        id = graphene.ID()
        addtional_unit = graphene.Int()
        conversion_factor = graphene.Decimal()
        fixed = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    alternate_unit = graphene.Field(Alternate_Unit_Type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        alternate_unit = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            alternate_unit_instance = Alternate_unit.objects.filter(id=kwargs['id']).first()
            if not alternate_unit_instance:
                errors.append("Alternate Unit not found.")
            else:
                serializer = Alternate_unitSerializer(alternate_unit_instance, data=kwargs, partial=True)
        else:
            serializer = Alternate_unitSerializer(data=kwargs)

        if serializer.is_valid():
            serializer.save()
            alternate_unit = serializer.instance
            success = True

        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return AlternateUnitCreateMutation(alternate_unit=alternate_unit, success=success, errors=errors)


class AlternateUnitDeleteMutation(graphene.Mutation):
    """AlternateUnit Group Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            alternate_unit_instance = Alternate_unit.objects.get(id=id)
            alternate_unit_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return AlternateUnitDeleteMutation(success=success, errors=errors)


class ItemComboCreateMutation(graphene.Mutation):
    """ItemCombo Create and update"""

    class Arguments:
        id = graphene.ID()
        s_no = graphene.Int()
        part_number = graphene.Int()
        item_qty = graphene.Decimal()
        item_display = graphene.Int()
        is_mandatory = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    ItemCombo = graphene.Field(ItemComboType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        Item_combo_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            Item_combo_instance = Item_Combo.objects.filter(id=kwargs['id']).first()
            if not Item_combo_instance:
                errors.append(f"Item Combo Item with {kwargs['id']} not found.")
            else:
                serializer = ItemComboSerializer(Item_combo_instance, data=kwargs, partial=True)
        else:
            serializer = ItemComboSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            Item_combo_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ItemComboCreateMutation(ItemCombo=Item_combo_instance, success=success, errors=errors)


class ItemComboDeleteMutation(graphene.Mutation):
    """Item Combo Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            Item_Combo_instance = Item_Combo.objects.get(id=id)
            Item_Combo_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ItemComboDeleteMutation(success=success, errors=errors)


class StoreCreateMutation(graphene.Mutation):
    """Store Create and update"""

    class Arguments:
        id = graphene.ID()
        store_name = graphene.String()
        store_account = graphene.Int()
        store_incharge = graphene.Decimal()
        matained = graphene.Boolean()
        conference = graphene.Boolean()
        action = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    Store = graphene.Field(StoreType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Store", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        Store_instance = None
        success = False
        errors = []
        if kwargs['id'] is not None:
            Store_instance = Store.objects.filter(id=kwargs['id']).first()
            if not Store_instance:
                errors.append(f"Store Item with {kwargs['id']} not found.")
            else:
                if Store_instance.matained != kwargs.get("matained"):
                    errors.append("Keep Stock cannot be changed during Edit.")
                if Store_instance.conference != kwargs.get("conference"):
                    errors.append("Conference cannot be changed during Edit.")

                serializer = StoreSerializer(Store_instance, data=kwargs, partial=True)
            if len(errors) > 0:
                return StoreCreateMutation(Store=Store_instance, success=success, errors=errors)
        else:
            serializer = StoreSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                Store_instance = serializer.instance
                success = True
            except ValidationError as e:
                errors = [str(detail) for detail in e.detail]
            except Exception as e:
                errors = [str(error) for error in e]
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return StoreCreateMutation(Store=Store_instance, success=success, errors=errors)


class StoreDeleteMutation(graphene.Mutation):
    """Store Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Store", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            Store_instance = Store.objects.get(id=id)
            Store_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return StoreDeleteMutation(success=success, errors=errors)


class FinishedGoodsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.Int()
        part_no = graphene.Int()
        category = graphene.String()
        qty = graphene.Decimal()
        unit = graphene.Int()
        cost_allocation = graphene.Int()
        remarks = graphene.String()
        labour_charges = graphene.Decimal()
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.DateTime()
        updated_at = graphene.DateTime()

    finished_goods = graphene.Field(FinishedGoodsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        finished_goods_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            finished_goods_instance = FinishedGoods.objects.filter(id=kwargs['id']).first()
            if not finished_goods_instance:
                errors.append(f"Finished Goods Item with {kwargs['id']} not found.")
            else:
                serializer = FinishedGoodsSerializer(finished_goods_instance, data=kwargs, partial=True)
        else:
            serializer = FinishedGoodsSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            finished_goods_instance = serializer.instance
            success = True
        else:
            
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return FinishedGoodsCreateMutation(finished_goods=finished_goods_instance, success=success, errors=errors)


class FinishedGoodsDeleteMutation(graphene.Mutation):
    """Delete Finished Goods item using id"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = FinishedGoods.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return FinishedGoodsDeleteMutation(success=success, errors=errors)


class RawMaterialCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.Int()
        part_no = graphene.Int()
        category = graphene.String()
        qty = graphene.Decimal()
        raw_qty = graphene.Decimal()
        unit = graphene.Int()
        store = graphene.Int()
        fixed = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.DateTime()
        updated_at = graphene.DateTime()
        item_cost = graphene.Decimal()

    raw_materials = graphene.Field(RawMaterialType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        raw_material_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            raw_material_instance = RawMaterial.objects.filter(id=kwargs['id']).first()
            if not raw_material_instance:
                errors.append(f"Raw Material Item with {kwargs['id']} not found.")
            else:
                serializer = RawMaterialSerializer(raw_material_instance, data=kwargs, partial=True)
        else:
            serializer = RawMaterialSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            raw_material_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return RawMaterialCreateMutation(raw_materials=raw_material_instance, success=success, errors=errors)


class RawMaterialDeleteMutation(graphene.Mutation):
    """Delete Raw Material item using id"""

    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.ID)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id=None, id_list=None):
        success = False
        errors = []
        try:
            item_instance = None
            if id:
                item_instance = RawMaterial.objects.get(id=id)
                # delete child bom if linked
                try:
                    child_bom_instance = get_list_or_404(RawMaterialBomLink, raw_material=id)
                    for child in child_bom_instance:
                        child.delete()
                except Exception as e:
                    pass

            if id_list:
                item_instance = RawMaterial.objects.filter(id__in=id_list)
                # delete child boms if linked
                try:
                    child_bom_instances = get_list_or_404(RawMaterialBomLink, raw_material__in=id_list)
                    for child in child_bom_instances:
                        child.delete()
                except Exception as e:
                    pass

            if item_instance:
                if isinstance(item_instance, RawMaterial):
                    item_instance.delete()
                else:
                    for instance in item_instance:
                        instance.delete()
                success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return RawMaterialDeleteMutation(success=success, errors=errors)


class ScrapCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.Int()
        part_no = graphene.Int()
        category = graphene.String()
        qty = graphene.Decimal()
        unit = graphene.Int()
        cost_allocation = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.DateTime()
        created_at = graphene.DateTime()

    scrap = graphene.Field(ScrapType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        scrap_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            scrap_instance = Scrap.objects.filter(id=kwargs['id']).first()
            if not scrap_instance:
                errors.append(f"Scrap Item with {kwargs['id']} not found.")
            else:
                serializer = ScrapSerializer(scrap_instance, data=kwargs, partial=True)
        else:
            serializer = ScrapSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            scrap_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ScrapCreateMutation(scrap=scrap_instance, success=success, errors=errors)


class ScrapDeleteMutation(graphene.Mutation):
    """Delete Scrap item using id"""

    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.ID)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id=None, id_list=None):
        success = False
        errors = []
        try:
            scrap_instance = None
            if id:
                scrap_instance = Scrap.objects.get(id=id)
            if id_list:
                scrap_instance = Scrap.objects.filter(id__in=id_list)
            if scrap_instance:
                scrap_instance.delete()
                success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ScrapDeleteMutation(success=success, errors=errors)


class RoutingCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.Int()
        route_name = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.DateTime()
        updated_at = graphene.DateTime()

    routing = graphene.Field(RoutingType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        routing_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            routing_instance = Routing.objects.filter(id=kwargs['id']).first()
            if not routing_instance:
                errors.append(f"Routing with {kwargs['id']} not found.")
            else:
                serializer = RoutingSerializer(routing_instance, data=kwargs, partial=True)
        else:
            serializer = RoutingSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            routing_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return RoutingCreateMutation(routing=routing_instance, success=success, errors=errors)


class RoutingDeleteMutation(graphene.Mutation):
    """Delete Routing item using id"""

    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.ID)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id=None, id_list=None):
        success = False
        errors = []
        try:
            item_instance = None
            if id:
                item_instance = Routing.objects.get(id=id)
            if id_list:
                item_instance = Routing.objects.filter(id__in=id_list)
            if item_instance:
                item_instance.delete()
                success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return RoutingDeleteMutation(success=success, errors=errors)


class BomRoutingCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.String()
        route = graphene.Int()
        work_center = graphene.Int()
        duration = graphene.Int()

    routing = graphene.Field(BomRoutingType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        routing_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            routing_instance = BomRouting.objects.filter(id=kwargs['id']).first()
            if not routing_instance:
                errors.append(f"Bom Routing with {kwargs['id']} not found.")
            else:
                serializer = BomRoutingSerializer(routing_instance, data=kwargs, partial=True)
        else:
            serializer = BomRoutingSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            routing_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return BomRoutingCreateMutation(routing=routing_instance, success=success, errors=errors)


class BomRoutingDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = BomRouting.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return BomRoutingDeleteMutation(success=success, errors=errors)


class ChargesType(graphene.InputObjectType):
    amount = graphene.String()
    remarks = graphene.String()


class BomCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        bom_name = graphene.String()
        bom_type = graphene.String()
        fg_store = graphene.Int()
        scrap_store = graphene.Int()
        remarks = graphene.String()
        action = graphene.Boolean()
        default = graphene.Boolean()
        cost_variation = graphene.Int()
        finished_goods = graphene.Int()
        raw_material = graphene.List(graphene.Int)
        scrap = graphene.List(graphene.Int)
        routes = graphene.List(graphene.Int)
        labour_charges = graphene.Argument(ChargesType)
        machinery_charges = graphene.Argument(ChargesType)
        electricity_charges = graphene.Argument(ChargesType)
        other_charges = graphene.Argument(ChargesType)
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()
        created_at = graphene.Date()
        updated_at = graphene.Date()
        total_raw_material = graphene.Int()
        status = graphene.Int()
        supplier = graphene.List(graphene.Int)
        is_default = graphene.Boolean()
        is_active = graphene.Boolean()

    bom = graphene.Field(BomType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        bom_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            bom_instance = Bom.objects.filter(id=kwargs['id']).first()
            if not bom_instance:
                errors.append(f"Bom with {kwargs['id']} not found.")
            else:
                serializer = BomSerializer(bom_instance, data=kwargs, partial=True)
        else:
            serializer = BomSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            bom_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return BomCreateMutation(bom=bom_instance, success=success, errors=errors)


class BomDuplicateItemMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)
        model_name = graphene.String()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    items = graphene.List(graphene.Int)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        items = []
        if kwargs['model_name'] == 'fg':
            existing_row = get_object_or_404(FinishedGoods, pk=kwargs['id_list'][0])
            existing_row_data = existing_row.__dict__.copy()
            existing_row_data.pop('id', None)
            existing_row_data.pop('_state', None)
            new_row = FinishedGoods(**existing_row_data)
            new_row.save()
            items.append(new_row.id)
        elif kwargs['model_name'] == 'rm':
            for rm_id in kwargs['id_list']:
                existing_row = get_object_or_404(RawMaterial, pk=rm_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                new_row = RawMaterial(**existing_row_data)
                new_row.save()
                items.append(new_row.id)
        elif kwargs['model_name'] == 'scrap':
            for scrap_id in kwargs['id_list']:
                existing_row = get_object_or_404(Scrap, pk=scrap_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                new_row = Scrap(**existing_row_data)
                new_row.save()
                items.append(new_row.id)
        return BomDuplicateItemMutation(items=items, success=success, errors=errors)


class BomDuplicateFgItemMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)

    finished_goods = graphene.Field(FinishedGoodsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        new_finished_goods = None
        try:
            existing_row = get_object_or_404(FinishedGoods, pk=kwargs['id_list'][0])
            existing_row_data = existing_row.__dict__.copy()
            existing_row_data.pop('id', None)
            existing_row_data.pop('_state', None)

            new_row = FinishedGoods(**existing_row_data)
            new_row.save()
            new_finished_goods = new_row
            success = True
        except Exception as e:
            errors.append(str(e))
        return BomDuplicateFgItemMutation(finished_goods=new_finished_goods, success=success, errors=errors)


class BomDuplicateRmItemMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)

    raw_material = graphene.List(RawMaterialType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        new_raw_material = []
        try:
            for rm_id in kwargs['id_list']:
                existing_row = get_object_or_404(RawMaterial, pk=rm_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                new_row = RawMaterial(**existing_row_data)
                new_row.save()
                new_raw_material.append(new_row)
                try:
                    rm_bom_link = get_object_or_404(RawMaterialBomLink, raw_material=rm_id)
                    if rm_bom_link:
                        existing_rm_bom_data = rm_bom_link.__dict__.copy()
                        existing_rm_bom_data.pop('id', None)
                        existing_rm_bom_data.pop('_state', None)
                        existing_rm_bom_data.pop('raw_material', None)
                        existing_rm_bom_data.update('raw_material', new_row.id)
                        new_rm_bom_row = RawMaterialBomLink(**existing_rm_bom_data)
                        new_rm_bom_row.save()
                except Exception as e:
                     
                    pass
                success = True
        except Exception as e:
            errors.append(str(e))
        return BomDuplicateRmItemMutation(raw_material=new_raw_material, success=success, errors=errors)


class BomDuplicateScrapItemMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)

    scrap = graphene.List(ScrapType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        new_scrap = []
        try:
            for scrap_id in kwargs['id_list']:
                existing_row = get_object_or_404(Scrap, pk=scrap_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                new_row = Scrap(**existing_row_data)
                new_row.save()
                new_scrap.append(new_row)
                success = True
        except Exception as e:
            errors.append(str(e))
        return BomDuplicateScrapItemMutation(scrap=new_scrap, success=success, errors=errors)


class BomDuplicateRoutingItemMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)

    routes = graphene.List(BomRoutingType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        new_routes = []
        try:
            for route_id in kwargs['id_list']:
                existing_row = get_object_or_404(BomRouting, pk=route_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                new_row = BomRouting(**existing_row_data)
                new_row.save()
                new_routes.append(new_row)
                success = True
        except Exception as e:
            errors.append(str(e))
        return BomDuplicateRoutingItemMutation(routes=new_routes, success=success, errors=errors)


class BomDuplicateChildBomMutation(graphene.Mutation):
    class Arguments:
        id_list = graphene.List(graphene.Int)
        raw_material = graphene.List(graphene.Int)

    raw_material_bom_link = graphene.List(RawMaterialBomLinkType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        new_raw_material_bom_link = []
        try:
            for child_id, rm_id in zip(kwargs['id_list'], kwargs['raw_material']):
                existing_row = get_object_or_404(RawMaterialBomLink, raw_material_id=child_id)
                existing_row_data = existing_row.__dict__.copy()
                existing_row_data.pop('id', None)
                existing_row_data.pop('_state', None)
                existing_row_data['raw_material'] = get_object_or_404(RawMaterial, pk=rm_id)
                new_row = RawMaterialBomLink(**existing_row_data)
                new_row.save()
                new_raw_material_bom_link.append(new_row)
                success = True
        except Exception as e:
            errors.append(str(e))
        return BomDuplicateChildBomMutation(raw_material_bom_link=new_raw_material_bom_link, success=success,
                                            errors=errors)


class BomDeleteMutation(graphene.Mutation):
    """Delete BOM item using id"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            bom_instance = Bom.objects.get(id=id)
            bom_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return BomDeleteMutation(success=success, errors=errors)


class ItemDisplayCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        display = graphene.String()
        part_number = graphene.Int()

    display_group_item = graphene.Field(DisplayGroupType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        display_group_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            # Update operation
            display_group_item = display_group.objects.filter(id=kwargs['id']).first()
            if not display_group_item:
                errors.append(f"Display Group with {kwargs['id']} not found.")
            else:
                serializer = displayGroupSerializer(display_group_item, data=kwargs, partial=True)
        else:
            serializer = displayGroupSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            display_group_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ItemDisplayCreateMutation(display_group_item=display_group_item, success=success, errors=errors)


class ItemDisplayDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        success = graphene.Boolean()
        errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = display_group.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ItemDisplayDeleteMutation(success=success, errors=errors)


class StockSerialHistoryCreateMutation(graphene.Mutation):
    """Stock Serial History Create and update"""

    class Arguments:
        id = graphene.ID()
        part_no = graphene.Int()
        store = graphene.Int()
        last_serial_history = graphene.Int()

    stock_serial_history_instance = graphene.Field(StockSerialHistoryType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        stock_serial_history_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            stock_serial_history_instance = StockSerialHistory.objects.filter(id=kwargs['id']).first()
            if not stock_serial_history_instance:
                errors.append("Stock serial history not found.")
            else:
                serializer = StockSerialHistorySerializer(stock_serial_history_instance, data=kwargs, partial=True)
        else:
            serializer = StockSerialHistorySerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            stock_serial_history_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return StockSerialHistoryCreateMutation(stock_serial_history_instance=stock_serial_history_instance,
                                                success=success, errors=errors)


class StockSerialHistoryDeleteMutation(graphene.Mutation):
    """stock serial history Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            stock_history_instance = StockSerialHistory.objects.get(id=id)
            stock_history_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return StockSerialHistoryDeleteMutation(success=success, errors=errors)


class ItemStockCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_number = graphene.Int()
        current_stock = graphene.Decimal()
        store = graphene.Int()
        serial_number = graphene.List(graphene.Int)
        batch_number = graphene.Int()
        unit = graphene.Int()
        last_serial_history = graphene.Int()
        conference = graphene.Int()

    item_stock = graphene.Field(ItemStockType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        item_stock_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            item_stock_instance = ItemStock.objects.filter(id=kwargs['id']).first()
            if not item_stock_instance:
                errors.append(f"Item Stock with {kwargs['id']} not found.")
            else:
                serializer = ItemStockSerializer(item_stock_instance, data=kwargs, partial=True)
        else:
            serializer = ItemStockSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            item_stock_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ItemStockCreateMutation(item_stock=item_stock_instance, success=success, errors=errors)


class ItemStockDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            stock_history_instance = ItemStock.objects.get(id=id)
            stock_history_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ItemStockDeleteMutation(success=success, errors=errors)



class ItemInventoryApprovalInput(graphene.InputObjectType): 
    id = graphene.ID()
    part_number = graphene.Int()
    qty = graphene.Int()
    serial_number = graphene.List(graphene.String)
    rate = graphene.Decimal()
    amount = graphene.Decimal()
    batch_number = graphene.String()
    unit = graphene.Int()



class StockAddtionsCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.String()
        inventory_id = graphene.List(ItemInventoryApprovalInput)
        store = graphene.Int()
        conference = graphene.Int()
        
    inventory_handler = graphene.Field(InventoryHandlerType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("Stock_Addition")
    def mutate(self, info, **kwargs):
        status = kwargs.get("status")
        inventory_handler= None

        stock = StockAdditionService(kwargs, info,status )
        stock.process()
        if stock.success:
            return StockAddtionsCreateMutations(success=True, errors=[],
                                                inventory_handler=stock.inventory_handler)
        
        return StockAddtionsCreateMutations(success=False, errors=stock.errors,
                                                inventory_handler=inventory_handler)

class SerialNumberInput(graphene.InputObjectType):
    id = graphene.ID()
    serial = graphene.String()

class ItemInventoryApprovalForDeletionInput(graphene.InputObjectType):
    id = graphene.ID()
    part_number = graphene.Int()
    qty = graphene.Int()
    serial_number = graphene.List(SerialNumberInput)
    rate = graphene.Decimal()
    amount = graphene.Decimal()
    batch_number = graphene.Int()
    unit = graphene.Int()

class StockDeletionscreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.String()
        inventory_id = graphene.List(ItemInventoryApprovalForDeletionInput)
        store = graphene.Int()
        conference = graphene.Int()
    
    inventory_handler = graphene.Field(InventoryHandlerType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("Stock_Deletion")
    def mutate(self, info, **kwargs):
        status = kwargs.get("status")
        inventory_handler= None

        stock = StockdeletionService(kwargs, info,status )
        stock.process()
        if stock.success:
            return StockDeletionscreateMutations(success=True, errors=[],
                                                inventory_handler=stock.inventory_handler)
        
        return StockDeletionscreateMutations(success=False, errors=stock.errors,
                                                inventory_handler=inventory_handler)
        

class SerialNumberCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.String()
        created_at = graphene.String()
        updated_at = graphene.String()

    serial_number_item = graphene.Field(SerialNumberType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        serial_number_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            serial_number_item = SerialNumbers.objects.filter(id=kwargs['id']).first()
            if not serial_number_item:
                errors.append(f"Serial number with {kwargs['id']} not found.")
            else:
                serializer = SerialNumbersSerializer(serial_number_item, data=kwargs, partial=True)
        else:
            serializer = SerialNumbersSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            serial_number_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return SerialNumberCreateMutation(serial_number_item=serial_number_item, success=success, errors=errors)


class SerialNumberDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = SerialNumbers.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SerialNumberDeleteMutation(success=success, errors=errors)


class SerialNumberStringDeleteMutation(graphene.Mutation):
    class Arguments:
        serial = graphene.String()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, serial):
        success = False
        errors = []
        try:
            item_master_instance = SerialNumbers.objects.get(serial_number=serial)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SerialNumberDeleteMutation(success=success, errors=errors)


class ValidatAndSerialNumberCreateMutation(graphene.Mutation):
    class Arguments:
        serial_number = graphene.List(graphene.String)
        itemmaster_id = graphene.Int(required=True)
        qty = graphene.Int(required=True)

    serial_number_item = graphene.List(SerialNumberType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        serial_number_item = None
        success = False
        savedSerialObjects = []
        errors = []
        serial_list = []
        serial_numbers_list = kwargs['serial_number']
        selectItemmasterData = ItemMaster.objects.get(id=kwargs['itemmaster_id'])
        if not serial_numbers_list:
            errors.append('Serial Number is required.')
            return ValidatAndSerialNumberCreateMutation(success=success, errors=errors)
        if len(serial_numbers_list) != int(kwargs['qty']):
            errors.append('Serial Number length does not match with quantity.')
            return ValidatAndSerialNumberCreateMutation(success=success, errors=errors)
        for serial in serial_numbers_list:
            if str(serial).strip() not in serial_list:
                serial_list.append(str(serial).strip())
            else:
                errors.append(f'{serial}  Serial Number is Already exist')
                break
        if len(errors) == 0:
            if selectItemmasterData.serial_auto_gentrate:
                stockHistory = StockSerialHistory.objects.get(part_no=selectItemmasterData.id)
                stockHistory.last_serial_history = int(stockHistory.last_serial_history) + len(kwargs['serial_number'])
                stockHistory.save()
            duplicate_queryset = SerialNumbers.objects.filter(serial_number__in=serial_list)
            duplicate_serial_numbers = duplicate_queryset.values_list('serial_number', flat=True)
            duplicate_serial_numbers = list(duplicate_serial_numbers)
            if len(duplicate_serial_numbers) > 0:
                errors.append(f'{duplicate_serial_numbers} Serial Number is Already exist')
            else:
                try:
                    with transaction.atomic():
                        for serial in serial_list:
                            savedSerial = SerialNumbers.objects.create(serial_number=serial)
                            savedSerialObjects.append(savedSerial)
                    success = True
                    serial_number_item = savedSerialObjects
                    errors = []
                except Exception as e:
                    errors.append(str(e))
        return ValidatAndSerialNumberCreateMutation(serial_number_item=serial_number_item, success=success,
                                                    errors=errors)


class SerialNumberAutoCreateMutation(graphene.Mutation):
    class Arguments:
        part_code = graphene.Int(required=True)
        qty = graphene.Int(required=True)

    serial_number_item = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        errors = []
        selectItemmasterData = ItemMaster.objects.get(id=kwargs['part_code'])
        serialFormat = selectItemmasterData.serial_format
        serial_list = []
        if selectItemmasterData.serial_auto_gentrate:
            stockHistory = StockSerialHistory.objects.get(part_no=kwargs['part_code'])
            starting_letter = serialFormat.split('#')[0]
            number_of_zeros = serialFormat.split('#')[1]
            for count in range(int(kwargs['qty'])):
                Current_Value = int(stockHistory.last_serial_history) + count
                temp_serial_number = f"{starting_letter}{Current_Value:0{number_of_zeros}d}"
                serial_list.append(temp_serial_number)
            serial_number = str(serial_list).replace("[", "").replace("]", "")
            return SerialNumberAutoCreateMutation(serial_number_item=serial_number, success=True, errors=[])
        else:
            errors.append("It is not auto gentrate")
            return SerialNumberAutoCreateMutation(serial_number_item=str(serial_list), success=False, errors=errors)


class BatchNumberCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_number = graphene.Int()
        batch_number_name = graphene.String()
        created_at = graphene.String()
        updated_at = graphene.String()

    batch_number_item = graphene.Field(BatchNumberType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        batch_number_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            batch_number_item = BatchNumber.objects.filter(id=kwargs['id']).first()
            if not batch_number_item:
                errors.append(f"Serial number with {kwargs['id']} not found.")
            else:
                serializer = BatchNumberSerializer(batch_number_item, data=kwargs, partial=True)
        else:
            # if 'batch_number_name' in kwargs:
            #     batch_number_item = BatchNumber.objects.filter(batch_number_name=kwargs['batch_number_name']).first()
            #     serializer = BatchNumberSerializer(batch_number_item, data=kwargs, partial=True)
            # else:
            serializer = BatchNumberSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            batch_number_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return BatchNumberCreateMutation(batch_number_item=batch_number_item, success=success, errors=errors)


class BatchNumberDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = BatchNumber.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return BatchNumberDeleteMutation(success=success, errors=errors)


class GetBatchNumberId(graphene.Mutation):
    class Arguments:
        batchNumber = graphene.String(required=True)
        part_number_id = graphene.Int(required=True)

    batch_number_instance = graphene.Field(BatchNumberType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        batch_number_instance = None
        success = False
        errors = []

        if kwargs['batchNumber'] and kwargs['part_number_id']:

            query = BatchNumber.objects.filter(part_number=kwargs['part_number_id'],
                                               batch_number_name=kwargs['batchNumber']).first()
            if query:
                batch_number_instance = query

                success = True
            else:
                try:
                    batch_number_instance = BatchNumber.objects.create(
                        part_number_id=kwargs['part_number_id'],
                        batch_number_name=kwargs['batchNumber']
                    )
                    success = True
                except Exception as e:
                    errors.append(str(e))

        else:
            errors = ['Batch Number, part Number id is required']
        return GetBatchNumberId(batch_number_instance=batch_number_instance, success=success, errors=errors)


class InventoryApprovalCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_number = graphene.Int()
        serial_number = graphene.List(graphene.Int)
        batch_number = graphene.Int()
        qty = graphene.String()
        unit = graphene.Int()
        store = graphene.Int()
        is_delete = graphene.Boolean()

    inventory_approval_item = graphene.Field(InventoryApprovalType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        inventory_approval_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            inventory_approval_item = ItemInventoryApproval.objects.filter(id=kwargs['id']).first()
            if not inventory_approval_item:
                errors.append(f"Inventory Approval with {kwargs['id']} not found.")
            else:
                serializer = ItemInventoryApprovalSerializer(inventory_approval_item, data=kwargs, partial=True)
        else:
            serializer = ItemInventoryApprovalSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            inventory_approval_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return InventoryApprovalCreateMutation(inventory_approval_item=inventory_approval_item, success=success,
                                               errors=errors)


class InventoryApprovalDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = ItemInventoryApproval.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return InventoryApprovalDeleteMutation(success=success, errors=errors)


class InventoryHandlerCreateMutation(graphene.Mutation):
    class Arguments:
        inventory_id = graphene.List(graphene.Int)
        store = graphene.Int()
        conference = graphene.Int()
        actions = graphene.String()
        saved_by = graphene.Int()

    inventory_handler_item = graphene.Field(InventoryHandlerType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        inventory_handler_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            inventory_handler_item = InventoryHandler.objects.filter(id=kwargs['id']).first()
            if not inventory_handler_item:
                errors.append(f"Inventory Handler with {kwargs['id']} not found.")
            else:
                serializer = InventoryHandlerSerializer(inventory_handler_item, data=kwargs, partial=True)
        else:
            serializer = InventoryHandlerSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            inventory_handler_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return InventoryHandlerCreateMutation(inventory_handler_item=inventory_handler_item, success=success,
                                              errors=errors)


class InventoryHandlerDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = InventoryHandler.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return InventoryHandlerDeleteMutation(success=success, errors=errors)


# class CreateStockAddtionsMutation()

class CurrencyexchangeCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        Currency = graphene.Int()
        rate = graphene.Decimal()
        date = graphene.Date()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    currency_exchange_instance = graphene.Field(CurrencyExchangeType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Currency_Exchange", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        currency_exchange_instance = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id']:
            currency_exchange_instance_instance = CurrencyExchange.objects.filter(id=kwargs['id']).first()
            if not currency_exchange_instance_instance:
                errors.append("currency exchange history not found.")
            else:
                serializer = CurrencyExchangeSerializer(currency_exchange_instance_instance, data=kwargs, partial=True)
        else:
            serializer = CurrencyExchangeSerializer(data=kwargs)

        if serializer.is_valid():
            serializer.save()
            currency_exchange_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return CurrencyexchangeCreateMutation(currency_exchange_instance=currency_exchange_instance, success=success,
                                              errors=errors)


class CurrencyexchangeDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Currency_Exchange", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            currency_exchange_instance = CurrencyExchange.objects.get(id=id)
            currency_exchange_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return CurrencyexchangeDeleteMutation(success=success, errors=errors)


class CurrencyMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        currency_symbol = graphene.String()
        # formate = graphene.Int()
        active = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int(required=True)

    currency_master_instance = graphene.Field(CurrencyMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Currency_Master", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        currency_master_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            currency_master_instance = CurrencyMaster.objects.filter(id=kwargs['id']).first()
            if not currency_master_instance:
                errors.append("currency master history not found.")
            else:
                serializer = CurrencyMasterSerializer(currency_master_instance, data=kwargs, partial=True)
        else:
            serializer = CurrencyMasterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            currency_master_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return CurrencyMasterCreateMutation(currency_master_instance=currency_master_instance, success=success,
                                            errors=errors)


class CurrencyMasterDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Currency_Master", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            currency_master_instance = CurrencyMaster.objects.get(id=id)
            currency_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return CurrencyMasterDeleteMutation(success=success, errors=errors)


def handle_numbering_series(resource, postype_id, default, department=None, id=None):
    """In the same resource, only one item allowed to be true. Make others false."""
    if default and resource == 'Pos':
        conditions = {}

        if resource:
            conditions = {"resource": resource}
        if postype_id:
            conditions = {"pos_type": postype_id}
        try:
            # Filter NumberingSeries directly by `resource` and `pos_type`
            for single_series in NumberingSeries.objects.filter(**conditions):
                # No need to check `if single_series.resource == "Pos":` since we're already filtering by resource and pos_type
                if single_series.default:
                    single_series.default = False
                    single_series.save()
        except Exception as e:
            pass
    elif resource in ["SalesOrder", "Quotations","SalesOrder Delivery Challan", "Challan Sales Invoice"]:
        if department:
                exists = NumberingSeries.objects.filter(
                    resource=resource,
                    department_id=department,
                    active=True
                ).exclude(id=id).exists()
                if exists:
                    raise Exception(f"Numbering Series for '{resource}' already exists for this department.")
    else:
        exists = NumberingSeries.objects.filter(
            resource=resource,
            active=True
        ).exclude(id=id).exists()
        if exists:
            raise Exception(f"Numbering Series for '{resource}' already exists.")

class NumberingSeriesCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        numbering_series_name = graphene.String()
        resource = graphene.String()
        department = graphene.Int()
        pos_type = graphene.Int()
        formate = graphene.String()
        current_value = graphene.Int()
        last_serial_history = graphene.Int()
        default = graphene.Boolean()
        active = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int(required=True)

    numbering_series_instance = graphene.Field(NumberingSeriesType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Numbering_Series", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        numbering_series_instance = None
        success = False
        errors = []
        if kwargs['id']:
            numbering_series_instance = NumberingSeries.objects.filter(id=kwargs['id']).first()
            if not numbering_series_instance:
                errors.append("Numbering Series  not found.")
            else:
                handle_numbering_series(kwargs["resource"], kwargs["pos_type"], kwargs['default'],kwargs['department'],
                                        kwargs['id'])
                serializer = NumberingSeriesSerializer(numbering_series_instance, data=kwargs, partial=True)
        else:
            try:
                serializer = NumberingSeriesSerializer(data=kwargs)
            except Exception as e:
                pass
        if serializer.is_valid():
            handle_numbering_series(kwargs["resource"], kwargs["pos_type"], kwargs['default'],kwargs['department'],
                                    kwargs['id'])
            try:
                serializer.save()
                numbering_series_instance = serializer.instance
                success = True
            except Exception as e:
                pass

        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return NumberingSeriesCreateMutation(numbering_series_instance=numbering_series_instance, success=success,
                                             errors=errors)


class NumberingSeriesDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Numbering_Series", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            item_master_instance = NumberingSeries.objects.get(id=id)
            item_master_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SerialNumberDeleteMutation(success=success, errors=errors)


def POSPreVaidation(data):
    error = []
    conditions = {'resource': 'Pos', 'pos_type__ReSourceIsPosType': data.get("posType"), 'default': True}
    numbering_series = NumberingSeries.objects.filter(**conditions).first()
    if not numbering_series:
        error.append("No matching NumberingSeries found.")
    if data.get("itemDetails") and len(data.get("itemDetails")) > 0:
        itemDetails_error = validate_with_serializer(data['itemDetails'],
                                                     SalesOrderItem,
                                                     SalesOrderItemSerializer,
                                                     ItemMaster,
                                                     "part_code",
                                                     "part code found",
                                                     'item_part_code')

        error.extend(itemDetails_error)
    else:
        error.extend("At least one Item Details is Required.")
    if data.get("payment") and len(data.get("payment")) > 0:
        payment_error = validate_with_serializer_with_out_related_model(data['payment'],
                                                                        paymentMode,
                                                                        PaymentModeSerializer,
                                                                        'pay_amount',
                                                                        "Pay Amount")
        error.extend(payment_error)
    if data.get("other_income_charge") and len(data.get("other_income_charge")) > 0:
        other_income_charge_error = validate_with_serializer(
            data['other_income_charge'],
            posOtherIncomeCharges,
            posOtherIncomeChargeSerializer,
            OtherIncomeCharges,
            "other_income_charges_id",
            "Other Income charges",
            'name'
        )
        error.extend(other_income_charge_error)
    if 'id' in data and data['id'] is not None:
        sales_order_pos_instance = SalesOrder.objects.get(id=data['id'])
        if not sales_order_pos_instance:
            error.append("Sales Order not found.")
    if data.get("posType") == "Sample" and ContactDetalis.objects.exclude(pk=data.get('sample_contact_link')).filter(
            phone_number__iexact=data.get("Mobile")).exists():
        error.append("Mobile Number Already Exists in Contact.")

    success = len(error) == 0
    return {"success": success, "error": error}


def savePOSItemDetails(data):
    return save_items(data, SalesOrderItem, SalesOrderItemSerializer, "POSItemDetails")


def savePOSpayMent(data):
    return save_items(data, paymentMode, PaymentModeSerializer, "POSpayment")


def savePOSOtherIncomeCharge(data):
    return save_items(data, posOtherIncomeCharges, posOtherIncomeChargeSerializer, "posOtherIncomeCharge")


class SalesOrderItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    part_code = graphene.Int()
    description = graphene.String()
    uom = graphene.Int()
    qty = graphene.Decimal()
    hsn = graphene.Int()
    serial = graphene.List(graphene.Int)
    batch = graphene.Int()
    stock_reduce = graphene.Boolean()
    isCanceled = graphene.Boolean()
    rate = graphene.Decimal()
    gst_rate = graphene.Int()
    amount = graphene.Decimal()
    discount_percentage = graphene.Decimal()
    discount_value = graphene.Decimal()
    discount_value_for_per_item = graphene.Decimal()
    final_value = graphene.Decimal()
    item_combo = graphene.List(graphene.Int)
    pos_item_combo_bool = graphene.Boolean()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class posPaymentInput(graphene.InputObjectType):
    id = graphene.ID()
    payby = graphene.Int()

    pay_amount = graphene.Decimal()
    balance_amount = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class posOtherIncomeChargeInput(graphene.InputObjectType):
    id = graphene.ID()
    other_income_charges_id = graphene.Int(required=True)
    tax = graphene.Int(required=True)
    amount = graphene.Decimal(required=True)
    hsn = graphene.Int()
    igst = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    discount_value = graphene.Decimal()
    after_discount_value = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class SalesorderPosCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        IsPOS = graphene.Boolean()
        posType = graphene.String()
        marketingEvent = graphene.Int()
        OrderDate = graphene.Date()
        status = graphene.String()
        store = graphene.Int()
        POS_ID = graphene.String()
        sample_contact_link = graphene.Int()
        Mobile = graphene.String()
        WhatsappNumber = graphene.String()
        CosName = graphene.String()
        Email = graphene.String()
        district = graphene.String()
        State = graphene.String()
        pincode = graphene.Int()
        Remarks = graphene.String()
        customerName = graphene.Int()
        BillingAddress = graphene.Int()
        DeliverAddress = graphene.Int()
        contactPerson = graphene.Int()
        Currency = graphene.Int()
        itemDetails = graphene.List(SalesOrderItemDetailsInput)
        payment = graphene.List(posPaymentInput)
        other_income_charge = graphene.List(posOtherIncomeChargeInput)
        OverallDiscountPercentage = graphene.Decimal()
        OverallDiscountPercentageValue = graphene.Decimal()
        OverallDiscountValue = graphene.Decimal()
        DiscountFinalTotal = graphene.Decimal()
        TotalAmount = graphene.Decimal()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        receivedAmount = graphene.Decimal()
        balance_Amount = graphene.Decimal()
        FinalTotalValue = graphene.Decimal()
        SalesPerson = graphene.Int()
        isDelivered = graphene.Boolean()
        Pending = graphene.Boolean()
        AllStockReduced = graphene.Boolean()
        Remarks = graphene.String()
        modified_by = graphene.Int()
        createdby = graphene.Int()
        isDelete = graphene.Boolean()

    sales_order_pos_instance = graphene.Field(SalesOrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("POS", create_action="Save", edit_action="Save")
    def mutate(self, info, **kwargs):
        serializer = ''
        sales_order_pos_instance = None
        success = False
        errors = []
        itemdetails_id = []
        payment_id = []
        othercharges_id = []
        validate_result = POSPreVaidation(kwargs)
        if not validate_result['success']:
            return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                               success=success,
                                               errors=validate_result['error'])
        if 'other_income_charge' in kwargs and kwargs.get("other_income_charge") and len(
                kwargs.get("other_income_charge")) > 0:
            pos_other_income_charge = savePOSOtherIncomeCharge(kwargs.get("other_income_charge"))
            if not pos_other_income_charge['success']:
                return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                                   success=success,
                                                   errors=pos_other_income_charge["error"])
            else:
                kwargs['other_income_charge'] = pos_other_income_charge['ids']
        itemdetails_result = savePOSItemDetails(kwargs['itemDetails'])
        if not itemdetails_result['success']:
            return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                               success=success,
                                               errors=itemdetails_result["error"])
        kwargs['itemDetails'] = itemdetails_result['ids']
        if kwargs.get('payment') and len(kwargs.get('payment')) > 0:
            itemPaymentresult = savePOSpayMent(kwargs['payment'])
            if not itemPaymentresult['success']:
                return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                                   success=success,
                                                   errors=itemPaymentresult['success'])
            kwargs['payment'] = itemPaymentresult['ids']
        if 'id' in kwargs and kwargs['id'] != None:
            sales_order_pos_instance = SalesOrder.objects.get(id=kwargs['id'])
            if not sales_order_pos_instance:
                errors.append("Sales Order not found.")
                return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                                   success=success,
                                                   errors=errors)
            else:
                itemdetails_id = [item.id for item in sales_order_pos_instance.itemDetails.all()]
                payment_id = [item.id for item in sales_order_pos_instance.payment.all()]
                othercharges_id = [item.id for item in sales_order_pos_instance.other_income_charge.all()]
                if kwargs['posType'] == "Sample":
                    contactId = CreateOrEditContact(kwargs['sample_contact_link'], kwargs['CosName'], kwargs['Email'],
                                                    kwargs['Mobile'],
                                                    kwargs['WhatsappNumber'], "Customer")
                    if contactId['success']:
                        kwargs['sample_contact_link'] = contactId['data'].id
                    else:
                        return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                                           success=success,
                                                           errors=contactId['errors'])
                serializer = SalesOrderSerializer(sales_order_pos_instance, data=kwargs, partial=True)
        else:
            serializer = SalesOrderSerializer(data=kwargs)
            if kwargs['posType'] == "Sample":
                contact_type = Contact_type.objects.get(name="Customer")
                if contact_type:
                    contactId = CreateOrEditContact(kwargs['sample_contact_link'], kwargs['CosName'],
                                                    kwargs['Email'], kwargs['Mobile'], kwargs['WhatsappNumber'],
                                                    "Customer")

                    if contactId['success']:
                        kwargs['sample_contact_link'] = contactId['data'].id
                    else:
                        return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance,
                                                           success=success,
                                                           errors=contactId['errors'])
        if serializer.is_valid():
            try:
                serializer.save()
                sales_order_pos_instance = serializer.instance

                deleteCommanLinkedTable(itemdetails_id,
                                        [item.id for item in sales_order_pos_instance.itemDetails.all()],
                                        SalesOrderItem)
                deleteCommanLinkedTable(payment_id,
                                        [item.id for item in sales_order_pos_instance.payment.all()],
                                        paymentMode)
                deleteCommanLinkedTable(othercharges_id,
                                        [item.id for item in sales_order_pos_instance.other_income_charge.all()],
                                        posOtherIncomeCharges)
                success = True
            except Exception as e:
                 
                errors.append(e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in
                      serializer.errors.items()]
        return SalesorderPosCreateMutation(sales_order_pos_instance=sales_order_pos_instance, success=success,
                                           errors=errors)


class SalesorderPosDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("POS", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []

        try:
            sales_order_instance = SalesOrder.objects.get(id=id)

            # Ensure status is exactly "Canceled"
            if sales_order_instance.status == "Canceled":
                sales_order_instance.delete()
                success = True
            else:
                errors.append("Before deleting the record, change the status to 'Canceled'.")
        
        except SalesOrder.DoesNotExist:
            errors.append(f"Sales Order with ID {id} not found.")

        except ProtectedError:
            errors.append("This record is linked with other modules and cannot be deleted.")

        except Exception as e:
            errors.append(str(e))

        return SalesorderPosDeleteMutation(success=success, errors=errors)

class SalesOrderSubmitMutation(graphene.Mutation):
    class Arguments:
        posId = graphene.ID()
        submitBy = graphene.Int()

    sales_order_pos_instance = graphene.Field(SalesOrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, posId, submitBy):
        user = info.context.user
        if not user or not user.is_authenticated:
            raise GraphQLError(
                "Authentication required",
                extensions={"code": "UNAUTHENTICATED"}
            )
        if not has_permission_mutations(user, "POS", ["Submit"]):
            raise GraphQLError(
                f"You do not have permission to Submit POS",
                extensions={"code": "PERMISSION_DENIED"}
            )
        success = ""
        errors = []
        salesOrderInstence = SalesOrder.objects.get(id=posId)
        store = salesOrderInstence.store
        conference_id = salesOrderInstence.marketingEvent.id
        user = User.objects.get(id=submitBy)
        for index, salesOrderItem in enumerate(salesOrderInstence.itemDetails.all()):
            if not salesOrderItem.stock_reduce:
                
                if salesOrderItem.part_code.batch_number:
                    batch = salesOrderItem.batch
                    batchstock = StockReduce(partCode_id=salesOrderItem.part_code.id, Store_id=store.id,
                                            batch_id=batch.id, qty=salesOrderItem.qty, serial_id_list=[], partCode = salesOrderItem.part_code,
                                            batch=batch.batch_number_name)
                    result = batchstock.reduceBatchNumber()
                    if result['success']:
                        salesOrderItem.stock_reduce = True
                        salesOrderItem.save()
                        stock_data_existing_list = ItemStock.objects.filter(part_number=salesOrderItem.part_code.id, )
                        total_stock = 0
                        for singleStock in stock_data_existing_list:
                            total_stock += int(singleStock.current_stock)
                        stockHistoryUpdate("DELETE", store, salesOrderItem.part_code, total_stock + salesOrderItem.qty,
                                           total_stock, 0, result['reduce'], user, "SalesOrder", posId,
                                           salesOrderInstence.POS_ID.linked_model_id, 'POS', result['stocklink'],
                                           conference_id)
                    else:
                        return SalesOrderSubmitMutation(success=success, errors=result['error'])
                elif salesOrderItem.serial:
                    serial = salesOrderItem.serial.all()
                    serial_ids = [serial.id for serial in serial]
                    serialstock = StockReduce(partCode_id=salesOrderItem.part_code.id, Store_id=store.id,
                                              batch_id="", qty=salesOrderItem.qty, serial_id_list=serial_ids,
                                              partCode = salesOrderItem.part_code, batch = None)
                    result = serialstock.reduceSerialNumber()
                    if result['success']:
                        salesOrderItem.stock_reduce = True
                        salesOrderItem.save()
                        stockHistoryUpdate("DELETE", store, salesOrderItem.part_code, result['previousSates'],
                                           result['updatedState'], 0, result['reduce'], user, "SalesOrder", posId,
                                           salesOrderInstence.POS_ID.linked_model_id, 'POS', result['stocklink'],
                                           conference_id)
                    else:
                        return SalesOrderSubmitMutation(success=success, errors=result['error'])
                else:
                    stock = StockReduce(partCode_id=salesOrderItem.part_code.id, Store_id=store.id,
                                        batch_id="", qty=salesOrderItem.qty, serial_id_list=[],
                                        partCode = salesOrderItem.part_code, batch = None)
                    result = stock.reduceNoBatchNoSerial()
                    if result['success']:
                        salesOrderItem.stock_reduce = True
                        salesOrderItem.save()
                        stockHistoryUpdate("DELETE", store, salesOrderItem.part_code, result['previousSates'],
                                           result['updatedState'], 0, result['reduce'], user, "SalesOrder", posId,
                                           salesOrderInstence.POS_ID.linked_model_id, 'POS', result['stocklink'],
                                           conference_id)
                    else:
                        return SalesOrderSubmitMutation(success=success, errors=result['error'], )
                if index + 1 == len(salesOrderInstence.itemDetails.all()):
                    salesOrderInstence.status = "Submited"
                    salesOrderInstence.all_stock_reduced = True
                    salesOrderInstence.save()
                    success = True

        return SalesOrderSubmitMutation(success=success, errors=errors, sales_order_pos_instance=salesOrderInstence)

class SalesOrderCancleMutation(graphene.Mutation):
    class Arguments:
        posID = graphene.ID()

    sales_order_pos_instance = graphene.Field(SalesOrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, posID):
        user = info.context.user
        if not user or not user.is_authenticated:
            raise GraphQLError(
                "Authentication required",
                extensions={"code": "UNAUTHENTICATED"}
            )
        if not has_permission_mutations(user, "POS", ["Cancel"]):
            raise GraphQLError(
                f"You do not have permission to Cancel POS",
                extensions={"code": "PERMISSION_DENIED"}
            )
        success = True
        errors = []
        salesOrderInstance = None
        try:
            salesOrderInstance = SalesOrder.objects.get(id=posID)
        except SalesOrder.DoesNotExist:
            errors.append(f"Sales order with ID {posID} does not exist.")
            return SalesOrderCancleMutation(success=False, errors=errors, sales_order_pos_instance=salesOrderInstance)

        store = salesOrderInstance.store
        if salesOrderInstance.status == "Submited":
            for salesOrderItem in salesOrderInstance.itemDetails.all():
                if salesOrderItem.stock_reduce:
                    try:
                        if salesOrderItem.part_code.batch_number:
                            batch = salesOrderItem.batch
                            stock_data_existing = ItemStock.objects.filter(
                                part_number=salesOrderItem.part_code.id,
                                store=store.id,
                                batch_number=batch.id
                            ).first()
                            if stock_data_existing:
                                added_stock = Decimal(salesOrderItem.qty)
                                stock_data_existing.current_stock += added_stock
                                stock_data_existing.save()
                                salesOrderItem.stock_reduce = False
                                salesOrderItem.is_canceled = True
                                salesOrderItem.save()
                            else:
                                errors.append(
                                    f"No stock data found for part code {salesOrderItem.part_code.item_part_code} and batch {batch.id}")
                                return SalesOrderCancleMutation(success=success, errors=errors)

                        elif salesOrderItem.part_code.serial:
                            serial = salesOrderItem.serial.all()
                            stock_data_existing = ItemStock.objects.filter(
                                part_number=salesOrderItem.part_code.id,
                                store=store.id,
                            ).first()
                            if stock_data_existing:
                                existing_serials = stock_data_existing.serial_number.all()
                                existing_serial_ids = {serial.id for serial in existing_serials}
                                new_serial_ids = {serial.id for serial in serial}
                                all_serial_ids = existing_serial_ids.union(new_serial_ids)

                                stock_data_existing.serial_number.set(
                                    SerialNumbers.objects.filter(id__in=all_serial_ids))

                                # Update the stock quantity
                                added_stock = Decimal(salesOrderItem.qty)
                                current_stock = Decimal(stock_data_existing.current_stock)
                                stock_data_existing.current_stock = current_stock + added_stock
                                stock_data_existing.save()
                                salesOrderItem.stock_reduce = False
                                salesOrderItem.is_canceled = True
                                salesOrderItem.save()
                            else:
                                errors.append(
                                    f"No stock data found for part code {salesOrderItem.part_code.item_part_code}")
                                return SalesOrderCancleMutation(success=success, errors=errors)

                        else:
                            stock_data_existing = ItemStock.objects.filter(
                                part_number=salesOrderItem.part_code.id,
                                store=store.id
                            ).first()
                            if stock_data_existing:
                                added_stock = Decimal(salesOrderItem.qty)
                                stock_data_existing.current_stock += added_stock
                                stock_data_existing.save()
                                salesOrderItem.stock_reduce = False
                                salesOrderItem.is_canceled = True
                                salesOrderItem.save()
                            else:
                                errors.append(
                                    f"No stock data found for part code {salesOrderItem.part_code.item_part_code}")
                                return SalesOrderCancleMutation(success=success, errors=errors,
                                                                sales_order_pos_instance=salesOrderInstance)

                    except Exception as e:
                        errors.append(str(e))
                        success = False
            try:
                """Stock History Detele"""
                history = StockHistory.objects.filter(transaction_module="SalesOrder", transaction_id=posID)
                history.delete()
                """delete paymentes"""
                paymentes = salesOrderInstance.payment.all()
                for pay in paymentes:
                    pay.delete()
            except Exception as e:
                errors.append(str(e))
                success = False

        try:
            salesOrderInstance.status = "Canceled"
            salesOrderInstance.all_stock_reduced = False
            salesOrderInstance.save()
            for salesOrderItem in salesOrderInstance.itemDetails.all():
                salesOrderItem.stock_reduce = False
                salesOrderItem.is_canceled = True
                salesOrderItem.save()
        except Exception as e:
            errors.append(str(e))
            success = False

        return SalesOrderCancleMutation(success=success, errors=errors, sales_order_pos_instance=salesOrderInstance)

"""pos item details creates """

class SalesorderCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_code = graphene.Int()
        description = graphene.String()
        uom = graphene.Int()
        qty = graphene.Decimal()
        serial = graphene.List(graphene.Int)
        batch = graphene.Int()
        stock_reduce = graphene.Boolean()
        isCanceled = graphene.Boolean()
        rate = graphene.Decimal()
        gst_rate = graphene.Int()
        amount = graphene.Decimal()
        discount_percentage = graphene.Decimal()
        discount_value = graphene.Decimal()
        discount_value_for_per_item = graphene.Decimal()
        final_value = graphene.Decimal()
        item_combo = graphene.List(graphene.Int)
        pos_item_combo_bool = graphene.Boolean()
        sgst = graphene.Decimal()
        cgst = graphene.Decimal()
        igst = graphene.Decimal()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    Salesoder_instance = graphene.Field(SalesOrderItemType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        Salesoder_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            Salesoder_instance = SalesOrderItem.objects.filter(id=kwargs['id']).first()
            if not Salesoder_instance:
                errors.append("Sales Order not found.")
            else:
                serializer = SalesOrderItemSerializer(Salesoder_instance, data=kwargs, partial=True)
        else:
            serializer = SalesOrderItemSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                Salesoder_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(e)
                success = False
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return SalesorderCreateMutation(Salesoder_instance=Salesoder_instance, success=success,
                                        errors=errors)

"""pos item details  """


class SalesorderDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            supplier_form_instance = SalesOrderItem.objects.get(id=id)
            supplier_form_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SalesorderPosDeleteMutation(success=success, errors=errors)


"""To Check Stock"""


class CheckStock(graphene.Mutation):
    class Arguments:
        posID = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    needStock = graphene.String()

    def mutate(self, info, posID):
        success = False
        errors = []
        needStock = []
        try:
            salesOrderInstance = SalesOrder.objects.get(id=posID)
        except SalesOrder.DoesNotExist:
            errors.append(f"Sales order with ID {posID} does not exist.")
            return CheckStock(success=False, errors=errors, needStock=json.dumps(needStock))
        store = salesOrderInstance.store
        for salesOrderItem in salesOrderInstance.itemDetails.all():
            if not salesOrderItem.stock_reduce:
                if salesOrderItem.part_code.batch_number:
                    required_stock = float(salesOrderItem.qty)
                    batch = salesOrderItem.batch
                    stock_data_existing = ItemStock.objects.filter(
                        part_number=salesOrderItem.part_code.id,
                        store=store.id,
                        batch_number=batch.id
                    ).first()

                    if stock_data_existing:
                        current_stock = float(stock_data_existing.current_stock)
                        if (current_stock - required_stock) < 0:
                            needStock.append({
                                "partcode": salesOrderItem.part_code.item_part_code,
                                "batch": salesOrderItem.batch.batch_number_name,
                                "needStock": abs(current_stock - required_stock)
                            })
                    else:
 
                        needStock.append({
                            "partcode": salesOrderItem.part_code.item_part_code,
                            "batch": salesOrderItem.batch.batch_number_name,
                            "needStock": required_stock
                        })
                elif salesOrderItem.part_code.serial:
                    serial = salesOrderItem.serial.all()
                    serial_ids = [serial.id for serial in serial]
                    stock_data_existing = ItemStock.objects.filter(
                        part_number=salesOrderItem.part_code.id,
                        store=store.id,
                    ).first()
                    if stock_data_existing:
                        # Fetch the serial numbers associated with this stock
                        serial_list = [serial.id for serial in stock_data_existing.serial_number.all()]

                        # Check if all serial_ids are in serial_list
                        missing_serial_ids = [serial_id for serial_id in serial_ids if serial_id not in serial_list]

                        # Fetch the missing serial numbers
                        missing_serials = SerialNumbers.objects.filter(id__in=missing_serial_ids)

                        if missing_serial_ids:
                            # Extract serial_number for missing serial IDs
                            needSerial = [serial.serial_number for serial in missing_serials]
                            needStock.append({
                                "partcode": salesOrderItem.part_code.item_part_code,
                                "Serial": needSerial,
                                "needStock": len(needSerial)
                            })
                else:
                    stock_data_existing = ItemStock.objects.filter(part_number=salesOrderItem.part_code.id,
                                                                   store=store.id).first()
                    if stock_data_existing:
                        current_stock = float(stock_data_existing.current_stock)
                        required_stock = float(salesOrderItem.qty)

                        if (current_stock - required_stock) < 0:
                            needStock.append({
                                "partcode": salesOrderItem.part_code.item_part_code,
                                "needStock": abs(current_stock - required_stock)
                            })
                    else:
                        needStock.append({
                            "partcode": salesOrderItem.part_code.item_part_code,
                            "needStock": required_stock
                        })
            if len(needStock) == 0:
                success = True
        return CheckStock(success=success, errors=errors, needStock=json.dumps(needStock))


class paymentModeCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        payby = graphene.Int()
        pay_amount = graphene.Decimal()
        balance_amount = graphene.Decimal()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    payment_mode_instance = graphene.Field(PaymentModeType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        payment_mode_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            payment_mode_instance = paymentMode.objects.filter(id=kwargs['id']).first()
            if not payment_mode_instance:
                errors.append("Payment mode not found.")
            else:
                serializer = PaymentModeSerializer(payment_mode_instance, data=kwargs, partial=True)
        else:
            serializer = PaymentModeSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()

                payment_mode_instance = serializer.instance
            except Exception as e:
                pass
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return paymentModeCreateMutation(payment_mode_instance=payment_mode_instance, success=success,
                                         errors=errors)


class paymentModeDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            payment_mode_instance = paymentMode.objects.get(id=id)
            payment_mode_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return paymentModeDeleteMutation(success=success, errors=errors)


class CompanyAddressCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        address_type = graphene.String()
        address_line_1 = graphene.String()
        address_line_2 = graphene.String()
        city = graphene.String()
        pincode = graphene.String()
        state = graphene.String()
        country = graphene.String()
        default = graphene.Boolean()

    company_address_item = graphene.Field(CompanyAddressType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):

        company_address_item = None
        success = False
        errors = []
        if "id" in kwargs and kwargs['id']:
            company_address_item = CompanyAddress.objects.filter(id=kwargs['id']).first()
            if not company_address_item:
                errors.append(f"Company Address with {kwargs['id']} not found.")
            else:
                serializer = ItemAddressSerializer(company_address_item, data=kwargs, partial=True)
        else:
            serializer = ItemAddressSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            company_address_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return CompanyAddressCreateMutation(company_address_item=company_address_item, success=success,
                                            errors=errors)


class CompanyAddressDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        id_list = graphene.List(graphene.Int)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, id_list):
        success = False
        errors = []
        try:
            company_address_instance = None
            if id:
                company_address_instance = CompanyAddress.objects.get(id=id)
            if id_list:
                company_address_instance = CompanyAddress.objects.filter(id__in=id_list)
            if company_address_instance:
                company_address_instance.delete()
                success = True
            else:
                errors.append('This data not found')
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return CompanyAddressDeleteMutation(success=success, errors=errors)


class CustomerGroupCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        Active = graphene.Boolean()
        parent_group = graphene.String()
        Saved_by = graphene.Int()

    customer_group_item = graphene.Field(CustomerGroupsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Customer", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        customer_group_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            customer_group_item = CustomerGroups.objects.filter(id=kwargs['id']).first()
            if not customer_group_item:
                errors.append(f"Contact Groups with {kwargs['id']} not found.")
            else:
                serializer = CustomerGroupsSerializer(customer_group_item, data=kwargs, partial=True)
        else:
            serializer = CustomerGroupsSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            customer_group_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return CustomerGroupCreateMutation(customer_group_item=customer_group_item, success=success,
                                           errors=errors)


class CustomerGroupDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Customer", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            customer_group_instance = CustomerGroups.objects.get(id=id)
            customer_group_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return CustomerGroupDeleteMutation(success=success, errors=errors)


class SupplierGroupCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        Active = graphene.Boolean()
        parent_group = graphene.String()
        Saved_by = graphene.Int()

    supplier_group_item = graphene.Field(SupplierGroupsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Supplier", create_action="Save", edit_action="Delete")
    def mutate(self, info, **kwargs):
        serializer = ''
        supplier_group_item = None
        success = False
        errors = []

        if 'id' in kwargs:
            supplier_group_item = SupplierGroups.objects.filter(id=kwargs['id']).first()
            if not supplier_group_item:
                errors.append(f"item with {kwargs['id']} not found.")
            else:
                serializer = SupplierGroupsSerializer(supplier_group_item, data=kwargs, partial=True)
        else:
            serializer = SupplierGroupsSerializer(data=kwargs)

        if serializer.is_valid():
            serializer.save()
            supplier_group_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return SupplierGroupCreateMutation(supplier_group_item=supplier_group_item, success=success,
                                           errors=errors)


class SupplierGroupDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Supplier", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            supplier_group_instance = SupplierGroups.objects.get(id=id)
            supplier_group_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SupplierGroupDeleteMutation(success=success, errors=errors)


class ContactValidation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        Number = graphene.String()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    createdby = graphene.Int()

    @mutation_permission("Contact", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        createdby = None
        if ContactDetalis.objects.exclude(pk=kwargs['id']).filter(phone_number__iexact=kwargs['Number']).exists():
            errors.append("Mobile Number Already Exists in Contact.")
            success = False
        else:
            success = True
        return ContactValidation(success=success, errors=errors, createdby=createdby)





class ContactDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    contact_person_name = graphene.String()
    salutation = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    whatsapp_no = graphene.String()
    other_no = graphene.String()
    default = graphene.Boolean()
    modified_by = graphene.Int()
    created_by = graphene.Int()


def supplierPreValidation(data):
    success = False
    error = []

    # Check Transporter ID uniqueness
    if data.get('transporter_id') and SupplierFormData.objects.exclude(pk=data['id']).filter(
            transporter_id__iexact=data['transporter_id']).exists():
        error.append("Transporter Id must be unique.")

    # Check Company Name uniqueness
    if data.get('company_name') and SupplierFormData.objects.exclude(pk=data['id']).filter(
            company_name__iexact=data['company_name']).exists():
        error.append("Company Name must be unique.")

    # Check GSTIN uniqueness (except for 'URP')
    if data.get('gstin') and data.get('gstin') != "Export/Import" and data['gstin'] != 'URP' and SupplierFormData.objects.exclude(pk=data['id']).filter(
            gstin__iexact=data['gstin']).exists():
        if len(data.get('gstin')) == 15:
            error.append("Enter the valid GSTIN.")
        error.append("GSTIN must be unique.")
    # Check pan uniqueness
    # if data.get('pan_no') and str(data.get('pan_no')).strip() and data.get(
    #         'pan_no') is not None and SupplierFormData.objects.exclude(pk=data['id']).filter(
    #     pan_no__iexact=data['pan_no']).exists():
    #     error.append("Pan No must be unique.")
    if data.get('pan_no').strip() == "":
        data['pan_no'] = None
    # Validate Contact details
    if data.get('contact'):
        contact_errors = validate_contact_details(data['contact'])
        error.extend(contact_errors)

    # Validate Address details
    if data.get('address'):
        print('data.get("gst_in_type",None)', data)
        gst_type = GstType.objects.filter(id=data.get("gstin_type",None)).first()
        gst_type_name = None 

        if gst_type:
            gst_type_name = gst_type.gst_type
        address_errors = validate_address_details(data['address'], gst_type_name)
        error.extend(address_errors)

    success = len(error) == 0
    return {"success": success, "error": error}


def validate_contact_details(contact_data):
    errors = []
    if len(contact_data) == 0:
        errors.append("At least one contact is required.")
    else:
        for contact in contact_data:
            if 'id' in contact and contact['id']:
                contact_details_item = ContactDetalis.objects.filter(id=contact['id']).first()
                if not contact_details_item:
                    errors.append(f"Contact with ID {contact['contact_person_name']} not found.")
                    break
                else:
                    serializer = ItemContactSerializer(contact_details_item, data=contact, partial=True)
            else:
                serializer = ItemContactSerializer(data=contact)

            if not serializer.is_valid():
                for field, error_list in serializer.errors.items():
                    errors.append(
                        f"{contact.get('contact_person_name', 'Unknown')} - {field}: {'; '.join([str(e) for e in error_list])}")
                break
    return errors





def save_items(data, model_class, serializer_class, item_type, context=None):
    ids = []
    errors = []
    instance_list = []
    try:
        for index, item in enumerate(data):
            if model_class == ContactDetalis:
                item['index'] = index
            if 'id' in item and item['id']:
                item_instance = model_class.objects.filter(id=item['id']).first()
                if not item_instance:
                    errors.append(f"{item_type} with ID {item['id']} not found.")
                    break
                serializer = serializer_class(item_instance, data=item, partial=True, context={'request': context})
            else:
                serializer = serializer_class(data=item, context={'request': context})
            
            if serializer.is_valid():
                
                try: 
                    serializer.save() 
                    ids.append(serializer.instance.id)
                    
                    instance_list.append(serializer.instance)
                except ValidationError as e:
                    errors.extend([f"{item_type} - {str(error)}" for error in e.detail])
                    break
                except Exception as e:
                    errors.append(f"{item_type} - {str(e)}")
                    break
            else:
                errors.extend([f"{item_type} - {field}: {'; '.join([str(e) for e in error])}" for field, error in
                               serializer.errors.items()])
                break
    except Exception as e:
        pass

    return {"ids": ids, "success": len(errors) == 0, "error": errors, "instance_list": instance_list}


def SaveContact(data):
    return save_items(data, ContactDetalis, ItemContactSerializer, "Contact")




def checkUserPermission(user, model_name, action):
    if not user or not user.is_authenticated:
        raise GraphQLError(
            "Authentication required",
            extensions={"code": "UNAUTHENTICATED"}
        )
    
    if not has_permission_mutations(user, model_name, [action]):
        raise GraphQLError(
            f"You do not have permission to {action} {model_name}",
            extensions={"code": "PERMISSION_DENIED"}
        )


class SupplierFormCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        company_name = graphene.String(required=True)
        legal_name = graphene.String(required=True)
        customer = graphene.Boolean()
        supplier = graphene.Boolean()
        transporter = graphene.Boolean()
        transporter_id = graphene.String()
        gstin_type = graphene.Int()
        gstin = graphene.String(required=True)
        tcs = graphene.String()
        tds = graphene.Boolean()
        pan_no = graphene.String()
        opening_balance = graphene.Decimal()
        contact = graphene.List(ContactDetailsInput)
        address = graphene.List(CompanyAddressInput)
        active = graphene.Boolean()
        customer_group = graphene.Int()
        sales_person = graphene.Int()
        customer_credited_period = graphene.Int()
        credited_limit = graphene.Int()
        currency = graphene.Int()
        supplier_group = graphene.Int()
        is_lead = graphene.Boolean()
        supplier_credited_period = graphene.Int()
        history_details = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()
        is_delete = graphene.Boolean()

    supplier_form_item = graphene.Field(SupplierFormDataType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

  
    def mutate(self, info, **kwargs):
        user = info.context.user
        instance_id = kwargs.get("id")
        action = "Edit" if instance_id else "Save"
        if kwargs['customer']:
            checkUserPermission(user, "Customer", action)

        elif kwargs["supplier"]:
            checkUserPermission(user, "Supplier", action)
        else:
            raise GraphQLError("Unexpected Error.")
        if kwargs['tds'] and not kwargs['pan_no']:
            return SupplierFormCreateMutation(success=False,
                                              errors=["PAN number is required when TDS is selected.."])

        # Pre-validation
        contact_ids = []
        address_ids = []
        validation_result = supplierPreValidation(kwargs)
        if not validation_result["success"]:
            return SupplierFormCreateMutation(success=False, errors=validation_result["error"])
        for address in kwargs['address']:
            if address['default']:
                kwargs['state'] = address['state']
                kwargs['city'] = address['city']

        # Save Contacts
        contact_result = SaveContact(kwargs['contact'])
        if not contact_result['success']:
            return SupplierFormCreateMutation(success=False, errors=contact_result["error"])
        kwargs['contact'] = contact_result['ids']

        # Save Addresses
        address_result = SaveAddress(kwargs['address'])
        if not address_result['success']:
            return SupplierFormCreateMutation(success=False, errors=address_result["error"])
        kwargs['address'] = address_result['ids']

        # Create or update the SupplierFormData
        if 'id' in kwargs and kwargs['id']:
            supplier_form_item = SupplierFormData.objects.filter(id=kwargs['id']).first()
            if not supplier_form_item:
                return SupplierFormCreateMutation(success=False, errors=[f"Item with ID {kwargs['id']} not found."])
            contact_ids = [contact.id for contact in supplier_form_item.contact.all()]
            address_ids = [address.id for address in supplier_form_item.address.all()]

            serializer = ItemSupplierSerializer(supplier_form_item, data=kwargs, partial=True)
        else:
            serializer = ItemSupplierSerializer(data=kwargs)
        # Validate and save SupplierFormData
        if serializer.is_valid():
            try:
                serializer.save()
                result_c = deleteCommanLinkedTable(contact_ids,
                                                   [contact.id for contact in serializer.instance.contact.all()],
                                                   ContactDetalis),
                result_a = deleteCommanLinkedTable(address_ids,
                                                   [address.id for address in serializer.instance.address.all()],
                                                   CompanyAddress),

                return SupplierFormCreateMutation(supplier_form_item=serializer.instance, success=True, errors=[])
            except Exception as e:
                return SupplierFormCreateMutation(success=False, errors=[str(e)])
        else:
            return SupplierFormCreateMutation(success=False,
                                              errors=[f"{field}: {'; '.join([str(e) for e in error])}" for field, error
                                                      in serializer.errors.items()])


class SupplierFormDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id):
        success = False
        errors = []
        user = info.context.user
        related_contacts = []
        related_addresses = []
        try:
            # Fetch the SupplierFormData instance
            supplier_form_instance = SupplierFormData.objects.get(id=id)
            if supplier_form_instance.customer:
                checkUserPermission(user, "Customer", 'Delete')

            else:
                checkUserPermission(user, "Supplier", 'Delete')

            # Fetch related contacts and addresses before deletion
            related_contacts = list(supplier_form_instance.contact.all())
            related_addresses = list(supplier_form_instance.address.all())

            # Delete the SupplierFormData instance
            supplier_form_instance.delete()

            # Print for debugging purposes

            success = True
        except ProtectedError:
            errors.append('This data is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
            # Attempt cleanup of orphan contacts/addresses
        try:
            for contact in related_contacts:
                if not SupplierFormData.objects.filter(contact=contact).exists():
                    contact.delete()

            for address in related_addresses:
                if not SupplierFormData.objects.filter(address=address).exists():
                    address.delete()
        except Exception as e:
            errors.append(f"Cleanup error: {str(e)}")
        return SupplierFormDeleteMutation(success=success, errors=errors)


class SupplierFormGstEffectiveDateCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        supplier_form_data_id = graphene.ID()
        gstin_type = graphene.ID()
        gstin = graphene.String()
        effective_date = graphene.String()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        success = False
        errors = []

        if kwargs['id']:
            supplierGstEffectiveInstance = SupplierFormGstEffectiveDate.objects.filter(id=kwargs['id']).first()
            if not supplierGstEffectiveInstance:
                errors.append(f"Supplier Form Gst Effective Date with {kwargs['id']} not found.")
            else:
                serializer = SupplierFormGstEffectiveDateSerializer(supplierGstEffectiveInstance, data=kwargs,
                                                                    partial=True)
        else:
            serializer = SupplierFormGstEffectiveDateSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return SupplierFormGstEffectiveDateCreateMutation(success=success, errors=errors)


class WorkCenterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        work_center = graphene.String()
        in_charge = graphene.Int()

    work_type_item = graphene.Field(WorkCenterMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = ''
        work_type_item = None
        success = False
        errors = []
        if 'id' in kwargs:
            work_type_item = WorkCenter.objects.filter(id=kwargs['id']).first()
            if not work_type_item:
                errors.append(f"Work Center with {kwargs['id']} not found.")
            else:
                serializer = WorkCenterSerializer(work_type_item, data=kwargs, partial=True)
        else:
            serializer = WorkCenterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            work_type_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return WorkCenterCreateMutation(work_type_item=work_type_item, success=success,
                                        errors=errors)


class WorkCenterDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            supplier_form_instance = WorkCenter.objects.get(id=id)
            supplier_form_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return WorkCenterDeleteMutation(success=success, errors=errors)


class StockHistoryCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        action = graphene.String()
        stock_link = graphene.Int()
        store_link = graphene.Int()
        part_number = graphene.Int()
        previous_state = graphene.String()
        updated_state = graphene.String()
        added = graphene.String()
        reduced = graphene.String()
        saved_by = graphene.Int()
        transaction_module = graphene.String()
        transaction_id = graphene.Int()
        display_id = graphene.String()
        conference = graphene.Int()
        display_name = graphene.String()

    stock_history_type_item = graphene.Field(StockHistoryType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        stock_history_type_item = None
        success = False
        errors = []
        kwargs['modified_date'] = timezone.now()
        if 'id' in kwargs:
            stock_history_type_item = StockHistory.objects.filter(id=kwargs['id']).first()
            if not stock_history_type_item:
                errors.append(f"Stock History with {kwargs['id']} not found.")
            else:
                serializer = StockHistorySerializer(stock_history_type_item, data=kwargs, partial=True)
        else:
            serializer = StockHistorySerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            stock_history_type_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return StockHistoryCreateMutation(stock_history_type_item=stock_history_type_item, success=success,
                                          errors=errors)


class StockHistoryDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            supplier_form_instance = StockHistory.objects.get(id=id)
            supplier_form_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return StockHistoryDeleteMutation(success=success, errors=errors)


class ImageCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()  # Optional if you are not using it, can be removed
        mainModel = graphene.String(required=False)  # Make required=False if it's optional
        image = graphene.String(required=True)  # Changed to String type for Base64 data

    image_Type = graphene.Field(ImageType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, image, ):
        success = False
        image_Type = None
        errors = []

        if not image:
            errors.append("Image data is missing.")
            return ImageCreateMutation(success=success, errors=errors)

        try:
            imagedata_instance = Imagedata.objects.create(
                image=image,
            )
            image_Type = imagedata_instance
            success = True
        except Exception as e:
            errors.append(str(e))
             
        return ImageCreateMutation(image_Type=image_Type, success=success, errors=errors)


class ImageDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            image_instance = Imagedata.objects.get(id=id)
            image_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ImageDeleteMutation(success=success, errors=errors)


class DocumentCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()  # Optional if you are not using it, can be removed
        document = graphene.String(required=True)  # Base64-encoded document data

    document_Type = graphene.Field(DocumentType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, document):
        success = False
        document_Type = None
        errors = []

        if not document:
            errors.append("Document data is missing.")
            return DocumentCreateMutation(document_Type=document_Type, success=success, errors=errors)
        try:
            # Decode the Base64 string to binary data
            # decoded_doc_data = base64.b64decode(document)

            # # Generate a unique name for the ContentFile
            # unique_name = f"document_{uuid.uuid4().hex}.bin"

            # # Create a ContentFile from the decoded data
            # content_file = ContentFile(decoded_doc_data, name=unique_name)

            # Create an instance of the document model
            document_instance = Document.objects.create(document_file=document)

            document_Type = document_instance
            success = True
        except Exception as e:
            errors.append(str(e))
             

        return DocumentCreateMutation(document_Type=document_Type, success=success, errors=errors)


class DocumentDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            image_instance = Document.objects.get(id=id)
            image_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return DocumentDeleteMutation(success=success, errors=errors)


class RawMaterialBomLinkCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        raw_material = graphene.Int()
        bom = graphene.Int()

    raw_material_bom_link = graphene.Field(RawMaterialBomLinkType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        raw_material_bom_link = None
        success = False
        errors = []
        if 'id' in kwargs:
            raw_material_bom_link = RawMaterialBomLink.objects.filter(id=kwargs['id']).first()
            if not raw_material_bom_link:
                errors.append(f"Child BOM {kwargs['id']} not found.")
            else:
                serializer = RawMaterialBomLinkSerializer(raw_material_bom_link, data=kwargs, partial=True)
        else:
            serializer = RawMaterialBomLinkSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            raw_material_bom_link = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return RawMaterialBomLinkCreateMutation(raw_material_bom_link=raw_material_bom_link, success=success,
                                                errors=errors)


class RawMaterialBomLinkDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        bom_id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id=None, bom_id=None):
        success = False
        errors = []
        try:
            if id:
                data_instance = RawMaterialBomLink.objects.get(id=id)
            if bom_id:
                data_instance = RawMaterialBomLink.objects.get(bom_id=bom_id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return RawMaterialBomLinkDeleteMutation(success=success, errors=errors)


class DepartmentCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        department_head_user_id = graphene.Int(required=True)
        modified_by = graphene.Int()
        created_by = graphene.Int(required =True)

    department_instance = graphene.Field(DepartmentType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Department", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        department_instance = None
        success = False
        errors = []
        if kwargs["id"]:
            department_instance = Department.objects.filter(id=kwargs['id']).first()
            if not department_instance:
                errors.append("Department not found.")
            else:
                serializer = DepartmentSerializer(department_instance, data=kwargs, partial=True)
        else:
            serializer = DepartmentSerializer(data=kwargs) 
        if serializer.is_valid():
            try:
                serializer.save()
                department_instance = serializer.instance
                success = True
            except Exception as e: 
                errors.append(str(e))
           
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return DepartmentCreateMutation(department_instance=department_instance, success=success,
                                        errors=errors)


class DepartmentDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Department", create_action="Create", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            department_instance = Department.objects.get(id=id)
            department_instance.delete()
            success = True
        except Department.DoesNotExist:
            errors.append('Department matching query does not exist.')
        except ProtectedError as e:
            errors.append('This department is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return DepartmentDeleteMutation(success=success, errors=errors)


class OtherExpensesCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        account = graphene.Int()
        HSN = graphene.Int()
        active = graphene.Boolean()
        effective_date = graphene.Date()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    other_expenses_instance = graphene.Field(OtherExpensesType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Other_Expenses", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        other_expenses_instance = None
        success = False
        errors = []
        commanHsnEffectiveDate_instance = ""
        if kwargs["id"]:
            other_expenses_instance = OtherExpenses.objects.filter(id=kwargs['id']).first()
            if not other_expenses_instance:
                errors.append("Department not found.")
            else:
                serializer = OtherExpensesSerializer(other_expenses_instance, data=kwargs, partial=True)
                hsn = Hsn.objects.get(id=kwargs['HSN'])
                created_by = User.objects.get(id=kwargs['created_by'])
                if kwargs['effective_date'] == datetime.now().date():
                    kwargs['HSN'] = hsn.id
                else:
                    kwargs['HSN'] = other_expenses_instance.HSN.id
                if other_expenses_instance.HSN.hsn_code == hsn.hsn_code:
                    pass  # No change needed if the hsn codes match
                else:
                    if kwargs['effective_date']:
                        # Create commanHsnEffectiveDate if needed
                        commanHsnEffectiveDate_instance = CommanHsnEffectiveDate(
                            None, "other_expenses", hsn.id, kwargs['effective_date'],
                            created_by.id)
                        commanHsnEffectiveDate_instance.save()
                    else:
                        errors.append('Effective date is required')
                        return OtherExpensesCreateMutation(other_expenses_instance=other_expenses_instance,
                                                           success=success,
                                                           errors=errors)
        else:
            serializer = OtherExpensesSerializer(data=kwargs)
   
        if serializer.is_valid():
            try:
                serializer.save()
                other_expenses_instance = serializer.instance
                if commanHsnEffectiveDate_instance:
                    other_expenses_instance.comman_hsn_effective_date.add(commanHsnEffectiveDate_instance)
                success = True
            except Exception as e:
                errors.append(str(e))

        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return OtherExpensesCreateMutation(other_expenses_instance=other_expenses_instance, success=success,
                                           errors=errors)

class OtherExpensesDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Other_Expenses", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            other_expenses_instance = OtherExpenses.objects.get(id=id)
            other_expenses_instance.delete()
            success = True
        except OtherExpenses.DoesNotExist:
            errors.append('OtherExpenses matching query does not exist.')
        except ProtectedError:
            errors.append('This OtherExpenses is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return OtherExpensesDeleteMutation(success=success, errors=errors)

class TermsConditionsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        tc = graphene.String()
        module = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int(required=True)

    terms_conditions_instance = graphene.Field(TermsConditionsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Terms_Conditions", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        terms_conditions_instance = None
        success = False
        errors = []
        if kwargs["id"]:
            terms_conditions_instance = TermsConditions.objects.filter(id=kwargs['id']).first()
            if not terms_conditions_instance:
                errors.append("Terms Conditions not found.")
            else:
                serializer = TermsConditionsSerializer(terms_conditions_instance, data=kwargs, partial=True)
        else:
            serializer = TermsConditionsSerializer(data=kwargs)
        if serializer.is_valid():
            try:
                serializer.save()
                terms_conditions_instance = serializer.instance
            except Exception as e:
                errors.append(str(e))
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return TermsConditionsCreateMutation(terms_conditions_instance=terms_conditions_instance, success=success,
                                             errors=errors)

class TermsConditionsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    # @mutation_permission("Terms_Conditions", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            other_expenses_instance = TermsConditions.objects.get(id=id)
            other_expenses_instance.delete()
            success = True
        except OtherExpenses.DoesNotExist:
            errors.append('TermsConditions matching query does not exist.')
        except ProtectedError:
            errors.append('This TermsConditions is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return TermsConditionsDeleteMutation(success=success, errors=errors)

class PurchaseOrderItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    item_master_id = graphene.Int()
    description = graphene.String()
    category = graphene.String()
    qty = graphene.Decimal()
    uom = graphene.Int()
    hsn_id = graphene.Int()
    rate = graphene.Decimal()
    po_qty = graphene.Decimal()
    po_uom = graphene.Int()
    po_rate = graphene.Decimal()
    conversion_factor = graphene.Decimal()
    tax = graphene.Int()
    parent = graphene.Int()
    amount = graphene.Decimal()
    po_amount = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    fixed = graphene.Boolean()

class PurchaseOrderOtherExpenceInput(graphene.InputObjectType):
    id = graphene.ID()
    other_expenses_id = graphene.Int()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    amount = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    parent = graphene.Int()
    igst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()

class PurchaseOrderCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String() 
        po_date = graphene.Date()
        currency = graphene.Int(required=True)
        exchange_rate = graphene.Decimal(required=True)
        gst_nature_transaction = graphene.Int()
        department = graphene.Int()
        due_date = graphene.Date()
        receiving_store_id = graphene.Int()
        scrap_reject_store_id = graphene.Int()
        credit_period = graphene.Int()
        payment_terms = graphene.String()
        supplier_ref = graphene.String()
        supplier_id = graphene.Int()
        address = graphene.Int()
        remarks = graphene.String()
        contact = graphene.Int()
        gstin_type = graphene.String()
        gstin = graphene.String() 
        state = graphene.String()
        place_of_supply = graphene.String()
        item_details = graphene.List(PurchaseOrderItemDetailsInput)
        other_expenses = graphene.List(PurchaseOrderOtherExpenceInput)
        parent_order = graphene.Int()
        item_total_befor_tax = graphene.Decimal()
        other_charges_befor_tax = graphene.Decimal()
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        tax_total = graphene.Decimal()
        taxable_value =graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        igst = graphene.JSONString()
        cess = graphene.JSONString()
        parent_order = graphene.Int() 

    purchase_order_instance = graphene.Field(purchaseOrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString()
    other_expences = graphene.JSONString()
    version = graphene.Field(versionListType)

    @status_mutation_permission("Purchase_Order")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status']
        purchaseService_result = PurchaseService(data,status,info)
        purchase_result = purchaseService_result.process()
 
        return PurchaseOrderCreateMutation(purchase_order_instance=purchase_result['purchase'], success=purchase_result['success'],
                                    errors=purchase_result['errors'],item_details= purchase_result['item_details'],
                                    other_expences= purchase_result['other_expences'],version=purchase_result['version'])

class PurchaseOrderCancleMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase_Order", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        unCancleData = []
        purchase_instance = purchaseOrder.objects.get(id=id)
        try:
            if purchase_instance:
                goods_receipt_notes = purchase_instance.gin.all() 
                for goods_receipt_notes in goods_receipt_notes:
                    if goods_receipt_notes.status.name == "Canceled":
                        pass
                    else:
                        unCancleData.append(goods_receipt_notes.gin_no.linked_model_id)
                if len(unCancleData) == 0:
                    status_obj = CommanStatus.objects.filter(name="Canceled", table="Purchase").first()
                    if status_obj:
                        if purchase_instance.status and purchase_instance.status.name in ['Draft',"Submit"]:
                            purchase_instance.status = status_obj
                            purchase_instance.save()
                            success = True
                        elif purchase_instance.status and purchase_instance.status.name in ["Canceled"]:
                            errors.append("This purchase is already Canceled.")
                        else:
                            errors.append("An exception status.")
                    else:
                        errors.append("Ask developer to add status Canceled")
                else:
                    errors.append(f"Befor cancel GIN. set the status to 'Canceled' the GIN {','.join(unCancleData)}")
        except Exception as e:
            errors.append(f"An exception occurred-{str(e)}")
        return PurchaseOrderCancleMutation(success=success, errors=errors)

class PurchaseOrderDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase_Order", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        unCancleData = []
        try:
            purchase_instance = purchaseOrder.objects.get(id=id)
            goods_receipt_notess = purchase_instance.gin.all()
            for goods_receipt_notes in goods_receipt_notess:
                unCancleData.append(goods_receipt_notes.gin_no.linked_model_id)
            
            if len(unCancleData) > 0:
                errors.append(f"Before Delete Purchase Order You Need to Delete {', '.join(unCancleData)}")
                return PurchaseOrderDeleteMutation(success=success, errors=errors)
            purchase_instance.delete()
            success = True
        except purchaseOrder.DoesNotExist:
            errors.append('PurchaseOrder  query does not exist.')
        except ProtectedError as e:
             
            errors.append('PurchaseOrder is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
          
        return PurchaseOrderDeleteMutation(success=success, errors=errors)

class GeneratePdfForPurchaseOrder(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        
        try:
            purchase_instance = purchaseOrder.objects.get(id=id) 
            bank_data = company_bank_info()
            html = purchase_instance.terms_conditions_text
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            status = purchase_instance.status.name
          
            try:
                purchase_data = { 
                    "purchaseNo":str(purchase_instance.purchaseOrder_no.linked_model_id),
                    "purchaseOrderDate":str(purchase_instance.po_date.strftime('%d/%m/%Y')),
                    "customerName":purchase_instance.supplier_id.company_name,
                    "customerAddress": f"{purchase_instance.address.address_line_1},\n"
                                f"{purchase_instance.address.address_line_2},"
                                f"{purchase_instance.address.city} - {purchase_instance.address.pincode},\n"
                                f"{purchase_instance.address.state}, {purchase_instance.address.country}." if purchase_instance.address.address_line_2 and purchase_instance.address.address_line_2 != None else
                                f"{purchase_instance.address.address_line_1},\n"
                                f"{purchase_instance.address.city} - {purchase_instance.address.pincode},\n"
                                f"{purchase_instance.address.state}, {purchase_instance.address.country}.",
                    "department":purchase_instance.department.name,
                    "contactPerson":purchase_instance.contact.contact_person_name,
                    "phoneNumber":purchase_instance.contact.phone_number,
                    "mail":purchase_instance.contact.email,
                    "supplierRef":purchase_instance.supplier_ref,
                    "creditPeriod":str(purchase_instance.credit_period),
                    "dueDate":str(purchase_instance.due_date.strftime('%d/%m/%Y')),
                    "paymentTerms":purchase_instance.payment_terms,
                    "Table Name": ['SI',"OtherIncome"],
                    "Other Table": ["OtherIncome"],
                    "OtherIncome_Datas": [
                        {
                            "account": other_charges.other_expenses_id.name,
                            # "%": other_charges.discount_value if  other_charges.discount_value else "",
                            # "tax": other_charges.tax,
                            "Total": format_currency(other_charges.amount,
                                                purchase_instance.currency.Currency.currency_symbol, False)
                        }
                        for other_charges in purchase_instance.other_expenses.all()
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
                        "Rate": "Rate",
                        "%": "%",
                        "Amount": "Amount",
                        "Total": "Total"
                    },
                    "SI_Datas":[
                    {
                        "No": f"{str(index + 1)}",
                        "Description": f"{itemdetail.description}",
                        "Item's HSN Code (Text)": f"{itemdetail.hsn_id.hsn_code}",
                        "Quantity": f"{itemdetail.po_qty:.0f} {itemdetail.po_uom.name}",
                        "Rate": f"{itemdetail.po_rate:.2f}",
                        
                        "%": str(int(itemdetail.tax)) if float(itemdetail.tax).is_integer() else str(float(itemdetail.tax)),
                        "Amount": f"{round((itemdetail.tax * itemdetail.po_amount) / 100, 2)}",
                        "Total": f"{itemdetail.amount:.2f}"
                    }
                    for index, itemdetail in enumerate(purchase_instance.item_details.all())
                ],
                "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "HSN": "center",
                    "Qty": "center",
                    "UOM": "center",
                    "Rate": "right", 
                    "Disc":"right", 
                    "%": "right",
                    "Amount": "right",
                    "Total": "right"
                },
                "totalAmoutInWords":num2words(purchase_instance.net_amount, lang='en').title() + " Only",
                "termsandcondition":tc,
                "totalTax":format_currency(str(float(purchase_instance.taxable_value or 0)), purchase_instance.currency.Currency.currency_symbol, False),
                "gst":format_currency(str(float(purchase_instance.tax_total or 0)), purchase_instance.currency.Currency.currency_symbol, False),
                "AfterTax":format_currency(purchase_instance.net_amount, purchase_instance.currency.Currency.currency_symbol),
                "bankName":bank_data.bank_name if bank_data else "",
                "ifsc":bank_data.ifsc_code if bank_data else "",
                "accountNo":bank_data.account_number if bank_data else "",
                "branch":bank_data.branch_name if bank_data else ""
                } 
            except Exception  as e:
               pass
            

             
            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\PurchaseOrder.docx".format(BASE_DIR)

                if status == "Draft":
                    doc_path = r"{}\static\PDF_TEMP\PO_PT_ND_V03 -Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}\static\PDF_TEMP\PO_PT_ND_V03 -Submit.docx".format(BASE_DIR)
    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/PurchaseOrder.docx".format(BASE_DIR)
                if status == "Draft":
                    doc_path = r"{}/static/PDF_TEMP/PO_PT_ND_V03 -Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}/static/PDF_TEMP/PO_PT_ND_V03 -Submit.docx".format(BASE_DIR)
                
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, purchase_data)
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
             
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForPurchaseOrder(pdf_data =pdf_base64, success=success, errors=errors)

class GoodsInwardNoteItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    item_master = graphene.Int()
    received = graphene.Decimal()
    qc = graphene.Boolean()
    purchase_order_parent = graphene.Int()
    reword_delivery_challan_item = graphene.Int()

class GoodsInwardNoteCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        gin_date = graphene.Date()
        status = graphene.String()
        remark = graphene.String()
        purchase_order_id = graphene.Int()
        goods_receipt_note_item_details_id = graphene.List(GoodsInwardNoteItemDetailsInput)
        rework_delivery_challan = graphene.Int()
        parent_type = graphene.String()

    goods_inward_note_instance = graphene.Field(GoodsInwardNote_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("GIN")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status'] 
        gin_service_result = GinService(data,status,info)
        gin_result = gin_service_result.process()
      
        if not gin_result.get("success"):
            return GoodsInwardNoteCreateMutation(goods_inward_note_instance=gin_result.get("gin"),
                                            success=gin_result.get("success"),errors=gin_result.get("errors"))


        return GoodsInwardNoteCreateMutation(goods_inward_note_instance=gin_result.get("gin"),
                                            success=gin_result.get("success"),errors=gin_result.get("errors"))

class GoodsInwardNotecancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        parent_type = graphene.String(required=True)

    goods_inward_note_instance = graphene.Field(GoodsInwardNote_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GIN", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, **kwargs):
        gin_cancle_service = GinCancelService(kwargs, info)
        gin_cancel_result = gin_cancle_service.process() 
        if not gin_cancel_result.get("success"):
            return GoodsInwardNotecancelMutation(goods_inward_note_instance=gin_cancel_result.get("gin"),
                                            success=gin_cancel_result.get("success"),
                                            errors=gin_cancel_result.get("errors"))

        return GoodsInwardNotecancelMutation(goods_inward_note_instance=gin_cancel_result.get("gin"),
                                            success=gin_cancel_result.get("success"),
                                            errors=gin_cancel_result.get("errors"))

class GoodsInwardNoteDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GIN", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            gin  = GoodsInwardNote.objects.get(id=id)
            if gin.status.name == "Canceled":
                qir = gin.quality_inspection_report_id
                if qir:
                    errors.append(f"Befor Delete GIN. delete The QIR {qir.qir_no.linked_model_id}")
                grn_ = gin.grn
                if grn_:
                    errors.append(f"Befor Delete GIN. delete The GRN {grn_.grn_no.linked_model_id}")
                if len(errors) > 0:
                    return GoodsInwardNoteDeleteMutation(success=success, errors=errors)
                gin.delete()
                success = True
            else:
                errors.append("Before deleting, set the status to 'Canceled'.")
        except GoodsInwardNote.DoesNotExist:
            errors.append('GIN query does not exist.')
        except ProtectedError:
            errors.append('GIN is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return GoodsInwardNoteDeleteMutation(success=success, errors=errors)

class QualityInspectionsReportItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    goods_inward_note_item = graphene.Int()
    accepted = graphene.Decimal()
    rejected = graphene.Decimal()
    rework = graphene.Decimal()
    checked_by = graphene.Int()

class QirCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        qir_date = graphene.Date()
        remarks = graphene.String()
        quality_inspections_report_item_detail_id = graphene.List(QualityInspectionsReportItemDetailsInput)
        goods_inward_note = graphene.String()

    quality_inspection_report_instance = graphene.Field(QualityInspectionReportType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("QIR")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status']
        qir_service_result = QirService(data,status,info)
        result = qir_service_result.process()
         
        return QirCreateMutation(quality_inspection_report_instance=result.get("QIR"),
                                        success=result.get("success"),errors=result.get("errors"))

class QirCancleMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String) 

    @mutation_permission("QIR", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            status_obj = CommanStatus.objects.filter(name="Canceled", table="QIR").first()
            if status_obj:
                quality_inspection_report_instance = QualityInspectionReport.objects.get(id=id)
                rwc = quality_inspection_report_instance.rework_received
                if rwc:
                    if rwc.status.name != "Canceled":
                        errors.append("Befor Cancele QIR. set the status to 'Canceled' the Rework Delivery Challan {rwc.dc_no.linked_model_id}")
                        return QirCancleMutation(success=success, errors=errors)
                grn = quality_inspection_report_instance.goods_inward_note.grn
                if grn and grn.status.name != "Canceled":
                    errors.append("Befor Cancele QIR. set the status to 'Canceled' the Goods Receipt Note {grn.grn_no.linked_model_id}")
                    return QirCancleMutation(success=success, errors=errors)


                if quality_inspection_report_instance.status and quality_inspection_report_instance.status.name in ['Pending',"Checked"]:
                    quality_inspection_report_instance.status = status_obj
                    quality_inspection_report_instance.save()
                    success = True
                elif quality_inspection_report_instance.status and quality_inspection_report_instance.status.name in ["Canceled"]:
                    errors.append("This QIR is already Canceled.")
                else:
                    errors.append("An exception status.")
            else:
                errors.append("Ask developer to add status Canceled")
        except Exception as e:
            errors.append(f"An exception occurred-{str(e)}")

        return QirCancleMutation(success=success, errors=errors)

class QirDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    actions = graphene.String()

    @mutation_permission("QIR", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        actions = ""
        try:
            qir = QualityInspectionReport.objects.get(id=id)
            rwc = qir.rework_received
            if rwc:
                if rwc.status.name != "Canceled":
                    errors.append("Befor Delete QIR. delete The Rework Delivery Challan {rwc.dc_no.linked_model_id}")
                    return QirDeleteMutation(success=success, errors=errors)
            grn = qir.goods_inward_note.grn
            if grn and grn.status.name != "Canceled":
                errors.append("Befor Delete QIR. delete The Goods Receipt Note {grn.grn_no.linked_model_id}")
                return QirDeleteMutation(success=success, errors=errors)

            if qir.status.name == "Canceled":
                qir.delete()
                success = True
            else:
                errors.append("Before deleting, set the status to 'Canceled'.")
        except QualityInspectionReport.DoesNotExist:
            errors.append('QIR query does not exist.')
        except ProtectedError:
            errors.append('QIR is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return QirDeleteMutation(success=success, errors=errors, actions=actions)

class GeneratePdfForQir(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            qir_instance = QualityInspectionReport.objects.get(id=id) 
            gin_instance = qir_instance.goods_inward_note 
            purchase_instance = gin_instance.purchase_order_id 
            status = qir_instance.status.name
            try:
                qir_data = {
                   "qirNo": str(qir_instance.qir_no.linked_model_id),
                   "qirDate":str(qir_instance.qir_date.strftime('%d/%m/%Y')),
                   "poNo":str(purchase_instance.purchaseOrder_no.linked_model_id),
                   "poDate":str(purchase_instance.po_date.strftime('%d/%m/%Y')),
                   "ginNo": str(gin_instance.gin_no.linked_model_id),
                   "ginDate":str(gin_instance.gin_date.strftime('%d/%m/%Y')),
                #    "store":str(purchase_instance.scrap_reject_store_id.store_name),
                   "checkedBy":str(qir_instance.quality_inspections_report_item_detail_id.first().checked_by.username) if qir_instance.quality_inspections_report_item_detail_id.first().checked_by.username else None,
                   "Table Name": ['SI'],
                   "SI_Columns": {
                       "S.No": "No",
                       "Description":"Description",
                       "PO Qty":"PO Qty",
                       "GIN Qty":"GIN Qty",
                       "UOM":"UOM",
                       "Accepted":"Accepted",
                       "Rejected":"Rejected",
                       "Rework":"Rework"
                   },
                   "SI_Datas":[
                       {
                           "No": f"{str(index + 1)}",
                           "Description": f"{itemdetail.goods_inward_note_item.purchase_order_parent.description}",
                           "PO Qty": f"{itemdetail.goods_inward_note_item.purchase_order_parent.po_qty:.0f}",
                           "GIN Qty":f"{itemdetail.goods_inward_note_item.received:.0f}",
                           "UOM": f"{itemdetail.goods_inward_note_item.purchase_order_parent.uom.name}",
                           "Accepted":f"{itemdetail.accepted:.0f}",
                           "Rejected":f"{itemdetail.rejected:.0f}",
                           "Rework":f"{itemdetail.rework:.0f}",
                       }
                       for index, itemdetail in enumerate(qir_instance.quality_inspections_report_item_detail_id.all())
                   ],
                   "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "PO Qty":"center",
                    "GIN Qty":"center",
                    "UOM":"center",
                    "Accepted":"center",
                    "Rejected":"center",
                    "Rework":"center",
                },
                "totalQty": f"{qir_instance.quality_inspections_report_item_detail_id.aggregate(total=Sum('accepted'))['total'] or 0:.0f}"
                }
                 
                current_os = platform.system().lower()
                if current_os == 'windows':
                    output_docx =  r"{}\static\PDF_OUTPUT\QIR.docx".format(BASE_DIR)
                        
                    if status == "Pending":
                            doc_path = r"{}\static\PDF_TEMP\QIR_V01 - Pending.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}\static\PDF_TEMP\QIR_V01 - Checked.docx".format(BASE_DIR)
                    
                else:
                    output_docx = r"{}/static/PDF_OUTPUT/QIR.docx".format(BASE_DIR)
                    if status == "Pending":
                            doc_path = r"{}/static/PDF_TEMP/QIR_V01 - Pending.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}/static/PDF_TEMP/QIR_V01 - Checked.docx".format(BASE_DIR)

                doc = Documentpdf(doc_path)
                doc = fill_document_with_mock_data(doc, qir_data)
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
            except Exception as e : 
                print("ee----",e)
                errors.append(f'An exception occurred in PDF creation -{str(e)}')

        except Exception as e : 
            print("e----",e)
            errors.append(f'An exception occurred in PDF creation -{str(e)}')

        return GeneratePdfForQir(pdf_data =pdf_base64, success=success, errors=errors)

class GoodsReceiptNoteItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    gin = graphene.Int()
    qty = graphene.Decimal()
    base_qty =graphene.Decimal()
    conversion_factor = graphene.Decimal()
    serial_number = graphene.String()
    batch_number = graphene.String()
    
class GoodsReceiptNoteCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        grn_date = graphene.Date()
        e_way_bill = graphene.String()
        e_way_bill_date = graphene.Date()
        goods_receipt_note_item_details = graphene.List(GoodsReceiptNoteItemDetailsInput)
        remarks = graphene.String()
        goods_inward_note = graphene.Int()
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    goods_receipt_note = graphene.Field(GoodsReceiptNoteType)

    @status_mutation_permission("GRN")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status']
        grn_service_result = GrnService(data,status,info)
        result = grn_service_result.process()
        return GoodsReceiptNoteCreateMutation(goods_receipt_note=result.get("grn"),
                                        success=result.get("success"),errors=result.get("errors"))

class GoodsReceiptNoteCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GRN", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        errors = []
        success = False

        try:
            status_obj = CommanStatus.objects.filter(name="Canceled", table="GRN").first()
            if not status_obj:
                return GoodsReceiptNoteCancelMutation(success=False, errors=["Ask Admin to add status Canceled"])

            grn = GoodsReceiptNote.objects.filter(id=id).first()
            if not grn:
                return GoodsReceiptNoteCancelMutation(success=False, errors=["GRN not found."])

            def collect_conflicts(qs, label, number_field):
                conflicts = qs.exclude(status__name="Canceled").values(
                    status_name=F("status__name"),
                    return_no=F(number_field)
                )
                if conflicts:
                    errors.append(
                        f"Before Cancel GRN, need to cancel {label} "
                        + ", ".join([f"{c['status_name']} ({c['return_no']})" for c in conflicts])
                    )

            collect_conflicts(grn.purchase_invoice, "purchase invoice", "purchase_invoice_no__linked_model_id")
            collect_conflicts(grn.purchase_retun, "purchase return", "purchase_return_no__linked_model_id")

            if errors:
                return GoodsReceiptNoteCancelMutation(success=False, errors=errors)

            if grn.status and grn.status.name in ["Draft", "Received"]:
                service = GrnCancelService(id, info)
                service.Process()
                return GoodsReceiptNoteCancelMutation(success=service.success, errors=service.errors or [])
            elif grn.status and grn.status.name == "Canceled":
                errors.append("This GRN is already Canceled.")
            else:
                errors.append("Invalid GRN status.")
        except Exception as e:
            errors.append(f"An exception occurred - {e}")

        return GoodsReceiptNoteCancelMutation(success=success, errors=errors)

class GoodsReceiptNoteDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("GRN", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = [] 
        try:
            grn  = GoodsReceiptNote.objects.get(id=id)
            
            
            if grn.status.name == "Canceled":
                grn.delete()
                success = True
            else:
                errors.append("Before deleting, set the status to 'Canceled'.")
        except GoodsReceiptNote.DoesNotExist:
            errors.append('GRN query does not exist.')
        except ProtectedError:
            errors.append('GRN is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return GoodsReceiptNoteDeleteMutation(success=success, errors=errors)

class GeneratePdfForGoodsReceiptNote(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
 
        try:
            grn_instance = GoodsReceiptNote.objects.get(id=id) 
            purchase_instance = grn_instance.goods_inward_note.purchase_order_id
            gin = grn_instance.goods_inward_note
            status = grn_instance.status.name
            grn_data ={
                "grnNo":str(grn_instance.grn_no.linked_model_id),
                "grnDate":str(grn_instance.grn_date.strftime('%d/%m/%Y')),
                "supplierCode":str(purchase_instance.supplier_id.supplier_no),
                "supplierName":str(purchase_instance.supplier_id.company_name),
                "department":purchase_instance.department.name,
                "createdBy":purchase_instance.created_by.username,
                "dueDate":purchase_instance.due_date,
                "poNo":str(purchase_instance.purchaseOrder_no.linked_model_id),
                "poDate":str(purchase_instance.po_date.strftime('%d/%m/%Y')),
                "ginNo":str(gin.gin_no.linked_model_id),
                "ginDate":str(gin.gin_date.strftime('%d/%m/%Y')),
                "store":purchase_instance.receiving_store_id.store_name,
                "dueDate":str(purchase_instance.due_date.strftime('%d/%m/%Y')),
                "Table Name": ['SI'],
                "SI_Columns": {
                    "S.No": "No",
                    "Description": "Description",
                    "PO Qty":"PO Qty",
                    "GIN/QC Qty":"GinQCQty",
                    "UOM":"UOM",
                    "Conv Factor":"ConvFactor",
                    "Batch No /Serial No":"BatchSerial"
                },
                "SI_Datas":[
                    {
                        "No": f"{str(index + 1)}",
                        "Description": f"{itemdetail.gin.purchase_order_parent.description}",
                        "PO Qty":f"{itemdetail.gin.purchase_order_parent.po_qty:.0f}",
                        "GinQCQty":f"{itemdetail.qty:.0f}",
                        "UOM":itemdetail.gin.purchase_order_parent.uom.name,
                        "ConvFactor":f"{(itemdetail.gin.purchase_order_parent.conversion_factor or 0):.0f}",
                        "BatchSerial": (
                            itemdetail.batch_number
                            if itemdetail.batch_number
                            else itemdetail.serial_number
                            if itemdetail.serial_number
                            else "-"
                        )
                    }
                    for index, itemdetail in enumerate(grn_instance.goods_receipt_note_item_details.all())
                ],
                "SI_Columns_Style":{
                    "S.No": "center",
                    "Description": "left",
                    "PO Qty":"center",
                    "GIN/QC Qty":"center",
                    "UOM":"center",
                    "Conv Factor":"center",
                    "Batch No /Serial No":"left",
                },
               "totalQty": f"{grn_instance.goods_receipt_note_item_details.aggregate(total=Sum('qty'))['total'] or 0:.0f}"
            }
            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\GRN.docx".format(BASE_DIR)
                print("status-----",status)   
                if status == "Draft":
                        doc_path = r"{}\static\PDF_TEMP\GRN_V01 - Draft.docx".format(BASE_DIR)
                else:
                        doc_path = r"{}\static\PDF_TEMP\GRN_V01 - Received.docx".format(BASE_DIR)
                    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/GRN.docx".format(BASE_DIR)
                if status == "Draft":
                        doc_path = r"{}/static/PDF_TEMP/GRN_V01 - Draft.docx".format(BASE_DIR)
                else:
                        doc_path = r"{}/static/PDF_TEMP/GRN_V01 - Received.docx".format(BASE_DIR)
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, grn_data)
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
             
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForPurchaseOrder(pdf_data =pdf_base64, success=success, errors=errors)

class PurchaseRetunBatchInput(graphene.InputObjectType):
    id = graphene.ID()
    batch_str = graphene.String(required=True)
    batch = graphene.Int(required=True)
    qty = graphene.Decimal()

class purchaseRetunNobatchNoserialInput(graphene.InputObjectType):
    id = graphene.ID()
    grn_no = graphene.String(required=True)
    nobatch_noserial = graphene.Int(required=True)
    qty = graphene.Decimal()

class PurchaseReturnChallanItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    purchase_invoice_item = graphene.Int()
    grn_item = graphene.List(graphene.String)
    serial = graphene.List(graphene.Int)
    batch = graphene.List(PurchaseRetunBatchInput)
    nobatch_noserial = graphene.List(purchaseRetunNobatchNoserialInput)
    po_return_qty = graphene.Decimal()
    base_return_qty = graphene.Decimal()
    po_amount = graphene.Decimal()

class PurchaseReturnChallanCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        purchase_return_date = graphene.Date()
        purchase_invoice = graphene.Int()
        purchase_order = graphene.Int(required = True)
        eway_bill_no = graphene.String()
        eway_bill_date = graphene.Date()
        remarks = graphene.String()
        purchase_return_challan_item_Details = graphene.List(PurchaseReturnChallanItemDetailsInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        transportation_mode = graphene.String()
        vehicle_no = graphene.String()
        driver_name = graphene.String()
        transport = graphene.Int()
        docket_no = graphene.String()
        docket_date = graphene.Date()
        other_model = graphene.String()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        befor_tax = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        
        
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    purchase_return_challan = graphene.Field(PurchaseReturnChallanType)
 
    @status_mutation_permission("Purchase Return")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status'] 
        purchase_retun_service_result = PurchaseRetunService(data,status,info)
        result = purchase_retun_service_result.process()
        
        return PurchaseReturnChallanCreateMutation(purchase_return_challan=result.get("purchase_return"),
                                        success=result.get("success"),errors=result.get("errors"))

class PurchaseReturnChallanCancleMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    purchase_return_challan = graphene.Field(PurchaseReturnChallanType)

    @mutation_permission("Purchase Return", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, id):
        purchase_retun_service_result = PurchaseRetunCancelService(id,info)
        result = purchase_retun_service_result.process()
        return PurchaseReturnChallanCancleMutation(purchase_return_challan=result.get("purchase_return"),
                                        success=result.get("success"),errors=result.get("errors"))

class PurchaseReturnChallanDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase Return", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success =False
        errors = []
        try:
            purchase_return = PurchaseReturnChallan.objects.get(id=id)
            
            if purchase_return.status.name == "Canceled":
                debit_note = purchase_return.debitnote_set.first()
                if debit_note:
                    errors.append(f"Befor delete purchase return need to delete the debit note {debit_note.debit_note_no.linked_model_id}")
                    return PurchaseReturnChallanDeleteMutation(success=success, errors=errors)
                purchase_return.delete()
                success = True
            else:
                errors.append("Before deleting, set the status to 'Canceled'.")
        except GoodsReceiptNote.DoesNotExist:
            errors.append('Purchase Return query does not exist.')
        except ProtectedError:
            errors.append('Purchase Return is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
            
        return PurchaseReturnChallanDeleteMutation(success=success, errors=errors)

class GeneratePdfForPurchaseReturn(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        
        try:
            purchase_return = PurchaseReturnChallan.objects.get(id=id) 
            if not purchase_return:
                return GraphQLError("Purchase return not found")
            html = purchase_return.terms_conditions_text
           
            soup = BeautifulSoup(html, "html.parser")
            tc = soup.get_text(separator="\n")  # Optional: use '\n' or ' ' as needed
            tc = "\n".join([f"* {line}" for line in tc.strip().splitlines()])
            status = purchase_return.status.name
         
            grn = purchase_return.goodsreceiptnote_set.first()
            purchase_invoice  = purchase_return.purchaseinvoice_set.first()

            purchase_order = grn.goods_inward_note.purchase_order_id if grn and grn.goods_inward_note else  purchase_invoice.goodsreceiptnote_set.first().goods_inward_note.purchase_order_id
            
            def find_batch_serial(itemdetail):
                if itemdetail.serial.exists():
                    return ", ".join( serial.serial_number for serial in  itemdetail.serial.all())
                elif itemdetail.batch.exists():
                    for i in itemdetail.batch.all():
                        print("i", i)
                    return ", ".join( bacth.batch.batch_number for bacth in  itemdetail.batch.all())

                return ""
           
            try:
                purchase_return = { 
                  "purchaseRetunNo":str(purchase_return.purchase_return_no.linked_model_id),
                  "purchaseReturnDate":str(purchase_return.purchase_return_date.strftime('%d/%m/%Y')),
                  "supplierName":purchase_order.supplier_id.company_name ,
                  "supplierAddress":f"{purchase_order.address.address_line_1},\n"
                                f"{purchase_order.address.address_line_2},"
                                f"{purchase_order.address.city} - {purchase_order.address.pincode},\n"
                                f"{purchase_order.address.state}, {purchase_order.address.country}." if purchase_order.address.address_line_2 and purchase_order.address.address_line_2 != None else
                                f"{purchase_order.address.address_line_1},\n"
                                f"{purchase_order.address.city} - {purchase_order.address.pincode},\n"
                                f"{purchase_order.address.state}, {purchase_order.address.country}.",
                  "gstIn":purchase_order.gstin if purchase_order.gstin else "",
                  "contactPerson":purchase_order.contact.contact_person_name if purchase_order.contact else "",
                  "phoneNumber":purchase_order.contact.phone_number if purchase_order.contact else "",
                  "mail":purchase_order.contact.email if purchase_order.contact else "",
                  "poNo":purchase_order.purchaseOrder_no.linked_model_id,
                  "grnNo":grn.grn_no.linked_model_id if grn else  "",
                  "dueDate":str(purchase_order.due_date.strftime('%d/%m/%Y')) if purchase_order.due_date else "",
                  "ewayBill":purchase_return.eway_bill_no if purchase_return.eway_bill_no else "",
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
                  for index, itemdetail in enumerate(purchase_return.purchase_return_challan_item_Details.all())
                ],
                  "taxTotal":format_currency(purchase_return.net_amount, purchase_order.currency.Currency.currency_symbol),
                  "totalQty": f"{sum(itemdetail.po_return_qty for itemdetail in purchase_return.purchase_return_challan_item_Details.all()):.3f}",
                  "termsandcondition":tc
                } 
            except Exception  as e:
               print("Exception in pdf",e)
               pass
 
            

            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\PurchaseReturn.docx".format(BASE_DIR)

                if status == "Draft":
                    doc_path = r"{}\static\PDF_TEMP\PRC_PT_V02-Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}\static\PDF_TEMP\PRC_PT_V02-Submit.docx".format(BASE_DIR)
    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/PurchaseReturn.docx".format(BASE_DIR)
                if status == "Draft":
                    doc_path = r"{}/static/PDF_TEMP/PRC_PT_V02-Draft.docx".format(BASE_DIR)
                else:
                    doc_path = r"{}/static/PDF_TEMP/PRC_PT_V02-Submit.docx".format(BASE_DIR)
                
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, purchase_return)
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
        
        return GeneratePdfForPurchaseReturn(pdf_data =pdf_base64, success=success, errors=errors)

class ReworkDeliveryChallanItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID() 
    purchase_item = graphene.Int()
    qc_item = graphene.Int()
    rework_qty = graphene.Decimal()
    amount = graphene.Decimal()

class ReworkDeliveryChallanCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        dc_date = graphene.Date()
        address = graphene.JSONString()
        purchase_order_no = graphene.Int()
        qc = graphene.Int()
        remarks = graphene.String()
        e_way_bill = graphene.String()
        e_way_bill_date = graphene.Date()
        place_of_supply = graphene.String()
        rework_delivery_challan_item_details = graphene.List(ReworkDeliveryChallanItemDetailsInput)
        befor_tax = graphene.Decimal()
        tax_total = graphene.Decimal()
        round_off = graphene.Decimal()
        round_off_method = graphene.String()
        net_amount = graphene.Decimal()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        transportation_mode = graphene.String()
        vehicle_no = graphene.String()
        driver_name = graphene.String()
        transport = graphene.Int()
        docket_no = graphene.String()
        docket_date = graphene.String()
        other_model = graphene.String()

    rework_delivery_challan_instance = graphene.Field(ReworkDeliveryChallanType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @status_mutation_permission("Rework DC")
    def mutate(self, info, **kwargs):
        status = kwargs.get("status")
        rdc_serives = ReworkDeliveryService(kwargs, status, info)
        rdc_serives.process()
        return ReworkDeliveryChallanCreateMutation(success=rdc_serives.success, errors=rdc_serives.errors,
                                                rework_delivery_challan_instance=rdc_serives.rework_delivery_service)

class ReworkDeliveryChallanCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    rework_delivery_challan_instance = graphene.Field(ReworkDeliveryChallanType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Rework DC", create_action="Draft", edit_action="Cancel")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        rework_delivery_challan_instance = None

        with transaction.atomic():
            challan_id = kwargs.get("id")
            if not challan_id:
                errors.append("Challan ID is required.")
                return ReworkDeliveryChallanCancelMutation(success=success, errors=errors)

            # Lock the row for safe cancel
            rework_delivery_challan_instance = (
                ReworkDeliveryChallan.objects.select_for_update()
                .filter(id=challan_id)
                .first()
            )
            if not rework_delivery_challan_instance:
                errors.append("Delivery Challan not found.")
                return ReworkDeliveryChallanCancelMutation(success=success, errors=errors)
            if rework_delivery_challan_instance.goodsinwardnote_set.exists() and rework_delivery_challan_instance.goodsinwardnote_set.first().status.name in ["Draft", "Submit"]:
                gin_number = rework_delivery_challan_instance.goodsinwardnote_set.first().gin_no.linked_model_id
                errors.append(f"Befor cancel rework dc need to cancel GIN{gin_number}.")
                return ReworkDeliveryChallanCancelMutation(success=success, errors=errors)

            # Find canceled status
            status_name = CommanStatus.objects.filter(
                name="Canceled", table="Rework Delivery Challan"
            ).first()
            if not status_name:
                errors.append("Canceled status not configured. Contact admin.")
                return ReworkDeliveryChallanCancelMutation(success=success, errors=errors)

            try:
                # Update challan status
                rework_delivery_challan_instance.status = status_name
                rework_delivery_challan_instance.save()

                purchase_order = rework_delivery_challan_instance.purchase_order_no
                if not purchase_order:
                    errors.append("Purchase order not found.")
                    return ReworkDeliveryChallanCancelMutation(success=success, errors=errors)

                # Recalculate percentage only from remaining submitted challans
                # rework_qty = 0
                # received_qty = 0
                # other_challans = purchase_order.rework_delivery_challan_set.filter(
                #     status__name="Submit"
                # ).exclude(id=rework_delivery_challan_instance.id)

                # for rdc in other_challans:
                #     for item in rdc.rework_delivery_challan_item_details.all():
                #         rework_qty += (item.rework_qty or 0)
                #         received_qty += (item.received_qty or 0)

                 

                success = True

            except Exception as e:
                errors.append(str(e))

        return ReworkDeliveryChallanCancelMutation(
            success=success,
            errors=errors,
            rework_delivery_challan_instance=rework_delivery_challan_instance,
        )

class ReworkDeliveryChallanDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Rework DC", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            delivery_challan = ReworkDeliveryChallan.objects.get(id=id)
            if delivery_challan.status and delivery_challan.status.name == "Canceled":
                if delivery_challan.goodsinwardnote_set.exists():
                    gin_number = delivery_challan.goodsinwardnote_set.first().gin_no.linked_model_id
                    errors.append(f"Befor delete rework dc need to delete GIN {gin_number}.")
                else:
                    with transaction.atomic():
                        delivery_challan.delete()
                    success = True
            else:
                errors.append(f"Before Delete set status cancel.")
        except ReworkDeliveryChallan.DoesNotExist:
            errors.append('Rework Delivery Challan does not exist')
        except ProtectedError as e:
             
            errors.append('Rework Delivery Challan is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return ReworkDeliveryChallanDeleteMutation(success=success, errors=errors)

class GeneratePdfForReworkDeliveryChallan(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        
        try:
            rework_instance = ReworkDeliveryChallan.objects.get(id=id) 
            purchase_instance = rework_instance.purchase_order_no
            qir = rework_instance.qc
            gin = qir.goods_inward_note
            status = rework_instance.status.name
            try:
                rework_data={
                    "reworkNo":str(rework_instance.dc_no.linked_model_id),
                    "reworkDate":str(rework_instance.dc_date.strftime('%d/%m/%Y')),
                    "supplier":purchase_instance.supplier_id.company_name,
                    "supplierAddress": f"{purchase_instance.address.address_line_1},\n"
                                f"{purchase_instance.address.address_line_2},"
                                f"{purchase_instance.address.city} - {purchase_instance.address.pincode},\n"
                                f"{purchase_instance.address.state}, {purchase_instance.address.country}." if purchase_instance.address.address_line_2 and purchase_instance.address.address_line_2 != None else
                                f"{purchase_instance.address.address_line_1},\n"
                                f"{purchase_instance.address.city} - {purchase_instance.address.pincode},\n"
                                f"{purchase_instance.address.state}, {purchase_instance.address.country}.",
                    "gstIn":purchase_instance.gstin,
                    "contactPerson":purchase_instance.contact.contact_person_name,
                    "phoneNumber":purchase_instance.contact.phone_number,
                    "mail":purchase_instance.contact.email,
                    "purchaseOrderNo":str(purchase_instance.purchaseOrder_no.linked_model_id),
                    "ginNo":str(gin.gin_no.linked_model_id),
                    "qirNo":str(qir.qir_no.linked_model_id),
                    "ewayNo":str(rework_instance.e_way_bill) if rework_instance.e_way_bill else "-",
                    "Table Name": ['SI'],
                    "SI_Columns": {
                        "S.No": "No",
                        "Description": "Description",
                        "HSN": "Item's HSN Code (Text)",
                        "Qty": "Quantity", 
                        "UOM":"UOM",
                        "Rate": "Rate", 
                        "%": "%",
                        "Amount": "Amount",
                        "Total": "Total"
                    },
                    "SI_Datas":[
                    {
                        "No": f"{str(index + 1)}",
                        "Description": f"{itemdetail.purchase_item.description}",
                        "Item's HSN Code (Text)": f"{itemdetail.purchase_item.hsn_id.hsn_code}",
                        "Quantity": f"{itemdetail.rework_qty:.0f}",
                        "UOM":itemdetail.purchase_item.uom.name,
                        "Rate": f"{itemdetail.purchase_item.rate:.2f}", 
                        "%": str(int(itemdetail.purchase_item.tax)) if float(itemdetail.purchase_item.tax).is_integer() else str(float(itemdetail.purchase_item.tax)),
                        "Amount": f"{round((itemdetail.purchase_item.tax * itemdetail.amount) / 100, 2)}",
                        "Total": f"{itemdetail.amount:.2f}"
                    }
                    for index, itemdetail in enumerate(rework_instance.rework_delivery_challan_item_details.all())
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
                "AfterTax": format_currency(rework_instance.net_amount, purchase_instance.currency.Currency.currency_symbol,False),
                "gst": format_currency(float(rework_instance.tax_total),  purchase_instance.currency.Currency.currency_symbol, False),
                "totalTax": format_currency(str(float(rework_instance.befor_tax)), purchase_instance.currency.Currency.currency_symbol, False),
                "totalAmoutInWords":num2words(rework_instance.befor_tax, lang='en').title() + " Only",
                "reason":rework_instance.remarks,
                }
                 
            except Exception as e:
                pass

            current_os = platform.system().lower()
            if current_os == 'windows':
                output_docx =  r"{}\static\PDF_OUTPUT\ReworkDC.docx".format(BASE_DIR)
                print("status",status)
                if status == "Draft":
                        doc_path = r"{}\static\PDF_TEMP\RDC_PT_V01 -Draft.docx".format(BASE_DIR)
                else:
                        doc_path = r"{}\static\PDF_TEMP\RDC_PT_V01 -Submit.docx".format(BASE_DIR)
                    
            else:
                output_docx = r"{}/static/PDF_OUTPUT/ReworkDC.docx".format(BASE_DIR)
                if status == "Draft":
                        doc_path = r"{}/static/PDF_TEMP/RDC_PT_V01 -Draft.docx".format(BASE_DIR)
                else:
                        doc_path = r"{}/static/PDF_TEMP/RDC_PT_V01 -Submit.docx".format(BASE_DIR)
                

            doc = Documentpdf(doc_path)
            doc = fill_document_with_mock_data(doc, rework_data)
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
             
            errors.append(f'An exception occurred in PDF creation -{str(e)}')
        
        return GeneratePdfForReworkDeliveryChallan(pdf_data =pdf_base64, success=success, errors=errors)

class PurchaseInvoiceImportInput(graphene.InputObjectType):
    id = graphene.ID()
    purchase_invoice = graphene.Int( )
    bill_of_entry_no = graphene.String( )
    bill_of_entry_date = graphene.Date( )
    port_code = graphene.String( )
    total_duty = graphene.Decimal( )

class PurchaseInvoiceImportLineInput(graphene.InputObjectType):
    id = graphene.ID()
    import_header = graphene.Int( )
    item = graphene.Int( )
    assessable_hsn = graphene.Int( )
    assessable_value = graphene.Decimal()
    igst = graphene.Decimal( )

class PurchaseInvoiceItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    grn_item = graphene.List(graphene.String)
    po_item = graphene.Int()
    po_rate = graphene.Decimal()
    po_qty = graphene.Decimal()
    conversion_factor = graphene.Decimal()
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
    po_amount = graphene.Decimal() 

class PurchaseInvoiceCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        purchase_invoice_date = graphene.Date()
        payment_terms = graphene.String()
        remarks = graphene.String()
        due_date = graphene.Date()  
        credit = graphene.Int()
        credit_date = graphene.Date() 
        place_of_supply = graphene.String()
        item_detail = graphene.List(PurchaseInvoiceItemDetailsInput)
        other_expence_charge = graphene.List(PurchaseOrderOtherExpenceInput)
        purchase_invoice_import_line = graphene.List(PurchaseInvoiceImportLineInput)
        purchase_invoice_import = graphene.List(PurchaseInvoiceImportInput)
        terms_conditions = graphene.Int()
        terms_conditions_text = graphene.String()
        igst = graphene.JSONString()
        sgst = graphene.JSONString()
        cgst = graphene.JSONString()
        cess = graphene.JSONString()
        igst_value = graphene.Decimal()
        sgst_value = graphene.Decimal()
        cgst_value = graphene.Decimal()
        cess_value = graphene.Decimal()
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
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    PurchaseInvoice = graphene.Field(PurchaseInvoiceType)

    @status_mutation_permission("Purchase Invoice")
    def mutate(self, info, **kwargs):
        data = kwargs
        status=kwargs['status']
        result = PurchaseInvoiceService(data, status, info)
        result.process() 
        return PurchaseInvoiceCreateMutation(success= result.success, errors=[",".join(result.errors)],PurchaseInvoice= result.purchase_invoice)

class PurchaseInvoiceCancelMutation(graphene.Mutation):
    """PurchaseInvoice Delete"""
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase Invoice", create_action="Save", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        po_item_value= {}
        with transaction.atomic():
            try:
                status = CommanStatus.objects.filter(
                    name="Canceled", table="Purchase Invoice"
                ).first()
                if not status:
                    return PurchaseInvoiceCancelMutation(success=success, errors=['Canceled status not configured. Contact admin'])
                purchase_invoice = PurchaseInvoice.objects.filter(id=id).first()
                if not purchase_invoice:
                    errors.append("Purchase Invoice not found.")
                    return PurchaseInvoiceCancelMutation(success=success, errors=errors)
              
                po_instance = (
                    purchase_invoice.goodsreceiptnote_set.first().goodsinwardnote_set.first().purchase_order_id
                    if  purchase_invoice.goodsreceiptnote_set.first()
                    and purchase_invoice.goodsreceiptnote_set.first().goodsinwardnote_set.first()
                    else None
                ) 
                if not po_instance:
                    errors.append("Purchase order not found.")
                    return False
                def collect_conflicts(qs, label, number_field):
                    conflicts = qs.exclude(status__name="Canceled").values(
                        status_name=F("status__name"),
                        return_no=F(number_field)
                    )
                    if conflicts:
                        errors.append(
                            f"Before Cancel GRN, need to cancel {label} "
                            + ", ".join([f"{c['status_name']} ({c['return_no']})" for c in conflicts])
                        )

                collect_conflicts(purchase_invoice.purchase_retun, "purchase return", "purchase_return_no__linked_model_id")

                if errors:
                    return PurchaseInvoiceCancelMutation(success=success, errors=errors)
                purchase_total_qty = po_instance.item_details.aggregate(total=Sum("po_qty"))["total"] or 0
                for item in purchase_invoice.item_detail.all():
                    grn_item_details_intance = item.grn_item.all()
                    if not grn_item_details_intance:
                        po_item = item.po_item
                        po_item.invoiced_qty = (po_item.invoiced_qty or 0) - (item.po_qty or 0)
                        po_item.save()
                        po_item_value[po_item.id] = po_item.invoiced_qty
                        continue

                    for grn_item_ in grn_item_details_intance:
                        grn_item_.is_draft_purchase_invoice=False
                        grn_item_.purchase_invoice_qty = 0
                        grn_item_.is_submited_purchase_invoice=False
                        grn_item_.save()
                    
                    po_item = item.grn_item.first().gin.purchase_order_parent
                    if po_item:
                        po_item.invoiced_qty = (po_item.invoiced_qty or 0) - (item.po_qty or 0)
                        po_item.save()
                        po_item_value[po_item.id] = po_item.invoiced_qty
                current_invoiced_qty = sum(po_item_value.values())
                purchase_total_invoiced_qty = po_instance.item_details.exclude(id__in =po_item_value.keys()).aggregate(total=Sum("invoiced_qty"))["total"] or 0
                total_invoiced_qty = current_invoiced_qty+purchase_total_invoiced_qty
                
                po_instance.invoice_percentage = (total_invoiced_qty/purchase_total_qty)*100 if purchase_total_qty else 0
                agl = AccountsGeneralLedger.objects.filter(purchase_invoice= purchase_invoice.id)
                if agl.exists():
                    agl.delete()
                po_instance.save()
    
                purchase_invoice.status = status
                purchase_invoice.save()
                success = True
            except Exception as e:
                transaction.set_rollback(True)
                errors.append(str(e))
        return PurchaseInvoiceCancelMutation(success=success, errors=errors)
    
class PurchaseInvoiceDeleteMutation(graphene.Mutation):
    """PurchaseInvoice Delete"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Purchase Invoice", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            purchase_invoice_instance = PurchaseInvoice.objects.filter(id=id).first()
            if not purchase_invoice_instance:
                errors.append(f"Purchase Invoice not found.")
            
            if purchase_invoice_instance.status.name != "Canceled":
                errors.append(f"Befor Delete need to cancel this Purchase invoice.")
            if len(errors) >0:
                return ReportTempletedDeleteMutation(success=success, errors=errors)

            purchase_invoice_instance.delete()
            success = True
        except ProtectedError as e:
            print("e", e)
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ReportTempletedDeleteMutation(success=success, errors=errors)

class DirectPurchaseOrderOtherExpenceInput(graphene.InputObjectType):
    id = graphene.ID()
    hsn = graphene.Int()
    other_expenses_id = graphene.Int()
    tax = graphene.Decimal()
    amount = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    igst_value = graphene.Decimal()
    sgst_value = graphene.Decimal()
    cgst_value = graphene.Decimal()
    cess_value = graphene.Decimal()
    discount_value = graphene.Decimal()
    after_discount_value = graphene.Decimal()

class DirectPurchaseInvoiceAccountInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    direct_purchase_invoice = graphene.Int()
    description = graphene.String()
    account_master = graphene.Int()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
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

class DirectPurchaseInvoiceItemDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
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

class DirectPurchaseInvoiceCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        direct_purchase_invoice_date = graphene.Date()
        due_date = graphene.Date()
        gst_nature_transaction = graphene.Int()
        currency = graphene.Int(required=True)
        exchange_rate = graphene.Decimal(required=True)
        supplier = graphene.Int(required=True)
        supplier_address = graphene.Int(required=True)
        supplier_contact_person = graphene.Int(required=True)
        supplier_gstin_type = graphene.String(required=True)
        supplier_gstin = graphene.String(required=True)
        supplier_state = graphene.String(required=True)
        supplier_place_of_supply = graphene.String(required=True)
        remarks = graphene.String()
        creadit_period = graphene.Int()
        creadit_date = graphene.Date()
        payment_term = graphene.String() 
        supplier_ref = graphene.String()
        department = graphene.Int()
        item_detail = graphene.List(DirectPurchaseInvoiceItemDetailsInput)
        other_expence_charge = graphene.List(DirectPurchaseOrderOtherExpenceInput)
        accounts = graphene.List(DirectPurchaseInvoiceAccountInput)
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
        taxable_value = graphene.String()
        tax_total = graphene.String()
        round_off = graphene.String()
        round_off_method = graphene.String()
        net_amount = graphene.String()
    
    directPurchaseInvoice = graphene.Field(DirectPurchaseinvoiceType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString() 
    other_expense = graphene.JSONString() 

    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        """Validation Class"""
        service = DirectPurchaseInvoiceService(kwargs, status, info)
        validations_result = service.process()
        

        return DirectPurchaseInvoiceCreateMutations(
            directPurchaseInvoice=validations_result.get("direct_purchase_invoice"),
            success= validations_result.get("success") ,
            errors=validations_result.get("errors"),
            item_details= validations_result.get("item_details") if validations_result.get("item_details") else None,
            other_expense = validations_result.get("other_expence") if validations_result.get("other_expence") else None
              )

class DirectPurchaseInvoiceCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    
    def mutate(self, info, id): 
        success = False
        errors = []
        try:
            status_obj = CommanStatus.objects.filter(name="Canceled", table="Direct Purchase Invoice").first()
            if status_obj:
                direct_purchaseinvoice_instance = DirectPurchaseinvoice.objects.filter(id=id).first()
                if not direct_purchaseinvoice_instance:
                    errors.append("Direct purchase invoice not found.")
                elif direct_purchaseinvoice_instance.status.name in ['Draft', "Submit"]:
                    direct_purchaseinvoice_instance.status = status_obj
                    agl = AccountsGeneralLedger.objects.filter(direct_purchase_invoice= direct_purchaseinvoice_instance.id)
                    if agl.exists():
                        agl.delete()
                    direct_purchaseinvoice_instance.save()
                else:
                    errors.append("Direct purchase invoice is already Canceled.")
                success = True
            else:
                errors.append("Ask Admin to add status Canceled")
        except Exception as e:
            errors.append(f"An exception occurred-{str(e)}")

        return DirectPurchaseInvoiceCancelMutation(success=success, errors=errors)

class DirectPurchaseInvoiceDeleteMutation(graphene.Mutation):
    """Direct PurchaseInvoice Delete"""
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []

        try:
            direct_purchase_invoice_instance = DirectPurchaseinvoice.objects.filter(id=id).first()
            if not direct_purchase_invoice_instance:
                errors.append(f"Direct Purchase Invoice not found.")
            
            if direct_purchase_invoice_instance.status.name != "Canceled":
                errors.append(f"Befor Delete need to cancel this Direct Purchase Invoice.")
            if len(errors) >0:
                return DirectPurchaseInvoiceDeleteMutation(success=success, errors=errors)

            direct_purchase_invoice_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return DirectPurchaseInvoiceDeleteMutation(success=success, errors=errors)

class DebitNoteOtherIncomeChargeInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    debit_note = graphene.Int()
    other_income_charges = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()

class DebitNoteAccountInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    debit_note = graphene.Int()
    description = graphene.String()
    account_master = graphene.Int()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    sgst = graphene.Decimal()
    cgst = graphene.Decimal()
    igst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()

class DebitNoteItemDetailInput(graphene.InputObjectType):
    id = graphene.ID()
    index = graphene.Int()
    debit_note = graphene.ID()
    item_master = graphene.Int()
    description = graphene.String()
    purchase_return_item = graphene.Int()
    qty = graphene.Decimal()
    uom = graphene.Int()
    rate = graphene.Decimal()
    po_qty = graphene.Decimal()
    po_uom = graphene.Int()
    po_rate = graphene.Decimal()
    conversion_factor = graphene.Decimal()
    hsn = graphene.Int()
    tax = graphene.Decimal()
    igst = graphene.Decimal()
    cgst = graphene.Decimal()
    sgst = graphene.Decimal()
    cess = graphene.Decimal()
    tds_percentage = graphene.Decimal()
    tcs_percentage = graphene.Decimal()
    amount = graphene.Decimal()
    po_amount = graphene.Decimal()

class DebitNoteCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        debit_note_date = graphene.Date()
        note_no = graphene.String()
        note_date = graphene.Date()
        return_invoice = graphene.Int()
        supplier = graphene.Int()
        supplier_ref = graphene.String()
        remarks = graphene.String()
        purchase_order_no = graphene.Int()
        department = graphene.Int()
        gstin_type = graphene.String()
        gstin = graphene.String()
        gst_nature_transaction = graphene.Int()
        gst_nature_type = graphene.String()
        place_of_supply = graphene.String()
        e_way_bill = graphene.String()
        e_way_bill_date = graphene.Date()
        contact = graphene.Int()
        address = graphene.Int()
        currency = graphene.Int(required=True)
        exchange_rate = graphene.Decimal(required=True)
        item_detail = graphene.List(DebitNoteItemDetailInput)
        other_income_charge = graphene.List(DebitNoteOtherIncomeChargeInput)
        accounts = graphene.List(DebitNoteAccountInput)
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
    
    debit_note = graphene.Field(DebitNoteType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    item_details = graphene.JSONString() 
    other_income_charges = graphene.JSONString() 
    
    @mutation_permission("Debit Note", create_action="Submit", edit_action="Edit")
    def mutate(self, info, **kwargs):
        status = kwargs.get('status')
        """Validation Class"""
        service = DebitNoteSerivce(kwargs, status, info)
        validations_result = service.process()

        return DebitNoteCreateMutations(
            debit_note=validations_result.get("debit_note"),
            success= validations_result.get("success") ,
            errors=validations_result.get("errors"),
            item_details=  validations_result.get("item_detail"),
            other_income_charges= validations_result.get("other_income_charges"))

class DebitNoteCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Debit Note", create_action="Submit", edit_action="Cancel")
    def mutate(self, info, id): 
        success = False
        errors = []
        try:
            status_obj = CommanStatus.objects.filter(name="Canceled", table="Debit Note").first()
            if status_obj:
                direct_purchaseinvoice_instance = DebitNote.objects.filter(id=id).first()
                if not direct_purchaseinvoice_instance:
                    errors.append("Debit Note not found.")
                elif direct_purchaseinvoice_instance.status.name in ['Draft', "Submit"]:
                    direct_purchaseinvoice_instance.status = status_obj
                    direct_purchaseinvoice_instance.save()
                else:
                    errors.append("Debit Note is already Canceled.")
                success = True
            else:
                errors.append("Ask Admin to add status Canceled")
        except Exception as e:
            errors.append(f"An exception occurred-{str(e)}")

        return DebitNoteCancelMutation(success=success, errors=errors)

class DebitNoteDeleteMutation(graphene.Mutation):
    """Debit Note Delete"""
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Debit Note", create_action="Submit", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []

        try:
            debit_note_instance = DebitNote.objects.filter(id=id).first()
            if not debit_note_instance:
                errors.append(f"Debit Note not found.")
            
            if debit_note_instance.status.name != "Canceled":
                errors.append(f"Befor Delete need to cancel this Debit Note.")
            if len(errors) >0:
                return DebitNoteDeleteMutation(success=success, errors=errors)

            debit_note_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return DebitNoteDeleteMutation(success=success, errors=errors)


def company_bank_info():
    cache_key = "company_bank_detail"
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data
    company_bank_info = BankDetails.objects.filter(is_active=True).first()
    if not company_bank_info:
        return None
    cache.set(cache_key, company_bank_info, timeout=86400)# cache for 14 hours
    return company_bank_info


class GeneratePdfForDebitNote(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
    pdf_data = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            debit_note_instance = DebitNote.objects.filter(id=id).first()
            bank_data = company_bank_info()
             
            if not debit_note_instance:
                return GraphQLError("Debit note not found.")
           
            item_details = [{
                "No": str(itemdetail.index or ""),
                "Description": str(itemdetail.description or ""),
                "Item's HSN Code (Text)": str(getattr(itemdetail.hsn, "hsn_code", "") or ""),
                "Quantity": f"{(itemdetail.po_qty or 0):.0f} {getattr(itemdetail.po_uom, 'name', '')}",
                "Rate": f"{(itemdetail.rate or 0):.2f}",
                "%": str(int(itemdetail.tax or 0)) if float(itemdetail.tax or 0).is_integer() else str(float(itemdetail.tax or 0)),
                "Amount": f"{round(((itemdetail.tax or 0) * (itemdetail.po_amount or 0)) / 100, 2)}",
                "Total": f"{(itemdetail.po_amount or 0):.2f}"
            } for index, itemdetail in enumerate(debit_note_instance.debitnoteitemdetail_set.all())]
            
            account = [
                {
                        "No":str(account.index or ''),
                        "Description": str(account.description or ""),
                        "Item's HSN Code (Text)": str(getattr(account.hsn, "hsn_code", "") or ""),
                        "Quantity":  "-",
                        "Rate": f"{account.amount:.2f}",
                        "%": str(int(account.tax)) if float(account.tax).is_integer() else str(float(account.tax)),
                        "Amount": f"{round((account.tax * account.amount) / 100, 2)}",
                        "Total": f"{account.amount:.2f}"
                    }
                    for index, account in enumerate(debit_note_instance.debitnoteaccount_set.all())
            ] 
            combo_list = item_details + account
           
            item_detail_and_account_list = sorted(combo_list, key=lambda x: int(x["No"]))
          
            try:
                debit_note_data = {
                 "debitNoteNo": debit_note_instance.debit_note_no.linked_model_id,
                 "debitNoteDate":str(debit_note_instance.debit_note_date.strftime('%d/%m/%Y')),
                 "customerName":debit_note_instance.supplier.company_name,
                 "customerAddress": f"{debit_note_instance.address.address_line_1},\n"
                                f"{debit_note_instance.address.address_line_2},"
                                f"{debit_note_instance.address.city} - {debit_note_instance.address.pincode},\n"
                                f"{debit_note_instance.address.state}, {debit_note_instance.address.country}." if debit_note_instance.address.address_line_2 and debit_note_instance.address.address_line_2 != None else
                                f"{debit_note_instance.address.address_line_1},\n"
                                f"{debit_note_instance.address.city} - {debit_note_instance.address.pincode},\n"
                                f"{debit_note_instance.address.state}, {debit_note_instance.address.country}.",
                "gstIn":debit_note_instance.gstin,
                "contactPerson":debit_note_instance.contact.contact_person_name,
                "phoneNumber":debit_note_instance.contact.phone_number,
                "mail":debit_note_instance.contact.email,
                "poNo":debit_note_instance.purchase_order_no.purchaseOrder_no.linked_model_id if debit_note_instance.purchase_order_no and  debit_note_instance.purchase_order_no.purchaseOrder_no.linked_model_id else "-",
                "invoiceNo":", ".join(po_invoice.purchase_invoice_no.linked_model_id for po_invoice in debit_note_instance.return_invoice.purchaseinvoice_set.all() ) if debit_note_instance.return_invoice else "",
                "invoiceDate": ", ".join(po_invoice.purchase_invoice_date.strftime("%d-%m-%Y") for po_invoice in debit_note_instance.return_invoice.purchaseinvoice_set.all()) if debit_note_instance.return_invoice else "",
                "supplierNo":debit_note_instance.note_no if debit_note_instance.note_no else "-",
                "supplierDate":str(debit_note_instance.note_date.strftime('%d/%m/%Y')) if debit_note_instance.note_date else "-",
                "Table Name": ['SI',"OtherIncome"],
                "Other Table": ["OtherIncome"],
                "OtherIncome_Datas": [
                         {
                            "account": other_charges.other_income_charges.name, 
                            "Total": format_currency(other_charges.amount, debit_note_instance.currency.Currency.currency_symbol)  
                        }
                        for other_charges in debit_note_instance.debitnoteotherincomecharge_set.all()
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
                        "Rate": "Rate",
                        "%": "%",
                        "Amount": "Amount",
                        "Total": "Total"
                },
                "SI_Datas":item_detail_and_account_list,
                "totalTax":format_currency(str(float(debit_note_instance.taxable_value or 0)), debit_note_instance.currency.Currency.currency_symbol, False),
                "gst":format_currency(str(float(debit_note_instance.tax_total or 0)), debit_note_instance.currency.Currency.currency_symbol, False),
                "AfterTax":format_currency(debit_note_instance.net_amount, debit_note_instance.currency.Currency.currency_symbol),
                "totalAmoutInWords":num2words(debit_note_instance.net_amount, lang='en').title() + " Only",
                "bankName":bank_data.bank_name if bank_data else "",
                "ifsc":bank_data.ifsc_code if bank_data else "",
                "accountNo":bank_data.account_number if bank_data else "",
                "branch":bank_data.branch_name if bank_data else ""
                } 
                current_os = platform.system().lower()
                if current_os == 'windows':
                    output_docx =  r"{}\static\PDF_OUTPUT\QIR.docx".format(BASE_DIR)
                        
                    if status == "Pending":
                            doc_path = r"{}\static\PDF_TEMP\DN_V01-Draft.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}\static\PDF_TEMP\DN_V01-Submit.docx".format(BASE_DIR)
                    
                else:
                    output_docx = r"{}/static/PDF_OUTPUT/QIR.docx".format(BASE_DIR)
                    if status == "Pending":
                            doc_path = r"{}/static/PDF_TEMP/DN_V01-Draft.docx".format(BASE_DIR)
                    else:
                        doc_path = r"{}/static/PDF_TEMP/DN_V01-Submit.docx".format(BASE_DIR)

                doc = Documentpdf(doc_path)
                doc = fill_document_with_mock_data(doc, debit_note_data)
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
            except Exception as e : 
                print("ee----",e)
                errors.append(f'An exception occurred in PDF creation -{str(e)}')

        except Exception as e : 
            print("e----",e)
            errors.append(f'An exception occurred in PDF creation -{str(e)}')

        return GeneratePdfForDebitNote(pdf_data =pdf_base64, success=success, errors=errors)


class stockReducecheck(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            stockReduceFuntions(id)
        except Exception as e:
            pass

class EditListViewCreateMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        view_name = graphene.String()
        visible_to = graphene.String()
        visible_to_user = graphene.List(graphene.Int)
        default_sort_column = graphene.String()
        default_sort_order = graphene.String()
        filiter_conditions = graphene.JSONString()
        coloumn_to_display = graphene.JSONString()
        is_default = graphene.Boolean()
        table = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    edit_list_view_instance = graphene.Field(EditListViewType)

    @mutation_permission("FilterView", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        edit_list_view_instance = None
        success = False
        errors = []
        if "visible_to_user" in kwargs and kwargs['visible_to_user'] is None:
            kwargs['visible_to_user'] = []
        if 'id' in kwargs and kwargs['id']:
            edit_list_view_instance = EditListView.objects.get(id=kwargs['id'])
            if not edit_list_view_instance:
                errors.append("EditListView Not Found.")
            else:
                if edit_list_view_instance.is_default is False:
                    if kwargs['is_default']:
                        kwargs['default_update_date_time'] = datetime.now()
                serializer = EditListViewSerializer(edit_list_view_instance, data=kwargs, partial=True)
        else:
            if kwargs['is_default']:
                kwargs['default_update_date_time'] = datetime.now()
            serializer = EditListViewSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            edit_list_view_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return EditListViewCreateMutations(success=success, errors=errors,
                                           edit_list_view_instance=edit_list_view_instance)

class EditListViewDeleteMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("FilterView", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            EditListView_instance = EditListView.objects.get(id=id)
            EditListView_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except EditListView.DoesNotExist:
            errors.append('EditListView does not exist.')
        except ProtectedError:
            errors.append('EditListView is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return EditListViewDeleteMutations(success=success, errors=errors)

class importSupplierMutations(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
 
    def mutate(self, info, id):
        # supplierDataImport.bulk_update_supplier_from_csv(r'C:\Users\Jegathish.E.STDOMAIN\Downloads\Suppliers_1.csv')
        return EditListViewDeleteMutations(success=True)

 

class Mutation(graphene.ObjectType):
    company_master_create_mutation = CompanyMasterCreateMutation.Field()

    report_templeted_create_mutation = ReportTempletedCreateMutation.Field()
    report_templeted_delete_mutation = ReportTempletedDeleteMutation.Field()

    user_group_create_mutation = UserGroupCreateMutation.Field()
    user_group_delete_mutation = UserGroupDeleteMutation.Field()

    stockReducecheck = stockReducecheck.Field()
    item_master_create_mutation = ItemMasterCreateMutation.Field()
    item_master_delete_mutation = ItemMasterDeleteMutation.Field()

    item_groups_name_create_mutation = ItemGroupsNameCreateMutation.Field()
    item_group_name_delete_mutation = ItemGroupNameDeleteMutation.Field()

    uom_create_mutation = UomCreateMutation.Field()
    uom_delete_mutation = UomDeleteMutation.Field()

    contact_delete_mutation = ContactDeleteMutation.Field()

    hsn_create_mutation = HsnCreateMutation.Field()
    hsn_delete_mutation = HsnDeleteMutation.Field()
    hsn_effective_date_create_mutation = HsnEffectiveDateCreateMutation.Field()

    alternate_unit_create_mutation = AlternateUnitCreateMutation.Field()
    alternate_unit_delete_mutation = AlternateUnitDeleteMutation.Field()

    accounts_master_create_mutation = AccountsMasterCreateMutation.Field()
    accounts_master_delete_mutation = AccountsMasterDeleteMutation.Field()

    gst_nature_transaction_create_mutation = GSTNatureTransactioncreateMutation.Field()
    gst_nature_transaction_delete_mutation = GSTNatureTransactionDeleteMutation.Field()

    accounts_group_create_mutation = AccountsGroupCreateMutation.Field()
    accounts_group_delete_mutation = AccountsGroupDeleteMutation.Field()

    store_create_mutations = StoreCreateMutation.Field()
    store_delete_mutations = StoreDeleteMutation.Field()

    item_combo_create_mutatio = ItemComboCreateMutation.Field()
    item_combo_delete_mutation = ItemComboDeleteMutation.Field()

    finished_goods_create_mutation = FinishedGoodsCreateMutation.Field()
    finished_goods_delete_mutation = FinishedGoodsDeleteMutation.Field()

    raw_material_create_mutation = RawMaterialCreateMutation.Field()
    raw_material_delete_mutation = RawMaterialDeleteMutation.Field()

    scrap_create_mutation = ScrapCreateMutation.Field()
    scrap_delete_mutation = ScrapDeleteMutation.Field()

    routing_create_mutation = RoutingCreateMutation.Field()
    routing_delete_mutation = RoutingDeleteMutation.Field()

    # duplicate item
    bom_duplicate_item_mutation = BomDuplicateItemMutation.Field()
    bom_duplicate_fg_item_mutation = BomDuplicateFgItemMutation.Field()
    bom_duplicate_rm_item_mutation = BomDuplicateRmItemMutation.Field()
    bom_duplicate_scrap_item_mutation = BomDuplicateScrapItemMutation.Field()
    bom_duplicate_routing_item_mutation = BomDuplicateRoutingItemMutation.Field()
    bom_duplicate_child_bom_mutation = BomDuplicateChildBomMutation.Field()

    bom_create_mutation = BomCreateMutation.Field()
    bom_delete_mutation = BomDeleteMutation.Field()

    display_group_create_mutation = ItemDisplayCreateMutation.Field()
    # display_group_delete_mutation = ItemDisplayDeleteMutation.Field()

    stock_serial_history_create_mutation = StockSerialHistoryCreateMutation.Field()
    stock_serial_history_delete_mutation = StockSerialHistoryDeleteMutation.Field()

    item_stock_create_mutation = ItemStockCreateMutation.Field()
    item_stock_delete_mutation = ItemStockDeleteMutation.Field()

    serial_number_create_mutation = SerialNumberCreateMutation.Field()
    serial_number_delete_mutation = SerialNumberDeleteMutation.Field()
    # item_stock_validation_mutations = ItemStockvalidationMutations.Field()

    serial_number_string_delete_mutation = SerialNumberStringDeleteMutation.Field()

    stock_addtions_create_mutations = StockAddtionsCreateMutations.Field()

    stock_deletions_create_mutations = StockDeletionscreateMutations.Field()
    
    validat_and_serial_number_create_mutation = ValidatAndSerialNumberCreateMutation.Field()
    serial_number_auto_create_mutation = SerialNumberAutoCreateMutation.Field()

    batch_number_create_mutation = BatchNumberCreateMutation.Field()
    batch_number_delete_mutation = BatchNumberDeleteMutation.Field()

    inventory_approval_create_mutation = InventoryApprovalCreateMutation.Field()
    inventory_approval_delete_mutation = InventoryApprovalDeleteMutation.Field()

    inventory_handler_create_mutation = InventoryHandlerCreateMutation.Field()
    inventory_handler_delete_mutation = InventoryHandlerDeleteMutation.Field()

    currency_exchange_create_mutation = CurrencyexchangeCreateMutation.Field()
    currency_exchange_delete_mutation = CurrencyexchangeDeleteMutation.Field()

    currency_master_create_mutation = CurrencyMasterCreateMutation.Field()
    currency_master_delete_mutation = CurrencyMasterDeleteMutation.Field()

    numbering_series_create_mutation = NumberingSeriesCreateMutation.Field()
    numbering_series_delete_mutation = NumberingSeriesDeleteMutation.Field()

    sales_order_pos_create_mutation = SalesorderPosCreateMutation.Field()
    sales_order_pos_delete_mutation = SalesorderPosDeleteMutation.Field()

    check_stock = CheckStock.Field()
    sales_order_cancle_mutation = SalesOrderCancleMutation.Field()

    sales_order_create_mutation = SalesorderCreateMutation.Field()
    sales_order_delete_mutation = SalesorderDeleteMutation.Field()
    sales_order_submit_mutation = SalesOrderSubmitMutation.Field()

    payment_Mode_create_Mutation = paymentModeCreateMutation.Field()
    payment_mode_delete_mutation = paymentModeDeleteMutation.Field()

    company_address_create_mutation = CompanyAddressCreateMutation.Field()
    company_address_delete_mutation = CompanyAddressDeleteMutation.Field()

    contact_validation = ContactValidation.Field()

    customer_group_create_mutation = CustomerGroupCreateMutation.Field()
    customer_group_delete_mutation = CustomerGroupDeleteMutation.Field()

    supplier_group_create_mutation = SupplierGroupCreateMutation.Field()
    supplier_group_delete_mutation = SupplierGroupDeleteMutation.Field()

    supplier_form_create_mutation = SupplierFormCreateMutation.Field()
    supplier_form_delete_mutation = SupplierFormDeleteMutation.Field()

    supplier_form_gst_effective_date_create_mutation = SupplierFormGstEffectiveDateCreateMutation.Field()

    bom_routing_create_mutation = BomRoutingCreateMutation.Field()
    bom_routing_delete_mutation = BomRoutingDeleteMutation.Field()

    work_center_create_mutation = WorkCenterCreateMutation.Field()
    work_center_delete_mutation = WorkCenterDeleteMutation.Field()

    stock_history_create_mutation = StockHistoryCreateMutation.Field()
    stock_history_delete_mutation = StockHistoryDeleteMutation.Field()

    raw_material_bom_link_create_mutation = RawMaterialBomLinkCreateMutation.Field()
    raw_material_bom_link_delete_mutation = RawMaterialBomLinkDeleteMutation.Field()

    image_create_mutation = ImageCreateMutation.Field()
    image_delete_mutation = ImageDeleteMutation.Field()

    document_create_mutation = DocumentCreateMutation.Field()
    document_delete_mutation = DocumentDeleteMutation.Field()

    department_create_mutation = DepartmentCreateMutation.Field()
    department_delete_mutation = DepartmentDeleteMutation.Field()

    other_expenses_create_mutation = OtherExpensesCreateMutation.Field()
    other_expenses_delete_mutation = OtherExpensesDeleteMutation.Field()

    terms_conditions_create_mutation = TermsConditionsCreateMutation.Field()
    terms_conditions_delete_mutation = TermsConditionsDeleteMutation.Field()

    purchase_order_create_mutation = PurchaseOrderCreateMutation.Field()
    purchase_order_delete_mutation = PurchaseOrderDeleteMutation.Field()
    purchase_order_cancle_mutation = PurchaseOrderCancleMutation.Field()
    generate_pdf_for_purchase_order = GeneratePdfForPurchaseOrder.Field()

    goods_inward_note_create_mutation = GoodsInwardNoteCreateMutation.Field()
    goods_inward_note_cancel_mutation = GoodsInwardNotecancelMutation.Field()
    goods_inward_note_delete_mutation = GoodsInwardNoteDeleteMutation.Field()

    qir_create_mutation = QirCreateMutation.Field()
    qir_cancle_mutation = QirCancleMutation.Field()
    qir_delete_mutation = QirDeleteMutation.Field()
    generate_pdf_for_qir = GeneratePdfForQir.Field()

    goods_receipt_note_create_mutation = GoodsReceiptNoteCreateMutation.Field()
    goods_receipt_note_cancle_mutation = GoodsReceiptNoteCancelMutation.Field()
    goods_receipt_note_delete_mutation = GoodsReceiptNoteDeleteMutation.Field()
    generate_pdf_for_goods_receipt_note = GeneratePdfForGoodsReceiptNote.Field()

    get_batch_number_id = GetBatchNumberId.Field()

    rework_delivery_challan_create_mutation = ReworkDeliveryChallanCreateMutation.Field()
    rework_delivery_challan_delete_mutation = ReworkDeliveryChallanDeleteMutation.Field()
    rework_delivery_challan_cancel_mutation = ReworkDeliveryChallanCancelMutation.Field()
    generate_pdf_for_rework_delivery_challan = GeneratePdfForReworkDeliveryChallan.Field()

    purchase_invoice_create_mutation = PurchaseInvoiceCreateMutation.Field()
    purchase_invoice_cancel_mutation = PurchaseInvoiceCancelMutation.Field()
    purchase_invoice_delete_mutation = PurchaseInvoiceDeleteMutation.Field()
 
    purchase_return_challan_create_mutation = PurchaseReturnChallanCreateMutation.Field()
    purchase_return_challan_cancle_mutation = PurchaseReturnChallanCancleMutation.Field()
    purchase_return_challan_delete_mutation = PurchaseReturnChallanDeleteMutation.Field()
    generate_pdf_for_purchase_return = GeneratePdfForPurchaseReturn.Field()
    
    direct_purchase_invoice_create_mutation = DirectPurchaseInvoiceCreateMutations.Field()
    direct_purchase_invoice_cancel_mutation = DirectPurchaseInvoiceCancelMutation.Field()
    direct_purchase_invoice_delete_mutation = DirectPurchaseInvoiceDeleteMutation.Field()

    debit_note_create_mutations = DebitNoteCreateMutations.Field()
    debit_note_cancel_mutation = DebitNoteCancelMutation.Field()
    debit_note_delete_mutation = DebitNoteDeleteMutation.Field()
    generate_pdf_for_debit_note = GeneratePdfForDebitNote.Field()

    edit_list_view_create_mutations = EditListViewCreateMutations.Field()
    edit_list_view_delete_mutations = EditListViewDeleteMutations.Field()

    import_supplier_mutations = importSupplierMutations.Field()