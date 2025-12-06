import graphene

from itemmaster.schema import *
from itemmaster2.models import *
from EnquriFromapi.models import *
from itemmaster.schema import *
from itemmaster2.Utils.ItemMasterComman import *
from django.apps import apps

CallLog_type = create_graphene_type(CallLog)
Meeting_type = create_graphene_type(Meeting)
Notes_type = create_graphene_type(Notes)
EmailRecord_type = create_graphene_type(EmailRecord)


class CallLogConnection(graphene.ObjectType):
    items = graphene.List(CallLog_type)
    page_info = graphene.Field(PageInfoType)


class CallLogWithPagination(graphene.ObjectType):
    calls = graphene.List(CallLog_type)
    page_info = graphene.Field(PageInfoType)


class MeetingWithPagination(graphene.ObjectType):
    meeting = graphene.List(Meeting_type)
    page_info = graphene.Field(PageInfoType)


class ActivityUnion(graphene.Union):
    class Meta:
        types = (CallLog_type, Meeting_type, Notes_type)

    @classmethod
    def resolve_type(cls, instance, info):
        if isinstance(instance, CallLog):
            return CallLog_type
        if isinstance(instance, Meeting):
            return Meeting_type
        if isinstance(instance, Notes):
            return Notes_type
        return None


class BulkMailContactType(graphene.ObjectType):
    id = graphene.ID()
    email = graphene.String()

class BulkWhatsAppContactType(graphene.ObjectType):
    id = graphene.ID()
    ph_num = graphene.String()
    name = graphene.String()


class Leads_type(DjangoObjectType):
    # Adding the fields for the counts
    sales_order_count = graphene.Int()  # For sales order count
    quotation_count = graphene.Int()  # For quotation count

    class Meta:
        model = Leads
        fields = "__all__"

    # Resolving the counts for sales orders and quotations
    def resolve_sales_order_count(self, info):
        # Count related SalesOrder instances for this Lead
        return self.sales_order_id.count()  # Adjust if the related name is different

    def resolve_quotation_count(self, info):
        # Count related Quotation instances for this Lead
        return self.quotation_ids.count()  # Adjust if the related name is different


class LeadsConnection(graphene.ObjectType):
    items = graphene.List(Leads_type)
    page_info = graphene.Field(PageInfoType)

class SalesInitialFetch(graphene.ObjectType):
    items = graphene.JSONString()


OtherIncomeCharges_type = create_graphene_type(OtherIncomeCharges)


class OtherIncomeChargesConnection(graphene.ObjectType):
    items = graphene.List(OtherIncomeCharges_type)
    page_info = graphene.Field(PageInfoType)

QuotationsItemDetails_type = create_graphene_type(QuotationsItemDetails)
QuotationsOtherIncomeCharges_type = create_graphene_type(QuotationsOtherIncomeCharges)

class QuotationsItemDetailsConnection(graphene.ObjectType):
    items = graphene.List(QuotationsItemDetails_type)

class Discount_value(graphene.ObjectType):
    items = graphene.List(QuotationsItemDetails_type)
    quotationsOtherIncomeCharges = graphene.List(QuotationsOtherIncomeCharges_type)

Quotations_type = create_graphene_type(Quotations)
QuotationsItemComboItemDetails_type = create_graphene_type(QuotationsItemComboItemDetails)


class QuotationsConnection(graphene.ObjectType):
    items = graphene.List(Quotations_type)
    page_info = graphene.Field(PageInfoType)
    version = graphene.Field(versionListType)

SalesOrder_2_ItemComboItemDetails_type = create_graphene_type(SalesOrder_2_temComboItemDetails)
SalesOrder_2_otherIncomeCharges_type = create_graphene_type((SalesOrder_2_otherIncomeCharges))
SalesOrder_2_ItemDetails_type = create_graphene_type(SalesOrder_2_ItemDetails)
SalesOrder_2_type = create_graphene_type(SalesOrder_2)

class SalesOrder_2Connection(graphene.ObjectType):
    items = graphene.List(SalesOrder_2_type)
    page_info = graphene.Field(PageInfoType)
    version = graphene.Field(versionListType)

class LeadChildType(graphene.ObjectType):
    id = graphene.ID()
    label = graphene.String()
    Number = graphene.String()
    isShow = graphene.Boolean()
    date = graphene.Date()
    status = graphene.String()
    children = graphene.List(graphene.NonNull(lambda: LeadChildType))

class LeadTimeLine(graphene.ObjectType):
    id = graphene.ID()
    label = graphene.String()
    Number = graphene.String()
    isShow = graphene.Boolean()
    date = graphene.Date()
    status = graphene.String()
    children = graphene.List(graphene.NonNull(LeadChildType))  # This ensures children are of LeadChildType

class LeadTimeLine_new(graphene.ObjectType):
    item = graphene.JSONString() 

"""activity"""
ActivityType_type = create_graphene_type(ActivityType)
Activity_Type = create_graphene_type(Activites)
EmailResource_Type = create_graphene_type(EmailResource)
EmailTemplete_Type = create_graphene_type(EmailTemplete)

"""Target"""
TargetMonth_type = create_graphene_type(TargetMonth)
TargetSalesperson_type = create_graphene_type(TargetSalesperson)
Target_type = create_graphene_type(Target)


class TargeModulesType(graphene.ObjectType):
    model_list = graphene.JSONString()


class TargetAchievementType(graphene.ObjectType):
    model_list = graphene.JSONString()

""" deliver Challen"""
SalesOrder_2_RetunBatch__type = create_graphene_type(SalesOrder_2_RetunBatch)
salesOrder_2_DeliveryChallan_type = create_graphene_type(SalesOrder_2_DeliveryChallan)
salesOrder_2_DeliveryChallanItemDetails_type = create_graphene_type(SalesOrder_2_DeliveryChallanItemDetails)
salesOrder_2_DeliverChallanItemCombo = create_graphene_type(SalesOrder_2_DeliverChallanItemCombo)

"""Sales invoice"""
SalesInvoice_type = create_graphene_type(SalesInvoice)
SalesInvoiceItemDetail_type = create_graphene_type(SalesInvoiceItemDetail)
SalesInvoiceItemcombo_type =  create_graphene_type(SalesInvoiceItemCombo)

class combineMultiDcToSalesInvoice_Type(graphene.ObjectType):
    sales_invoice = graphene.JSONString()



"""Direct Sales Invoice"""
DirectSalesInvoice_type = create_graphene_type(DirectSalesInvoice)
DirectSalesInvoiceItemDetail_type = create_graphene_type(DirectSalesInvoiceItemDetails)

"""sales return"""
salesReturn_type = create_graphene_type(SalesReturn)
SalesReturnItemDetails_type = create_graphene_type(SalesReturnItemDetails)
SalesRetunItemCombo_type = create_graphene_type(SalesReturnItemCombo)
# SalesReturnBatch_type = create_graphene_type(SalesReturnBatch)

# "History"
ItemMasterHistory_Type = create_graphene_type(ItemMasterHistory)

ReceiptVoucher_Type = create_graphene_type(ReceiptVoucher)
ReceiptVoucherAgainstInvoice_Type = create_graphene_type(ReceiptVoucherAgainstInvoice)
ReceiptVoucherAdvanceDetails_Type = create_graphene_type(ReceiptVoucherAdvanceDetails)
ReceiptVoucherLine_Type = create_graphene_type(ReceiptVoucherLine)
"""CreditNote"""
credit_other_income = create_graphene_type(CreditNoteOtherIncomeCharges)
credit_item_combo = create_graphene_type(CreditNoteComboItemDetails)
credit_item_detail = create_graphene_type(CreditNoteItemDetails)
credit_note_type = create_graphene_type(CreditNote)


class Query(ObjectType):
    all_CallLog = graphene.Field(CallLogConnection, page=graphene.Int(), page_size=graphene.Int(),
                                 order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                 id_list=graphene.List(graphene.Int))
    id_CallLog = graphene.Field(CallLogWithPagination, id=graphene.Int(), isEnquiry=graphene.Boolean(),
                                page=graphene.Int(), page_size=graphene.Int())
    id_meeting = graphene.Field(MeetingWithPagination, id=graphene.Int(), isEnquiry=graphene.Boolean(),
                                page=graphene.Int(), page_size=graphene.Int())
    activities = graphene.List(ActivityUnion, id=graphene.Int(), isEnquiry=graphene.Boolean(),
                               app_name=graphene.String(), modal_name=graphene.String(),
                               page=graphene.Int(), page_size=graphene.Int())
    all_lead = graphene.Field(LeadsConnection, page=graphene.Int(), page_size=graphene.Int(),
                              order_by=graphene.String(),
                              descending=graphene.Boolean(), id=graphene.Int(), lead_no=graphene.String(),
                              lead_name=graphene.String(), customer=graphene.String(), requirement=graphene.String(),
                              lead_currency=graphene.String(), lead_value=graphene.Int(),
                              expected_closing_date=graphene.String(),
                              priority=graphene.Int(), sales_person=graphene.String(), created_by=graphene.String(),
                              user_id=graphene.Int())
    other_income_charges = graphene.Field(OtherIncomeChargesConnection, page=graphene.Int(), page_size=graphene.Int(),
                            order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                            name=graphene.String(), account=graphene.String(), HSN=graphene.String(),
                            active=graphene.Boolean())
    quotations_item_details = graphene.Field(QuotationsItemDetails_type, id=graphene.Int(required=True))
    quotations_item_combo_item_details = List(QuotationsItemComboItemDetails_type, id_list=graphene.List(graphene.Int))
    all_quotations = graphene.Field(QuotationsConnection, page=graphene.Int(), page_size=graphene.Int(),
                                    order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                    quotation_no=graphene.String(), customer_id=graphene.String(),
                                    city=graphene.String(),
                                    state=graphene.String(), net_amount=graphene.String(), created_by=graphene.String(),
                                    status=graphene.String(), active=graphene.Boolean(), CreatedAt=graphene.String(), )

    quotations_overall_discount_percentage = graphene.Field(Discount_value,
                                                            item_id_list=graphene.List(graphene.Int),
                                                            other_income_charge_id_list=graphene.List(graphene.Int),
                                                            percentage=graphene.String())
    quotations_overall_discount_value = graphene.Field(Discount_value,
                                                       id_list=graphene.List(graphene.Int),
                                                       other_income_charge_id_list=graphene.List(graphene.Int),
                                                       totalToSubtract=graphene.Decimal(),
                                                       totalValue=graphene.Decimal())
    quotations_final_total_discount = graphene.Field(Discount_value,
                                                     id_list=graphene.List(graphene.Int),
                                                     other_income_charge_id_list=graphene.List(graphene.Int),
                                                     final_total=graphene.Decimal(),
                                                     TotalWithTaxValue=graphene.Decimal())
    quotations_item_clear_discount = graphene.Field(Discount_value,
                                                    id_list=graphene.List(graphene.Int), other_income_charge_id_list=
                                                    graphene.List(graphene.Int),
                                                    )
    salesOrder_2_ItemDetails_all = graphene.Field(SalesOrder_2_ItemDetails_type, id_list=graphene.List(graphene.Int))
    all_SalesOrder_2 = graphene.Field(SalesOrder_2Connection, page=graphene.Int(), page_size=graphene.Int(),
        eorder_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
        status=graphene.String(), active=graphene.Boolean(),
        sales_order_no=graphene.String(),
        customer_po_no=graphene.String(), department=graphene.String(),
        buyer=graphene.String(),
        buyer_address=graphene.String(), net_amount=graphene.String(),
        crated_by=graphene.String(), CreatedAt=graphene.String(), city=graphene.String(),
        state=graphene.String(), consignee=graphene.String() , salesPerson=graphene.String(),salesPerson_dc_list=graphene.List(graphene.Int),
        sales_order_no_list=graphene.List(graphene.Int),dc_status=graphene.List(graphene.String), dc_link_is_exists=graphene.Boolean(),dc_no_list=graphene.List(graphene.Int),
        sales_invoice = graphene.List(graphene.Int)
        )
    

    lead_time_line = graphene.Field(LeadTimeLine, lead_id=graphene.Int())
    lead_time_line_new = graphene.Field(LeadTimeLine_new, lead_id=graphene.Int())
    enquiry_time_line = graphene.Field(LeadTimeLine, enquiry_id=graphene.Int())
    allActivityType_type = graphene.List(ActivityType_type, id=graphene.Int(), name=graphene.String())
    # allActivity_Type=graphene.List(Activity_Type,id_list=graphene.List(graphene.Int))
    allActivity_Type = graphene.List(Activity_Type, id=graphene.Int(), app_name=graphene.String(),
                                     modal_name=graphene.String(), activity_id=graphene.Int())
    allNotes_type = graphene.List(Notes_type, id=graphene.Int(), app_name=graphene.String(),
                                  modal_name=graphene.String())
    allEmailTemplete_Type = graphene.List(EmailTemplete_Type, id=graphene.Int(), title=graphene.String(),
                                          resource=graphene.String(),whatsAppTemplate=graphene.Boolean(),mailTemplate=graphene.Boolean(),active=graphene.Boolean())
    allEmailResource_Type = graphene.List(EmailResource_Type, name=graphene.String(), resource=graphene.String())
    allEmailRecord_Type = graphene.List(EmailRecord_type, id=graphene.Int(), app_name=graphene.String(),
                                        modal_name=graphene.String(), mail_id=graphene.Int())
    allBulkMailContact_Type = graphene.List(BulkMailContactType, id=graphene.List(graphene.ID),
                                            app_name=graphene.String(), modal_name=graphene.String())
    allBulkWhatsApp_Type = graphene.List(BulkWhatsAppContactType, id=graphene.List(graphene.ID),
                                            app_name=graphene.String(), modal_name=graphene.String())
    allHistory_Type = graphene.List(ItemMasterHistory_Type, modal_id=graphene.Int(), app_name=graphene.String(),
                                    modal_name=graphene.String())
    allTarget_type = graphene.List(Target_type, target_name=graphene.String(), id=graphene.Int(),
                                   target_mode=graphene.String())
    allTargeModulesType = graphene.Field(TargeModulesType)
    target_Achievement = graphene.Field(TargetAchievementType, salesperson=graphene.Int(),
                                        financial_year_start=graphene.Date(), financial_year_end=graphene.Date(),
                                        target_id=graphene.Int(), is_admin=graphene.Boolean())
    activity_calender = graphene.List(Activity_Type,user_id =graphene.Int(), status=graphene.String(),sales_person = graphene.String(),user_group=graphene.String())
    salesOrder_2__deliver_challan = graphene.List(salesOrder_2_DeliveryChallan_type,id=graphene.Int(),dc_no_list=graphene.List(graphene.Int),sales_invoice_is_exists=graphene.Boolean())
    sales_dc_initial_fetch = graphene.Field(SalesInitialFetch, id=graphene.Int())
    sales_dc_edit_fetch = graphene.Field(SalesInitialFetch, id=graphene.Int())
    sales_invoice_type = graphene.Field(SalesInvoice_type, id=graphene.Int())
    direct_sales_invoice_type = graphene.Field(DirectSalesInvoice_type, id=graphene.Int())
    multi_dc_invoice = graphene.Field( SalesInitialFetch, buyer=graphene.Int(), consignee=graphene.Int(), sales_person=graphene.List(graphene.Int), department=graphene.Int())
    combine_multi_dc_to_sales_invoice_type = graphene.List(combineMultiDcToSalesInvoice_Type,  dc_ids=graphene.List(graphene.Int))
    combine_multi_sales_invoice = graphene.Field(combineMultiDcToSalesInvoice_Type,  dc_ids=graphene.List(graphene.Int))
    sales_return_initial_fetch = graphene.Field(SalesInitialFetch, dc_item_ids=graphene.List(graphene.Int), sales_invoice_item_ids=graphene.List(graphene.Int), sales_id=graphene.Int())
    sales_return_edit_fetch = graphene.Field(SalesInitialFetch, sr_id=graphene.Int())

    sales_return_multi_select = graphene.Field(combineMultiDcToSalesInvoice_Type,buyer=graphene.Int(), consignee=graphene.Int(),sales_order_id=graphene.Int(),module=graphene.String())
    receipt_voucher_edit_fetch = graphene.Field(SalesInitialFetch, id=graphene.Int())
    unpaid_sales_invoice = graphene.Field(SalesInitialFetch, customer_id=graphene.Int())
    receipt_voucher_type = graphene.Field(ReceiptVoucher_Type, id=graphene.Int())    
    credit_note_initial_fetch = graphene.Field(SalesInitialFetch, sales_return_id=graphene.Int())
    credit_note_edit_fetch = graphene.Field(SalesInitialFetch, credit_note_id=graphene.Int())
    credit_note = graphene.List(credit_note_type,id=graphene.Int())


    @permission_required(models=["Activites"])
    def resolve_activity_calender(self, info, user_id=None, status=None, sales_person=None, user_group=None):
        try:
            queryset = Activites.objects.all()

            if user_id is None:
                return queryset.none()

            user_management = UserManagement.objects.filter(user__id=user_id).first()

            if not user_management or not (
                user_management.admin or user_management.sales_executive or user_management.sales_person or user_management.service or user_management.service_executive
            ):
                return queryset.none()

            # Common filter for all roles
            if status:
                queryset = queryset.filter(status__name__iexact=status)

            # Admin logic: All sales or service persons, and allow filtering
            if user_management.admin:
                user_ids = UserManagement.objects.filter(
                    models.Q(sales_person=True) | models.Q(service=True) | models.Q(service_executive=True) | models.Q(sales_executive=True) | models.Q(admin=True)
                ).values_list('user__id', flat=True)
                queryset = queryset.filter(assigned__id__in=user_ids)

                if sales_person:
                    queryset = queryset.filter(assigned__id=sales_person)

                if user_group:
                    group_user_ids = UserManagement.objects.filter(
                        user_group=user_group
                    ).values_list('user__id', flat=True)

                    if group_user_ids:
                        queryset = queryset.filter(assigned__id__in=group_user_ids)
                    else:
                        return queryset.none()

            # Sales Executive logic: Only sales_persons, allow filtering by salesperson
            elif user_management.sales_executive:
                # Get all users who are sales_person or this executive themselves
                sales_person_ids = list(
                    UserManagement.objects.filter(sales_person=True).values_list('user__id', flat=True)
                )

                # Add the sales executive's own ID
                sales_person_ids.append(user_id)
                queryset = queryset.filter(assigned__id__in=sales_person_ids)

                if sales_person:
                    queryset = queryset.filter(assigned__id=sales_person)
            
            # ---------- SERVICE EXECUTIVE ----------
            
            elif user_management.service_executive:
                service_person_ids = list(
                    UserManagement.objects.filter(service=True).values_list('user__id', flat=True)
                )
                service_person_ids.append(user_id)

                queryset = queryset.filter(assigned__id__in=service_person_ids)

            # Sales Person logic: show only self + subordinates
            elif user_management.sales_person:
                subordinate_ids = get_subordinate(user_id)  # returns list of user IDs
                queryset = queryset.filter(assigned__id__in=[user_id] + subordinate_ids)

            elif user_management.service:
                # You can add a `get_service_subordinate(user_id)` method if hierarchy exists for service
                queryset = queryset.filter(assigned__id=user_id)

            return queryset

        except Exception as e:
            raise Exception(f"An error occurred: {e}")

    def resolve_lead_time_line(self, info, lead_id):

        try:
            lead = Leads.objects.get(id=lead_id)
            quotations = Quotations.objects.filter(lead_no__id=lead_id, active=True)
            parent_children = []

            # Constructing children
            children = []

            # Add standalone sales orders (without quotations)
            standalone_sales_orders = SalesOrder_2.objects.filter(lead_no__id=lead_id, quotations=None, active=True)
            children.extend([
                LeadChildType(
                    id=str(order.id),
                    label="Sales Order",
                    isShow=True,
                    Number=order.sales_order_no.linked_model_id,
                    date=order.CreatedAt,
                    status=order.status.name,
                    children =[
                            LeadChildType(
                                id=str(dc.id),
                                label="Sales Deliver Challan",
                                Number=dc.dc_no.linked_model_id,
                                isShow=True,
                                date=dc.created_at,
                                status=dc.status.name,
                                children = [
                                    LeadChildType(
                                        id=str(dc.sales_invoice.id),
                                        label="Sales Invoice",
                                        Number=dc.sales_invoice.sales_invoice_no.linked_model_id,
                                        isShow=True,
                                        date=dc.sales_invoice.created_at,
                                        status=dc.sales_invoice.status.name,
                                    )
                                ] if dc.sales_invoice else []
                            )

                            for dc in order.dc_links.all()
                        ]
                )
                for order in standalone_sales_orders
            ])

            # Add quotations with nested sales orders
            for quotation in quotations:
                # Fetch sales orders linked to this quotation
                linked_sales_orders = SalesOrder_2.objects.filter(quotations__id=quotation.id, active=True)
               
                # Add quotation with nested sales orders as children
                children.append(
                    LeadChildType(
                        id=str(quotation.id),
                        label="Quotation",
                        isShow=True,
                        Number=quotation.quotation_no.linked_model_id,
                        date=quotation.CreatedAt,
                        status=quotation.status.name,
                        children=[
                            LeadChildType(
                                id=str(order.id),
                                label="Sales Order",
                                isShow=True,
                                Number=order.sales_order_no.linked_model_id,
                                date=order.CreatedAt,
                                status=order.status.name,
                                children =[
                                        LeadChildType(
                                            id=str(dc.id),
                                            label="Sales Deliver Challan",
                                            Number=dc.dc_no.linked_model_id,
                                            isShow=True,
                                            date=dc.created_at,
                                            status=dc.status.name,
                                            children=[
                                                
                                                        LeadChildType(
                                                            id=str(dc.sales_invoice.id),
                                                            label="Sales Invoice",
                                                            Number=dc.sales_invoice.sales_invoice_no.linked_model_id,
                                                            isShow=True,
                                                            date=dc.sales_invoice.created_at,
                                                            status=dc.sales_invoice.status.name,
                                                        )
                                                    ] if dc.sales_invoice else []
                                        )
                                        
                                        for dc in order.dc_links.all()
                                    ]

                            )
                       
                            for order in linked_sales_orders
                        ]
                    )
                )

            if lead.Enquiry:
                lead_child_instance = LeadChildType(
                    id=str(lead.id),
                    label="Lead",
                    isShow=True,
                    Number=lead.lead_no,
                    date=lead.created_at,
                    status=lead.status.name,
                    children=children,
                )
                parent_children.append(lead_child_instance) 
            # Returning LeadTimeLine
            return LeadTimeLine(
                id=lead.Enquiry.id if lead.Enquiry else str(lead.id),
                label="Enquiry" if lead.Enquiry else "Lead",
                Number=lead.Enquiry.name if lead.Enquiry else lead.lead_no,
                isShow=True,
                date=lead.Enquiry.created_at if lead.Enquiry else lead.created_at,
                status="" if lead.Enquiry else lead.status.name,
                children=parent_children if lead.Enquiry else children
            )
        except Leads.DoesNotExist:
            raise Exception(f"Lead with id {lead_id} does not exist")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

    def resolve_lead_time_line_new(self, info, lead_id):
        try:
            lead = Leads.objects.get(id=lead_id)
            
            quotations = lead.quotation_ids.filter(active=True)

            # FINAL CHILDREN ARRAY
            children = []

            # ----------------------------------------------------
            # 1. Standalone Sales Orders (no quotation)
            # ----------------------------------------------------
            standalone_sales_orders = lead.sales_order_id.filter(quotations__isnull=True, active=True)

            for order in standalone_sales_orders:
                order_dict = {
                    "id": str(order.id),
                    "label": "Sales Order",
                    "Number": order.sales_order_no.linked_model_id,
                    "isShow": True,
                    "date": str(order.CreatedAt),
                    "status": order.status.name,
                    "children": []
                } 
                # Add DCs under sales order
                for dc in order.delivery_challans.all():
                    dc_dict = {
                        "id": str(dc.id),
                        "label": "Sales Deliver Challan",
                        "Number": dc.dc_no.linked_model_id,
                        "isShow": True,
                        "date": str(dc.created_at),
                        "status": dc.status.name,
                        "children": []
                    }

                    # Add Invoice under DC
                    if dc.salesinvoice_set.exists():
                        for invoice in dc.salesinvoice_set.all():
                            dc_dict["children"].append({
                                "id": str(invoice.id),
                                "label": "Sales Invoice",
                                "Number": invoice.sales_invoice_no.linked_model_id,
                                "isShow": True,
                                "date": str(invoice.created_at),
                                "status": invoice.status.name,
                                "children": []
                            })
                    if dc.sales_return.exists():
                            for sales_return in  dc.sales_return.all():
                                dc_dict["children"].append({
                                    "id": str(sales_return.id),
                                    "label": "Sales Return",
                                    "Number": sales_return.sr_no.linked_model_id,
                                    "isShow": True,
                                    "date": str(sales_return.created_at),
                                    "status": sales_return.status.name,
                                    "children": []
                                })

                    order_dict["children"].append(dc_dict)

                children.append(order_dict)

            # ----------------------------------------------------
            # 2. Quotations → Sales Orders → DC → Invoice
            # ----------------------------------------------------
            for quotation in quotations:
                quotation_dict = {
                    "id": str(quotation.id),
                    "label": "Quotation",
                    "Number": quotation.quotation_no.linked_model_id,
                    "isShow": True,
                    "date": str(quotation.CreatedAt),
                    "status": quotation.status.name,
                    "children": []
                }

                linked_sales_orders = SalesOrder_2.objects.filter(
                    quotations__id=quotation.id, active=True
                )

                for order in linked_sales_orders:
                    order_dict = {
                        "id": str(order.id),
                        "label": "Sales Order",
                        "Number": order.sales_order_no.linked_model_id,
                        "isShow": True,
                        "date": str(order.CreatedAt),
                        "status": order.status.name,
                        "children": []
                    } 
                    for dc in order.delivery_challans.all():
                        dc_dict = {
                            "id": str(dc.id),
                            "label": "Sales Deliver Challan",
                            "Number": dc.dc_no.linked_model_id,
                            "isShow": True,
                            "date": str(dc.created_at),
                            "status": dc.status.name,
                            "children": []
                        }

                        if dc.salesinvoice_set.exists():
                            for invoice in dc.salesinvoice_set.all():
                                dc_dict["children"].append({
                                    "id": str(invoice.id),
                                    "label": "Sales Invoice",
                                    "Number": invoice.sales_invoice_no.linked_model_id,
                                    "isShow": True,
                                    "date": str(invoice.created_at),
                                    "status": invoice.status.name,
                                    "children": []
                                })
                        if dc.sales_return.exists():
                            for sales_return in  dc.sales_return.all():
                                dc_dict["children"].append({
                                    "id": str(sales_return.id),
                                    "label": "Sales Return",
                                    "Number": sales_return.sr_no.linked_model_id,
                                    "isShow": True,
                                    "date": str(sales_return.created_at),
                                    "status": sales_return.status.name,
                                    "children": []
                                })


                        order_dict["children"].append(dc_dict)

                    quotation_dict["children"].append(order_dict)

                children.append(quotation_dict)

            # ----------------------------------------------------
            # 3. Wrap inside Lead or Enquiry
            # ----------------------------------------------------
            if lead.Enquiry:
                parent = {
                    "id": str(lead.id),
                    "label": "Lead",
                    "Number": lead.lead_no,
                    "isShow": True,
                    "date": str(lead.created_at),
                    "status": lead.status.name,
                    "children": children
                }

                return LeadTimeLine_new(item={
                    "id": lead.Enquiry.id,
                    "label": "Enquiry",
                    "Number": lead.Enquiry.name,
                    "isShow": True,
                    "date": str(lead.Enquiry.created_at),
                    "status": "",
                    "children": [parent]
                })

            # No enquiry → return Lead only
            return LeadTimeLine_new(item = {
                "id": str(lead.id),
                "label": "Lead",
                "Number": lead.lead_no,
                "isShow": True,
                "date": str(lead.created_at),
                "status": lead.status.name,
                "children": children
            })

        except Leads.DoesNotExist:
            raise Exception(f"Lead with id {lead_id} does not exist")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")




    def resolve_all_CallLog(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, id_list=None):

        queryset = CallLog.objects.all().order_by('-id')

        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        elif id_list:
            filter_kwargs['id__in'] = id_list
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return CallLogConnection(items=paginated_data.object_list,
                                 page_info=page_info)

    def resolve_id_CallLog(self, info, id=None, isEnquiry=None, page=1, page_size=50):

        if isEnquiry is not None and id:
            enquiry_instance = enquiryDatas.objects.get(id=id)
            calls_list = enquiry_instance.call_log.all().order_by('-id')
            paginator = Paginator(calls_list, page_size)
            paginated_data = paginator.get_page(page)

            page_info = PageInfoType(
                total_items=paginator.count,
                has_next_page=paginated_data.has_next(),
                has_previous_page=paginated_data.has_previous(),
                total_pages=paginator.num_pages,
            )
            return CallLogWithPagination(calls=paginated_data.object_list, page_info=page_info)

    def resolve_id_meeting(self, info, id=None, isEnquiry=None, page=1, page_size=50):
        if isEnquiry is not None and id:
            enquiry_instance = enquiryDatas.objects.get(id=id)
            meeting_list = enquiry_instance.meetings.all().order_by('-id')

            paginator = Paginator(meeting_list, page_size)
            paginated_data = paginator.get_page(page)

            page_info = PageInfoType(
                total_items=paginator.count,
                has_next_page=paginated_data.has_next(),
                has_previous_page=paginated_data.has_previous(),
                total_pages=paginator.num_pages,
            )
            return MeetingWithPagination(meeting=paginated_data.object_list, page_info=page_info)

    def resolve_activities(self, info, id=None, isEnquiry=None, page=1, page_size=50, app_name=None, modal_name=None):
        try:
            if app_name is not None and modal_name is not None and id:
                ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                # Get the specific record using ID
                query_instance = ModelClass.objects.get(id=id)

                # Fetch the related CallLog objects (ManyToMany field)
                call_logs = query_instance.call_log.all()
                meetings = query_instance.meetings.all()
                notes = query_instance.notes.all()

                activities = list(call_logs) + list(meetings) + list(notes)

                activities.sort(key=lambda x: x.created_at, reverse=True)

                return activities
        except Exception as e:
            print("e-----", e)

    @permission_required(models=["Lead"])
    def resolve_all_lead(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, lead_no=None,
                         lead_name=None, customer=None, requirement=None, lead_currency=None, lead_value=None
                         , expected_closing_date=None, priority=None, sales_person=None, created_by=None, user_id=None):
        """apply filters"""
        filter_kwargs = {}

        queryset = Leads.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        elif lead_value:
            filter_kwargs['lead_value__icontains'] = lead_value
        elif lead_no:
            filter_kwargs['lead_no'] = lead_no
        elif lead_name:
            filter_kwargs['lead_name__icontains'] = lead_name
        elif customer:
            filter_kwargs['customer__company_name__icontains'] = customer
        elif requirement:
            filter_kwargs['requirement__icontains'] = requirement
        elif lead_currency:
            filter_kwargs['lead_currency__name__icontains'] = lead_currency
        elif sales_person:
            filter_kwargs['sales_person__username__icontains'] = sales_person
        elif created_by:
            filter_kwargs['created_by__username__icontains'] = created_by
        elif expected_closing_date:
            start_date, end_date = expected_closing_date.split(' - ')
            expected_closing_date_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            expected_closing_date_end_date = datetime.strptime(end_date, '%d-%m-%Y')
            if start_date == end_date:
                filter_kwargs['created_at__date'] = expected_closing_date_start_date
            else:
                filter_kwargs['created_at__range'] = (expected_closing_date_start_date, expected_closing_date_end_date)
        queryset = queryset.filter(**filter_kwargs) \
            .annotate(
            sales_order_count=Count('sales_order_id'),  # Count related SalesOrders
            quotation_count=Count('quotation_ids')  # Count related Quotations
        )

        db_s = {
            "id": {"field": "id", "is_text": False},
            "lead_no": {"field": "lead_no", "is_text": True},
            "lead_name": {"field": "lead_name", "is_text": True},
        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return LeadsConnection(items=paginated_data.object_list,
                               page_info=page_info)

    @permission_required(models=["Other_Income", "POS","Quotation", "SalesOrder_2" , "Debit Note"])
    def resolve_other_income_charges(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                                     name=None, account=None, HSN=None, active=None):
        """return the data with filter"""
        filter_kwargs = {}
        queryset = OtherIncomeCharges.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        elif name:
            filter_kwargs['name__icontains'] = name
        elif account:
            filter_kwargs['account__accounts_name__icontains'] = account
        elif HSN:
            filter_kwargs['hsn__hsn_code__icontains'] = HSN
        elif active:
            filter_kwargs['active'] = active
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return OtherIncomeChargesConnection(
            items=paginated_data.object_list,
            page_info=page_info

        )

    def resolve_quotations_item_details(self, info, id):
        if id:
            try:
                queryset = QuotationsItemDetails.objects.get(id=id)
                return queryset
            except QuotationsItemDetails.DoesNotExist:
                return None

    def resolve_quotations_item_combo_item_details(self, info, id_list=[]):
        if id_list:
            try:
                # Use filter instead of get to retrieve multiple records
                queryset = QuotationsItemComboItemDetails.objects.filter(id__in=id_list)
                return queryset  # This will return a QuerySet, which is iterable
            except QuotationsItemDetails.DoesNotExist:
                return []  # Return an empty list instead of None for consistency
        return []

    @permission_required(models=["Quotation"])
    def resolve_all_quotations(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, status=None,
                               active=None, quotation_no=None, customer_id=None, city=None, state=None, net_amount=None,
                               created_by=None, CreatedAt=None):
        filter_kwargs = {}
        queryset = Quotations.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if status:
            filter_kwargs['status__name__icontains'] = status
        if quotation_no:
            filter_kwargs['quotation_no__linked_model_id__icontains'] = quotation_no
        if customer_id:
            filter_kwargs['customer_id__company_name__icontains'] = customer_id
        if city:
            filter_kwargs['customer_address__city__icontains'] = city
        if state:
            filter_kwargs['customer_address__state__icontains'] = state
        if net_amount:
            filter_kwargs['net_amount__icontains'] = net_amount
        if created_by:
            filter_kwargs['created_by__username__icontains'] = created_by
        if CreatedAt:
            start_date, end_date = CreatedAt.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['CreatedAt__range'] = (updated_start_date, updated_end_date)
            else:
                filter_kwargs['CreatedAt__range'] = (updated_start_date, updated_end_date)

        if active is not None:
            filter_kwargs['active'] = active
        queryset = queryset.filter(**filter_kwargs)
        if id:
            version_ids = get_all_related_version(queryset.first(), Quotations)
        else:
            version_ids = []
        db_s = {
            "id": {"field": "id", "is_text": False},
            "quotationNo": {"field": "quotation_no__linked_model_id", "is_text": False},
            "customerId": {"field": "customer_id__company_name", "is_text": True},
            "city": {"field": "customer_address__city", "is_text": True},
            "state": {"field": "customer_address__state", "is_text": True},
            "netAmount": {"field": "net_amount", "is_text": False},
            "CreatedAt": {"field": "CreatedAt", "is_text": False},
        }
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return QuotationsConnection(
            items=paginated_data.object_list,
            page_info=page_info,
            version=versionListType(versionList=version_ids),

        )

    @permission_required(models=["SalesOrder_2"])
    def resolve_all_SalesOrder_2(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                                 status=None, active=None, sales_order_no=None,sales_order_no_list=[], customer_po_no=None, department=None,
                                 city=None,
                                 buyer=None, buyer_address=None, net_amount=None, created_by=None, CreatedAt=None,
                                 state=None, userId=None, consignee=None , salesPerson=None,dc_status=None,dc_no_list=[], dc_link_is_exists=None,salesPerson_dc_list=[],
                                 sales_invoice = []
                                 ):
        version_ids = []
        filter_kwargs = {}
        queryset = SalesOrder_2.objects.all().order_by('-id') 

        if id:
            filter_kwargs['id'] = id
        if status:
            filter_kwargs['status__name__icontains'] = status
        if sales_order_no:
            filter_kwargs['sales_order_no__linked_model_id__icontains'] = sales_order_no
        if customer_po_no:
            filter_kwargs['customer_po_no__icontains'] = customer_po_no
        if department:
            filter_kwargs['department__id'] = department
        if buyer:
            filter_kwargs['buyer__id'] = buyer
        if buyer_address:
            filter_kwargs['buyer_address__icontains'] = buyer_address
        if city:
            filter_kwargs['buyer_address__city__icontains'] = city
        if net_amount:
            filter_kwargs['net_amount__icontains'] = net_amount
        if state:
            filter_kwargs['buyer_address__state__icontains'] = state
        if created_by:
            filter_kwargs['created_by__username__icontains'] = created_by
        if CreatedAt:
            start_date, end_date = CreatedAt.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['CreatedAt__range'] = (updated_start_date, updated_end_date)
            else:
                filter_kwargs['CreatedAt__range'] = (updated_start_date, updated_end_date)
        if consignee:
            filter_kwargs['consignee__id'] = consignee
        if salesPerson:
            filter_kwargs['sales_person__id'] = salesPerson
        if len(salesPerson_dc_list)>0: 
            filter_kwargs['sales_person__id__in'] = salesPerson_dc_list
        if len(sales_order_no_list)>0:
            filter_kwargs['id__in'] = sales_order_no_list
        if len(dc_no_list)>0:
            filter_kwargs['delivery_challans__id__in'] = dc_no_list
        if dc_status:
            filter_kwargs['delivery_challans__status__name__in'] = dc_status
        if sales_invoice : 
            filter_kwargs['delivery_challans__sales_invoice__id__in'] = sales_invoice
        if active is not None:
            filter_kwargs['active'] = active 
 
        db_s = {
            "id": {"field": "id", "is_text": False},
            "salesOrderNo": {"field": "sales_order_no__linked_model_id", "is_text": False},
            "customerPoNo": {"field": "customer_po_no", "is_text": True},
            "buyer": {"field": "buyer__company_name", "is_text": True},
            "city": {"field": "buyer_address__city", "is_text": True},
            "state": {"field": "buyer_address__state", "is_text": True},
            "netAmount": {"field": "net_amount", "is_text": False},
            "createdBy": {"field": "created_by__username", "is_text": False},
            "CreatedAt": {"field": "CreatedAt", "is_text": False},
        }
        
        queryset = queryset.filter(**filter_kwargs)  
        # if dc_link_is_exists:
        # queryset = queryset.filter(
        #     dc_links__status__name__in=["Submit", "Dispatch"]
        # )

            # # Step 2: Prefetch ALL dc_links (not just the Submit ones)
            # queryset = queryset.prefetch_related(
            #     Prefetch(
            #         'dc_links',
            #         queryset=SalesOrder_2_DeliveryChallan.objects.filter(status__name='Submit').select_related('status'),
            #         to_attr='submit_dc_links'
            #     )
            # )

 
        # queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        try:
            if id:
                version_ids = get_all_related_version(queryset.first(), SalesOrder_2)
        except Exception as e:
            print(e)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return SalesOrder_2Connection(
            items=paginated_data.object_list,
            page_info=page_info,
            version=versionListType(versionList=version_ids),
        )
    
   
    @permission_required(models=["ActivityType","Enquiry","Lead", "Activites"])
    def resolve_allActivityType_type(self, info, id=None, name=None):
        filter_kwargs = {}
        queryset = ActivityType.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        elif name:
            filter_kwargs['name__icontains'] = name
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset

    # @permission_required(models=["Email_Template","Activites"])
    def resolve_allEmailTemplete_Type(self, info, id=None, title=None, resource=None,whatsAppTemplate=False,mailTemplate=False,active=None):
        filter_kwargs = {}
        queryset = EmailTemplete.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if title:
            filter_kwargs['title__icontains'] = title
        if resource:
            filter_kwargs['resource__modal_name__icontains'] = resource
        if active != None:
            filter_kwargs['active'] = active
        if whatsAppTemplate:
            filter_kwargs['whats_app_template'] = True
        if mailTemplate:
            filter_kwargs['mail_template'] = True
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset

    # @permission_required(models=["Email_Template", ])
    def resolve_allEmailResource_Type(self, info, name=None, resource=None):
        filter_kwargs = {}
        queryset = EmailResource.objects.all().order_by('-id')
        if name:
            filter_kwargs['name__icontains'] = name
        if resource:
            filter_kwargs['resource__name'] = resource

        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset

    @permission_required(models=["Activites"])
    def resolve_allActivity_Type(self, info, id=None, app_name=None, modal_name=None, activity_id=None):
        try:
            try:
                if activity_id:
                    queryset = Activites.objects.filter(id=activity_id)
                    return queryset
            except Exception as e:
                print("e-----", e)
            if app_name is not None and modal_name is not None and id:
                ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                # Get the specific record using ID
                query_instance = ModelClass.objects.get(id=id)
                # print("query_instance",query_instance)
                return query_instance.activity.all().order_by('-id')

        except Exception as e:
            print("e-----", e)

    @permission_required(models=["Activites"])
    def resolve_allNotes_type(self, info, id=None, app_name=None, modal_name=None):
        try:
            if app_name is not None and modal_name is not None and id:
                ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                # Get the specific record using ID
                query_instance = ModelClass.objects.get(id=id)
                return query_instance.note.all().order_by('-id')

        except Exception as e:
            print("e-----", e)

    def resolve_allEmailRecord_Type(self, info, id=None, app_name=None, modal_name=None, mail_id=None):
        try:
            try:
                if mail_id:
                    queryset = EmailRecord.objects.filter(id=mail_id)
                    return queryset
            except Exception as e:
                print("e-----", e)
            if app_name is not None and modal_name is not None and id:
                ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                # Get the specific record using ID
                query_instance = ModelClass.objects.get(id=id)
                return query_instance.email_record.all()

        except Exception as e:
            print("e-----", e)

    def resolve_allBulkMailContact_Type(self, info, app_name, modal_name, id):
        try:
            if not (app_name and modal_name and id):
                return []

            results = []  # To store ID and email pairs

            if app_name == "EnquriFromapi" and modal_name == "enquiryDatas":
                # Fetch enquiryDatas objects with given IDs
                enquiries = enquiryDatas.objects.filter(id__in=id)

                # Extract emails from linked ContactDetalis
                results = [
                    BulkMailContactType(id=enquiry.id, email=enquiry.email)
                    for enquiry in enquiries
                    if enquiry.email
                ]

            elif app_name == "itemmaster2" and modal_name == "Leads":
                # Fetch Leads objects with given IDs
                leads = Leads.objects.filter(id__in=id)

                for lead in leads:
                    if lead.customer:
                        # Fetch all related contacts and get their emails
                        for contact in lead.customer.contact.all():
                            if contact.email and contact.default:
                                results.append(BulkMailContactType(id=lead.id, email=contact.email))
                                break

            return results  # Return only valid email-ID pairs

        except Exception as e:
            print("Error:", e)
            return []

    def resolve_allBulkWhatsApp_Type(self, info, app_name, modal_name, id):
        try:
            if not (app_name and modal_name and id):
                return []

            temp_results = []

            if app_name == "EnquriFromapi" and modal_name == "enquiryDatas":
                enquiries = enquiryDatas.objects.filter(id__in=id)

                for enquiry in enquiries:
                    if enquiry.alternate_mobile_number:
                        temp_results.append(
                            BulkWhatsAppContactType(
                                id=enquiry.id,
                                ph_num=enquiry.alternate_mobile_number,
                                name=enquiry.name
                            )
                        )

            elif app_name == "itemmaster2" and modal_name == "Leads":
                leads = Leads.objects.filter(id__in=id)

                for lead in leads:
                    if lead.customer:
                        for contact in lead.customer.contact.all():
                            if contact.whatsapp_no and contact.default:
                                temp_results.append(
                                    BulkWhatsAppContactType(
                                        id=lead.id,
                                        ph_num=contact.whatsapp_no,
                                        name=contact.contact_person_name
                                    )
                                )
                                break

            # ✅ Ensure global uniqueness of phone numbers in final result
            seen_numbers = set()
            results = []
            for entry in temp_results:
                if entry.ph_num not in seen_numbers:
                    seen_numbers.add(entry.ph_num)
                    results.append(entry)

            return results

        except Exception as e:
            print("Error:", e)
            return []

    @permission_required(
        models=["Item_Master", "Target","Activites","SalesOrder_2","Quotation","Department","Employee","UserGroup",  "Roles", "Conference", "Accounts_Master", "Account_Group",
                "Currency_Exchange", "Currency_Master", "Other_Expenses","Other_Income","Enquiry","Customer","Supplier","PaymentVoucher", "ReworkDeliveryChallan", "Debit Note", "history_details",
                "Receipt Voucher", 'PaymentVoucher', "Credit Note"], type="query", action="History")
    def resolve_allHistory_Type(self, info, modal_id, app_name, modal_name):
        try:
            if app_name is not None and modal_name is not None and modal_id:
                ModelClass = apps.get_model(app_label=app_name, model_name=modal_name)
                query_instance = ModelClass.objects.get(id=modal_id)
                return query_instance.history_details.all().order_by('-id')
        except Exception as e:
            print("e-----", e)

    @permission_required(models=["Target","Target_Summary"])
    def resolve_allTarget_type(self, info, target_name=None, id=None, target_mode=None):
        target_list = Target.objects.all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if target_name:
            filter_kwargs['target_name__icontains'] = target_name
        if target_mode:
            filter_kwargs['target_mode'] = target_mode
        if filter_kwargs:
            target_list = target_list.filter(**filter_kwargs)
        return target_list
    
    @permission_required(models=["Target"])
    def resolve_allTargeModulesType(self, info):
        list_options = []
        for key_1, value_1 in targe_modules.items():
            list_of_fields = [{key_2: value_2} for key_2, value_2 in value_1.items()]
            list_options.append({"label": key_1, "value": key_1, "list_of_fields": list_of_fields})
        json_result = json.dumps(list_options, indent=4)
        return TargeModulesType(model_list=json_result)

    @permission_required(models=["Target_Summary"])
    def resolve_target_Achievement(self, info, salesperson=None,
                                   financial_year_start=None,
                                   financial_year_end=None,
                                   target_id=None,
                                   is_admin=False):
        target_achievement_list = []

        # Admin override: fetch all data
        if is_admin:
            targets = Target.objects.filter(
                financial_year_start=financial_year_start,
                financial_year_end=financial_year_end
            )
        elif salesperson:
            targets = Target.objects.filter(
                target_sales_person__sales_person__id=salesperson,
                financial_year_start=financial_year_start,
                financial_year_end=financial_year_end
            )
        elif target_id:
            targets = Target.objects.filter(id=target_id)
        else:
            return target_achievement_list  # Nothing to filter by

        for target_instance in targets:
            start_year = target_instance.financial_year_start.year
            end_year = target_instance.financial_year_end.year

            for sp in target_instance.target_sales_person.all():
                if not is_admin and salesperson and sp.sales_person.id != salesperson:
                    continue

                target_achievement_month = []
                for tm in sp.target_months.all():
                    year = end_year if tm.month <= 3 else start_year
                    target_field_month = target_instance.target_module
                    target_field_name = target_instance.target_field
                    dynamic_field = targe_modules[target_field_month][target_field_name]

                    lead_datas = []
                    if target_instance.target_module == "Leads":
                        lead_datas = Leads.objects.filter(
                            created_at__month=tm.month,
                            created_at__year=year,
                            sales_person_id=sp.sales_person.id
                        )

                    weightPipeLine = Decimal("0.00")
                    pipeline = Decimal("0.00")

                    try:
                        for lead_data in lead_datas:
                            lead_value = Decimal(getattr(lead_data, dynamic_field, 0) or 0)
                            if lead_data.lead_currency and lead_data.lead_currency.rate:
                                lead_value *= Decimal(lead_data.lead_currency.rate)

                            if lead_data.status:
                                status_name = lead_data.status.name
                                percentage_map = {
                                    "Qualified": Decimal("0.10"),
                                    "Quotation": Decimal("0.20"),
                                    "Demo": Decimal("0.30"),
                                    "Negotiation": Decimal("0.40"),
                                }
                                if status_name in percentage_map:
                                    weightPipeLine += percentage_map[status_name] * lead_value
                                    pipeline += lead_value
                    except Exception as e:
                        print("Error in calculating pipeline:", e)

                    achievement = tm.target_achievement or Decimal("0.00")
                    total_expected_revenue = achievement + weightPipeLine
                    expected_variance = total_expected_revenue - tm.target_value

                    target_achievement_month.append({
                        "month": tm.month,
                        "target_value": float(tm.target_value),
                        "target_achievement": float(achievement),
                        "pipeline": float(pipeline),
                        "weight_pipeLine": float(weightPipeLine),
                        "total_expected_revenue": float(total_expected_revenue),
                        "expected_variance": float(expected_variance)
                    })

                target_achievement_list.append({
                    "salesperson_name": sp.sales_person.username,
                    "role": sp.role.role_name,
                    "ishead": sp.is_head,
                    "target": target_achievement_month,
                    "financial_year": f"{start_year} - {end_year}"
                })

        return TargetAchievementType(model_list=target_achievement_list)

    @permission_required(models=["Sales Invoice"])
    def resolve_sales_invoice_type(self, info, id):
        try:
            return SalesInvoice.objects.get(id=id)
        except SalesInvoice.DoesNotExist: 
            return None
        except Exception as e: 
            return e
    
    @permission_required(models=["Direct Sales Invoice"])
    def resolve_direct_sales_invoice_type(self, info, id):
        try:
            return DirectSalesInvoice.objects.get(id=id)
        except SalesInvoice.DoesNotExist: 
            return None
        except Exception as e: 
            return e
    
    def resolve_salesOrder_2__deliver_challan(self, info, id=None,dc_no_list=[],sales_invoice_is_exists=False):
        filter_kwargs = {}
        queryset = SalesOrder_2_DeliveryChallan.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if len(dc_no_list) > 0:
            filter_kwargs['id__in'] = dc_no_list
        if sales_invoice_is_exists:
            queryset = queryset.filter(sales_invoice__isnull=False).exclude(sales_invoice__status__name__in=["Draft","Delete","Canceled"]).distinct()
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset

    def resolve_sales_dc_initial_fetch(self, info, id=None):
        if not id:
            return GraphQLError("ID is required.")

        queryset = (
            SalesOrder_2.objects
            .select_related(
                "sales_person", "department", "consignee", 
                "consignee_address", "currency"
            )
            .prefetch_related("item_details__itemmaster", "item_details__uom", "item_details__hsn", "item_details__item_combo_item_details")
            .filter(id=id)
            .first()
        )

        if not queryset:
            return GraphQLError("Sales order not found.")

        # ✅ Helper to serialize address
        def serialize_address(address):
            return {
                "id": address.id,
                "addressLine1": address.address_line_1,
                "addressLine2": address.address_line_2,
                "addressType": address.address_type,
                "city": address.city,
                "country": address.country,
                "pincode": address.pincode,
                "state": address.state,
            } if address else {}

        # ✅ Helper to serialize item combo details
        def serialize_combo(combo,index): 
            allowed_qty =  (combo.qty - (combo.dc_submit_count or 0))
            
            if allowed_qty <= 0:
                return 
            return { 
                "itemComboId":str(combo.id),
                "partName": {"value": combo.itemmaster.id, "label": combo.itemmaster.item_name},
                "partCode": {"value": combo.itemmaster.id, "label": combo.itemmaster.item_part_code},
                "itemmasterId":str(combo.itemmaster.id) if combo.itemmaster.id else None,
                "isSerial":combo.itemmaster.serial,
                "isBatch": combo.itemmaster.batch_number,
                "uom": {"id": combo.uom.id, "name": combo.uom.name},
                "qty": str(allowed_qty or 0),
                "rate":str(combo.after_discount_value_for_per_item) if combo.after_discount_value_for_per_item else str(combo.rate or 0),
                "display": combo.display,
                "is_mandatory": combo.is_mandatory, 
                "amount": str(combo.amount or 0),
                "is_have_draft": str(combo.is_have_draft) if combo.is_have_draft else None,
                "dc_submit_count": str(combo.dc_submit_count) if combo.dc_submit_count else None,
                "index":index + 1,
            }

        # ✅ Helper to serialize item details
        def serialize_item(item, index):
            item_master = item.itemmaster 
            allowed_qty =  (item.qty - (item.dc_submit_count or 0 ))
            if allowed_qty <=0:
                return None
            combo_item_dtails =  [serialize_combo(c,idx) for idx,c in enumerate(item.item_combo_item_details.all())]
            rate = item.after_discount_value_for_per_item  if item.after_discount_value_for_per_item else item.rate
            amount = allowed_qty * rate
            return {
                "salesOrderItemDetail": {
                    "id": item.id,
                    "description": item.description,
                    "cgst": str(item.cgst) if item.cgst else None,
                    "igst": str(item.igst) if item.igst else None,
                    "sgst": str(item.sgst) if item.sgst else None,
                    "cess": str(item.cess) if item.cess else None,
                    "uom": {"id": item.uom.id, "name": item.uom.name},
                    "hsn": {"id": item.hsn.id, "hsnCode": item.hsn.hsn_code},
                    "tax": str(item.tax),
                },
                "partName": {"value": item_master.id, "label": item_master.item_name},
                "partCode": {"value": item_master.id, "label": item_master.item_part_code},
                "qty": str(allowed_qty),
                "discountPercentage": str(item.discount_percentage) if item.discount_percentage else None,
                "finalValue": str(item.final_value) if item.final_value else None,  
                "rate": str(rate),
                "amount": str(amount),
                "is_have_draft": str(item.is_have_draft) if item.is_have_draft else None,
                "dcSubmitCount": str(item.dc_submit_count) if item.dc_submit_count else None,
                "itemmasterId": item_master.id,
                "isSerial": item_master.serial,
                "isBatch": item_master.batch_number,
                "itemCombo": item.item_combo,
                "itemComboItemDetails": [combo_item for combo_item in combo_item_dtails if combo_item],
                "stockReduce": False,
                "batch": "",
                "serial": "",
                "batchList": [],
                "serialList": [],
                "store": "",
                "id": "",
                "createdBy": "",
                "modifiedBy": "",
                "index": index + 1,
            }
        
        
        sales_dc = {
            "salesPerson": {"id": queryset.sales_person.id, "name": queryset.sales_person.username},
            "department": {"id": queryset.department.id, "name": queryset.department.name},
            "salesOrderNo": queryset.sales_order_no.linked_model_id,
            "salesOrderId": str(queryset.id),
            "salesOrderDate": str(queryset.sales_order_date),
            "leadId": str(queryset.lead_no.id),
            "customerPoNo": queryset.customer_po_no,
            "consigneeId": queryset.consignee.id,
            "consignee":{
                "id": queryset.consignee.id,
                "companyName": queryset.consignee.company_name
            },
            "consigneeNumber": {
                "id": queryset.consignee.id,
                "supplierNo": queryset.consignee.supplier_no
            },
            "consigneeAddress": serialize_address(queryset.consignee_address),
            "consigneeContactPerson": {
                "id": queryset.consignee_contact_person.id,
                "contactPersonName": queryset.consignee_contact_person.contact_person_name,
                "email": queryset.consignee_contact_person.email,
                "phoneNumber": queryset.consignee_contact_person.phone_number,
                "whatsappNo":queryset.consignee_contact_person.whatsapp_no
            },
            "consigneeGstinType": queryset.consignee_gstin_type,
            "consigneeGstin": queryset.consignee_gstin,
            "consigneePlaceOfSupply": queryset.consignee_place_of_supply,
            "consigneeState": queryset.consignee_address.state,
            "currency": {
                "id": queryset.currency.id,
                "symbol":queryset.currency.Currency.currency_symbol,
                "rate": str(queryset.currency.rate),
                "Currency": queryset.currency.Currency.name if queryset.currency.Currency else None
            },
            "salesOrderItemDetail": [ serialize_item(item, idx)
                                      for idx, item in enumerate(queryset.item_details.all())],
        } 
        
        return SalesInitialFetch(items=sales_dc)

    def resolve_sales_dc_edit_fetch(self, info, id=None):
        if not id:
            return GraphQLError("ID is required.")

        queryset = (
            SalesOrder_2_DeliveryChallan.objects
            .select_related(
                "status", "dc_no", "sales_order", "terms_conditions",
                "comman_store",  "transport","created_by","modified_by"
            ).prefetch_related(
            "item_details__salesorder_2_retunbatch_set",
            "item_details__serial",
            "item_details__item_combo_itemdetails__salesorder_2_retunbatch_set",
            "item_details__item_combo_itemdetails__serial",
            )
            .filter(id=id)
            .first()
        )
        if not queryset:
            return GraphQLError("Sales DC not found.")

        # Helper to serialize address
        def serialize_address(address):
            return {
                "id": address.id,
                "addressLine1": address.address_line_1,
                "addressLine2": address.address_line_2,
                "addressType": address.address_type,
                "city": address.city,
                "country": address.country,
                "pincode": address.pincode,
                "state": address.state,
            } if address else {}

        # Helper to serialize item combo details
        def serialize_combo(combo,index):
            try:
                sales_item_combo = combo.item_combo
                item_master = combo.item_combo.itemmaster
                already_exists_id = []
                batch_obj = []
                store = combo.store
                for batch in combo.salesorder_2_retunbatch_set.all():
                    batch_ = batch.batch
                    already_exists_id.append(batch_.id)
                    batch_obj.append({"id": batch.id, "value":batch_.id,"label" : batch_.batch_number_name,
                            "qty" : fetch_batch_stock(item_master.id, batch_.id, store.id),"returnQty":str(batch.qty), 'is_stock_reduce': batch.is_stock_reduce})
                batch_obj.extend(get_new_batchs(item_master.id, store.id, already_exists_id))

                return { 
                    "id" : combo.id,
                    "itemComboId":str(sales_item_combo.id),
                    "partName": {"value": item_master.id, "label": item_master.item_name},
                    "partCode": {"value": item_master.id, "label": item_master.item_part_code},
                    "itemmasterId":str(item_master.id) if item_master.id else None,
                    "store" : {"value":str(combo.store.id),"label":combo.store.store_name},
                    "invoiceSubmitCount":str(combo.invoice_submit_count) if combo.invoice_submit_count else None,
                    "isSerial":item_master.serial,
                    "isBatch": item_master.batch_number,
                    "batch": batch_obj, 
                    "stockReduce": combo.stock_reduce,
                    "batchList": [],
                    "serial": [{"value":serial.id,"label":serial.serial_number} for serial in combo.serial.all()],
                    "serialList":[],
                    "uom": {"id": sales_item_combo.uom.id, "name": sales_item_combo.uom.name},
                    "qty": str(combo.qty or 0),
                    "rate":str(sales_item_combo.after_discount_value_for_per_item) if sales_item_combo.after_discount_value_for_per_item else str(sales_item_combo.rate or 0),
                    "display": sales_item_combo.display,
                    "is_mandatory": sales_item_combo.is_mandatory,
                    "amount":str(sales_item_combo.amount or 0),
                    "is_have_draft": str(combo.invoice_draft_count) if  combo.invoice_draft_count else None,
                    "dc_submit_count": str(combo.invoice_submit_count) if combo.invoice_submit_count else None,
                    "index":index + 1,
                }
            except Exception as e:
                print("combo", e)
        
        def fetch_batch_stock(master_id, batch_id,store_id):
                stock = ItemStock.objects.filter(part_number__id=master_id, batch_number__id=batch_id,store__id= store_id).first()
                print("stock", stock)
                if stock:
                    return str(stock.current_stock or 0)
                else:
                    return 0
        
        def get_new_batchs(master_id, store_id, already_exists_id):
            new_batch = []
            
            stocks = ItemStock.objects.filter(part_number__id=master_id, store__id= store_id).exclude(batch_number__id__in = already_exists_id)

            if stocks:
                for stock in stocks:
                    if stock.current_stock:
                        batch_obj = stock.batch_number
                        if batch_obj:
                            new_batch.append({"id": None, "value":batch_obj.id,"label" : batch_obj.batch_number_name,
                                        "qty" : str(stock.current_stock or 0),"returnQty":None, 'is_stock_reduce': False})
            
            return new_batch

        def get_new_serial(master_id, store_id):
            new_serial = []
            
            stocks = ItemStock.objects.filter(part_number__id=master_id, store__id= store_id)
            if stocks:
                for stock in stocks:
                    if stock.current_stock and stock.serial_number.exists():
                        
                        new_serial.extend(
                            { "value":serial_data.id,"label" : serial_data.serial_number,}  for serial_data in stock.serial_number.all()
                        )
            # print(new_serial)
            return new_serial


        # Helper to serialize item details
        def serialize_item(item, index):
            try:
                sales_order_item = item.sales_order_item_detail
                item_master = item.sales_order_item_detail.itemmaster
                already_exists_id = []
                batch_obj = []
                store = item.store
                if  not item_master.item_combo_bool:
                    for batch in item.salesorder_2_retunbatch_set.all():
                        batch_ = batch.batch 
                         
                        already_exists_id.append(batch_.id)
                        batch_obj.append({"id": batch.id, "value":batch_.id,"label" : batch_.batch_number_name,
                                "qty" : fetch_batch_stock(item_master.id, batch_.id, store.id),"returnQty":str(batch.qty), 'is_stock_reduce': batch.is_stock_reduce})
                     
                    batch_obj.extend(get_new_batchs(item_master.id, store.id, already_exists_id))
                    

                
                return {
                    "salesOrderItemDetail": {
                        "id": sales_order_item.id,
                        "description": sales_order_item.description,
                        "cgst": str(sales_order_item.cgst) if sales_order_item.cgst else None,
                        "igst": str(sales_order_item.igst) if sales_order_item.igst else None,
                        "sgst": str(sales_order_item.sgst) if sales_order_item.sgst else None,
                        "cess": str(sales_order_item.cess) if sales_order_item.cess else None,
                        "uom": {"id": sales_order_item.uom.id, "name": sales_order_item.uom.name} if sales_order_item.uom else None,
                        "hsn": {"id": sales_order_item.hsn.id, "hsnCode": sales_order_item.hsn.hsn_code} if sales_order_item.hsn else None,
                        "tax": str(sales_order_item.tax),
                    },
                    "partName": {"value": item_master.id, "label": item_master.item_name},
                    "partCode": {"value": item_master.id, "label": item_master.item_part_code},
                    "qty": str(item.qty),
                    "discountPercentage": str(sales_order_item.discount_percentage) if sales_order_item.discount_percentage else None,
                    "finalValue": str(sales_order_item.final_value) if sales_order_item.final_value else None, 
                    "rate": str(sales_order_item.after_discount_value_for_per_item) if sales_order_item.after_discount_value_for_per_item else str(sales_order_item.rate),
                    "amount": str(item.amount),
                    "is_have_draft": str(sales_order_item.is_have_draft) if sales_order_item.is_have_draft   else None,
                    "dcSubmitCount": str(sales_order_item.dc_submit_count) if sales_order_item.dc_submit_count else None,
                    "itemmasterId": item_master.id,
                    "isSerial": item_master.serial,
                    "isBatch": item_master.batch_number,
                    "itemCombo": sales_order_item.item_combo,
                    "invoiceSubmitCount":str(item.invoice_submit_count) if item.invoice_submit_count else None,
                    "itemComboItemDetails": [serialize_combo(c,idx) for idx,c in enumerate(item.item_combo_itemdetails.all())],
                    "stockReduce": item.stock_reduce,
                    "batch": batch_obj,
                    "serial": [{ "value": serial.id, "label" : serial.serial_number} for serial in item.serial.all() if serial],
                    "batchList": [],
                    "serialList": get_new_serial(item_master.id, store.id) if item_master.serial else [],
                    "store": {"value": item.store.id, "label":item.store.store_name} if item.store else None,
                    "id": item.id,
                    "createdBy": item.created_by.username,
                    "modifiedBy": item.modified_by.username,
                    "index": index + 1,
                }
            except Exception as e:
                print("e item", e)
        

        sales_dc = {
                "id":queryset.id if queryset.id else None,
                "dc_no":queryset.dc_no.linked_model_id,
                "dc_date":str(queryset.dc_date),
                "leadId": str(queryset.sales_order.lead_no.id),
                "salesPerson": {"id": queryset.sales_order.sales_person.id, "name": queryset.sales_order.sales_person.username} if queryset.sales_order.sales_person.id else None,
                "department": {"id": queryset.sales_order.department.id, "name": queryset.sales_order.department.name} if queryset.sales_order.department.id else None,
                "salesOrderNo": queryset.sales_order.sales_order_no.linked_model_id,
                "salesOrderDate": str(queryset.sales_order.sales_order_date),
                "customerPoNo": queryset.sales_order.customer_po_no,
                "salesOrderId": str(queryset.sales_order.id),
                "consigneeId": queryset.sales_order.consignee.id if queryset.sales_order.consignee.id else None,
                "consignee":{
                    "id":queryset.sales_order.consignee.id,
                    "companyName": queryset.sales_order.consignee.company_name
                } if queryset.sales_order.consignee.id else None,
                "consigneeNumber": {
                    "id":queryset.sales_order.consignee.id,
                    "supplierNo": queryset.sales_order.consignee.supplier_no
                } if queryset.sales_order.consignee.id else None, 
                "consigneeAddress": serialize_address(queryset.sales_order.consignee_address),
                "consigneeContactPerson": {
                    "id": queryset.sales_order.consignee_contact_person.id,
                    "name": queryset.sales_order.consignee_contact_person.contact_person_name,
                } if queryset.sales_order.consignee_contact_person.id else None,
                "consigneeContactPerson": {
                    "id": queryset.sales_order.consignee_contact_person.id,
                    "contactPersonName": queryset.sales_order.consignee_contact_person.contact_person_name,
                    "email": queryset.sales_order.consignee_contact_person.email,
                    "phoneNumber": queryset.sales_order.consignee_contact_person.phone_number,
                    "whatsappNo":queryset.sales_order.consignee_contact_person.whatsapp_no,
                } if queryset.sales_order.consignee_contact_person.id  else None,
                "consigneeGstinType": queryset.sales_order.consignee_gstin_type,
                "consigneeGstin":queryset.sales_order.consignee_gstin,
                "consigneePlaceOfSupply": queryset.sales_order.consignee_place_of_supply,
                "consigneeState": queryset.sales_order.consignee_address.state,
                "allStockReduce": queryset.all_stock_reduce,
                "currency": {
                    "id": queryset.sales_order.currency.id,
                    "symbol":queryset.sales_order.currency.Currency.currency_symbol,
                    "rate": str(queryset.sales_order.currency.rate),
                    "Currency": queryset.sales_order.currency.Currency.name if queryset.sales_order.currency.Currency else None
                } if queryset.sales_order.currency.id else None,
                "store":{"value":queryset.comman_store.id,"label":queryset.comman_store.store_name} if queryset.comman_store and  queryset.comman_store.id else None,
                "termsConditions":{
                    "id":queryset.terms_conditions.id,
                    "name":queryset.terms_conditions.name
                } if queryset.terms_conditions.id else None,
                "termsConditionsText":queryset.terms_conditions_text,
                "updatedAt":str(queryset.updated_at) if queryset.updated_at else str(queryset.created_at),
                "createdBy":{
                    "id":queryset.created_by.id,
                    "username":queryset.created_by.username
                } if queryset.created_by.id else None,
                "status":queryset.status.name,
                "roundOffMethod":queryset.round_off_method if queryset.round_off_method else None,
                "salesOrderItemDetail": [serialize_item(item, idx) for idx, item in enumerate(queryset.item_details.all())],
                "transport":queryset.transport or None,
                "docketDate":str(queryset.docket_date) if queryset.docket_date else None,
                "docketNo":queryset.docket_no or None,
                "driverName":queryset.driver_name or None,
                "vehicleNo":queryset.vehicle_no or None,
                "otherModel":queryset.other_model or None,
                "eWayBill":queryset.e_way_bill or None,
                "eWayBillDate":str(queryset.e_way_bill_date) if queryset.e_way_bill_date else None
            }
        

        print("sales_dc",sales_dc)
        return SalesInitialFetch(items=sales_dc)

    def resolve_multi_dc_invoice(self, info, buyer=None, consignee=None, sales_person=[], department=None):
        try:
            filter_kwargs = {}
            if buyer:
                filter_kwargs['buyer__id'] = buyer
            if consignee:
                filter_kwargs['consignee__id'] = consignee
            if sales_person:
                filter_kwargs['sales_person__id__in'] = sales_person
            if department:
                filter_kwargs['department__id'] = department

            queryset = SalesOrder_2.objects.filter(**filter_kwargs).order_by('-id')
            
            
            sales_list = []
            for index, sales in enumerate(queryset):
                print(sales.id)
                current_sales = {
                    "id": sales.id,
                    "index": index,
                    "label": sales.sales_order_no.linked_model_id,
                    "isSelected":  False,
                    "isSalesInVoiceForSales":  False,
                    "dcData" : []
                }
                # print("current_sales", current_sales)
                dc_index = 0
                dc_list = []
                for dc in sales.delivery_challans.all():
                    if dc.status.name in  ["Submit", "Dispatch"]:
                        dc_index+=1
                        dc_item_list = []
                        dc_data = {
                            "id": dc.id,
                            "dcIndex": dc_index,
                            "label": dc.dc_no.linked_model_id,
                            "isSelected": False,
                            "isSalesInVoiceForDc": False
                        }
                        
                        for item in dc.item_details.all():
                            allowed_qty =  (item.qty or 0)- (item.invoice_submit_count or 0)
                            if allowed_qty:
                                dc_item_list.append({
                                    "id": item.id,
                                    "qty": str(allowed_qty),
                                    "amount": str(item.amount),
                                    "invoiceSubmitCount": str(item.return_draft_count) if item.return_draft_count else None,
                                    "salesOrderItemDetail": {
                                        "afterDiscountValueForPerItem": str(item.sales_order_item_detail.after_discount_value_for_per_item),
                                        "rate": str(item.sales_order_item_detail.after_discount_value_for_per_item) if item.sales_order_item_detail.after_discount_value_for_per_item else str(item.sales_order_item_detail.rate),
                                        "qty": str(item.sales_order_item_detail.qty),
                                        "itemmaster": {
                                            "itemPartCode": item.sales_order_item_detail.itemmaster.item_part_code,
                                            "itemName": item.sales_order_item_detail.itemmaster.item_name,
                                        }
                                    }
                                })
                        if dc_item_list:
                            dc_data['itemDetails'] = dc_item_list
                            dc_list.append(dc_data) 
                
                if dc_list:
                    current_sales["dcData"] = dc_list
                    sales_list.append({"salesOrder": current_sales})
 
            return SalesInitialFetch(items = sales_list)
        except Exception as e:
            print(e)
            return None
        
    @permission_required(models=["Sales Invoice"],action="MultiDC")
    def resolve_combine_multi_dc_to_sales_invoice_type(self, info, dc_ids):
        Invoice_data = {
            # "sales_invoice": [],
            "Department": {"value": "", "label": ""},
            "salesOrderNo":[],
            "dcNo":[],
            "sales_dc": [],
            "salesPerson": "",
            "dueDate": "",
            "Period": "",
            "payment_terms": "",
            "po_no": "",
            "po_date": "",
            "buyer_name": "",
            "buyer_code": "",
            "buyer_address": "",
            "buyer_contact_person": "",
            "buyer_mobile": "",
            "buyer_email": "",
            "buyer_gstin_type": "",
            "buyer_gstin": "",
            "buyer_state": "",
            "buyer_place_of_supply": "",
            "consignee_name": "",
            "consignee_code": "",
            "consignee_address": "",
            "consignee_contact_person": "",
            "consignee_mobile": "",
            "consignee_email": "",
            "consignee_gstin_type": "",
            "consignee_gstin": "",
            "consignee_state": "",
            "consignee_place_of_supply": "",
            "item_details_list": [],
            "other_charges_befor_tax": []
        }

        try:
            dc_instances = SalesOrder_2_DeliveryChallan.objects.filter(id__in=dc_ids)
            
            if not dc_instances.exists():
                return [combineMultiDcToSalesInvoice_Type(sales_invoice=f"Error: No Dc Founded.")] 

            # Check: If any DC already has an invoice, stop immediately
            for dc in dc_instances:
                if dc.sales_invoice:
                    return [combineMultiDcToSalesInvoice_Type(sales_invoice=f"Error: DC {dc.dc_no.linked_model_id} already exists in an invoice.")] 

            # All DCs are clean – continue
            for dc_instance in dc_instances:
                salesOrder = dc_instance.sales_order
                Invoice_data["sales_dc"].append(dc_instance.id)
                # Invoice_data["sales_invoice"].append(dc_instance.sales_invoice.id if dc_instance.sales_invoice else None)
                if not salesOrder:
                    return f"Sales Order missing for {dc_instance.dc_no.linked_model_id}"
                Invoice_data["salesOrderNo"].append(salesOrder.sales_order_no.linked_model_id)
                Invoice_data["dcNo"].append(dc_instance.dc_no.linked_model_id)
                # Set Department once
                if not Invoice_data["Department"]["value"]:
                    Invoice_data["Department"] = {
                        "value": salesOrder.department.id,
                        "label": salesOrder.department.name,
                    }

                Invoice_data["salesPerson"] = salesOrder.sales_person.username

                def append_field(field, value):
                    if Invoice_data[field]:
                        Invoice_data[field] += ", " + str(value)
                    else:
                        Invoice_data[field] = str(value)

                append_field("dueDate", salesOrder.due_date)
                append_field("Period", salesOrder.credit_period)
                append_field("payment_terms", salesOrder.payment_terms)
                append_field("po_no", salesOrder.customer_po_no)
                append_field("po_date", salesOrder.customer_po_date)

                # Only set buyer & consignee once
                if not Invoice_data["buyer_code"]:
                    Invoice_data["buyer_name"] ={"value" : str(salesOrder.buyer.id),"label":str(salesOrder.buyer.company_name)} 
                    Invoice_data["buyer_code"] ={"value" : str(salesOrder.buyer.id),"label":str(salesOrder.buyer.supplier_no)}
                    Invoice_data["buyer_address"] = {
                        "fullAddredd":{
                            "addressLine1": salesOrder.buyer_address.address_line_1,
                            "addressLine2": salesOrder.buyer_address.address_line_2,
                            "city": salesOrder.buyer_address.city,
                            "country": salesOrder.buyer_address.country,
                            "pincode": salesOrder.buyer_address.pincode,
                            "state": salesOrder.buyer_address.state,
                            "id":salesOrder.buyer_address.id,
                            "addressType":salesOrder.buyer_address.address_type,
                        }
                    }
                    Invoice_data["buyerContactPerson"] ={
                        "mobile":salesOrder.buyer_contact_person.phone_number,
                        "whatsappNo":salesOrder.buyer_contact_person.whatsapp_no,
                        "Email":salesOrder.buyer_contact_person.email,
                        "value":salesOrder.buyer_contact_person.id,
                        "label":salesOrder.buyer_contact_person.contact_person_name
                    }
                    Invoice_data["buyer_gstin_type"] = salesOrder.buyer_gstin_type
                    Invoice_data["buyer_gstin"] = salesOrder.buyer_gstin
                    Invoice_data["buyer_state"] = salesOrder.buyer_state
                    Invoice_data["buyer_place_of_supply"] = salesOrder.buyer_place_of_supply

                if not Invoice_data["consignee_name"]:
                    Invoice_data["consignee_name"] = salesOrder.consignee.company_name
                    Invoice_data["consignee_code"] = salesOrder.consignee.supplier_no
                    Invoice_data["consignee_address"] = {
                        "fullAddredd":{
                            "addressLine1": salesOrder.consignee_address.address_line_1,
                            "addressLine2": salesOrder.consignee_address.address_line_2,
                            "city": salesOrder.consignee_address.city,
                            "country": salesOrder.consignee_address.country,
                            "pincode": salesOrder.consignee_address.pincode,
                            "state": salesOrder.consignee_address.state
                        }
                    }
                    Invoice_data["consigneeContactPerson"] ={
                        "mobile":salesOrder.consignee_contact_person.phone_number,
                        "whatsappNo":salesOrder.consignee_contact_person.whatsapp_no,
                        "Email":salesOrder.consignee_contact_person.email,
                        "value":salesOrder.consignee_contact_person.contact_person_name,
                        "label":salesOrder.consignee_contact_person.contact_person_name
                    }
                    Invoice_data["consignee_gstin_type"] = salesOrder.consignee_gstin_type
                    Invoice_data["consignee_gstin"] = salesOrder.consignee_gstin
                    Invoice_data["consignee_state"] = salesOrder.consignee_state
                    Invoice_data["consignee_place_of_supply"] = salesOrder.consignee_place_of_supply

                for item in dc_instance.item_details.all():
                        so_item = item.sales_order_item_detail
                        itemmaster = so_item.itemmaster if so_item else None
                        uom = so_item.uom if so_item else None
                        hsn = so_item.hsn if so_item else None

                        # Debug check
                        if not all([itemmaster, uom, hsn]):
                            print(f"Missing nested data for item ID: {item.id}")
                            continue  # Skip this item if essential parts are missing
                        item_combo_itemdetails = []
                        if item and so_item.item_combo:
                            try:
                                for item_combo_detail in item.item_combo_itemdetails.all():
                                    # Extract values
                                    qty = item_combo_detail.qty
                                    rate = item_combo_detail.item_combo.rate
                                    after_discount = item_combo_detail.item_combo.after_discount_value_for_per_item
                                    # Perform calculation
                                    try:
                                        qty_val = Decimal(qty)
                                        rate_val = Decimal(rate)
                                        after_discount_val = Decimal(after_discount)
                                        use_after_discount = after_discount_val > 0
                                    except (ValueError, TypeError):
                                        qty_val = rate_val = after_discount_val = 0
                                        use_after_discount = False

                                    if use_after_discount:
                                        amount = qty_val * after_discount_val
                                    else:
                                        amount = qty_val * rate_val

                                    item_combo_itemdetails.append({
                                        "id": str(item_combo_detail.id),
                                        "qty": str(item_combo_detail.qty),
                                        "amount": str(amount),
                                        "afterDiscountValueForPerItem": str(item_combo_detail.item_combo.after_discount_value_for_per_item),
                                        "rate": str(item_combo_detail.item_combo.rate),
                                        "display": str(item_combo_detail.item_combo.display),
                                        "itemmaster": {
                                            "id": str(item_combo_detail.item_combo.itemmaster.id),
                                            "itemName": str(item_combo_detail.item_combo.itemmaster.item_name),
                                            "itemPartCode": str(item_combo_detail.item_combo.itemmaster.item_part_code),
                                        }
                                    })
                            except Exception as e:
                                print("error processing item combo",e)
                        try:
                            Invoice_data["item_details_list"].append({
                                "id": item.id,
                                "qty":str(item.qty) if item.qty else None,
                                "amount": str(item.amount) if item.amount else None,
                                "salesOrderItemDetail": {
                                    "partCode": {
                                        "value": itemmaster.item_part_code,
                                        "label": itemmaster.item_part_code
                                    },
                                    "igst":str(so_item.igst) if so_item.igst else None,
                                    "cgst":str(so_item.cgst) if so_item.cgst else None,
                                    "sgst":str(so_item.sgst) if so_item.sgst else None,
                                    "partName": {
                                        "value": itemmaster.item_name,
                                        "label": itemmaster.item_name
                                    },
                                    "description":itemmaster.description,
                                    "uom": {
                                        "id": uom.name,
                                        "name": uom.name
                                    },
                                    "hsn": {
                                        "id": hsn.hsn_code,
                                        "hsnCode": hsn.hsn_code
                                    },
                                    "tax": str(so_item.tax) if so_item.tax else None,
                                    "afterDiscountValueForPerItem":str(so_item.after_discount_value_for_per_item) if so_item.after_discount_value_for_per_item else None,
                                    "rate": str(so_item.rate),
                                    "itemCombo":str(so_item.item_combo),
                                    "itemComboItemdetails": item_combo_itemdetails if so_item.item_combo else []
                                }
                            })
                        except Exception as e:
                            print(f"Error processing item ID {item.id}: {e}")


                for charge in salesOrder.other_income_charge.all():
                    total_amount_of_child = (
                        SalesOrder_2_otherIncomeCharges.objects
                        .filter(parent=charge.id)
                        .aggregate(total=Sum('amount'))['total'] or 0
                    )

                    if total_amount_of_child == 0:
                        remaining_amount = charge.amount

                        Invoice_data["other_charges_befor_tax"].append({
                            "otherIncomeChargesId":{
                                "label": str(charge.other_income_charges_id.name),
                                "value": str(charge.other_income_charges_id.id),
                                "hsnCode": str(charge.hsn_code) if hasattr(charge, 'hsn_code') else None,
                                "hsn": str(charge.hsn) if hasattr(charge, 'hsn') else None
                            },
                            "amount": str(remaining_amount),
                            "discountValue": str(charge.discount_value) if charge.discount_value else None,
                            "afterDiscountValue": str(charge.after_discount_value) if charge.after_discount_value else None,
                            "igst": str(charge.igst) if charge.igst else None,
                            "sgst": str(charge.sgst) if charge.sgst else None,
                            "cgst": str(charge.cgst) if charge.cgst else None,
                            "tax": str(charge.tax),
                            "parent": str(charge.id) if charge.id else None,
                        })


            return [combineMultiDcToSalesInvoice_Type(sales_invoice=Invoice_data)]

        except Exception as e: 
            return f"Error: {str(e)}"
    
    # @permission_required(models=["Sales Invoice"],action="MultiDC")
    def resolve_combine_multi_sales_invoice(self, info, dc_ids):
        Invoice_data = {
            # "sales_invoice": [],
            "Department": {"value": "", "label": ""},
            "salesOrderNo":[],
            "dcNo":[],
            "sales_dc": [],
            "salesPerson": "",
            "dueDate": "",
            "Period": "",
            "payment_terms": "",
            "po_no": "",
            "po_date": "",
            "buyer_name": "",
            "buyer_code": "",
            "buyer_address": "",
            "buyer_contact_person": "",
            "buyer_mobile": "",
            "buyer_email": "",
            "buyer_gstin_type": "",
            "buyer_gstin": "",
            "buyer_state": "",
            "buyer_place_of_supply": "",
            "buyer_pan_no":"",
            "tds_enable":"",
            "tcs_enable":"",
            "gst_nature_type":"",
            "nature_of_transaction":"",
            "consignee_name": "",
            "consignee_code": "",
            "consignee_address": "",
            "consignee_contact_person": "",
            "consignee_mobile": "",
            "consignee_email": "",
            "consignee_gstin_type": "",
            "consignee_gstin": "",
            "consignee_state": "",
            "consignee_place_of_supply": "",
            "item_details_list": [],
            "other_charges": [],
            "igst":"",
            "sgst":"",
            "cgst":"",
            "cess":"",
            "currency":"",
            "overallDiscountPercentage":"",
            "discountFinalTotal":"",
            "overallDiscountValue":"",
        }
        already_exist_sales_order_id = []
        try:
            dc_instances = SalesOrder_2_DeliveryChallan.objects.filter(id__in=dc_ids)
            
            if not dc_instances.exists():
                return combineMultiDcToSalesInvoice_Type(sales_invoice=f"Error: No Dc Founded.")

            # # Check: If any DC already has an invoice, stop immediately
            # for dc in dc_instances:
            #     if dc.sales_invoice:
            #         return [combineMultiDcToSalesInvoice_Type(sales_invoice=f"Error: DC {dc.dc_no.linked_model_id} already exists in an invoice.")] 

            # All DCs are clean – continue
            for dc_instance in dc_instances:
                salesOrder = dc_instance.sales_order
                Invoice_data["sales_dc"].append(dc_instance.id)
                
                if not salesOrder:
                    return f"Sales Order missing for {dc_instance.dc_no.linked_model_id}"
                Invoice_data["salesOrderNo"].append(salesOrder.sales_order_no.linked_model_id)
                Invoice_data["dcNo"].append(dc_instance.dc_no.linked_model_id)
                # Set Department once
                if not Invoice_data["Department"]["value"]:
                    Invoice_data["Department"] = {
                        "value": salesOrder.department.id,
                        "label": salesOrder.department.name,
                    }

                Invoice_data["salesPerson"] = {
                    "label":salesOrder.sales_person.username,
                    "value":salesOrder.sales_person.id
                }

                def append_field(field, value):
                    if Invoice_data[field]:
                        Invoice_data[field] += ", " + str(value)
                    else:
                        Invoice_data[field] = str(value)

                append_field("dueDate", salesOrder.due_date)
                append_field("Period", salesOrder.credit_period)
                append_field("payment_terms", salesOrder.payment_terms)
                append_field("po_no", salesOrder.customer_po_no)
                append_field("po_date", salesOrder.customer_po_date)
                
                if not Invoice_data["currency"]:
                    Invoice_data["currency"] = {
                        "name":str(salesOrder.currency.Currency.name),
                        "rate":str(salesOrder.exchange_rate or 1),
                        "currencySymbol":str(salesOrder.currency.Currency.currency_symbol),
                    }

                # Only set buyer & consignee once
                if not Invoice_data["buyer_code"]:
                    Invoice_data["buyer_name"] ={"value" : str(salesOrder.buyer.id),"label":str(salesOrder.buyer.company_name)} 
                    Invoice_data["buyer_code"] ={"value" : str(salesOrder.buyer.id),"label":str(salesOrder.buyer.supplier_no)}
                    Invoice_data["buyer_address"] = {
                        "fullAddredd":{
                            "addressLine1": salesOrder.buyer_address.address_line_1,
                            "addressLine2": salesOrder.buyer_address.address_line_2,
                            "city": salesOrder.buyer_address.city,
                            "country": salesOrder.buyer_address.country,
                            "pincode": salesOrder.buyer_address.pincode,
                            "state": salesOrder.buyer_address.state,
                            "id":salesOrder.buyer_address.id,
                            "addressType":salesOrder.buyer_address.address_type,
                        }
                    }
                    Invoice_data["buyerContactPerson"] ={
                        "mobile":salesOrder.buyer_contact_person.phone_number,
                        "whatsappNo":salesOrder.buyer_contact_person.whatsapp_no,
                        "Email":salesOrder.buyer_contact_person.email,
                        "value":salesOrder.buyer_contact_person.id,
                        "label":salesOrder.buyer_contact_person.contact_person_name
                    }
                    Invoice_data["buyer_gstin_type"] = salesOrder.buyer_gstin_type
                    Invoice_data["buyer_gstin"] = salesOrder.buyer_gstin
                    Invoice_data["buyer_state"] = salesOrder.buyer_state
                    Invoice_data["buyer_place_of_supply"] = salesOrder.buyer_place_of_supply
                    Invoice_data["tds_enable"] = salesOrder.buyer.tds
                    Invoice_data["tcs_enable"] = salesOrder.buyer.tcs
                    Invoice_data["buyer_pan_no"] = salesOrder.buyer.pan_no if salesOrder.buyer.pan_no else ""

                if not Invoice_data["consignee_name"]:
                    Invoice_data["consignee_name"] = {"value" : str(salesOrder.consignee.id),"label":str(salesOrder.consignee.company_name)} 
                    Invoice_data["consignee_code"] = {"value" : str(salesOrder.consignee.id),"label":str(salesOrder.consignee.supplier_no)}
                    Invoice_data["consignee_address"] = {
                        "fullAddredd":{
                            "addressLine1": salesOrder.consignee_address.address_line_1,
                            "addressLine2": salesOrder.consignee_address.address_line_2,
                            "city": salesOrder.consignee_address.city,
                            "country": salesOrder.consignee_address.country,
                            "pincode": salesOrder.consignee_address.pincode,
                            "id":salesOrder.consignee_address.id,
                            "state": salesOrder.consignee_address.state
                        }
                    }
                    Invoice_data["consigneeContactPerson"] ={
                        "mobile":salesOrder.consignee_contact_person.phone_number,
                        "whatsappNo":salesOrder.consignee_contact_person.whatsapp_no,
                        "Email":salesOrder.consignee_contact_person.email,
                        "value":salesOrder.consignee_contact_person.id,
                        "label":salesOrder.consignee_contact_person.contact_person_name
                    }
                    Invoice_data["consignee_gstin_type"] = salesOrder.consignee_gstin_type
                    Invoice_data["consignee_gstin"] = salesOrder.consignee_gstin
                    Invoice_data["consignee_state"] = salesOrder.consignee_state
                    Invoice_data["consignee_place_of_supply"] = salesOrder.consignee_place_of_supply

                    Invoice_data["gst_nature_type"] = salesOrder.gst_nature_type if salesOrder.gst_nature_type else ""
                    Invoice_data["nature_of_transaction"] = salesOrder.gst_nature_transaction.nature_of_transaction if salesOrder.gst_nature_transaction.nature_of_transaction else ""
                    Invoice_data["igst"] = salesOrder.igst
                    Invoice_data["sgst"] = salesOrder.sgst
                    Invoice_data["cgst"] = salesOrder.cgst
                    Invoice_data["cess"] = salesOrder.cess
                    Invoice_data['overallDiscountPercentage'] = str(salesOrder.overall_discount_percentage)  if salesOrder.overall_discount_percentage else None
                    Invoice_data['overallDiscountValue'] = str(salesOrder.overall_discount_value)  if salesOrder.overall_discount_value else None
                    Invoice_data['discountFinalTotal'] = str(salesOrder.discount_final_total)  if salesOrder.discount_final_total else None
           
                item_dict = {}
                
                for item in dc_instance.item_details.all():
                    so_item = item.sales_order_item_detail
                    if not so_item:
                        continue
                    
                    itemmaster = so_item.itemmaster
                    uom = so_item.uom
                    hsn = so_item.hsn
                    
                    if not all([itemmaster, uom, hsn]):
                        print(f"Missing nested data for item ID: {item.id}")
                        continue 
                    # ✅ Adjust qty using invoice_submit_count
                    actual_qty = Decimal(item.qty or 0)
                    invoice_qty = Decimal(item.invoice_submit_count or 0)
                    returned_qty = Decimal(item.return_submit_count or 0)
                    print(actual_qty , invoice_qty , returned_qty)
                    remaining_qty = actual_qty - invoice_qty - returned_qty
                    print("remaining_qty", remaining_qty)
                    if remaining_qty <= 0:
                        continue  # Skip fully invoiced items

                    # ✅ Recalculate amount
                    per_unit_amount = Decimal(item.amount) / actual_qty if actual_qty else 0
                    recalculated_amount = round(remaining_qty * per_unit_amount, 3)

                    item_combo_itemdetails = []
                    print(item, so_item.item_combo)
                    if item and so_item.item_combo:
                        try:
                            for item_combo_detail in item.item_combo_itemdetails.all():
                                try:
                                    total_qty = Decimal(item_combo_detail.qty or 0)
                                    invoive_qty = Decimal(item_combo_detail.invoice_submit_count or 0)
                                    return_qty = Decimal(item_combo_detail.return_submit_count or 0)
                                    remaining_qty = total_qty - invoive_qty - return_qty

                                    if remaining_qty <= 0:
                                        continue  # Skip fully invoiced combos

                                    rate = Decimal(item_combo_detail.item_combo.rate or 0)
                                    # print("rate", rate)
                                    after_discount = Decimal(item_combo_detail.item_combo.after_discount_value_for_per_item or 0)
                                    use_after_discount = after_discount > 0
                                except (ValueError, TypeError):
                                    remaining_qty = rate = after_discount = 0
                                    use_after_discount = False

                                effective_rate = after_discount if use_after_discount else rate
                                recalculated_combo_amount = round(remaining_qty * effective_rate, 3)

                                item_combo_itemdetails.append({
                                    "itemCombo": str(item_combo_detail.id),
                                    "qty": str(remaining_qty),
                                    "amount": str(recalculated_combo_amount),
                                    "afterDiscountValueForPerItem": str(after_discount),
                                    "rate": str(after_discount) if str(after_discount) else str(rate),
                                    "display": str(item_combo_detail.item_combo.display),
                                    "itemmaster": {
                                        "id": str(item_combo_detail.item_combo.itemmaster.id),
                                        "itemName": str(item_combo_detail.item_combo.itemmaster.item_name),
                                        "itemPartCode": str(item_combo_detail.item_combo.itemmaster.item_part_code),
                                    },
                                    "uom": {
                                        "name": str(item_combo_detail.item_combo.uom.name),
                                        "id": str(item_combo_detail.item_combo.uom.name)
                                    } if item_combo_detail.item_combo.uom else "",
                                })
                        except Exception as e:
                            return GraphQLError(f"error processing item combo : {e}")
                            
                    
                 
                    try:
                        
                        data = item_dict.setdefault(so_item.id, {
                            
                            "item": item.id,
                            "qty": str(remaining_qty),
                            "amount": str(recalculated_amount),
                            "salesOrderItemDetail": {
                                "partCode": {
                                    "value": itemmaster.id,
                                    "label": itemmaster.item_part_code
                                },
                                "partName": {
                                    "value": itemmaster.id,
                                    "label": itemmaster.item_name
                                },
                                "igst": str(so_item.igst) if so_item.igst else None,
                                "cgst": str(so_item.cgst) if so_item.cgst else None,
                                "sgst": str(so_item.sgst) if so_item.sgst else None,
                                "cess": str(so_item.cess) if so_item.cess else None,
                                "description": itemmaster.description,
                                "uom": {
                                    "id": uom.id,
                                    "name": uom.name
                                },
                                "hsn": {
                                    "id": hsn.hsn_code,
                                    "hsnCode": hsn.hsn_code
                                },
                                "tdsLink": {
                                    "percentOtherWithPan": str(itemmaster.tds_link.percent_other_with_pan) if itemmaster.tds_link and itemmaster.tds_link.percent_other_with_pan is not None else "",
                                    "percentIndividualWithPan": str(itemmaster.tds_link.percent_individual_with_pan) if itemmaster.tds_link and itemmaster.tds_link.percent_individual_with_pan is not None else "",
                                },
                                "tcsLink": {
                                    "percentIndividualWithPan": str(itemmaster.tcs_link.percent_individual_with_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_individual_with_pan is not None else "",
                                    "percentOtherWithPan": str(itemmaster.tcs_link.percent_other_with_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_other_with_pan is not None else "",
                                    "percentOtherWithoutPan": str(itemmaster.tcs_link.percent_other_without_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_other_without_pan is not None else "",
                                },
                                "tax": str(so_item.tax),
                                "discountPercentage": str(so_item.discount_percentage) if so_item.discount_percentage else None,
                                "discountValue": str(so_item.discount_value) if so_item.discount_value else None,
                                "finalValue": str(so_item.final_value) if so_item.final_value else None,
                                "afterDiscountValueForPerItem": str(so_item.after_discount_value_for_per_item) if so_item.after_discount_value_for_per_item else None,
                                "rate": str(so_item.rate),
                                "itemCombo": str(so_item.item_combo),
                                "itemComboItemdetails":item_combo_itemdetails
                            }
                        })
                        print(item_combo_itemdetails)
                        # combo_dict = {c["itemCombo"]: c for c in data["salesOrderItemDetail"]["itemComboItemdetails"]}
                        # for new_combo in item_combo_itemdetails:
                        #     combo_id = new_combo["itemCombo"]
                        #     if combo_id in combo_dict:
                        #         combo_dict[combo_id]["qty"] = str(Decimal(combo_dict[combo_id]["qty"]) + Decimal(new_combo["qty"]))
                        #         combo_dict[combo_id]["amount"] = str(Decimal(combo_dict[combo_id]["amount"]) + Decimal(new_combo["amount"]))
                        #     else:
                        #         combo_dict[combo_id] = new_combo
                        
                            
                        #     data["salesOrderItemDetail"]["itemComboItemdetails"] = list(combo_dict.values())


                        # data['qty'] = str(Decimal(data['qty']) + Decimal(remaining_qty))
                        # data['amount'] = str(Decimal(data['amount']) + Decimal(recalculated_amount))
                
                        Invoice_data["item_details_list"].append((data))
                    except Exception as e:
                        return GraphQLError(f"Error processing item ID {item.id}: {e}")
                
                
                if salesOrder.id not in already_exist_sales_order_id:
                    already_exist_sales_order_id.append(salesOrder.id)
                    for charge in salesOrder.other_income_charge.all():
                        
                        if  not SalesOrder_2_otherIncomeCharges.objects.filter(parent=charge.id).exists():
                            
                            remaining_amount = charge.amount 
                            Invoice_data["other_charges"].append({
                                "otherIncomeChargesId":{
                                    "label": str(charge.other_income_charges_id.name),
                                    "value": str(charge.other_income_charges_id.id),
                                    "hsn": {
                                        "id":str(charge.other_income_charges_id.hsn.id),
                                        "hsnCode":str(charge.other_income_charges_id.hsn.hsn_code)
                                    },
                                    
                                },
                                "amount": str(remaining_amount),
                                "discountValue": str(charge.discount_value) if charge.discount_value else None,
                                "afterDiscountValue": str(charge.after_discount_value) if charge.after_discount_value else None,
                                "igst": str(charge.igst) if charge.igst else None,
                                "sgst": str(charge.sgst) if charge.sgst else None,
                                "cgst": str(charge.cgst) if charge.cgst else None,
                                "cess": str(charge.cess) if charge.cess else None,
                                "tax": str(charge.tax),
                                "parent": str(charge.id) if charge.id else None,
                            }) 
            
            return combineMultiDcToSalesInvoice_Type(sales_invoice=Invoice_data)

        except Exception as e:
            return f"Error: {str(e)}"
    
    @permission_required(models=["Receipt Voucher"])
    def resolve_sales_return_initial_fetch(self, info, dc_item_ids, sales_invoice_item_ids, sales_id):
        try:
            itemdetails = []
            sales_dc_intance = set()
            sales_invoice_intances = set()
            if not sales_id:
                return GraphQLError("Sales order is required.")
            
            sales_order = SalesOrder_2.objects.filter(id=sales_id).first()

            if not sales_order:
                return GraphQLError("Sales order is not found.")
            
            
            def get_dc_item_combo(dc_item):
                dc_item_combo = []
                for index,dc_combo in  enumerate(dc_item.item_combo_itemdetails.all()):
                    dc_combo_rate = dc_combo.item_combo.after_discount_value_for_per_item  if dc_combo.item_combo.after_discount_value_for_per_item else  dc_combo.item_combo.rate 
                    
                    dc_combo_batch_serial_list = []
                    dc_combo_serial_list = []
                    
                    if dc_combo.item_combo.itemmaster.batch_number:
                        dc_combo_batchs = dc_combo.salesorder_2_retunbatch_set.all()
                        for dc_combo_batch in dc_combo_batchs:
                            if dc_combo_batch.is_stock_reduce:
                                batch_combo_allowed_qty = dc_combo_batch.qty
                                total_qty = dc_combo_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                    ).aggregate(total=Sum('qty'))['total'] or 0
                                if total_qty:
                                    batch_combo_allowed_qty = (dc_combo_batch.qty or 0) - total_qty
                                if not batch_combo_allowed_qty:
                                    continue
                                batch_serial = {
                                    "value": dc_combo_batch.id,
                                    "label" : dc_combo_batch.batch.batch_number_name,
                                    "qty" :str(batch_combo_allowed_qty),
                                }
                                dc_combo_batch_serial_list.append(batch_serial)
                    
                    elif dc_combo.item_combo.itemmaster.serial:
                        dc_combo_serial_list.extend({"value":dc_serial.id, "label":dc_serial.serial_number}  for dc_serial in dc_combo.serial.all())
                    
                    allowed_qty = (dc_combo.qty or 0) - (dc_combo.return_submit_count or 0) - (dc_combo.invoice_submit_count or 0)
                    if not allowed_qty:
                        continue
                    
                    amount = allowed_qty*dc_combo_rate
                    
                    combo_data = {
                        "itemComboId":str(dc_combo.item_combo.id),
                        "itemMasterId":str(dc_combo.item_combo.itemmaster.id), 
                        "partCode":{"value": dc_combo.item_combo.itemmaster.id, "label":dc_combo.item_combo.itemmaster.item_part_code},
                        "partName":{"value": dc_combo.item_combo.itemmaster.id, "label":dc_combo.item_combo.itemmaster.item_name}, 
                        "isSerial":dc_combo.item_combo.itemmaster.serial,
                        "isBatch": dc_combo.item_combo.itemmaster.batch_number,
                        "isNoBatchSerial" :True if not dc_combo.item_combo.itemmaster.serial and not dc_combo.item_combo.itemmaster.batch_number else False,
                        "uom":  dc_combo.item_combo.uom.name,
                        "dc_item_combo" : dc_combo.id,
                        "sales_invoice_item_combo" :"",
                        "qty" :str(allowed_qty),
                        "batch": "",
                        "serial":"",
                        "batch_list": dc_combo_batch_serial_list,
                        "serial_list" : dc_combo_serial_list,
                        "display" : dc_combo.item_combo.display,
                        "rate" : str(dc_combo_rate),
                        "amount" :str(amount),
                        "store" : {"value":dc_combo.store.id,
                                        "label" :dc_combo.store.store_name} if dc_combo.store else None,
                        "index":index + 1
                    }
                    dc_item_combo.append(combo_data)
                return dc_item_combo

            def get_invoice_item_combo(sales_invoice_item):
                sales_invoice_combos = []
                "sales_invoice combo"
                
                for index,sales_invoice_combo in enumerate(sales_invoice_item.item_combo.all()):
                    
                    invoice_batch_serial = []
                    invoice_combo_serial = []
                    "sales dc combo"
                    dc_item_combo = sales_invoice_combo.item_combo
                    
                    if dc_item_combo.item_combo.itemmaster.batch_number:
                        
                        for combo_bach in dc_item_combo.salesorder_2_retunbatch_set.all():
                            if combo_bach.is_stock_reduce:
                                batch_allowed_qty= (combo_bach.qty or 0)
                                total_qty = combo_bach.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                ).aggregate(total=Sum('qty'))['total'] or 0
                                if total_qty:
                                    batch_allowed_qty = (combo_bach.qty or 0) - total_qty
                                if not batch_allowed_qty:
                                    continue
                                batch_serial = {
                                    "value": str(combo_bach.id),
                                    "label" : combo_bach.batch.batch_number_name,
                                    "qty" : str(batch_allowed_qty),
                                    }
                                invoice_batch_serial.append(batch_serial)

                    elif dc_item_combo.item_combo.itemmaster.serial:
                        
                        invoice_combo_serial.extend({"value":dc_serial.id, "label":dc_serial.serial_number,  }  for dc_serial in dc_item_combo.serial.all())
                    
                    sales_invoice_combo_qty = (sales_invoice_item.qty or 0)
                    rate =  (dc_item_combo.item_combo.after_discount_value_for_per_item or 0) if dc_item_combo.item_combo.after_discount_value_for_per_item else  (dc_item_combo.item_combo.rate or 0)
                    total_sales_return_item_combo_qty = sales_invoice_combo.salesreturnitemcombo_set.aggregate(
                        total=Sum('qty')
                    )['total'] or 0

                    print("sales_invoice_combo_qty - total_sales_return_item_combo_qty ",sales_invoice_combo_qty , total_sales_return_item_combo_qty )
                    invoice_combo_balance_qty = sales_invoice_combo_qty - total_sales_return_item_combo_qty 
                    print("invoice_combo_balance_qty",invoice_combo_balance_qty)
                    amount = rate*invoice_combo_balance_qty

                    # print("invoice_batch_serial",invoice_batch_serial)

                    combo_data = {
                            "itemComboId": "",
                            "itemMasterId":str(dc_item_combo.item_combo.itemmaster.id),
                            "partCode":{"value": dc_item_combo.item_combo.itemmaster.id, "label": dc_item_combo.item_combo.itemmaster.item_part_code},
                            "partName":{"value": dc_item_combo.item_combo.itemmaster.id, "label":dc_item_combo.item_combo.itemmaster.item_name},      
                            "uom":  dc_item_combo.item_combo.uom.name,
                            "isSerial":dc_item_combo.item_combo.itemmaster.serial,
                            "isBatch": dc_item_combo.item_combo.itemmaster.batch_number,
                            "isNoBatchSerial" :True if not dc_item_combo.item_combo.itemmaster.serial and not dc_item_combo.item_combo.itemmaster.batch_number else False,
                            "dc_item_combo" : '',
                            "sales_invoice_item_combo" :sales_invoice_combo.id,
                            "qty" :str(invoice_combo_balance_qty),
                            "store" : {"value":dc_item_combo.store.id,
                                            "label" :dc_item_combo.store.store_name} if dc_item_combo.store else None,
                            "batch_list": invoice_batch_serial,
                            "serial_list" : invoice_combo_serial,
                            "batch": "",
                            "serial":"",
                            "display" : dc_item_combo.item_combo.display,
                            "rate" : str(rate), 
                            "amount" :str(amount), 
                            "index":index + 1
                        }
                    # print("combo_data", combo_data)
                    sales_invoice_combos.append(combo_data)
                return sales_invoice_combos

            if dc_item_ids:
                """get dc item data"""
                sales_dc_item_detail = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id__in=dc_item_ids)
                
                
                for index,dc_item in enumerate(sales_dc_item_detail):
                    sales_dc = dc_item.salesorder_2_deliverychallan_set.first()
                    
                    if not sales_dc:
                        return GraphQLError(f"{sales_dc_item_detail.sales_order_item_detail.itemmaster} sales dc not Found.")
                    
                    sales_dc_intance.add(sales_dc)
                    qty  = (dc_item.qty or 0)
                    rate = (dc_item.sales_order_item_detail.after_discount_value_for_per_item or 0) if dc_item.sales_order_item_detail.after_discount_value_for_per_item  else (dc_item.sales_order_item_detail.rate or 0)
                    
                    batch_serial_list = []
                    dc_item_serials = []
                    
                    is_batch = dc_item.sales_order_item_detail.itemmaster.batch_number
                    is_serial = dc_item.sales_order_item_detail.itemmaster.serial 
                    
                    if is_batch:
                        for dc_batch in dc_item.salesorder_2_retunbatch_set.all():
                            try:
                                if dc_batch.is_stock_reduce:
                                    batch_allowed_qty = dc_batch.qty 
                                    total_qty = dc_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                    ).aggregate(total=Sum('qty'))['total'] or 0
                                    if total_qty:
                                        batch_allowed_qty = (dc_batch.qty or 0) -  total_qty
                                    
                                    if not batch_allowed_qty:
                                        continue

                                    batch_serial = {
                                        "value": str(dc_batch.id),
                                        "label" : dc_batch.batch.batch_number_name,
                                        "qty" : str(batch_allowed_qty),
                                    }
                                    batch_serial_list.append(batch_serial)
                            except Exception as e:
                                print("e", e)
                    
                    elif is_serial:
                        dc_item_serials.extend({"value":item_serial.id, "label":item_serial.serial_number, } for item_serial in  dc_item.serial.all())
                    

                    sales_order_item = dc_item.sales_order_item_detail
                    # print((dc_item.qty or 0) , (dc_item.return_submit_count or 0) , (dc_item.invoice_submit_count or 0))
                    allowed_qty = (dc_item.qty or 0) - (dc_item.return_submit_count or 0) - (dc_item.invoice_submit_count or 0)
                    if not allowed_qty:
                        continue
                    amount = allowed_qty*rate
                    data = {
                        "itemMasterId":str(dc_item.sales_order_item_detail.itemmaster.id),
                        "partCode":{"value": dc_item.sales_order_item_detail.itemmaster.id, "label":dc_item.sales_order_item_detail.itemmaster.item_part_code},
                        "partName":{"value": dc_item.sales_order_item_detail.itemmaster.id, "label":dc_item.sales_order_item_detail.itemmaster.item_name},      
                        "description": dc_item.sales_order_item_detail.description,
                        "id": "",
                        "dc_item_detail": str(dc_item.id),
                        "sales_invoice_item_detail": "",
                        "store" : {"value":dc_item.store.id,
                                "label" :dc_item.store.store_name} if dc_item.store else None,
                        "qty": str(allowed_qty or 0),
                        "uom": dc_item.sales_order_item_detail.uom.name,
                        "rate" : str(rate),
                        "amount": str(amount),
                        "dc_qty": str(qty),
                        "invoice_qty":str(dc_item.invoice_submit_count or 0),
                        "returnQty":"",
                        "sgst": str(sales_order_item.sgst or 0),
                        "cgst": str(sales_order_item.cgst or 0),
                        "igst": str(sales_order_item.igst or 0),
                        "cess": str(sales_order_item.cess or 0),
                        "sgst_value": str(amount/100 * (sales_order_item.sgst or 0)),
                        "cgst_value": str(amount/100 * (sales_order_item.cgst or 0)),
                        "igst_value": str(amount/100 * (sales_order_item.igst or 0)),
                        "cess_value": str(amount/100 * (sales_order_item.cess or 0)),
                        "tax": str(sales_order_item.tax) if sales_order_item.tax else None,
                        "batch_list": batch_serial_list,
                        "serial_list" : dc_item_serials,
                        "isBatch": is_batch,
                        "isSerial": is_serial,
                        "batch":"",
                        "serial":"",
                        "isNoBatchSerial" :True if not is_batch and not is_serial else False,
                        "no_batch_no_serial_list" : [],
                        "noBatchSerial":"",
                        "itemCombo":dc_item.sales_order_item_detail.itemmaster.item_combo_bool if dc_item.sales_order_item_detail.itemmaster.item_combo_bool else False,
                        "itemComboItemdetails" : get_dc_item_combo(dc_item) if dc_item.item_combo_itemdetails.exists() else [],
                        "index" : index+1
                    }
                    
                    itemdetails.append(data)
                
            elif sales_invoice_item_ids:
                """get sales invoice item data"""
                sales_invoice_item_details = SalesInvoiceItemDetail.objects.filter(id__in=sales_invoice_item_ids)
                for index,sales_invoice_item in enumerate(sales_invoice_item_details):
                    sales_invoice = sales_invoice_item.salesinvoice_set.first()
                    for sales_dc_instance in sales_invoice.sales_dc.all():
                        sales_dc_intance.add(sales_dc_instance)
                    invoice_dc_item  = sales_invoice_item.item
                    batch_serial_list = []
                    invoice_dc_item_serials = []
                    if not sales_invoice:
                        return GraphQLError(f"{dc_item.itemmaster} sales invoice not Found.")
                    
                    is_batch = invoice_dc_item.sales_order_item_detail.itemmaster.batch_number
                    is_serial = invoice_dc_item.sales_order_item_detail.itemmaster.serial
                    if is_batch:
                        
                            for dc_batch in sales_invoice_item.item.salesorder_2_retunbatch_set.all():
                                if dc_batch.is_stock_reduce:
                                    batch_allowed_qty= (dc_batch.qty or 0)
                                    total_qty = dc_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                    ).aggregate(total=Sum('qty'))['total'] or 0
                                    if total_qty:
                                        batch_allowed_qty = (dc_batch.qty or 0) - total_qty
                                    batch_serial = {
                                        "value": str(dc_batch.id),
                                        "label" : dc_batch.batch.batch_number_name,
                                        "qty" : str(batch_allowed_qty),
                                    }
                                    
                                    batch_serial_list.append(batch_serial)
                    elif is_serial:
                        invoice_dc_item_serials.extend({"value":dc_serial.id, "label":dc_serial.serial_number} for dc_serial in sales_invoice_item.item.serial.all())
                    
                    sales_invoice_intances.add(sales_invoice)
                    sales_invoice_qty = (sales_invoice_item.qty or 0)
                    
                    total_sales_return_item_qty = sales_invoice_item.salesreturnitemdetails_set.filter(sales_return__status__name="Submit").aggregate(
                        total=Sum('qty')
                    )['total'] or 0
                    
                    print("sales_invoice_qty - total_sales_return_item_qty",sales_invoice_qty , total_sales_return_item_qty)
                    invoice_balance_qty = sales_invoice_qty - total_sales_return_item_qty
                    print("invoice_balance_qty",invoice_balance_qty)
                    if invoice_balance_qty:
                        rate = (sales_invoice_item.after_discount_value_for_per_item or 0) if sales_invoice_item.after_discount_value_for_per_item else (sales_invoice_item.rate or 0)
                        amount = invoice_balance_qty*rate
                        sales_order_item = invoice_dc_item.sales_order_item_detail
                        data = {
                            "itemMasterId":str(sales_order_item.itemmaster.id),  
                            "partCode":{"value": str(sales_order_item.itemmaster.id), "label": sales_order_item.itemmaster.item_part_code},
                            "partName":{"value": str(sales_order_item.itemmaster.id), "label":sales_order_item.itemmaster.item_name},      
                            "description":sales_order_item.description,
                            "sales_return": "",
                            "dc_item_detail": "",
                            "sales_invoice_item_detail": sales_invoice_item.id,
                            "so_qty": str(sales_order_item.qty or 0),
                            "rate" : str(rate),
                            "amount": str(amount),
                            "tax": str(sales_order_item.tax or 0),
                            "uom": sales_order_item.uom.name,
                            "qty":str(invoice_balance_qty or 0),
                            "store" : {"value":invoice_dc_item.store.id,
                                            "label" :invoice_dc_item.store.store_name} if invoice_dc_item.store else None,
                            "batch_list": batch_serial_list,
                            "serial_list" : invoice_dc_item_serials,
                            "invoice_qty":str(invoice_dc_item.invoice_submit_count or 0),
                            "returnQty":"",
                            "sgst": str(sales_order_item.sgst or 0),
                            "cgst": str(sales_order_item.cgst or 0),
                            "igst": str(sales_order_item.igst or 0),
                            "cess": str(sales_order_item.cess or 0),
                            "sgst_value": str(amount/100 * (sales_order_item.sgst or 0)),
                            "cgst_value": str(amount/100 * (sales_order_item.cgst or 0)),
                            "igst_value": str(amount/100 * (sales_order_item.igst or 0)),
                            "cess_value": str(amount/100 * (sales_order_item.cess or 0)),
                            "isBatch": is_batch,
                            "isSerial": is_serial,
                            "batch":"",
                            "serial":"",
                            "isNoBatchSerial" :True if not is_serial and not is_batch else False,
                            "no_batch_no_serial_list" : [],
                            "noBatchSerial":"",
                            "itemComboItemdetails" : get_invoice_item_combo(sales_invoice_item) if sales_invoice_item.item_combo.exists() else [],
                            "itemCombo":sales_order_item.itemmaster.item_combo_bool if sales_order_item.itemmaster.item_combo_bool else False,
                            "index" : index+1
                        }
                        itemdetails.append(data)
            
            exchange_rate = 1 
            if len(list(sales_invoice_intances)) > 0: 
                exchange_rates = set([(invoice_instance.exchange_rate or 1) for invoice_instance in list(sales_invoice_intances)])
                if len(set([(invoice_instance.exchange_rate or 1)  for invoice_instance in sales_invoice_intances])) > 1:
                    return GraphQLError(
                    f"Cannot process return: Multiple exchange rates detected across selected invoices. "
                    f"Found rates: {', '.join(map(str, sorted(exchange_rates)))}. "
                    f"Please select invoices with the same exchange rate."
                )
                exchange_rate = list(sales_invoice_intances)[0].exchange_rate if list(sales_invoice_intances)[0].exchange_rate else str(1) 
            else:
                exchange_rate = list(sales_dc_intance)[0].sales_order.exchange_rate if list(sales_dc_intance)[0].sales_order.exchange_rate else str(1)
                
            sales_return = {
                "sales_order_no" : sales_order.sales_order_no.linked_model_id,
                "sales_order_id":  str(sales_order.id),
                "delivery_note_no" : [dc_instance.dc_no.linked_model_id  for dc_instance in sales_dc_intance],
                "delivery_note_id" : [dc_instance.id  for dc_instance in sales_dc_intance] if not sales_invoice_intances else [] ,
                "sales_invoice_no" : [invoice_instance.sales_invoice_no.linked_model_id  for invoice_instance in sales_invoice_intances],
                "sales_invoice_id" : [invoice_instance.id  for invoice_instance in sales_invoice_intances],
                "currency": {
                    "label": str(sales_order.currency.Currency.name),
                    "rate": str(exchange_rate),
                    "currencySymbol": str(sales_order.currency.Currency.currency_symbol),
                },
                "nature_of_transaction": (
                    sales_order.gst_nature_transaction.nature_of_transaction
                    if sales_order.gst_nature_transaction and sales_order.gst_nature_transaction.nature_of_transaction
                    else ""
                ),
                "sales_person" : sales_order.sales_person.username, 
                "buyer" :{
                    "value" : str(sales_order.buyer.id),
                    "label":sales_order.buyer.company_name,
                    "buyer_no":sales_order.buyer.supplier_no,
                    "buyer_address":{
                        "value": str(sales_order.buyer_address.id or ""),
                        "label" : sales_order.buyer_address.address_type,
                        "address_line_1" : sales_order.buyer_address.address_line_1,
                        "address_line_2" : sales_order.buyer_address.address_line_2,
                        "city" : sales_order.buyer_address.city,
                        "pincode" : sales_order.buyer_address.pincode,
                        "state" : sales_order.buyer_address.state,
                        "country" : sales_order.buyer_address.country,
                    },
                    "buyer_gst_type":sales_order.buyer_gstin_type,
                    "buyer_gst_in":sales_order.buyer_gstin,
                    "buyer_contact_person":sales_order.buyer_contact_person.contact_person_name,
                    "buyer_contact_mobile":sales_order.buyer_contact_person.phone_number,
                    "buyer_contact_email":sales_order.buyer_contact_person.email,
                    "buyer_contact_whatsapp_no":sales_order.buyer_contact_person.whatsapp_no
                },
                "consignee" :{
                    "value":str(sales_order.consignee.id),
                    "label":sales_order.consignee.company_name,
                    "consignee_no":sales_order.consignee.supplier_no,
                    "consignee_address": {
                        "value": str(sales_order.consignee_address.id or ""),
                        "label" : sales_order.consignee_address.address_type, 
                        "address_line_1" : sales_order.consignee_address.address_line_1,
                        "address_line_2" : sales_order.consignee_address.address_line_2,
                        "city" : sales_order.consignee_address.city,
                        "pincode" : sales_order.consignee_address.pincode,
                        "state" : sales_order.consignee_address.state,
                        "country" : sales_order.consignee_address.country,
                    },
                    "consignee_gst_type":sales_order.consignee_gstin_type,
                    "consignee_gst_in":sales_order.consignee_gstin,
                    "consignee_contact_person":sales_order.consignee_contact_person.contact_person_name,
                    "consignee_contact_mobile":sales_order.consignee_contact_person.phone_number,
                    "consignee_contact_email":sales_order.consignee_contact_person.email,
                    "consignee_contact_whatsapp_no":sales_order.consignee_contact_person.whatsapp_no 
                    }, 
                    "igst": sales_order.igst if sales_order.igst else None,
                    "sgst": sales_order.sgst if sales_order.sgst else None,
                    "cgst": sales_order.cgst if sales_order.cgst else None,
                    "cess": sales_order.cess if sales_order.cess else None,
                    "itemdetails" : itemdetails, 
                }
                
            return SalesInitialFetch(items = sales_return)
        except Exception as e:
            return GraphQLError(f"Unexpeted error {e}")
    
    @permission_required(models=["Sales Return"])
    def resolve_sales_return_edit_fetch(self, info, sr_id):
        try:
            try:
                sales_return = SalesReturn.objects.get(id=sr_id)
            except SalesReturn.DoesNotExist:
                raise GraphQLError("Sales return not found.")

            sales_order = sales_return.sales_order
            sales_dc_intance = sales_return.salesorder_2_deliverychallan_set.all() or []  
            sales_invoice_intances = sales_return.salesinvoice_set.all() or []  
            sales_return_obj = {
                "id" : sales_return.id,
                "sr_no" : sales_return.sr_no.linked_model_id,
                "sr_date" : str(sales_return.sr_date),
                "leadID": str(sales_order.lead_no.id) if sales_order.lead_no.id else None,
                "sales_order_no" : sales_order.sales_order_no.linked_model_id, 
                "sales_order_id":  str(sales_order.id),
                "delivery_note_no" : [dc_instance.dc_no.linked_model_id  for dc_instance in sales_dc_intance],
                "delivery_note_id" : [dc_instance.id  for dc_instance in sales_dc_intance],
                "sales_invoice_no" : [invoice_instance.sales_invoice_no.linked_model_id  for invoice_instance in sales_invoice_intances],
                "sales_invoice_id" : [invoice_instance.id  for invoice_instance in sales_invoice_intances], 
                "currency": {
                    "label": str(sales_order.currency.Currency.name),
                    "rate": str(sales_return.sales_order.currency.rate) if sales_return.sales_order.currency.rate else None,
                    "currencySymbol": str(sales_return.sales_order.currency.Currency.currency_symbol),
                },
                "nature_of_transaction": (
                    sales_order.gst_nature_transaction.nature_of_transaction
                    if sales_order.gst_nature_transaction and sales_order.gst_nature_transaction.nature_of_transaction
                    else ""
                ),
                "sales_person" : sales_order.sales_person.username, 
                "buyer" :{
                    "value" : str(sales_order.buyer.id),
                    "label":sales_order.buyer.company_name,
                    "buyer_no":sales_order.buyer.supplier_no,
                    "buyer_address":{
                        "value": str(sales_order.buyer_address.id or ""),
                        "label" : sales_order.buyer_address.address_type,
                        "address_line_1" : sales_order.buyer_address.address_line_1,
                        "address_line_2" : sales_order.buyer_address.address_line_2,
                        "city" : sales_order.buyer_address.city,
                        "pincode" : sales_order.buyer_address.pincode,
                        "state" : sales_order.buyer_address.state,
                        "country" : sales_order.buyer_address.country,
                    },
                    "buyer_gst_type":sales_order.buyer_gstin_type,
                    "buyer_gst_in":sales_order.buyer_gstin,
                    "buyer_contact_person":sales_order.buyer_contact_person.contact_person_name,
                    "buyer_contact_mobile":sales_order.buyer_contact_person.phone_number,
                    "buyer_contact_email":sales_order.buyer_contact_person.email,
                    "buyer_contact_whatsapp_no":sales_order.buyer_contact_person.whatsapp_no
                },
                "consignee" :{
                    "value":str(sales_order.consignee.id),
                    "label":sales_order.consignee.company_name,
                    "consignee_no":sales_order.consignee.supplier_no,
                    "consignee_address": {
                        "value": str(sales_order.consignee_address.id or ""),
                        "label" : sales_order.consignee_address.address_type, 
                        "address_line_1" : sales_order.consignee_address.address_line_1,
                        "address_line_2" : sales_order.consignee_address.address_line_2,
                        "city" : sales_order.consignee_address.city,
                        "pincode" : sales_order.consignee_address.pincode,
                        "state" : sales_order.consignee_address.state,
                        "country" : sales_order.consignee_address.country,
                    },
                    "consignee_gst_type":sales_order.consignee_gstin_type,
                    "consignee_gst_in":sales_order.consignee_gstin,
                    "consignee_contact_person":sales_order.consignee_contact_person.contact_person_name,
                    "consignee_contact_mobile":sales_order.consignee_contact_person.phone_number,
                    "consignee_contact_email":sales_order.consignee_contact_person.email,
                    "consignee_contact_whatsapp_no":sales_order.consignee_contact_person.whatsapp_no
                    },
                "igst": sales_order.igst if sales_order.igst else None,
                "sgst": sales_order.sgst if sales_order.sgst else None,
                "cgst": sales_order.cgst if sales_order.cgst else None,
                "cess": sales_order.cess if sales_order.cess else None,
                "comman_store": {"value":str(sales_return.comman_store.id),"label":sales_return.comman_store.store_name} if sales_return.comman_store else None,
                "e_way_bill":sales_return.e_way_bill if sales_return.e_way_bill else None,
                "e_way_bill_date":str(sales_return.e_way_bill_date) if sales_return.e_way_bill_date else None,
                "status":sales_return.status.name,
                "created_by":sales_return.created_by.username,
                "created_at":str(sales_return.created_at) if sales_return.created_at else None,
                "updated_at":str(sales_return.updated_at) if sales_return.updated_at else None,
                "terms_conditions":{"value":str(sales_return.terms_conditions.id),"label":sales_return.terms_conditions.name} if sales_return.terms_conditions else None,
                "terms_conditions_text":sales_return.terms_conditions_text,
                "reason":sales_return.reason,
                "round_off_method":sales_return.round_off_method if sales_return.round_off_method  else None,
                }
            
            itemdetails = []

            def get_item_combo_data(item_data): 
                list_combo = []
                for index, combo_item in enumerate(item_data.salesreturnitemcombo_set.all()):
                    itemmaster = combo_item.itemmaster
                    dc_item_combo = combo_item.dc_item_combo
                    invoice_item_combo = combo_item.sales_invoice_item_combo
                    sales_order_item_combo = None
                    
                    if dc_item_combo:
                        sales_order_item_combo = dc_item_combo.item_combo
                    elif invoice_item_combo:
                        invoice_dc_item_combo = invoice_item_combo.item_combo
                        if invoice_dc_item_combo:
                            sales_order_item_combo = invoice_dc_item_combo.item_combo
                    
                    if not sales_order_item_combo:
                        return GraphQLError(f"{itemmaster} sales order item not linked.")
                    
                    selected_batch_list = []
                    selected_serial_list = []
                    unselected_batch_list = []
                    unselected_serial_list = []
                    if itemmaster.batch_number:
                        combo_batch_ids = []
                        
                        for item_batch in combo_item.salesreturnbatch_item_set.all():
                            
                            combo_batch_ids.append(item_batch.batch.id)
                            batch_serial = {
                                            "id" : item_batch.id,
                                            "value": str(item_batch.batch.id),
                                            "label" : item_batch.batch.batch.batch_number_name,
                                            "qty" : str(item_batch.batch.qty or 0),
                                            "returnQty":str(item_batch.qty or 0),
                                            "is_stock_added" : item_batch.is_stock_added
                                        }
                            selected_batch_list.append(batch_serial)

                        if dc_item_combo:
                            for dc_combo_batch in dc_item_combo.salesorder_2_retunbatch_set.all():
                                if dc_combo_batch.is_stock_reduce and dc_combo_batch.id not in combo_batch_ids:
                                    batch_combo_allowed_qty = dc_combo_batch.qty
                                    total_qty = dc_combo_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                        ).aggregate(total=Sum('qty'))['total'] or 0
                                    if total_qty:
                                        batch_combo_allowed_qty = (dc_combo_batch.qty or 0) - total_qty
                                    if not batch_combo_allowed_qty:
                                        continue

                                    batch_serial = {
                                        "value": dc_combo_batch.id,
                                        "label" : dc_combo_batch.batch.batch_number_name,
                                        "qty" :str(batch_combo_allowed_qty),
                                    }
                                    unselected_batch_list.append(batch_serial)

                        elif invoice_item_combo:
                            dc_combo =  invoice_item_combo.item_combo
                         
                            for combo_bach in dc_combo.salesorder_2_retunbatch_set.all():
                                if combo_bach.is_stock_reduce and combo_bach.id not in combo_batch_ids:
                                    batch_allowed_qty= (combo_bach.qty or 0)
                                    total_qty = combo_bach.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                    ).aggregate(total=Sum('qty'))['total'] or 0
                                    if total_qty:
                                        batch_allowed_qty = (combo_bach.qty or 0) - total_qty

                                    if not batch_allowed_qty:
                                        continue
                                    
                                    batch_serial = {
                                        "value": str(combo_bach.id),
                                        "label" : combo_bach.batch.batch_number_name,
                                        "qty" : str(batch_allowed_qty),
                                    }
                                    unselected_batch_list.append(batch_serial)
                    
                    elif itemmaster.serial:
                        combo_serial_ids = []
                        for item_serial in  combo_item.serial.all():
                            combo_serial_ids.append(item_serial.id)
                            selected_serial_list.append({"value":item_serial.id, "label":item_serial.serial_number})
                        
                        if dc_item_combo:
                            for dc_serial in dc_combo.serial.all():
                                if dc_serial.id not in combo_serial_ids:
                                    unselected_serial_list.append({"value":dc_serial.id, "label":dc_serial.serial_number} )
                        
                        elif invoice_item_combo:
                            dc_combo = invoice_item_combo.item_combo
                            
                            for dc_serial in dc_combo.serial.all():
                                if dc_serial.id not in combo_serial_ids:
                                    unselected_serial_list.append({"value":dc_serial.id, "label":dc_serial.serial_number})

                    
                    combo_data = {
                        "id":str(combo_item.id),
                        "itemMasterId":str(itemmaster.id), 
                        "partCode":{"value": itemmaster.id, "label":itemmaster.item_part_code},
                        "partName":{"value": itemmaster.id, "label":itemmaster.item_name}, 
                        "isSerial":itemmaster.serial,
                        "isBatch": itemmaster.batch_number,
                        "isNoBatchSerial" :True if not itemmaster.serial and not itemmaster.batch_number else False,
                        "uom":  sales_order_item_combo.uom.name,
                        "dc_item_combo" : dc_item_combo.id if dc_item_combo else None,
                        "sales_invoice_item_combo" : invoice_item_combo.id if invoice_item_combo else None,
                        "qty" :str(item.allowed_qty or 0),
                        "returnQty":str(item.qty or 0),
                        "batch": selected_batch_list,
                        "serial":selected_serial_list,
                        "batch_list": unselected_batch_list,
                        "serial_list" : unselected_serial_list,
                        "display" : sales_order_item_combo.display,
                        "rate" : str(sales_order_item_combo.rate),
                        "amount" :str(combo_item.amount),
                        "store" : {"value":combo_item.store.id,
                                        "label" :combo_item.store.store_name} if combo_item.store else None,
                        "is_stock_added":combo_item.is_stock_added if combo_item.is_stock_added else None,
                        "index":index + 1
                    } 
                    list_combo.append(combo_data)
                return list_combo
             

            for item in sales_return.salesreturnitemdetails_set.all():
                itemmaster = item.itemmaster
                dc_item = item.dc_item_detail 
                invoice_item = item.sales_invoice_item_detail
                sales_order_item = None 
                new_qty = 0

                if dc_item:
                    sales_order_item = dc_item.sales_order_item_detail
                    old_return = dc_item.return_submit_count or 0
                    old_invoice = dc_item.invoice_submit_count or 0
                    new_qty = (dc_item.qty or 0) + old_return + old_invoice
                    
                    

                
                elif invoice_item:
                    invoice_dc_item = invoice_item.item
                    sum_return = invoice_item.salesreturnitemdetails_set.filter(sales_return__status__name="Submit").aggregate(
                                                                    total=Sum('qty'))['total'] or 0
                    sum_invoice = invoice_dc_item.salesinvoiceitemdetail_set.filter(salesinvoice__status__name="Submit").exclude(id=invoice_item.id).aggregate(
                                                                    total=Sum('qty'))['total'] or 0
                    new_qty = (invoice_dc_item.qty or 0) + sum_return + sum_invoice

                    if invoice_dc_item:
                        sales_order_item = invoice_dc_item.sales_order_item_detail
                
                if not sales_order_item:
                    return GraphQLError(f"{itemmaster} sales order item not linked.")
                
                selected_batch_list = []
                selected_serial_list = []
                unselected_batch_list = []
                unselected_serial_list = []
                
                if itemmaster.batch_number:
                    batch_ids = []
                    for item_batch in item.salesreturnbatch_item_set.all():
                        batch_serial = {
                                        "id" : item_batch.id,
                                        "value": str(item_batch.batch.id),
                                        "label" : item_batch.batch.batch.batch_number_name,
                                        "qty":str(item_batch.batch.qty or 0),
                                        "returnQty" : str(item_batch.qty),
                                        "is_stock_added" : item_batch.is_stock_added
                                    }
                        batch_ids.append(item_batch.batch.id)
                        selected_batch_list.append(batch_serial)

                    if dc_item:
                        for dc_batch in dc_item.salesorder_2_retunbatch_set.all():
                                try:
                                    if dc_batch.is_stock_reduce and dc_batch.id not in batch_ids:
                                        
                                        batch_allowed_qty = dc_batch.qty
                                        total_qty = dc_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                        ).aggregate(total=Sum('qty'))['total'] or 0
                                        if total_qty:
                                            batch_allowed_qty = (dc_batch.qty or 0) -  total_qty
                                        
                                        if not batch_allowed_qty:
                                            continue

                                        batch_serial = {
                                            "value": str(dc_batch.id),
                                            "label" : dc_batch.batch.batch_number_name,
                                            "qty" : str(batch_allowed_qty),
                                        }
                                        unselected_batch_list.append(batch_serial) 
                                except Exception as e:
                                    return GraphQLError(f"Unexpeted error {str(e)}")

                    elif invoice_item:
                        dc_item_instance = invoice_item.item
                        for dc_batch in dc_item_instance.salesorder_2_retunbatch_set.all():
                                if dc_batch.is_stock_reduce and dc_batch.id not in batch_ids:
                                    batch_allowed_qty= (dc_batch.qty or 0)
                                    total_qty = dc_batch.salesreturnbatch_item_set.filter(is_stock_added=True
                                                                    ).aggregate(total=Sum('qty'))['total'] or 0
                                    if total_qty:
                                        batch_allowed_qty = (dc_batch.qty or 0) - total_qty
                                        
                                    batch_serial = {
                                            "value": str(dc_batch.id),
                                            "label" : dc_batch.batch.batch_number_name,
                                            "qty" : str(batch_allowed_qty),
                                        }
                                    unselected_batch_list.append(batch_serial)
                    
                elif itemmaster.serial:
                    serial_ids = []
                    for item_serial in  item.serial.all():
                        serial_ids.append(item_serial.id)
                        selected_serial_list.append({"value":item_serial.id, "label":item_serial.serial_number})
                    if dc_item:
                        for item_serial in  dc_item.serial.all():
                            if item_serial.id not in serial_ids:
                                unselected_serial_list.append({"value":item_serial.id, "label":item_serial.serial_number, })
                    elif invoice_item:
                        dc_item_instance = invoice_item.item
                        for dc_serial in dc_item_instance.serial.all():
                            if dc_serial.id not in serial_ids:
                                unselected_serial_list.append({"value":dc_serial.id, "label":dc_serial.serial_number} )
                           
                
                
                 
                data = {
                        "itemMasterId":str(itemmaster.id),  
                        "partCode":{"value": itemmaster.id, "label":itemmaster.item_part_code},
                        "partName":{"value": itemmaster.id, "label":itemmaster.item_name},      
                        "description":sales_order_item.description,
                        "id": item.id,
                        "dc_item_detail": dc_item.id if dc_item else None,
                        "sales_invoice_item_detail": invoice_item.id if invoice_item else None,
                        "qty": str(new_qty or 0) if new_qty else 0,
                        "returnQty":str(item.qty or 0),
                        "rate" : str(sales_order_item.rate) if dc_item else str(invoice_item.rate),
                        "amount": str(item.amount),
                        "uom": str(sales_order_item.uom.name),
                        "returnQty":str(item.qty),
                        "store" : {"value":item.store.id,
                                "label" :item.store.store_name} if item.store else None,
                        "dc_qty": str(dc_item.qty) if dc_item else None,
                        "invoice_qty":str(invoice_item.item.invoice_submit_count or 0) if invoice_item and invoice_item.item.invoice_submit_count else None,
                        "batch_list": unselected_batch_list,
                        "serial_list" :unselected_serial_list,
                        "sgst": str(sales_order_item.sgst or 0),
                        "cgst": str(sales_order_item.cgst or 0),
                        "igst": str(sales_order_item.igst or 0),
                        "cess": str(sales_order_item.cess or 0),
                        "sgst_value": str(item.amount/100 * (sales_order_item.sgst or 0)),
                        "cgst_value": str(item.amount/100 * (sales_order_item.cgst or 0)),
                        "igst_value": str(item.amount/100 * (sales_order_item.igst or 0)),
                        "cess_value": str(item.amount/100 * (sales_order_item.cess or 0)),
                        "isBatch": itemmaster.batch_number,
                        "isSerial": itemmaster.serial,
                        "batch":selected_batch_list,
                        "serial":selected_serial_list,
                        "isNoBatchSerial" :True if not itemmaster.batch_number and not itemmaster.serial else False,
                        "no_batch_no_serial_list" : [],
                        "noBatchSerial":"",
                        "itemCombo":itemmaster.item_combo_bool if itemmaster.item_combo_bool else False,
                        "itemComboItemdetails" : get_item_combo_data(item) if itemmaster.item_combo_bool else [],
                        "is_stock_added":item.is_stock_added if item.is_stock_added else None,
                    }
                itemdetails.append(data)
 
            sales_return_obj['itemdetails'] = itemdetails
            return SalesInitialFetch(items = sales_return_obj)
        except Exception as e:
            print("-------------ERROR-------------",e)
            return GraphQLError(f"Unexpeted error: {e}") 

    @permission_required(models=["Sales Return"])        
    def resolve_sales_return_multi_select(self, info, buyer=None, consignee=None, sales_order_id=None, module=None):
        try: 
            filter = {}
            if not buyer and not consignee:
                return GraphQLError("Buyer or Consignee is required")
            if not module: 
                return GraphQLError("Module is required")
            if not sales_order_id:
                return GraphQLError("Sales Order is required") 
            if buyer:
                filter['buyer__id'] = buyer
            if consignee:
                filter['consignee__id'] = consignee
            if sales_order_id:
                filter['id'] = sales_order_id 
            
            sales_order = SalesOrder_2.objects.filter(**filter).first() 
    
            if not sales_order:
                return GraphQLError("Sales Order not found.")
            
            sales_multi_select_data = []
            
            if module == "Delivery Challan":
                for index, dc in enumerate(sales_order.delivery_challans.all()):  
                    if dc.status.name in ["Submit", "Dispatch"]:
                        dc_item = []   
                                            # Get all sales returns for this DC
                        sales_returns = dc.sales_return.all()
                        
                        # Check if any sales return has a non-Draft status
                        has_non_draft_return = any(sr.status.name != "Draft" for sr in sales_returns)
                        
                        # Skip if there's any non-Draft sales return
                        if has_non_draft_return:
                            continue

                        for idx, item in enumerate(dc.item_details.all()):
                            sales_order_item = item.sales_order_item_detail or None
                            item_master = sales_order_item.itemmaster or None
                            qty = Decimal(str(item.qty or 0)) - Decimal(str(item.return_submit_count or 0)) - Decimal(str(item.invoice_submit_count or 0))
                            
                            if qty <= 0:  
                                continue
                                
                            rate = sales_order_item.after_discount_value_for_per_item if sales_order_item.after_discount_value_for_per_item else sales_order_item.rate
                            amount = qty * rate
                            item_json = {
                                "part_code": item_master.item_part_code,
                                "part_name": item_master.item_name,
                                "qty": str(qty),
                                "rate": str(rate),
                                "uom": sales_order_item.uom.name, 
                                "amount": str(amount), 
                                "isSelected": False,
                                "id": str(item.id),
                                "index": idx + 1 
                            }
                            dc_item.append(item_json)

                        dc_data = {
                            "module_no": dc.dc_no.linked_model_id,
                            "module_id": dc.id,
                            "isSelected": False,
                            "itemdetails": dc_item,  
                            "index": index + 1
                        }
                        sales_multi_select_data.append(dc_data)  

            if module == "Sales Invoice":
                try:
                    invoice_index = 0
                    already_exists_invoice = []
                    for dc in sales_order.delivery_challans.all(): 
                        for index, invoice in enumerate(dc.salesinvoice_set.all()):
                            if invoice.status.name in ["Submit"]:
                                invoice_item = []
                                sales_returns = invoice.sales_return.all()
                                # Check if any sales return has a non-Draft status
                                has_non_draft_return = any(sr.status.name != "Draft" for sr in sales_returns)
                                
                                # Skip if there's any non-Draft sales return
                                if has_non_draft_return:
                                    continue
                                if invoice in already_exists_invoice:
                                    continue
                                already_exists_invoice.append(invoice)

                                try:
                                    for idx, item in enumerate(invoice.item_detail.all()):
                                        sales_order_item = item.item.sales_order_item_detail or None
                                        item_master = sales_order_item.itemmaster or None
                                        dc_item = item.item
                                
                                        total_sales_return_item_qty = item.salesreturnitemdetails_set.filter(sales_return__status__name="Submit").aggregate(
                                                                        total=Sum('qty'))['total'] or 0
                                        
                                        total_invoice_return_item_qty = dc_item.salesinvoiceitemdetail_set.filter(salesinvoice__status__name="Submit").aggregate(
                                                                        total=Sum('qty'))['total'] or 0
                                        
                                        qty = Decimal(str(item.qty or 0)) - total_sales_return_item_qty - total_invoice_return_item_qty
                                        
                                        if qty <= 0:  
                                            continue

                                        rate = item.after_discount_value_for_per_item if item.after_discount_value_for_per_item else item.rate
                                        amount = qty * rate
                                        # print("amount",amount)
                                        item_json = {
                                            "part_code": item_master.item_part_code,
                                            "part_name": item_master.item_name,
                                            "qty": str(qty),
                                            "rate": str(rate),
                                            "uom": sales_order_item.uom.name, 
                                            "amount": str(amount), 
                                            "isSelected": False,
                                            "id": str(item.id),
                                            "index": idx + 1 
                                        }
                                        # print("item_json",item_json)
                                        invoice_item.append(item_json)
                                except Exception as e:
                                    print("eeee---------",e)

                                if invoice_item:
                                    invoice_index += 1
                                    invoice_data = {
                                        "module_no": invoice.sales_invoice_no.linked_model_id,
                                        "module_id": invoice.id,
                                        "isSelected": False,
                                        "itemdetails": invoice_item,  
                                        "index": invoice_index
                                    }

                                sales_multi_select_data.append(invoice_data)  
                except Exception as e:
                    print("eeeee",e)
            # print("sales_multi_select_data", sales_multi_select_data)
            return combineMultiDcToSalesInvoice_Type(sales_invoice= sales_multi_select_data or None)
        except Exception as e:
            return GraphQLError(f"Unexpected error: {e}")
    
    @permission_required(models=["Receipt Voucher"])
    def resolve_receipt_voucher_edit_fetch(self, info, id):
        
        try:
            rv_line_data = []
            receipt_voucher = ReceiptVoucher.objects.filter(id=id).first()
            if not receipt_voucher:
                return GraphQLError("Receipt Voucher did'n found.")
            
            if receipt_voucher.pay_by != "Supplier & Customer":
                return GraphQLError("Pay by Supplier & Customer should only be allowed to fetch the relevant records.")
            
            sales_exists_id = None
            for rv_line in receipt_voucher.receiptvoucherline_set.all():
                sales_exists_id = rv_line.receiptvoucheragainstinvoice_set.value_list("sales_invoice__id",  flat=True)

                supplier_invoices = []
                if receipt_voucher.cus_sup:
                    supplier_invoices = SalesInvoice.objects.filter(sales_dc__sales_order__buyer=rv_line.cus_sup.id).exclude(id__in=sales_exists_id)

                exists_against_invoice_details = []
            
                for index, rvai in enumerate(rv_line.receiptvoucheragainstinvoice_set.all()):
                    balance_amt = ( (rvai.sales_invoice.net_amount or 0) -
                            (
                                rvai.sales_invoice.salespaiddetails_set
                                .aggregate(total=Sum("amount"))["total"] or 0
                            )
                        )
                    
                        
                    exists_against_invoice_details.append(
                        {"id": str(rvai.id),
                        "sales_invoice" : rvai.sales_invoice.sales_invoice_no.linked_model_id,
                        "invoice_id": str(rvai.sales_invoice.id),
                        "bill_date": rvai.sales_invoice.sales_invoice_date.strftime("%d/%m/%Y") if rvai.sales_invoice.sales_invoice_date else None,
                        "due_date": rvai.sales_invoice.due_date.strftime("%d/%m/%Y") if rvai.sales_invoice.due_date else None,
                        "balance": str(balance_amt),
                        "amount": str(rvai.adjusted or 0),
                        "remarks": rvai.remarks if rvai.remarks else "",
                        "index": index+1})
                
                for idx,supplier_invoice in enumerate(supplier_invoices):
                    total_adjusted = supplier_invoice.salespaiddetails_set\
                    .aggregate(total=Sum("amount"))["total"] or 0
                    blance = (supplier_invoice.net_amount or 0) - total_adjusted
                    if blance > 0:
                        continue

                    exists_against_invoice_details.append({
                        "sales_invoice" : supplier_invoice.sales_invoice_no.linked_model_id,
                        "invoice_id" : supplier_invoice.id, 
                        "bill_date": supplier_invoice.sales_invoice_date.strftime("%d/%m/%Y") if supplier_invoice.sales_invoice_date else "",
                        "due_date": supplier_invoice.due_date.strftime("%d/%m/%Y") if supplier_invoice.due_date else "",
                        "balance" :  str(blance), 
                        "index": idx + 1
                    }) 
                
                rv_data = {
                        "id" : rv_line.id,
                        "account" : {"value":rv_line.account.id, "lable":rv_line.account.accounts_name},
                        "cus_sup" : {"value":rv_line.cus_sup.id, "lable":rv_line.account.company_name},
                        "employee" : {"value":rv_line.employee.id, "lable":rv_line.employee.employee_name},
                        "pay_for" : {"value":rv_line.pay_for.id, "lable":rv_line.pay_for.accounts_name},
                        "amount" : str(rv_line.amount),
                        "against_invoice_details" : exists_against_invoice_details
                }
                
                rv_line_data.append(rv_data)
            return SalesInitialFetch(items = rv_line_data)
        except Exception as e:
            return GraphQLError(f"An exception occurred: {str(e)}")
    
    @permission_required(models=["Receipt Voucher"])
    def resolve_unpaid_sales_invoice(self, info, customer_id):
 
        if not customer_id:
            return GraphQLError(f"Customer is mandatory.")
        try:
            invoice_datas= []
            customer_invoices = SalesInvoice.objects.filter(buyer__id = customer_id)
            if not customer_invoices.exists() :
                return GraphQLError(f"Invoice not found for this customer.")
  
            for idx,customer_invoice in enumerate(customer_invoices):
                total_adjusted = customer_invoice.salespaiddetails_set\
                .aggregate(total=Sum("amount"))["total"] or 0
                invoice_datas.append({
                    "invoice_no" : customer_invoice.sales_invoice_no.linked_model_id,
                    "invoice_id" : customer_invoice.id, 
                    "bill_date": customer_invoice.sales_invoice_date.strftime("%d/%m/%Y") if customer_invoice.sales_invoice_date else "",
                    "due_date": customer_invoice.due_date.strftime("%d/%m/%Y") if customer_invoice.due_date else "",
                    "balance" : str((customer_invoice.net_amount or 0) - total_adjusted), 
                    "index": idx + 1
                }) 
            return SalesInitialFetch(items = invoice_datas)
        except Exception as e:
            return GraphQLError(f"An exception occurred: {str(e)}")
    
    @permission_required(models=["Credit Note"])
    def resolve_credit_note_initial_fetch(self, info, sales_return_id):
        if not sales_return_id:
            return GraphQLError(f"Sales Return Id is mandatory.")

        try:
            sales_return = SalesReturn.objects.filter(id=sales_return_id).first()
            sales_invoice = sales_return.salesinvoice_set.first()
            if not sales_invoice:
                return GraphQLError("Invoice not found.")

            sales_dc = sales_invoice.sales_dc.first()
            sales_order = sales_dc.sales_order
            sales_invoice_no = ", ".join([sales_insatnce.sales_invoice_no.linked_model_id for sales_insatnce in  sales_return.salesinvoice_set.all()])

            
            data = {
                "sales_return" :{
                    "id" : sales_return.id,
                    "sr_no" : sales_return.sr_no.linked_model_id,
                },
                "sales_invoice" : sales_invoice_no,
                "sales_order" : sales_order.sales_order_no.linked_model_id,
                "department" : {'id': sales_order.department.id,
                                "name": sales_order.department.name},
                "buyer" :{
                    "value" : str(sales_order.buyer.id),
                    "label":sales_order.buyer.company_name,
                    "buyer_no":sales_order.buyer.supplier_no,
                    "buyer_address":{
                        "value": str(sales_order.buyer_address.id or ""),
                        "label" : sales_order.buyer_address.address_type,
                        "address_line_1" : sales_order.buyer_address.address_line_1,
                        "address_line_2" : sales_order.buyer_address.address_line_2,
                        "city" : sales_order.buyer_address.city,
                        "pincode" : sales_order.buyer_address.pincode,
                        "state" : sales_order.buyer_address.state,
                        "country" : sales_order.buyer_address.country,
                    },
                    "buyer_gst_type":sales_order.buyer_gstin_type,
                    "buyer_gst_in":sales_order.buyer_gstin,
                    "buyer_contact_person":sales_order.buyer_contact_person.contact_person_name,
                    "buyer_contact_mobile":sales_order.buyer_contact_person.phone_number,
                    "buyer_contact_email":sales_order.buyer_contact_person.email,
                    "buyer_contact_whatsapp_no":sales_order.buyer_contact_person.whatsapp_no
                },
                "consignee" :{
                    "value":str(sales_order.consignee.id),
                    "label":sales_order.consignee.company_name,
                    "consignee_no":sales_order.consignee.supplier_no,
                    "consignee_address": {
                        "value": str(sales_order.consignee_address.id or ""),
                        "label" : sales_order.consignee_address.address_type, 
                        "address_line_1" : sales_order.consignee_address.address_line_1,
                        "address_line_2" : sales_order.consignee_address.address_line_2,
                        "city" : sales_order.consignee_address.city,
                        "pincode" : sales_order.consignee_address.pincode,
                        "state" : sales_order.consignee_address.state,
                        "country" : sales_order.consignee_address.country,
                    },
                    "consignee_gst_type":sales_order.consignee_gstin_type,
                    "consignee_gst_in":sales_order.consignee_gstin,
                    "consignee_contact_person":sales_order.consignee_contact_person.contact_person_name,
                    "consignee_contact_mobile":sales_order.consignee_contact_person.phone_number,
                    "consignee_contact_email":sales_order.consignee_contact_person.email,
                    "consignee_contact_whatsapp_no":sales_order.consignee_contact_person.whatsapp_no
                    },
                "sales_person" : {
                    "id" : sales_order.sales_person.id,
                    "name" : sales_order.sales_person.username,
                },
                "currency" : {"id": sales_order.currency.id,
                            "name" : sales_order.currency.Currency.name},
                "exchange_rate"  : str(sales_order.currency.rate or 1),
                "gst_nature_type" : sales_order.gst_nature_type,
                "gst_nature_transaction" : {
                    "id": sales_order.gst_nature_transaction.id,
                    "name":sales_order.gst_nature_transaction.nature_of_transaction,
                },
                "item_details" : [
                    {
                        'itemmaster' : {
                            "value" : item.itemmaster.id,
                            "label"  : item.itemmaster.item_part_code,
                        },
                        'sales_return_item' : item.id,
                        "description" : item.itemmaster.description,
                        "uom" : {
                            "value" : item.sales_invoice_item_detail.item.sales_order_item_detail.uom.id,
                            "label" : item.sales_invoice_item_detail.item.sales_order_item_detail.uom.name,
                        },
                        "qty" : str(item.qty),
                        "rate " :  str(item.sales_invoice_item_detail.tax),
                        "hsn" :{
                            "value" : item.sales_invoice_item_detail.item.sales_order_item_detail.hsn.id,
                            "label" : item.sales_invoice_item_detail.item.sales_order_item_detail.hsn.hsn_code,
                        },
                        "tax"  : str(item.sales_invoice_item_detail.item.sales_order_item_detail.tax or 0),
                        "sgst" : str(item.sales_invoice_item_detail.item.sales_order_item_detail.sgst or 0),
                        "cgst" : str(item.sales_invoice_item_detail.item.sales_order_item_detail.cgst or 0),
                        "igst" : str(item.sales_invoice_item_detail.item.sales_order_item_detail.igst or 0),
                        "cess" : str(item.sales_invoice_item_detail.item.sales_order_item_detail.cess or 0),
                        "tds_percentage" : str(item.sales_invoice_item_detail.tds_percentage or 0),
                        "tcs_percentage" : str(item.sales_invoice_item_detail.tcs_percentage or 0),
                    }
                    for  item in sales_return.salesreturnitemdetails_set.all()
                ]
            }
            return SalesInitialFetch(items = data)
        except Exception as e:
            return GraphQLError(f"An exception error str{e}.")
    
    # @permission_required(models=["Credit Note"])
    def resolve_credit_note_edit_fetch(self, info, credit_note_id):
        if not credit_note_id:
            return GraphQLError(f"Credit Return Id is mandatory.")

        try:
            credit_note = CreditNote.objects.filter(id=credit_note_id).first()
            sales_return = credit_note.sales_return
            sales_invoice = sales_return.salesinvoice_set.first() if sales_return else None
            if not sales_invoice:
                return GraphQLError("Invoice not found.")
            
            sales_dc = sales_invoice.sales_dc.first()
            sales_order = sales_dc.sales_order
            sales_invoice_no = ", ".join([sales_insatnce.sales_invoice_no.linked_model_id for sales_insatnce in  sales_return.salesinvoice_set.all()])
            
            item_details = [
                    {
                        "id" : item.id,
                        "index" : item.index,
                        "credit_note" : item.credit_note.id,
                        'itemmaster' : {
                            "value" : item.itemmaster.id,
                            "label"  : item.itemmaster.item_part_code,
                        },
                        'sales_return_item' : item.id,
                        "description" : item.itemmaster.description,
                        "uom" : {
                            "value" : item.uom.id,
                            "label" : item.uom.name,
                        },
                        "qty" : str(item.qty),
                        "rate " :  str(item.tax),
                        "hsn" :{
                            "value" : item.hsn.id,
                            "label" : item.hsn.hsn_code,
                        } if  item.hsn else {},
                        "tax"  : str(item.tax or 0),
                        "sgst" : str(item.sgst or 0),
                        "cgst" : str(item.cgst or 0),
                        "igst" : str(item.igst or 0),
                        "cess" : str(item.cess or 0),
                        "tds_percentage" : str(item.tds_percentage or 0),
                        "tcs_percentage" : str(item.tcs_percentage or 0),
                        "amount" : str(item.amount),
                        "item_combo" :[
                            {
                                "id" : item_combo.id,
                                "credit_note_item" : item_combo.credit_note_item.id,
                                'itemmaster' : {
                                    "value" : item_combo.itemmaster.id,
                                    "label"  : item_combo.itemmaster.item_part_code,
                                },
                                'sales_return_combo_item' : item_combo.sales_return_combo_item.id,
                                "description" : item_combo.itemmaster.description,
                                "uom" : {
                                    "value" : item_combo.uom.id,
                                    "label" : item_combo.uom.name,
                                },
                                "qty" : str(item_combo.qty),
                                "rate " :  str(item_combo.tax),
                                "display" : item_combo.display,
                                "is_mandatory" : item_combo.is_mandatory,
                                "amount" : str(item_combo.amount),
                            }  for  item_combo in item.creditnotecomboitemsetails_set.all()
                        ]
                    }
                    for  item in credit_note.creditnoteitemdetails_set.all()
                ]
            accounts = [
                {
                "id" : account.id,
                "index" : account.index,
                "credit_note" : account.credit_note.id,
                "account_master" : {
                    "id": account.account_master.id,
                    "name" : account.account_master.accounts_name,
                },
                "description" : account.description,
                "hsn" : {
                    "id" : account.hsn.id,
                    "hsn_code" : account.hsn.hsn_code.id,
                },
                "tax"  : str(account.tax),
                "sgst" : str(account.sgst),
                "cgst" : str(account.cgst),
                "igst" : str(account.igst),
                "cess" : str(account.cess),
                "tds_percentage" : str(account.tds_percentage),
                "tcs_percentage" : str(account.tcs_percentage),
                "amount" : str(account.amount),
                
                }
                for  account in credit_note.creditnoteaccount_set.all()
            ]
            
            item_and_account = item_details+accounts
            item_and_account_sorted = sorted(item_and_account, key=lambda x: int(x["index"]))
            other_charges = [
                {
                    "id" : other_charges.id,
                    "other_income_charges" : {"id": other_charges.other_income_charges.id,
                                              "name":other_charges.other_income_charges.name },
                    "hsn" : {"id" : other_charges.hsn.id,
                            "hsn_code": other_charges.hsn.hsn_code} if other_charges.hsn else { },
                    "tax" :   str(other_charges.tax),
                    "sgst" : str(other_charges.sgst),
                    "cgst" : str(other_charges.cgst),
                    "igst" : str(other_charges.igst),
                    "cess" : str(other_charges.cess),
                    "amount" : str(other_charges.amount),


                }
                for  other_charges in credit_note.creditnoteotherincomecharges.all()
            ]
            
            data = {
                'status' : credit_note.status.name,
                "cn_no" : credit_note.cn_no.linked_model_id,
                "cn_date" : str(credit_note.cn_date),
                "sales_return" :{
                    "id" : sales_return.id,
                    "sr_no" : sales_return.sr_no.linked_model_id,
                },
                "sales_invoice" : sales_invoice_no,
                "sales_order" : sales_order.sales_order_no.linked_model_id,
                "department" : {'id': credit_note.department.id,
                                "name": credit_note.department.name},
                "buyer" :{
                    "value" : str(credit_note.buyer.id),
                    "label":credit_note.buyer.company_name,
                    "buyer_no":credit_note.buyer.supplier_no,
                    "buyer_address":{
                        "value": str(credit_note.buyer_address.id or ""),
                        "label" : credit_note.buyer_address.address_type,
                        "address_line_1" : credit_note.buyer_address.address_line_1,
                        "address_line_2" : credit_note.buyer_address.address_line_2,
                        "city" : credit_note.buyer_address.city,
                        "pincode" : credit_note.buyer_address.pincode,
                        "state" : credit_note.buyer_address.state,
                        "country" : credit_note.buyer_address.country,
                    },
                    "buyer_gst_type":credit_note.buyer_gstin_type,
                    "buyer_gst_in":credit_note.buyer_gstin,
                    "buyer_contact_person":credit_note.buyer_contact_person.contact_person_name,
                    "buyer_contact_mobile":credit_note.buyer_contact_person.phone_number,
                    "buyer_contact_email":credit_note.buyer_contact_person.email,
                    "buyer_contact_whatsapp_no":credit_note.buyer_contact_person.whatsapp_no
                },
                "consignee" :{
                    "value":str(credit_note.consignee.id),
                    "label":credit_note.consignee.company_name,
                    "consignee_no":credit_note.consignee.supplier_no,
                    "consignee_address": {
                        "value": str(credit_note.consignee_address.id or ""),
                        "label" : credit_note.consignee_address.address_type, 
                        "address_line_1" : credit_note.consignee_address.address_line_1,
                        "address_line_2" : credit_note.consignee_address.address_line_2,
                        "city" : credit_note.consignee_address.city,
                        "pincode" : credit_note.consignee_address.pincode,
                        "state" : credit_note.consignee_address.state,
                        "country" : credit_note.consignee_address.country,
                    },
                    "consignee_gst_type":credit_note.consignee_gstin_type,
                    "consignee_gst_in":credit_note.consignee_gstin,
                    "consignee_contact_person":credit_note.consignee_contact_person.contact_person_name,
                    "consignee_contact_mobile":credit_note.consignee_contact_person.phone_number,
                    "consignee_contact_email":credit_note.consignee_contact_person.email,
                    "consignee_contact_whatsapp_no":credit_note.consignee_contact_person.whatsapp_no
                    },
                "sales_person" : {
                    "id" : credit_note.sales_person.id,
                    "name" : credit_note.sales_person.username,
                },
                "currency" : {"id": credit_note.currency.id,
                            "name" : credit_note.currency.Currency.name},
                "exchange_rate"  : str(credit_note.currency.rate or 1),
                "gst_nature_type" : credit_note.gst_nature_type,
                "gst_nature_transaction" : {
                    "id": credit_note.gst_nature_transaction.id,
                    "name":credit_note.gst_nature_transaction.nature_of_transaction,
                },
                "item_details" : item_and_account_sorted,
                "other_charges" : other_charges,
                "reason" : credit_note.reason,
                "remarks" : credit_note.remarks,
                "e_way_bill_no" : credit_note.e_way_bill_no,
                "e_way_bill_date" : str(credit_note.e_way_bill_date) if credit_note.e_way_bill_date else None,
                "gst_nature_type" : credit_note.gst_nature_type,
                "gst_nature_transaction" : {
                    "id" : credit_note.reason.gst_nature_transaction.id,
                    "name" : credit_note.reason.gst_nature_transaction.nature_of_transaction,
                },
                "terms_conditions" : credit_note.terms_conditions,
                "terms_conditions_text" : credit_note.terms_conditions_text,
                "igst" : str(credit_note.igst),
                "sgst" : str(credit_note.sgst),
                "cgst" : str(credit_note.cgst),
                "cess" : str(credit_note.cess),
                "tds_bool" : credit_note.tds_bool,
                "tcs_bool" : credit_note.tcs_bool,
                "tds_total" : str(credit_note.tds_total),
                "tcs_total" : str(credit_note.tcs_total),
                "item_total_befor_tax" : str(credit_note.item_total_befor_tax),
                "other_charges_befor_tax" : str(credit_note.other_charges_befor_tax),
                "taxable_value" : str(credit_note.taxable_value),
                "tax_total" : str(credit_note.tax_total),
                "round_off" : str(credit_note.round_off),
                "round_off_method" : credit_note.round_off_method,
                "net_amount" :  str(credit_note.net_amount),
                "modified_by" :{"id" : credit_note.modified_by.id, "name" : credit_note.modified_by.username} if credit_note.modified_by else {},
                "created_by" : {"id" : credit_note.created_by.id, "name" : credit_note.modified_by.username} if credit_note.created_by else {},
                "created_at" : credit_note.created_at if credit_note.created_at else None,
                "updated_at" : credit_note.updated_at if credit_note.updated_at else None,
            }
            
            return SalesInitialFetch(items = data)
        except Exception as e:
            return GraphQLError(f"An exception occurred {str(e)}")

    def resolve_receipt_voucher_type(self, info, id):
         
        if not id:
            return GraphQLError("id id required.")
        rv = ReceiptVoucher.objects.filter(id=id).first()
       

        if not rv:
            return GraphQLError("Receipt Voucher not found.")
        return rv
        
    def resolve_credit_note(self, info, id):
        filter_kwargs = {}
        queryset = CreditNote.objects.all().order_by('-id')
       
        if id:
            filter_kwargs['id'] = id
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
            print("queryset",queryset)
        return queryset