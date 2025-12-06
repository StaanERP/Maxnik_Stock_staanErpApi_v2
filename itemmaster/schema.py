import graphene
from _decimal import InvalidOperation
from django.db.models import F, Q, Subquery, OuterRef, Prefetch, Max
from django.db.models.functions import Lower
from graphene import ObjectType, List, Int
from graphene.types.generic import GenericScalar
from graphene_django.types import DjangoObjectType
from graphene_django.rest_framework.mutation import SerializerMutation
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from userManagement.models import Employee
from .import_functions import supplierDataImport
from EnquriFromapi.Schema import *
from EnquriFromapi.models import UserPermission
from .serializer import *
from .models import *
from userManagement.models import *
from django.contrib.auth.models import User
from django.db.models.functions import TruncDate
from django.db.models import DateField
from datetime import datetime, timedelta
from itemmaster.Utils.stock_statement import *
from django.forms.models import model_to_dict
from .models import e_way_bill
from django.db.models import Count, Sum, IntegerField
from graphene import Enum
from django.core import serializers
import json
from .Utils.CommanUtils import *
from django.contrib.auth.decorators import login_required
import math
from django.forms.models import model_to_dict


def create_graphene_type(model_):
    class Meta:
        model = model_
        fields = "__all__"
        convert_choices_to_enum = False

    graphene_type = type(
        f'{model_.__name__}Type',
        (DjangoObjectType,),
        {'Meta': Meta}
    )

    return graphene_type

company_Type = create_graphene_type(CompanyMaster)

class CommanChildType(graphene.ObjectType):
    id = graphene.ID()
    label = graphene.String()
    Number = graphene.String()
    isShow = graphene.Boolean()
    date = graphene.Date()
    status = graphene.String()
    children = graphene.List(graphene.NonNull(lambda: CommanChildType))


class CommanTimeLine(graphene.ObjectType):
    id = graphene.ID()
    label = graphene.String()
    Number = graphene.String()
    isShow = graphene.Boolean()
    date = graphene.Date()
    status = graphene.String()
    children = graphene.List(graphene.NonNull(CommanChildType))

class PurchaseTimeLine(graphene.ObjectType):
    item = graphene.JSONString()

def create_with_page_info_comman_connection(model_type):
    """To Create with page info comman connection Dynamic"""

    class CommanConnection_1(graphene.ObjectType):
        items = graphene.List(model_type)
        page_info = graphene.Field(PageInfoType)

    return CommanConnection_1


def create_with_out_page_info_comman_connection(model_type):
    """To Create with out page info comman connection Dynamic"""

    class CommanConnection(graphene.ObjectType):
        items = graphene.List(model_type)

    return CommanConnection


class PageInfoType(graphene.ObjectType):
    total_items = graphene.Int()
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    total_pages = graphene.Int()




class ItemMasterHistoryType(DjangoObjectType):
    class Meta:
        model = ItemMasterHistory
        fields = "__all__"


class ItemMasterHistoryConnection(graphene.ObjectType):
    items = graphene.List(ItemMasterHistoryType)
    page_info = graphene.Field(PageInfoType)


class ItemMasterType(DjangoObjectType):
    class Meta:
        model = ItemMaster
        fields = "__all__"

tds_link_type = create_graphene_type(TDSMaster)
tcs_link_type = create_graphene_type(TCSMaster)


class ItemMasterConnection(graphene.ObjectType):
    items = graphene.List(ItemMasterType)
    page_info = graphene.Field(PageInfoType)


class ItemIndicatorsType(DjangoObjectType):
    class Meta:
        model = Item_Indicator
        fields = "__all__"


class ItemIndicatorsConnection(graphene.ObjectType):
    items = graphene.List(ItemIndicatorsType)


class ItemTypeType(DjangoObjectType):
    class Meta:
        model = ItemType
        fields = "__all__"


class ItemTypeConnection(graphene.ObjectType):
    items = graphene.List(ItemTypeType)


class UOMType(DjangoObjectType):
    class Meta:
        model = UOM
        fields = "__all__"
        convert_choices_to_enum = False


class UomConnection(graphene.ObjectType):
    items = graphene.List(UOMType)
    page_info = graphene.Field(PageInfoType)


class StockSerialHistoryType(DjangoObjectType):
    class Meta:
        model = StockSerialHistory
        fields = "__all__"


class StockSerialHistoryConnection(graphene.ObjectType):
    items = graphene.List(StockSerialHistoryType)
    page_info = graphene.Field(PageInfoType)


class ItemGroupsNameType(DjangoObjectType):
    class Meta:
        model = Item_Groups_Name  # Corrected from Model to model (case sensitive)
        fields = "__all__"  # This includes all fields from the model


class ItemGroupsNameConnection(graphene.ObjectType):
    items = graphene.List(ItemGroupsNameType)
    page_info = graphene.Field(PageInfoType)


class Alternate_Unit_Type(DjangoObjectType):
    class Meta:
        model = Alternate_unit
        fields = "__all__"


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"


class CategoryConnection(graphene.ObjectType):
    items = graphene.List(CategoryType)


class ContactDetalisType(DjangoObjectType):
    class Meta:
        model = ContactDetalis
        fields = "__all__"


class ContactDetalisConnection(graphene.ObjectType):
    items = graphene.List(ContactDetalisType)
    page_info = graphene.Field(PageInfoType)


class CompanyAddressType(DjangoObjectType):
    class Meta:
        model = CompanyAddress
        fields = "__all__"
        convert_choices_to_enum = False


class CompanyAddressConnection(graphene.ObjectType):
    items = graphene.List(CompanyAddressType)
    page_info = graphene.Field(PageInfoType)


class SupplierFormDataType(DjangoObjectType):
    class Meta:
        model = SupplierFormData
        fields = "__all__"


class SupplierFormDataConnection(graphene.ObjectType):
    items = graphene.List(SupplierFormDataType)
    page_info = graphene.Field(PageInfoType)


class AccountsMaster_Type(DjangoObjectType):
    class Meta:
        model = AccountsMaster
        fields = "__all__"
        convert_choices_to_enum = False


class AccountsMasterConnection(graphene.ObjectType):
    items = graphene.List(AccountsMaster_Type)
    page_info = graphene.Field(PageInfoType)


class AccountsGroupType(DjangoObjectType):
    class Meta:
        model = AccountsgroupType
        fields = "__all__"


class AccountsGroupTypeConnection(graphene.ObjectType):
    items = graphene.List(AccountsGroupType)
    page_info = graphene.Field(PageInfoType)


class AccountsGroupsType(DjangoObjectType):
    class Meta:
        model = AccountsGroup
        fields = "__all__"


class AccountsGroupsConnection(graphene.ObjectType):
    items = graphene.List(AccountsGroupsType)
    page_info = graphene.Field(PageInfoType)

GSTNatureTransactionType = create_graphene_type(GSTNatureTransaction)

class HsnType_Type(DjangoObjectType):
    class Meta:
        model = HsnType
        fields = "__all__"


class HsnType_TypeConnection(graphene.ObjectType):
    items = graphene.List(HsnType_Type)


class GstRateType(DjangoObjectType):
    class Meta:
        model = GstRate
        fields = "__all__"


class GstRate_TypeConnection(graphene.ObjectType):
    items = graphene.List(GstRateType)


class Hsn_Type(DjangoObjectType):
    class Meta:
        model = Hsn
        fields = "__all__"
        convert_choices_to_enum = False


class HsnConnection(graphene.ObjectType):
    items = graphene.List(Hsn_Type)
    page_info = graphene.Field(PageInfoType)


class StoreType(DjangoObjectType):
    class Meta:
        model = Store
        fields = "__all__"


class StoreConnection(graphene.ObjectType):
    items = graphene.List(StoreType)
    page_info = graphene.Field(PageInfoType)


class DisplayGroupType(DjangoObjectType):
    class Meta:
        model = display_group
        fields = "__all__"


class DisplayGroupConnection(graphene.ObjectType):
    items = graphene.List(DisplayGroupType)
    page_info = graphene.Field(PageInfoType)


class CustomerGroupsType(DjangoObjectType):
    class Meta:
        model = CustomerGroups
        fields = "__all__"


class CustomerGroupsConnection(graphene.ObjectType):
    items = graphene.List(CustomerGroupsType)
    page_info = graphene.Field(PageInfoType)


class SupplierGroupsType(DjangoObjectType):
    class Meta:
        model = SupplierGroups
        fields = "__all__"


class SupplierGroupsConnection(graphene.ObjectType):
    items = graphene.List(SupplierGroupsType)
    page_info = graphene.Field(PageInfoType)


class User_Type(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"


class ItemComboType(DjangoObjectType):
    class Meta:
        model = Item_Combo
        fields = "__all__"


class ItemComboConnection(graphene.ObjectType):
    items = graphene.List(ItemComboType)


class UserConnection(graphene.ObjectType):
    items = graphene.List(User_Type)

"""Comman query"""
CommonStatusType = create_graphene_type(CommanStatus)

class DuplicateItemType(graphene.ObjectType):
    id_list = graphene.List(graphene.Int)


class DuplicateItemConnection(graphene.ObjectType):
    items = graphene.List(DuplicateItemType)


class FinishedGoodsType(DjangoObjectType):
    class Meta:
        model = FinishedGoods
        fields = "__all__"


class FinishedGoodsConnection(graphene.ObjectType):
    items = graphene.List(FinishedGoodsType)


class RawMaterialType(DjangoObjectType):
    class Meta:
        model = RawMaterial
        fields = "__all__"


class RawMaterialConnection(graphene.ObjectType):
    items = graphene.List(RawMaterialType)


class ScrapType(DjangoObjectType):
    class Meta:
        model = Scrap
        fields = "__all__"


class ScrapConnection(graphene.ObjectType):
    items = graphene.List(ScrapType)


class RoutingType(DjangoObjectType):
    class Meta:
        model = Routing
        fields = "__all__"


class RoutingConnection(graphene.ObjectType):
    items = graphene.List(RoutingType)


class BomStatusType(DjangoObjectType):
    class Meta:
        model = BomStatus
        fields = "__all__"


class BomStatusConnection(graphene.ObjectType):
    items = graphene.List(BomStatusType)


class BomTypeOption(graphene.ObjectType):
    id = graphene.Int()
    bomType = graphene.String()


class BomTypeOptionConnection(graphene.ObjectType):
    items = graphene.List(BomTypeOption)


class BomType(DjangoObjectType):
    class Meta:
        model = Bom
        fields = "__all__"


class BomConnection(graphene.ObjectType):
    items = graphene.List(BomType)
    page_info = graphene.Field(PageInfoType)


class SerialNumberType(DjangoObjectType):
    class Meta:
        model = SerialNumbers
        fields = "__all__"


class SerialNumberConnection(graphene.ObjectType):
    items = graphene.List(SerialNumberType)


class BatchNumberType(DjangoObjectType):
    class Meta:
        model = BatchNumber
        fields = "__all__"


class BatchNumberConnection(graphene.ObjectType):
    items = graphene.List(BatchNumberType)
    page_info = graphene.Field(PageInfoType)


class ItemStockType(graphene.ObjectType):
    id = graphene.ID()
    part_number = graphene.Int()
    current_stock = graphene.Decimal()
    store = graphene.Int()
    serial_number = graphene.List(graphene.Int)
    batch_number = graphene.Int()
    unit = graphene.Int()
    last_serial_history = graphene.Int()


class ItemStockConnection(graphene.ObjectType):
    items = graphene.List(ItemStockType)
    page_info = graphene.Field(PageInfoType)


class QueryStockIdType(graphene.ObjectType):
    id = graphene.Int()
    part_number = graphene.Field(ItemMasterType)
    store = graphene.Field(StoreType)


class QueryStockIdConnection(graphene.ObjectType):
    items = graphene.List(QueryStockIdType)


class QueryItemStockType(graphene.ObjectType):
    id = graphene.ID()
    part_number = graphene.Field(ItemMasterType)
    current_stock = graphene.Decimal()
    store = graphene.Field(StoreType)
    serial_number = graphene.List(SerialNumberType)
    batch_number = graphene.Field(BatchNumberType)
    unit = graphene.Field(UOMType)
    last_serial_history = graphene.Int()
    store = graphene.Field(StoreType)

    def resolve_serial_number(self, info):
        serial_numbers = self.serial_number.all()
        return serial_numbers
    
class SerialNumberStringType(graphene.ObjectType):
    serialNumber = graphene.String()

class SerialNumberisDupilicate(graphene.ObjectType):
    isDupulicate = graphene.Boolean()
    serial_number = graphene.List(SerialNumberStringType)


class QueryItemStockConnection(graphene.ObjectType):
    items = graphene.List(QueryItemStockType)
    page_info = graphene.Field(PageInfoType)


class StockStatementType(graphene.ObjectType):
    id = graphene.ID()
    part_code = graphene.String()
    part_name = graphene.String()
    current_stock = graphene.Decimal()
    stores = graphene.String()
    item_group = graphene.String()
    stock_id = graphene.List(graphene.Int)
    description = graphene.String()
    is_batch = graphene.Boolean()
    is_serial = graphene.Boolean()


class StockStatementConnection(graphene.ObjectType):
    items = graphene.List(StockStatementType)
    page_info = graphene.Field(PageInfoType)
    total_qty = graphene.Int()

class StockStatementPartView(graphene.ObjectType):
    stock_and_history_data = graphene.JSONString()


class StockHistoryLogType(graphene.ObjectType):
    id = graphene.ID()
    part_code_id = graphene.ID()
    start_stock = graphene.Int()
    end_stock = graphene.Int()
    date = graphene.String()
    added = graphene.Int()
    reduced = graphene.Int()


class StockHistoryLogConnection(graphene.ObjectType):
    items = graphene.List(StockHistoryLogType)


class InventoryApprovalType(graphene.ObjectType):
    id = graphene.ID()
    part_number = graphene.Field(ItemMasterType)
    # serial_number = graphene.List(SerialNumberType)
    serial_number = graphene.String()
    deletion_serial_number =  graphene.List(SerialNumberType)
    batch_number = graphene.Field(BatchNumberType)
    unit = graphene.Field(UOMType)
    store = graphene.Field(StoreType)
    is_delete = graphene.Boolean()
    is_stock_added = graphene.Boolean()
    qty = graphene.Int()
    amount = graphene.Decimal()
    rate = graphene.Decimal()
    is_stock_added = graphene.Boolean()
    # serial_number_joined = graphene.String()
    def resolve_deletion_serial_number(parent, info):
        if hasattr(parent, 'deletion_serial_number'):
            return parent.deletion_serial_number.all()  # Ensure it's an iterable
        return [] 

    # def resolve_serial_number(self, info):
    #     serial_numbers = self.serial_number.all()
    #     return serial_numbers

    # def resolve_serial_number_joined(self, info):
    #     serial_numbers = [str(serial_number.serial_number) for serial_number in self.serial_number.all()]
    #     return ','.join(serial_numbers)


class InventoryApprovalConnection(graphene.ObjectType):
    items = graphene.List(InventoryApprovalType)
    page_info = graphene.Field(PageInfoType)


class InventoryHandlerType(graphene.ObjectType):
    id = graphene.ID()
    inventory_handler_id = graphene.ID()
    inventory_id = graphene.List(InventoryApprovalType)
    qtyofInventoryApproval = graphene.Int()
    created_at = graphene.String()
    conference = graphene.Field(ConferencedataType)
    updated_at = graphene.String()
    saved_by = graphene.Field(User_Type)
    store = graphene.Field(StoreType)
    actions = graphene.String()
    status = graphene.Field(CommonStatusType)

    def resolve_inventory_id(self, info):
        return self.inventory_id.all()


class InventoryHandlerConnection(graphene.ObjectType):
    items = graphene.List(InventoryHandlerType)
    page_info = graphene.Field(PageInfoType)


class CurrencyExchangeType(DjangoObjectType):
    class Meta:
        model = CurrencyExchange
        fields = "__all__"


class CurrencyExchangeConnection(graphene.ObjectType):
    items = graphene.List(CurrencyExchangeType)
    page_info = graphene.Field(PageInfoType)


class CurrencyMasterType(DjangoObjectType):
    class Meta:
        model = CurrencyMaster
        fields = "__all__"


class CurrencyMasterConnection(graphene.ObjectType):
    items = graphene.List(CurrencyMasterType)
    page_info = graphene.Field(PageInfoType)


# class CurrencyFormateType(DjangoObjectType):
#     class Meta:
#         model = CurrencyFormate
#         fields = "__all__"


# class CurrencyFormateTypeConnection(graphene.ObjectType):
#     items = graphene.List(CurrencyFormateType)


class ResourcePosType_Type(DjangoObjectType):
    class Meta:
        model = ResourcePosType
        fields = "__all__"


class ResourcePosTypeConnection(graphene.ObjectType):
    items = graphene.List(ResourcePosType_Type)
    page_info = graphene.Field(PageInfoType)


class NumberingSeriesType(DjangoObjectType):
    class Meta:
        model = NumberingSeries
        fields = "__all__"
        convert_choices_to_enum = False


class NumberingSeriesConnection(graphene.ObjectType):
    items = graphene.List(NumberingSeriesType)
    page_info = graphene.Field(PageInfoType)


class NumberingSeriesLinkingType(DjangoObjectType):
    class Meta:
        model = NumberingSeriesLinking
        fields = "__all__"


class NumberingSeriesLinkingConnection(graphene.ObjectType):
    items = graphene.List(NumberingSeriesLinkingType)
    page_info = graphene.Field(PageInfoType)


class SalesOrderType(DjangoObjectType):
    class Meta:
        model = SalesOrder
        fields = "__all__"
        convert_choices_to_enum = False


PosOtherIncomeChargesType = create_graphene_type(posOtherIncomeCharges)


class SalesOrderConnection(graphene.ObjectType):
    items = graphene.List(SalesOrderType)
    page_info = graphene.Field(PageInfoType)


class SalesOrderItemComboType(DjangoObjectType):
    class Meta:
        model = SalesOrderItemCombo
        fields = "__all__"


class SalesOrderItemComboConnection(graphene.ObjectType):
    items = graphene.List(SalesOrderItemComboType)


class SalesOrderItemType(DjangoObjectType):
    class Meta:
        model = SalesOrderItem
        fields = "__all__"


class SalesOrderItemConnection(graphene.ObjectType):
    items = graphene.List(SalesOrderItemType)


class PaymentModeType(DjangoObjectType):
    class Meta:
        model = paymentMode
        fields = "__all__"


class PaymentModeConnection(graphene.ObjectType):
    items = graphene.List(PaymentModeType)


class GstTypeType(DjangoObjectType):
    class Meta:
        model = GstType
        fields = "__all__"


class GstTypeConnection(graphene.ObjectType):
    items = graphene.List(GstTypeType)


class ItemStockByPartCodeType(DjangoObjectType):
    total_current_stock = graphene.Int()

    class Meta:
        model = ItemStock
        field = '__all__'


class ItemStockByPartCodeConnection(graphene.ObjectType):
    items = graphene.List(ItemStockByPartCodeType)


class FixedOptionType(graphene.ObjectType):
    id = graphene.String()
    eWayBillUom = graphene.String()


class FixedOptionConnection(graphene.ObjectType):
    items = graphene.List(FixedOptionType)


class posStatusType(graphene.ObjectType):
    id = graphene.String()
    Status = graphene.String()


class posStatusConnection(graphene.ObjectType):
    items = graphene.List(posStatusType)


class PosTypeType(graphene.ObjectType):
    id = graphene.String()
    posType = graphene.String()


class PosTypeConnection(graphene.ObjectType):
    items = graphene.List(PosTypeType)


class WorkCenterMasterType(DjangoObjectType):
    class Meta:
        model = WorkCenter
        fields = '__all__'


class WorkCenterMasterConnection(graphene.ObjectType):
    items = graphene.List(WorkCenterMasterType)
    page_info = graphene.Field(PageInfoType)


class BomRoutingType(DjangoObjectType):
    class Meta:
        model = BomRouting
        field = '__all__'


class BomRoutingConnection(graphene.ObjectType):
    items = graphene.List(BomRoutingType)


class posStockReportType(graphene.ObjectType):
    sno = graphene.String()
    part_number = graphene.String()
    part_name = graphene.String()
    stock_in = graphene.Int()
    stock_out = graphene.Int()
    stock_blance = graphene.Int()
    conference = graphene.String()


class posStockReportConnection(graphene.ObjectType):
    items = graphene.List(posStockReportType)


class StockHistoryType(graphene.ObjectType):
    id = graphene.Int()
    part_code_id = graphene.Int()
    start_stock = graphene.String()
    end_stock = graphene.String()
    date = graphene.String()
    added = graphene.String()
    reduced = graphene.String()
    transaction_id = graphene.Int()
    transaction_module = graphene.String()
    saved_by = graphene.String()
    unit = graphene.String()
    display_id = graphene.String()
    is_delete = graphene.String()
    display_name = graphene.String()


class StockHistoryConnection(graphene.ObjectType):
    items = graphene.List(StockHistoryType)


class RawMaterialBomLinkType(DjangoObjectType):
    class Meta:
        model = RawMaterialBomLink
        fields = "__all__"


class RawMaterialBomLinkConnection(graphene.ObjectType):
    items = graphene.List(RawMaterialBomLinkType)


class posDetailsResportObjectType(graphene.ObjectType):
    id = graphene.Int()
    IsPOS = graphene.String()
    OrderDate = graphene.String()
    POSId = graphene.String()
    CosName = graphene.String()
    Mobile = graphene.String()
    FinalTotalValue = graphene.Float()
    balanceAmount = graphene.Float()
    Remarks = graphene.String()
    Payments = GenericScalar()


class posDetailsResportTotalAmountType(graphene.ObjectType):
    FinalTotalValue = graphene.Decimal()
    balanceAmount = graphene.Decimal()
    bank = GenericScalar()


class posDetailsResportConnection(graphene.ObjectType):
    items = graphene.List(posDetailsResportObjectType)
    total_amount = graphene.Field(posDetailsResportTotalAmountType)


class PosReportType(graphene.ObjectType):
    total_pos_amount = graphene.String()
    current_balance_amount = graphene.String()
    cash_amount_received = graphene.String()
    bank_amount_received = graphene.String()
    swipe_amount_received = graphene.String()


class PosReportConnection(graphene.ObjectType):
    items = graphene.List(PosReportType)


class ImageType(DjangoObjectType):
    class Meta:
        model = Imagedata
        fields = "__all__"


class DocumentType(DjangoObjectType):
    class Meta:
        model = Document
        fields = "__all__"


class StockStatementItemComboQtyType(graphene.ObjectType):
    qty = graphene.Int()


class StockStatementItemComboQtyConnection(graphene.ObjectType):
    items = graphene.List(StockStatementItemComboQtyType)


class StatesType(DjangoObjectType):
    class Meta:
        model = States
        fields = "__all__"


class StatesConnection(graphene.ObjectType):
    items = graphene.List(StatesType)


class DistrictsType(DjangoObjectType):
    class Meta:
        model = Districts
        fields = "__all__"


class DistrictsConnection(graphene.ObjectType):
    items = graphene.List(DistrictsType)


class PincodeType(DjangoObjectType):
    class Meta:
        model = Pincode
        fields = "__all__"


class PincodeConnection(graphene.ObjectType):
    items = graphene.List(PincodeType)


class AreaNamesType(DjangoObjectType):
    class Meta:
        model = AreaNames
        fields = "__all__"


class AreaNamesConnection(graphene.ObjectType):
    items = graphene.List(AreaNamesType)


class AddressMasterType(DjangoObjectType):
    class Meta:
        model = AddressMaster
        fields = "__all__"


class AddressMasterConnection(graphene.ObjectType):
    items = graphene.List(AddressMasterType)


class DepartmentType(DjangoObjectType):
    class Meta:
        model = Department
        fields = "__all__"


class DepartmentConnection(graphene.ObjectType):
    items = graphene.List(DepartmentType)
    page_info = graphene.Field(PageInfoType)


class TermsConditionsType(DjangoObjectType):
    class Meta:
        model = TermsConditions
        fields = "__all__"
        convert_choices_to_enum = False


class TermsConditionsConnection(graphene.ObjectType):
    items = graphene.List(TermsConditionsType)
    page_info = graphene.Field(PageInfoType)


class OtherExpensesType(DjangoObjectType):
    class Meta:
        model = OtherExpenses
        fields = "__all__"


class OtherExpensesConnection(graphene.ObjectType):
    items = graphene.List(OtherExpensesType)
    page_info = graphene.Field(PageInfoType)

purchaseOrderItemDetailsType = create_graphene_type(purchaseOrderItemDetails)
other_expenses_purchase_order = create_graphene_type(OtherExpensespurchaseOrder)


class purchaseOrderType(DjangoObjectType):
    class Meta:
        model = purchaseOrder
        fields = "__all__"
        convert_choices_to_enum = False


class versionListType(graphene.ObjectType):
    versionList = graphene.List(graphene.Int)


class purchaseOrderConnection(graphene.ObjectType):
    items = graphene.List(purchaseOrderType)
    page_info = graphene.Field(PageInfoType)
    version = graphene.Field(versionListType)


class OtherExpensespurchaseOrderType(DjangoObjectType):
    class Meta:
        model = OtherExpensespurchaseOrder
        fields = "__all__"


class OtherExpensespurchaseOrderConnection(graphene.ObjectType):
    items = graphene.List(OtherExpensespurchaseOrderType)

class purchaseSupplierUpdateitemtax(graphene.ObjectType):
    items = graphene.JSONString()
    other_expence = graphene.JSONString()
    items = graphene.JSONString()
    other_expence = graphene.JSONString()

class GinInitialFetch(graphene.ObjectType):
    items = graphene.JSONString()
 

GoodsInwardNote_type = create_graphene_type(GoodsInwardNote)
GoodsInwardNoteItemDetails_type = create_graphene_type(GoodsInwardNoteItemDetails)
 
class getGinDataForQir(graphene.ObjectType):
    items = graphene.JSONString()


QualityInspectionsReportItemDetailsType = create_graphene_type(QualityInspectionsReportItemDetails)
QualityInspectionReportType = create_graphene_type(QualityInspectionReport)

GoodsReceiptNoteItemDetailsType = create_graphene_type(GoodsReceiptNoteItemDetails)
GoodsReceiptNoteType = create_graphene_type(GoodsReceiptNote)

"""Delivery Challan"""
ReworkDeliveryChallanItemDetailsType = create_graphene_type(ReworkDeliveryChallan)
ReworkDeliveryChallanType = create_graphene_type(ReworkDeliveryChallan)

PurchaseInvoiceItemDetailType = create_graphene_type(PurchaseInvoiceItemDetails)
PurchaseInvoiceType = create_graphene_type(PurchaseInvoice)

PurchaseRetunBatchType = create_graphene_type(PurchaseRetunBatch)
PurchaseReturnChallanItemDetailsType = create_graphene_type(PurchaseReturnChallanItemDetails)
PurchaseReturnChallanType = create_graphene_type(PurchaseReturnChallan)

DirectPurchaseInvoiceAccountsType = create_graphene_type(DirectPurchaseInvoiceAccount)
DirectPurchaseInvoiceItemDetailsType = create_graphene_type(DirectPurchaseInvoiceItemDetails)
DirectPurchaseinvoiceType = create_graphene_type(DirectPurchaseinvoice)
 
    
"""DeliveryChallanItemDetails"""
DeliveryChallanItemDetailsType = create_graphene_type(ReworkDeliveryChallanItemDetails)

"DebitNote"
DebitNoteOtherIncomeChargesType = create_graphene_type(DebitNoteOtherIncomeCharge)
DebitNoteItemDetailType = create_graphene_type(DebitNoteItemDetail)
DebitNoteType = create_graphene_type(DebitNote)


"""contact_type"""
Contact_type_type = create_graphene_type(Contact_type)


 
EditListViewType = create_graphene_type(EditListView)


class EditListViewTypeConnection(graphene.ObjectType):
    items = graphene.List(EditListViewType)
    page_info = graphene.Field(PageInfoType)


"""ReportTemplate Type"""
ReportTemplateType = create_graphene_type(ReportTemplate)

"User Group"
UserGroupType = create_graphene_type(UserGroup)

"Department"
DepartmentType = create_graphene_type(Department)

AccountsLedgerViewType = create_graphene_type(AccountsGeneralLedger)

BankDeatilsType = create_graphene_type(BankDetails)


class AccountsGeneralLedgerTypeConnection(graphene.ObjectType):
    items = graphene.List(AccountsLedgerViewType)
    total_debit = graphene.Decimal()
    total_credit = graphene.Decimal()
    page_info = graphene.Field(PageInfoType)


def apply_case_insensitive_sorting(queryset, order_by, descending, db_s):
    """
    Apply case-insensitive sorting to the queryset based on the given order_by field.
    """
    order_by_config = db_s.get(order_by)
    if order_by_config:
        order_by_field = order_by_config["field"]
        is_text_field = order_by_config["is_text"]

        if is_text_field:
            # For text fields, annotate with a lowercased version for case-insensitive sorting
            annotated_field_name = f'lower_{order_by_field}'
            queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
            order_by_field = annotated_field_name

        # Determine sorting direction
        if descending:
            order_by_field = f'-{order_by_field}'

        # Apply sorting
        queryset = queryset.order_by(order_by_field)

    return queryset

class AccountsGeneralLedgerFilterOptionListType(graphene.ObjectType):
    account_names = graphene.List(graphene.String)
    payment_voucher_nos = graphene.List(graphene.String)
    customer_suppliers = graphene.List(graphene.String)
    employees = graphene.List(graphene.String)
    voucher_types = graphene.List(graphene.String)
    voucher_no = graphene.List(graphene.String)
    purchase_account = graphene.List(graphene.String)

class ChildGeneralLedgerAccountList(graphene.ObjectType):
    id = graphene.String()
    account_names = graphene.String()

class ChildAccountGeneralLedgertype(graphene.ObjectType):
    date = graphene.Date()
    account = graphene.String()
    voucher_type = graphene.String()
    voucher_id = graphene.Int()
    voucher_no = graphene.String()
    debit = graphene.String()
    credit = graphene.String()




class ChildAccountGeneralLedgertypeConnection(graphene.ObjectType):
    items = graphene.List(ChildAccountGeneralLedgertype)
    total_debit = graphene.Decimal()
    total_credit = graphene.Decimal()
    page_info = graphene.Field(PageInfoType)

class Query(ObjectType):
    all_company_master = graphene.List(company_Type, id=graphene.Int())
    item_master = graphene.Field(ItemMasterConnection, page=graphene.Int(), page_size=graphene.Int(),
                                 order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),ids=graphene.List(graphene.Int),
                                 item_part_code=graphene.String(), item_name=graphene.String(),
                                 id_gt=graphene.Int(),
                                 id_lt=graphene.Int(),
                                 id_gte=graphene.Int(),
                                 id_lte=graphene.Int(),
                                 id_start=graphene.Int(),
                                 id_end=graphene.Int(),
                                 item_group=graphene.String(),
                                 category=graphene.String(), item_uom=graphene.String(),
                                 item_types=graphene.String(), item_indicators=graphene.String(),
                                 service=graphene.Boolean(),
                                 item_types_list = graphene.List(graphene.String),
                                 item_combo_bool=graphene.Boolean(), keep_stock=graphene.Boolean(),
                                 item_active=graphene.Boolean(),
                                 any=graphene.Boolean(), bom_linked=graphene.Boolean(),
                                 item_part_code_equals=graphene.String(),
                                 item_indicators_list=graphene.List(graphene.String), is_manufacture=graphene.Boolean(),
                                 source_from=graphene.String(),is_hsn_taxable=graphene.String())

    item_indicators = graphene.Field(ItemIndicatorsConnection)
    item_Type = graphene.Field(ItemTypeConnection)
    uom = graphene.Field(UomConnection, page=graphene.Int(), page_size=graphene.Int(), order_by=graphene.String(),
                         descending=graphene.Boolean(), name=graphene.String(), e_way_bill_uom=graphene.String(),
                         id=graphene.Int(), description_text=graphene.String())

    numbering_series = graphene.Field(NumberingSeriesConnection, page=graphene.Int(), page_size=graphene.Int(),
                                      order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                      numbering_series_name=graphene.String(),
                                      resource=graphene.String(), formate=graphene.String(),
                                      pos_type=graphene.Int(), current_value=graphene.Int(),
                                      default=graphene.Boolean(), active=graphene.Boolean()
                                      )
    resource_pos_type = graphene.Field(ResourcePosTypeConnection)
    currency_exchange_connection = graphene.Field(CurrencyExchangeConnection, page=graphene.Int(),
                                                  page_size=graphene.Int(), order_by=graphene.String(),
                                                  descending=graphene.Boolean(), name=graphene.String(),
                                                  rate=graphene.Decimal(),
                                                  rate_gt=graphene.Int(),  # Add id_min argument
                                                  rate_lt=graphene.Int(),  # Add id_max argument
                                                  rate_gte=graphene.Int(),  # Add id_min argument
                                                  rate_lte=graphene.Int(),  # Add id_max argument
                                                  rate_start=graphene.Int(),
                                                  rate_end=graphene.Int(),
                                                  date=graphene.String(), id=graphene.Int())
    currency_master = graphene.Field(CurrencyMasterConnection, page=graphene.Int(),
                                     page_size=graphene.Int(), order_by=graphene.String(),
                                     descending=graphene.Boolean(), name=graphene.String(),
                                     currency_symbol=graphene.String(), active=graphene.Boolean(),
                                     formate=graphene.String(), id=graphene.Int(), any=graphene.Boolean(),
                                     )
    # currency_Formate = graphene.Field(CurrencyFormateTypeConnection)
    item_groups_name = graphene.Field(ItemGroupsNameConnection, page=graphene.Int(), page_size=graphene.Int(),
                                      order_by=graphene.String(), descending=graphene.Boolean(),
                                      name=graphene.String(), parent_group=graphene.String(), hsn=graphene.String(),
                                      id=graphene.Int(), any=graphene.Boolean())
    alternate_unit = List(Alternate_Unit_Type, id=graphene.Int())
    categories = graphene.Field(CategoryConnection)
    supplier_form_data = graphene.Field(SupplierFormDataConnection, page=graphene.Int(), page_size=graphene.Int(),
                                        order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.ID(),
                                        supplier_no=graphene.String(),
                                        company_name=graphene.String(), legal_name=graphene.String(),
                                        gstin=graphene.String(), pan_no=graphene.String(),
                                        contact_person_name=graphene.String(), phone_number=graphene.String(),
                                        address_type=graphene.String(), city=graphene.String(),
                                        country=graphene.String(), state=graphene.String(),
                                        supplier=graphene.Boolean(), customer=graphene.Boolean(),
                                        transporter=graphene.Boolean(), source=graphene.String(),
                                        any=graphene.Boolean(), is_lead=graphene.Boolean(),
                                        is_lead_search=graphene.Boolean(),active=graphene.Boolean())

    accounts_master = graphene.Field(AccountsMasterConnection, page=graphene.Int(), page_size=graphene.Int(),
                                     order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                     accounts_name=graphene.String(), accounts_group_name=graphene.String()
                                     , gst_applicable=graphene.Boolean(), tds=graphene.Boolean(),
                                     accounts_active=graphene.Boolean(), accounts_type=graphene.String(),
                                     accounts_type_only=graphene.String(),
                                     accounts_type2=graphene.String(), account_master_type=graphene.String(),
                                     account_master_type_2=graphene.String(),account_type_list = graphene.List(graphene.String),
                                     allow_receipt=graphene.Boolean(), account_choice_type=graphene.String(), any=graphene.Boolean())
    accounts_master_type_with_index = graphene.List(
        AccountsMaster_Type,
        # Add other arguments here if needed
    )
    accounts_group_type = graphene.Field(AccountsGroupTypeConnection)
    accounts_group = graphene.Field(AccountsGroupsConnection, page=graphene.Int(), page_size=graphene.Int(),
                                    order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                    accounts_group_name=graphene.String(), accounts_type=graphene.String(),
                                    accounts_type2=graphene.String(),
                                    group_active=graphene.Boolean(), any=graphene.Boolean())
    Store = graphene.Field(StoreConnection, page=graphene.Int(), page_size=graphene.Int(), order_by=graphene.String(),
                           descending=graphene.Boolean(), store_name=graphene.String(), store_account=graphene.String()
                           , store_incharge=graphene.String(), matained=graphene.Boolean(), action=graphene.Boolean(),
                           id=graphene.Int(), any=graphene.Boolean(),is_conference=graphene.Boolean())
    hsn_type = graphene.Field(HsnType_TypeConnection)
    gst_rate = graphene.Field(GstRate_TypeConnection)
    gst_type = graphene.Field(GstTypeConnection ,company_master=graphene.Boolean())
    numbering_series_linking = graphene.Field(NumberingSeriesLinkingConnection)
    hsn = graphene.Field(HsnConnection, page=graphene.Int(), page_size=graphene.Int(), order_by=graphene.String(),
                         descending=graphene.Boolean(), id=graphene.Int(), hsn_types=graphene.String(),
                         hsn_code=graphene.Int(),
                         description="", gstRates=graphene.Int(), cess_rate=graphene.Int(), rcm=graphene.Boolean(),
                         itc=graphene.Boolean(), any=graphene.Boolean())
    display_group = graphene.Field(DisplayGroupConnection, id=graphene.Int(), part_code=graphene.Int())
    customer_groups = graphene.Field(CustomerGroupsConnection, page=graphene.Int(), page_size=graphene.Int(),
                                     order_by=graphene.String(), descending=graphene.Boolean(),
                                     name=graphene.String(), name_contains=graphene.String())
    contact_detalis = graphene.Field(ContactDetalisConnection, page=graphene.Int(), page_size=graphene.Int(),
                                     order_by=graphene.String(),
                                     descending=graphene.Boolean(), id=graphene.Int(), phone_number=graphene.String(),
                                     user_name=graphene.String(), email=graphene.String())
    company_address = graphene.Field(CompanyAddressConnection, id=graphene.Int())
    supplier_groups = graphene.Field(SupplierGroupsConnection, page=graphene.Int(),
                                     page_size=graphene.Int(),
                                     order_by=graphene.String(), descending=graphene.Boolean(), name=graphene.String())
    item_combo = List(ItemComboType, id=Int(required=False))
    User = graphene.Field(UserConnection, UserName=graphene.String(), email=graphene.String())
    finished_goods = graphene.Field(FinishedGoodsConnection, id=graphene.Int(), finished_goods_name=graphene.String())
    raw_materials = graphene.Field(RawMaterialConnection, id=graphene.Int(), id_list=graphene.List(graphene.Int))
    scrap = graphene.Field(ScrapConnection, id=graphene.Int(), id_list=graphene.List(graphene.Int))
    routing = graphene.Field(RoutingConnection, route_name=graphene.String(), route_name_contains=graphene.String())
    bom_routing = graphene.Field(BomRoutingConnection, id=graphene.Int(), id_list=graphene.List(graphene.Int),
                                 order_by=graphene.String(), descending=graphene.Boolean())
    bom_status = graphene.Field(BomStatusConnection)
    bom_type_option = graphene.Field(BomTypeOptionConnection)
    bom = graphene.Field(BomConnection, page=graphene.Int(), page_size=graphene.Int(),
                         id=graphene.Int(),
                         id_gt=graphene.Int(), id_lt=graphene.Int(), id_gte=graphene.Int(), id_lte=graphene.Int(),
                         id_start=graphene.Int(), id_end=graphene.Int(),
                         total_raw_material=graphene.Int(),
                         total_raw_material_gt=graphene.Int(), total_raw_material_lt=graphene.Int(),
                         total_raw_material_gte=graphene.Int(), total_raw_material_lte=graphene.Int(),
                         total_raw_material_start=graphene.Int(), total_raw_material_end=graphene.Int(),
                         bom_name=graphene.String(), updated_at=graphene.String(),
                         status=graphene.Int(), finished_goods=graphene.Int(), modified_by=graphene.Int(),
                         order_by=graphene.String(), descending=graphene.Boolean(), bom_name_contains=graphene.String(),
                         is_active=graphene.Boolean(), is_default=graphene.Boolean(),
                         finished_goods_part_code=graphene.Int(), bom_type=graphene.String(), bom_no=graphene.String(),
                         bom_no_contains=graphene.String(), finished_goods_part_code_list=graphene.List(graphene.Int)
                         )
    stock_serial_history = graphene.Field(StockSerialHistoryConnection)
    stock_statement = graphene.Field(StockStatementConnection, page=graphene.Int(), page_size=graphene.Int(),
                                     part_code=graphene.String(), part_name=graphene.String(),
                                     current_stock=graphene.Int(), item_group=graphene.String(),
                                     stores=graphene.String(), order_by=graphene.String(),
                                     descending=graphene.Boolean(), )
    stock_statement_part_view = graphene.Field(StockStatementPartView, part_id=graphene.Int())
    serial_number = graphene.Field(SerialNumberConnection, page=graphene.Int(), page_size=graphene.Int(),
                                   serial_number=graphene.String(), id=graphene.Int(),
                                   serial_number_list=graphene.List(graphene.String))
    batch_number = graphene.Field(BatchNumberConnection, page=graphene.Int(), page_size=graphene.Int(),
                                  batch_number_name=graphene.String(), batch_number=graphene.Int(),
                                  part_number=graphene.Int())
    serial_is_duplicate = graphene.Field(SerialNumberisDupilicate, serial_number_list=graphene.List(graphene.String),
                        part_number=graphene.Int())

    item_stock = graphene.Field(QueryItemStockConnection, page=graphene.Int(), page_size=graphene.Int(),
                                store=graphene.Int(), current_stock=graphene.Float(),
                                serial_number=graphene.Int(), batch_number=graphene.Int(),
                                unit=graphene.Int(), last_serial_history=graphene.Int(), part_number=graphene.Int()
                                , batch_number_string=graphene.String(),
                                part_code = graphene.String(),part_name = graphene.String())
    
    stock_items = graphene.Field(QueryItemStockConnection, page=graphene.Int(), page_size=graphene.Int(),
                                 stock_ids=graphene.List(graphene.Int))
    stock_ids = graphene.Field(QueryStockIdConnection, part_number=graphene.Int(), store=graphene.Int())
    stock_history_log = graphene.Field(StockHistoryLogConnection, stock_id=graphene.List(graphene.Int))
    inventory_approval = graphene.Field(InventoryApprovalConnection, page=graphene.Int(),
                                        page_size=graphene.Int(), approval_id=graphene.List(graphene.Int),
                                        item_part_code=graphene.String(), item_name=graphene.String(),
                                        qty=graphene.Int(), serial_number_joined=graphene.String(),
                                        batch_number=graphene.String(), store=graphene.String(),
                                        qty_gt=graphene.Int(), qty_lt=graphene.Int(), qty_gte=graphene.Int(),
                                        qty_lte=graphene.Int(),
                                        qty_start=graphene.Int(), qty_end=graphene.Int(), order_by=graphene.String(),
                                        descending=graphene.Boolean(), part_number=graphene.String())
    inventory_handler = graphene.Field(InventoryHandlerConnection, page=graphene.Int(), page_size=graphene.Int(),
                                       inventory_handler_id=graphene.String(), store=graphene.String(),
                                       saved_by=graphene.String(), created_at=graphene.String(),
                                       order_by=graphene.String(), descending=graphene.Boolean(),
                                       starts_with=graphene.String(), id=graphene.ID())

    sales_order = graphene.Field(SalesOrderConnection, page=graphene.Int(), page_size=graphene.Int(),
                                 order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.ID(),
                                 POSId=graphene.String(), posType=graphene.String(), CosName=graphene.String(),
                                 Mobile=graphene.String(), FinalTotalValue=graphene.Decimal(),
                                 balanceAmount=graphene.Decimal(), status=graphene.String(),
                                 Pending=graphene.Boolean(), isDelivered=graphene.Boolean(), remark=graphene.String(),
                                 createdby=graphene.String(), OrderDate=graphene.String(), Remarks=graphene.String(),
                                 marketingEvent=graphene.String())
    sales_order_item = graphene.Field(SalesOrderItemConnection, id=graphene.Int())
    sales_order_item_overall_discount_percentage = graphene.Field(SalesOrderItemConnection,
                                                                  id_list=graphene.List(graphene.Int),
                                                                  percentage=graphene.Int())
    sales_order_itemoverall_discount_value = graphene.Field(SalesOrderItemConnection,
                                                            id_list=graphene.List(graphene.Int),
                                                            totalToSubtract=graphene.Int())
    sales_order_item_final_total_discount = graphene.Field(SalesOrderItemConnection,
                                                           id_list=graphene.List(graphene.Int),
                                                           final_total=graphene.Float(),
                                                           TotalWithTaxValue=graphene.Float()
                                                           )
    sales_order_item_clear_discount = graphene.Field(SalesOrderItemConnection,
                                                     id_list=graphene.List(graphene.Int))
    sales_order_item_combo = graphene.Field(SalesOrderItemComboConnection, id=graphene.Int(),
                                            id_list=graphene.List(graphene.Int))
    payment_mode = graphene.Field(PaymentModeConnection, id=graphene.Int(), idList=graphene.List(graphene.Int))
    eway_bill_options = graphene.Field(FixedOptionConnection, eWayBillUom=graphene.String())
    pos_status = graphene.Field(posStatusConnection, Status=graphene.String())  
    postype_options = graphene.Field(PosTypeConnection, posType=graphene.String())
    item_stock_by_part_code = graphene.Field(ItemStockByPartCodeConnection, part_number=graphene.Int())
    work_center_master = graphene.Field(WorkCenterMasterConnection, page=graphene.Int(), page_size=graphene.Int(),
                                        work_center=graphene.String())
    raw_material_bom_link = graphene.Field(RawMaterialBomLinkConnection,
                                           bom=graphene.Int(), raw_material=graphene.Int())
    stock_history_details = graphene.Field(StockHistoryConnection, page=graphene.Int(), transaction_id=graphene.Int(),
                                           stock_id=graphene.List(graphene.Int), transaction_module=graphene.String())
    pos_stock_report = graphene.Field(posStockReportConnection, part_id=graphene.Int(),
                                      conference_id=graphene.Int()
                                      )
    pos_report = graphene.Field(PosReportConnection, event_id=graphene.Int(), start_date=graphene.String(),
                                end_date=graphene.String())
    report_details = graphene.Field(posDetailsResportConnection, event=graphene.Int(), start_date=graphene.String(),
                                    end_date=graphene.String(), iscollectionswise=graphene.Boolean(),
                                    useriId=graphene.Int())
    item_master_history = graphene.Field(ItemMasterHistoryConnection, id=graphene.Int())
    stock_statement_item_combo_qty = graphene.Field(StockStatementItemComboQtyConnection, id=graphene.Int(),
                                                    store=graphene.Int())
    states_list = graphene.Field(StatesConnection, id=graphene.Int(), state=graphene.String(), page=graphene.Int())
    districts_list = graphene.Field(DistrictsConnection, id=graphene.Int(), districts=graphene.String(),
                                    page=graphene.Int())
    pincode_list = graphene.Field(PincodeConnection, id=graphene.Int(), pincode=graphene.String(), page=graphene.Int())
    area_name_list = graphene.Field(AreaNamesConnection, area_name=graphene.String(), page=graphene.Int())
    address_master_list = graphene.Field(AddressMasterConnection, area_name=graphene.Int(),
                                         state=graphene.Int(), districts=graphene.Int(),
                                         pincode=graphene.Int(), pincode_string=graphene.String(),
                                         area_name_distinct=graphene.Boolean(),
                                         pincode_distinct=graphene.Boolean(), state_distinct=graphene.Boolean(),
                                         district_distinct=graphene.Boolean(), )
    department = graphene.Field(DepartmentConnection, id=graphene.Int(), page=graphene.Int(), page_size=graphene.Int(),
                                order_by=graphene.String(), descending=graphene.Boolean(), name=graphene.String())
    terms_conditions = graphene.Field(TermsConditionsConnection, page=graphene.Int(), page_size=graphene.Int(),
                                      order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                      name=graphene.String(), module=graphene.String())
    other_expenses = graphene.Field(OtherExpensesConnection, page=graphene.Int(), page_size=graphene.Int(),
                                    order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                    account=graphene.String(), active=graphene.Boolean(), account_group = graphene.String())
     
    other_expenses_purchase_order = graphene.Field(OtherExpensespurchaseOrderConnection, d=graphene.Int())
    purchase_order = graphene.Field(purchaseOrderConnection, page=graphene.Int(), page_size=graphene.Int(),
                                    order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                    active=graphene.Boolean(), purchaseOrder_no=graphene.String(),
                                    createdAt=graphene.String(), status=graphene.String(), supplierId=graphene.String(),
                                    isSupplierDistinct=graphene.Boolean(), companyName=graphene.String(),
                                    department=graphene.String(), isDepartmentDistinct=graphene.Boolean(),
                                    receivingStoreId=graphene.String(), isreceivingStoreDistinct=graphene.Boolean(),
                                    dueDate=graphene.String(), netAmount=graphene.String(), netAmount_gt=graphene.Int(),
                                    netAmount_lt=graphene.Int(), netAmount_gte=graphene.Int(),
                                    netAmount_lte=graphene.Int(),
                                    netAmount_start=graphene.Int(), netAmount_end=graphene.Int(),supplier=graphene.Int(),department_id=graphene.Int())
    
    purchase_supplier_update_item_tax = graphene.Field(purchaseSupplierUpdateitemtax, gst_nature_transaction=graphene.Int(),
                                                    state=graphene.String(),
                                                    itemdetails=graphene.List(graphene.Int),
                                                    otherexpenses =graphene.List(graphene.Int))
    purchase_time_line = graphene.Field(PurchaseTimeLine, purchase_id= graphene.Int())
    gin_initial_fetch = graphene.Field(GinInitialFetch, id=graphene.Int(), parent_module = graphene.String(), rework_id = graphene.Int())
    gin_edit_fetch = graphene.Field(GinInitialFetch, id=graphene.Int()) 
    goods_inward_note_type = graphene.List(GoodsInwardNote_type, id=graphene.Int())
    qir_initial_fetch = graphene.Field(getGinDataForQir, id=graphene.Int())
    qir_edit_fetch = graphene.Field(getGinDataForQir, id=graphene.Int())
    grn_initial_fetch  = graphene.Field(getGinDataForQir, id=graphene.Int())
    grn_edit_fetch  = graphene.Field(getGinDataForQir, id=graphene.Int())
    rework_delivery_challan_initial_fetch = graphene.Field(getGinDataForQir, id=graphene.Int())
    rework_delivery_challan = graphene.Field(getGinDataForQir, id=graphene.Int())
    quality_inspection_report_type = graphene.List(QualityInspectionReportType, id=graphene.Int())
    goods_receipt_note_type = graphene.List(GoodsReceiptNoteType, id=graphene.Int())
    rework_delivery_challan_type = graphene.Field(ReworkDeliveryChallanType, id=graphene.Int())
    purchase_invoice_selete_multi_purchase = graphene.Field(getGinDataForQir, supplier_id=graphene.Int(),
                                                        department_id=graphene.Int())
    purchase_invoice_initial_fetch = graphene.Field(getGinDataForQir, grn_id=graphene.List(graphene.Int), conformation=graphene.Boolean())
    purchase_invoice_edit_fetch = graphene.Field(getGinDataForQir, id=graphene.Int())
    purchase_return_multi_select = graphene.Field(getGinDataForQir, supplier_id=graphene.Int(),
                                                        department_id=graphene.Int(),module=graphene.String())
    initial_purchase_return_fetch = graphene.Field(getGinDataForQir,  grn_item_id=graphene.List(graphene.Int), purchase_invoice_item_ids=graphene.List(graphene.Int))
    edit_purchase_return_fetch = graphene.Field(getGinDataForQir,   purchase_return_id=graphene.Int())
    initial_debit_note_fetch = graphene.Field(getGinDataForQir,   purchase_return_id=graphene.Int())
    edit_debit_note_fetch = graphene.Field(getGinDataForQir,  debit_note_id=graphene.Int())
    direct_purchase_invoice = graphene.List(DirectPurchaseinvoiceType, id=graphene.Int())

    CommonStatus_type = graphene.List(CommonStatusType, table=graphene.String())
    EditListView_type = graphene.Field(EditListViewTypeConnection, page=graphene.Int(), page_size=graphene.Int(),
                                       table=graphene.String(), userID=graphene.Int(), id=graphene.Int(),
                                       view_name=graphene.String())
    ReportTemplate_report_folder_type = graphene.List(ReportTemplateType, report_folder=graphene.String())
    ReportTemplate_type = graphene.List(ReportTemplateType, id=graphene.ID())
    all_UserGroup_type = graphene.List(UserGroupType, id=graphene.ID(), group_name=graphene.String())
    allDepartment_type = graphene.List(DepartmentType, id=graphene.ID(),name=graphene.String())
    accounts_general_ledger = graphene.Field(AccountsGeneralLedgerTypeConnection, 
                                                 page=graphene.Int(),
                                                 page_size=graphene.Int(), order_by=graphene.String(),
                                                 descending=graphene.Boolean(),
                                                 date=graphene.String(),amount_filter=graphene.String(), employee=graphene.String(), 
                                                 voucher_type=graphene.String(),account_name=graphene.String(),purchase_account=graphene.String(),
                                                 remark=graphene.String(), customer_supplier=graphene.String(), voucher_no=graphene.String())
    accounts_general_ledger_filter_options = graphene.Field(
            AccountsGeneralLedgerFilterOptionListType,
            account_name=graphene.String(),
            payment_voucher_no=graphene.String(),
            customer_supplier=graphene.String(),
            employee=graphene.String(),
            voucher_type=graphene.String(),
            voucher_no=graphene.String(),
            purchase_account=graphene.String(),
            purchase_amount=graphene.Decimal()
            
        )
    child_account_general_ledger = graphene.Field(ChildAccountGeneralLedgertypeConnection,
                                                page=graphene.Int(),page_size=graphene.Int(), id=graphene.ID())
    child_general_ledger_account_list = List(ChildGeneralLedgerAccountList, account_name=graphene.String(required=False))
    
    gst_nature_transaction = List(GSTNatureTransactionType, id=graphene.Int(),gst_type = graphene.Int(),
                                applies_to =graphene.String(), gst_type_name=graphene.String())

    @permission_required(models=["GST Nature Transaction","Purchase_Order","Quotation","SalesOrder_2"])
    def resolve_gst_nature_transaction(self, info,id=None,gst_type=None,applies_to=None,gst_type_name=None):
        filter_kwargs = {}
        query = GSTNatureTransaction.objects.all()
        if id:
            filter_kwargs['id'] = id
        if gst_type:
            filter_kwargs['gstin_types__id'] = gst_type
        if applies_to:
            filter_kwargs['applies_to__icontains'] = applies_to
        if gst_type_name:
            filter_kwargs['gstin_types__gst_type'] = gst_type_name 
        return query.filter(**filter_kwargs)

    @permission_required(models=["ReportTemplate"])
    def resolve_ReportTemplate_report_folder_type(self, info, report_folder):
        query = ReportTemplate.objects.filter(report_folder__icontains=report_folder).distinct()
        return query
    @permission_required(models=["ReportTemplate"])
    def resolve_ReportTemplate_type(self, info, id):
        if id:
            query = ReportTemplate.objects.filter(id=id)
            return query

    def resolve_EditListView_type(self, info, page=1, page_size=10, table=None, userID=None, id=None, view_name=None):
        if view_name:
            query = Q(view_name__icontains=view_name) & Q(table=table) & (
                    Q(visible_to="Myself", created_by=userID) |
                    Q(visible_to="All User") |
                    Q(visible_to="Select Users", visible_to_user__in=[userID]))
        elif id:
            query = Q(id=id)
        else:
            query = Q(table=table) & (
                    Q(visible_to="Myself", created_by=userID) |
                    Q(visible_to="All User") |
                    Q(visible_to="Select Users", visible_to_user__in=[userID]))

        query = EditListView.objects.filter(query)
        paginator = Paginator(query, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return EditListViewTypeConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["POS_Report"])
    def resolve_pos_report(self, info, event_id=None, start_date=None, end_date=None):
        start_date_dt = datetime.strptime(start_date, '%d-%m-%Y')
        end_date_dt = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
        current_event_payment_modes = ""

        filter_criteria = {'marketingEvent__id': event_id}

        sales_orders = SalesOrder.objects.filter(**filter_criteria).exclude(status='Canceled')
        total_amount = sales_orders.aggregate(Sum('FinalTotalValue'))[
                           'FinalTotalValue__sum'] or 0

        total_received_amount = \
            sales_orders.aggregate(Sum('receivedAmount'))[
                'receivedAmount__sum'] or 0
        payment_ids = sales_orders.values_list('payment', flat=True)

        filter_kwargs = {}
        if len(payment_ids) > 0:
            filter_kwargs['id__in'] = payment_ids
            if start_date_dt == end_date_dt:
                filter_kwargs['CreatedAt__date'] = start_date_dt
            else:
                filter_kwargs['CreatedAt__range'] = (start_date_dt, end_date_dt)
            current_event_payment_modes = paymentMode.objects.filter(**filter_kwargs).annotate(
                account_type=Subquery(
                    AccountsMaster.objects.filter(id=OuterRef('payby')).values('account_type')[:1]
                )
            )
            seen_ids = set()
            total_balance = 0
            for sales_order in SalesOrder.objects.filter(payment__in=current_event_payment_modes, ).exclude(
                    status='Canceled'):

                if sales_order.id not in seen_ids:
                    latest_payment_id = current_event_payment_modes.filter(salesorder=sales_order).latest(
                        'id').balance_amount
                    total_balance += latest_payment_id
                    seen_ids.add(sales_order.id)
            for sales_order in SalesOrder.objects.filter(payment__isnull=True, marketingEvent__id=event_id).exclude(
                    status='Canceled'):
                if sales_order.id not in seen_ids:
                    total_balance += int(sales_order.balance_Amount)
            balance_amount = total_balance

        def filter_payments_by_type(payment_type):
            return current_event_payment_modes.filter(account_type=payment_type).aggregate(total=Sum('pay_amount'))[
                'total'] or 0.00

        cash_amount_received = filter_payments_by_type('Cash')
        bank_amount_received = filter_payments_by_type('Bank')
        swipe_amount_received = filter_payments_by_type('Swipe')
        # Create a list of PosReportType instances
        pos_reports = [PosReportType(
            total_pos_amount=total_amount,
            current_balance_amount=balance_amount,
            cash_amount_received=cash_amount_received,
            bank_amount_received=bank_amount_received,
            swipe_amount_received=swipe_amount_received,
        )]

        # Return the connection object with the list of reports
        return PosReportConnection(items=pos_reports)

    @permission_required(models=["Item_Master"], type="query", action="History")
    def resolve_item_master_history(self, info, id=None):
        queryset = ItemMasterHistory.objects.filter(id=id)
        return ItemMasterHistoryConnection(items=queryset)

    @permission_required(models=["POS"])
    def resolve_states_list(self, into, id=None, state=None, page=1):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if state:
            filter_kwargs['state_name__icontains'] = state
        queryset = States.objects.filter(**filter_kwargs)
        paginator = Paginator(queryset, 500)
        paginated_data = paginator.get_page(page)
        return StatesConnection(items=paginated_data.object_list)

    @permission_required(models=["POS"])
    def resolve_districts_list(self, into, id=None, districts=None, page=1):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if districts:
            filter_kwargs['district__icontains'] = districts
        queryset = Districts.objects.filter(**filter_kwargs)
        paginator = Paginator(queryset, 500)
        paginated_data = paginator.get_page(page)

        return DistrictsConnection(items=paginated_data.object_list)

    @permission_required(models=["POS", "Enquiry"])
    def resolve_address_master_list(self, into, area_name=None, pincode=None, pincode_string=None, state=None,
                                    districts=None,
                                    area_name_distinct=None, pincode_distinct=None, state_distinct=None,
                                    district_distinct=None):

        filter_kwargs = {}
        distinct_fields = []
        if district_distinct is not None:
            distinct_fields.append('district')
        if area_name_distinct is not None:
            distinct_fields.append('area_name')
        if pincode_distinct is not None:
            distinct_fields.append('pincode')
        if state_distinct is not None:
            distinct_fields.append('state_distinct')
        if area_name:
            filter_kwargs['area_name'] = area_name
        if pincode_string:
            filter_kwargs['pincode__pincode'] = pincode_string
        if pincode:
            filter_kwargs['pincode'] = pincode
        if state:
            filter_kwargs['state'] = state
        if districts:
            filter_kwargs['district'] = districts
        address_master_queryset = AddressMaster.objects.filter(**filter_kwargs)
        if distinct_fields:
            try:
                address_master_queryset = address_master_queryset.distinct(*distinct_fields)
            except Exception as e:
                return GraphQLError(f"Error applying distinct:{e}")
                
        return AddressMasterConnection(items=address_master_queryset)

    def resolve_districts_list(self, into, id=None, districts=None, page=1):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if districts:
            filter_kwargs['district__icontains'] = districts
        queryset = Districts.objects.filter(**filter_kwargs)
        paginator = Paginator(queryset, 500)
        paginated_data = paginator.get_page(page)

        return DistrictsConnection(items=paginated_data.object_list)

    @permission_required(models=["POS", "Enquiry"])
    def resolve_pincode_list(self, into, id=None, pincode=None, page=1):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if pincode:
            filter_kwargs['pincode__icontains'] = pincode
        queryset = Pincode.objects.filter(**filter_kwargs)
        paginator = Paginator(queryset, 500)
        paginated_data = paginator.get_page(page)
        return PincodeConnection(items=paginated_data.object_list)

    def resolve_area_name_list(self, into, area_name=None, page=1):
        queryset = AreaNames.objects.filter(area_name__icontains=area_name)
        paginator = Paginator(queryset, 500)
        paginated_data = paginator.get_page(page)
        return AreaNamesConnection(items=paginated_data.object_list)

    @permission_required(models=["Item_Master", "POS", "SalesOrder_2", "Quotation", "Stock_Addition","Purchase_Order","Purchase Return"])
    def resolve_item_master(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                            item_part_code=None,
                            id_gt=None, id_lt=None, id_gte=None, id_lte=None,
                            id_start=None, id_end=None,
                            item_name=None, category=None, item_group=None,
                            item_uom=None, item_types=None, item_indicators=None, service=None,
                            item_types_list =[],
                            item_combo_bool=None,
                            bom_linked=None
                            , keep_stock=None, item_active=None, any=None, item_part_code_equals=None,
                            is_manufacture=None,
                            item_indicators_list=None, source_from=None, is_hsn_taxable=None,ids=[]):
        """return the data with filter"""
        queryset = ItemMaster.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if ids:
            filter_kwargs['ids__in'] = ids
        if id_gt:
            filter_kwargs['id__gt'] = id_gt
        if id_lt:
            filter_kwargs['id__lt'] = id_lt
        if id_gte:
            filter_kwargs['id__gte'] = id_gte
        if id_lte:
            filter_kwargs['id__lte'] = id_lte
        if id_start and id_end:
            filter_kwargs['id__range'] = (id_start, id_end)
        if item_part_code_equals:
            filter_kwargs['item_part_code'] = item_part_code_equals
        if item_part_code:
            filter_kwargs['item_part_code__icontains'] = item_part_code
        if item_name:
            filter_kwargs['item_name__icontains'] = item_name
        if category:
            filter_kwargs['category__name__icontains'] = category
        if item_group:
            filter_kwargs['item_group__name__icontains'] = item_group
        if item_uom:
            filter_kwargs['item_uom__name__icontains'] = item_uom
        
        if item_types_list:
            filter_kwargs['item_types__name__in'] = item_types_list

        if item_types:
            filter_kwargs['item_types__name__icontains'] = item_types
        if item_indicators:
            filter_kwargs['item_indicators__name__icontains'] = item_indicators
        if source_from:
            if source_from == 'fg':
                # filter_kwargs['category__in'] = [16, 17, 20]
                filter_kwargs['category__in'] = [23, 1, 3]  # live
            elif source_from == 'rm':
                # filter_kwargs['category__in'] = [17, 18, 19, 21]
                filter_kwargs['category__in'] = [2, 3, 4, 21]  # live
        if item_types_list:
            filter_kwargs['service__in'] = item_types_list
        if service is not None:
            filter_kwargs['service'] = service
        if item_combo_bool is not None:
            filter_kwargs['item_combo_bool'] = item_combo_bool
        if keep_stock is not None:
            filter_kwargs['keep_stock'] = keep_stock
        if item_active is not None:
            filter_kwargs['item_active'] = item_active
        if is_manufacture is not None:
            filter_kwargs['is_manufacture'] = is_manufacture
        if is_hsn_taxable is not None:
            filter_kwargs['item_hsn__taxability_type']= "taxable"
        indicators_q = Q()
        if item_indicators_list is not None:
            for indicator in item_indicators_list:
                indicators_q |= Q(item_indicators__name__icontains=indicator)
        if any:
            pass
        else:
            filter_kwargs['item_active'] = True
        db_s = {
            "id": {"field": "id", "is_text": False},
            'itemPartCode': {"field": 'item_part_code', "is_text": True},
            'itemName': {"field": 'item_name', "is_text": True},
            "itemGroup": {"field": 'item_group', "is_text": True},
            "category": {"field": 'category', "is_text": True},
            "itemUom": {"field": 'item_uom', "is_text": True},
            "itemTypes": {"field": 'item_types', "is_text": True},
            "itemIndicators": {"field": 'item_indicators', "is_text": True},
            "service": {"field": 'service', "is_text": True},
            "itemComboBool": {"field": 'item_combo_bool', "is_text": True},
            "keepStock": {"field": 'keepStock', "is_text": True},
            "itemActive": {"field": 'item_active', "is_text": True},
        } 
        try:
            queryset = queryset.filter(**filter_kwargs)
        except Exception as e:
            return GraphQLError(f'An exception occurred {str(e)}')
        # Apply case-insensitive sorting
        
        if indicators_q:  # Check if indicators_q has conditions
            queryset = queryset.filter(indicators_q)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        if bom_linked is not None:
            if bom_linked:
                queryset = queryset.filter(id__in=FinishedGoods.objects.values_list('part_no', flat=True))
            else:
                queryset = []
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return ItemMasterConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Item_Master", ])
    def resolve_item_indicators(self, info):
        queryset = Item_Indicator.objects.all()

        return ItemIndicatorsConnection(
            items=queryset,
        )

    @permission_required(models=["Item_Master"])
    def resolve_item_Type(self, info):
        queryset = ItemType.objects.all()
        return ItemTypeConnection(
            items=queryset,
        )

    @permission_required(models=["UOM", "Item_Master"])
    def resolve_uom(self, info, page=1, page_size=20, order_by=None, descending=False, name=None,
                    e_way_bill_uom=None, id=None,
                    description_text=None
                    ):
        """retun the data with filiter"""
        queryset = UOM.objects.all().order_by('-id')

        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        if e_way_bill_uom:
            filter_kwargs['e_way_bill_uom'] = e_way_bill_uom
        if description_text:
            filter_kwargs['description_text__icontains'] = description_text
        db_s = {
            'name': {"field": 'name', "is_text": True},
            'eWayBillUom': {"field": 'e_way_bill_uom', "is_text": True},
            'descriptionText': {"field": 'description_text', "is_text": True}
        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return UomConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    # @permission_required(models=["Item_Master"])
    def resolve_item_stock_by_part_code(self, info, part_number=None):
        data = []
        if part_number:
            item_stock_query = ItemStock.objects.filter(part_number=part_number, store__matained=True)
            first_item_stock = item_stock_query.first()
            if first_item_stock:
                total_current_stock = item_stock_query.aggregate(total_current_stock=Sum('current_stock'))[
                    'total_current_stock']
                total_current_stock = total_current_stock if total_current_stock is not None else 0
                first_item_stock.total_current_stock = total_current_stock
                data.append(first_item_stock)
        return ItemStockByPartCodeConnection(items=data)

    @permission_required(models=["Item_Group", "Item_Master"])
    def resolve_item_groups_name(self, info, page=1, page_size=20, order_by=None, descending=False, name=None,
                                 parent_group=None, hsn=None, id=None, ):

        """retun the data with filiter"""
        queryset = Item_Groups_Name.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        if parent_group:
            filter_kwargs['parent_group__name__icontains'] = parent_group
        if hsn:
            filter_kwargs['hsn__hsn_code__icontains'] = hsn

        db_s = {
            'name': {"field": 'name', "is_text": True},
            'parentGroup': {"field": 'parent_group', "is_text": False},
            'hsn': {"field": 'hsn', "is_text": False}
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

        return ItemGroupsNameConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_alternate_unit(self, info, id=None):
        queryset = Alternate_unit.objects.filter(id=id)
        return queryset

    def resolve_sales_order_item(self, info, id=None):
        queryset = SalesOrderItem.objects.filter(id=id)
        return SalesOrderItemConnection(items=queryset)

    def resolve_sales_order_item_overall_discount_percentage(self, info, id_list=[], percentage=0):
        # Fetch all items that need updating
        SalesOrderItems = SalesOrderItem.objects.filter(id__in=id_list)

        updates = []

        for SalesOrderSingleItem in SalesOrderItems:
            percentageValue = (Decimal(SalesOrderSingleItem.rate) / Decimal(100)) * Decimal(percentage)
            rate = Decimal(SalesOrderSingleItem.rate) - percentageValue
            finalamount = Decimal(SalesOrderSingleItem.qty) * rate

            SalesOrderSingleItem.amount = finalamount
            SalesOrderSingleItem.discount_value_for_per_item = rate
            SalesOrderSingleItem.discount_percentage = Decimal(percentage)
            updates.append(SalesOrderSingleItem)

        # Use bulk_update to apply changes in a single database call
        with transaction.atomic():  # Ensure atomicity of the bulk update
            SalesOrderItem.objects.bulk_update(updates,
                                               ['amount', 'discount_value_for_per_item', 'discount_percentage'])

        return SalesOrderItemConnection(items=updates)

    def resolve_sales_order_itemoverall_discount_value(self, info, id_list=[], totalToSubtract=0):
        try:
            # Ensure `totalToSubtract` is a Decimal
            total_to_subtract = Decimal(totalToSubtract)
        except (TypeError, ValueError):
            raise ValueError("totalToSubtract must be a decimal number")

        SalesOrderItems = SalesOrderItem.objects.filter(id__in=id_list)

        # Handle case where no items are returned
        if not SalesOrderItems:
            return SalesOrderItemConnection(items=[])

        total_value = sum(Decimal(item.amount) for item in SalesOrderItems)
        total_checked_value = total_value or Decimal('1')  # Prevent division by zero

        # Calculate reductions for each item
        reductions = [(Decimal(item.rate) / total_checked_value) * total_to_subtract for item in SalesOrderItems]

        # Prepare data for bulk update
        updates = []
        for index, item in enumerate(SalesOrderItems):
            try:
                discounted_rate = Decimal(item.rate) - reductions[index]
                final_amount = Decimal(item.qty) * discounted_rate

                item.amount = final_amount.quantize(Decimal('0.01'))
                item.discount_value_for_per_item = discounted_rate.quantize(Decimal('0.01'))
                item.discount_value = reductions[index].quantize(Decimal('0.01'))

                # Add to updates list
                updates.append(item)
            except (InvalidOperation, TypeError) as e:
                raise ValueError(f"Error processing item {item.id}: {e}")

        # Use bulk_update to apply changes in a single database call
        with transaction.atomic():  # Ensure atomicity of the bulk update
            SalesOrderItem.objects.bulk_update(
                updates,
                ['amount', 'discount_value_for_per_item', 'discount_value']
            )

        return SalesOrderItemConnection(items=updates)

    def resolve_sales_order_item_final_total_discount(self, info, id_list=None, final_total=0, TotalWithTaxValue=0):
        if id_list is None:
            id_list = []
        SalesOrderItems = SalesOrderItem.objects.filter(id__in=id_list)

        total_value = sum(Decimal(item.amount) for item in SalesOrderItems)
        rounded_final_total = round(Decimal(final_total), 2)
        total_checked_value = round(Decimal(total_value), 2) if not TotalWithTaxValue else round(
            Decimal(TotalWithTaxValue), 2)
        ratios = [Decimal(item.rate) / total_checked_value for item in SalesOrderItems]
        reductions = [ratio * (total_checked_value - rounded_final_total) for ratio in ratios]

        updates = []
        for index, item in enumerate(SalesOrderItems):
            discounted_rate = Decimal(item.rate) - reductions[index]
            final_amount = discounted_rate * Decimal(item.qty)

            item.amount = final_amount.quantize(Decimal('0.01'))
            item.discount_value_for_per_item = reductions[index].quantize(Decimal('0.01'))
            item.final_value = reductions[index].quantize(Decimal('0.01'))

            updates.append(item)

        with transaction.atomic():
            SalesOrderItem.objects.bulk_update(
                updates,
                ['amount', 'discount_value_for_per_item', 'final_value']
            )

        return SalesOrderItemConnection(items=updates)

    def resolve_sales_order_item_clear_discount(self, info, id_list=None, ):
        if id_list is None:
            id_list = []
        SalesOrderItems = SalesOrderItem.objects.filter(id__in=id_list)
        updates = []
        for index, item in enumerate(SalesOrderItems):
            amount = Decimal(item.rate) * Decimal(item.qty)

            item.amount = amount.quantize(Decimal('0.01'))
            item.discount_value_for_per_item = None
            item.discount_percentage = None
            item.final_value = None
            item.discount_value = None
            updates.append(item)
            # Use bulk_update to apply changes in a single database call
        with transaction.atomic():  # Ensure atomicity of the bulk update
            SalesOrderItem.objects.bulk_update(updates,
                                               ['amount', 'discount_value_for_per_item', 'discount_percentage',
                                                'final_value', 'discount_value'])

        return SalesOrderItemConnection(items=updates)

    def resolve_sales_order_item_combo(self, info, id=None, id_list=None):
        queryset = SalesOrderItemCombo.objects.all()
        if id:
            queryset = queryset.filter(id=id)
        if id_list:
            queryset = queryset.filter(id__in=id_list)
        return SalesOrderItemComboConnection(items=queryset)

    def resolve_sales_order(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                            POSId=None, posType=None, CosName=None,
                            Mobile=None, FinalTotalValue=None, balanceAmount=None,
                            Pending=None, isDelivered=None, Remarks=None,
                            createdby=None, OrderDate=None, status=None, marketingEvent=None
                            ):

        # """retun the data with filiter"""
        queryset = SalesOrder.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if marketingEvent:
            filter_kwargs['marketingEvent__name'] = marketingEvent
        if POSId:
            filter_kwargs['POS_ID__linked_model_id__icontains'] = POSId
        if posType:
            filter_kwargs['posType'] = posType
        if CosName:
            filter_kwargs['CosName__icontains'] = CosName
        if Mobile:
            filter_kwargs['Mobile__icontains'] = Mobile
        if FinalTotalValue:
            filter_kwargs['FinalTotalValue__icontains'] = FinalTotalValue
        if balanceAmount:
            filter_kwargs['balance_Amount__icontains'] = balanceAmount
        if Pending != None:
            filter_kwargs['Pending'] = Pending
        if isDelivered != None:
            filter_kwargs['isDelivered'] = isDelivered
        if createdby:
            filter_kwargs['createdby__username'] = createdby
        if status:
            filter_kwargs['status'] = status
        if Remarks:
            filter_kwargs["Remarks__icontains"] = Remarks
        if OrderDate:
            start_date, end_date = OrderDate.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['OrderDate__range'] = (updated_start_date, updated_end_date)
            else:
                filter_kwargs['OrderDate__range'] = (updated_start_date, updated_end_date)
        db_s = {
            'id': {"field": 'id', "is_text": False},
            "POSId": {"field": 'POS_ID', "is_text": False},
            "marketingEvent": {"field": 'marketingEvent__name', "is_text": True},
            "posType": {"field": 'posType', "is_text": True},
            "CosName": {"field": 'CosName', "is_text": True},
            "status": {"field": 'status', "is_text": True},
            "FinalTotalValue": {"field": 'FinalTotalValue', "is_text": False},
            "balanceAmount": {"field": 'balance_Amount', "is_text": False},
            "Pending": {"field": "Pending", "is_text": False},
            "isDelivered": {"field": "isDelivered", "is_text": False},
            "OrderDate": {"field": "OrderDate", "is_text": False},
            "CreatedAt": {"field": "CreatedAt", "is_text": False},
            "Remarks": {"field": "Remarks", "is_text": True},
        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return SalesOrderConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["POS_Detailed_Report", "POS_Collection_Repor"])
    def resolve_report_details(self, info, event=None, start_date=None, end_date=None, iscollectionswise=None,
                               useriId=None):
        updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
        updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
        filter_criteria = {}
        if iscollectionswise:
            if updated_start_date == updated_end_date:
                filter_criteria['CreatedAt__date'] = updated_start_date
            else:
                filter_criteria['CreatedAt__range'] = (updated_start_date, updated_end_date)
        payment_prefetch = Prefetch('payment', queryset=paymentMode.objects.filter(
            **filter_criteria
        ))
        """retun the data with filiter"""
        queryset = SalesOrder.objects.all().order_by('-id')
        queryset = queryset.exclude(status="Canceled")
        filter_kwargs = {}
        user_data = UserPermission.objects.filter(user_id=useriId).first()

        if event != 0:
            if not iscollectionswise:
                if updated_start_date == updated_end_date:
                    filter_kwargs['OrderDate__date'] = updated_start_date
                else:
                    filter_kwargs['OrderDate__range'] = (updated_start_date, updated_end_date)
            if event:
                filter_kwargs['marketingEvent__id'] = event
            queryset = queryset.filter(**filter_kwargs).prefetch_related(payment_prefetch).all()
            queryset_items = serializers.serialize("json", queryset)
            report_details_data = []
            for queryset_item in json.loads(queryset_items):
                stock_item_dict = queryset_item['fields']
                stock_item_dict['id'] = queryset_item['pk']
                report_details_data.append(stock_item_dict)
            processed_data = posDetailsReports(report_details_data)
            return posDetailsResportConnection(
                items=processed_data[0],
                total_amount=processed_data[-1]
            )
        elif user_data.is_admin_person:
            queryset = queryset.filter(**filter_kwargs).prefetch_related(payment_prefetch).all()
            queryset_items = serializers.serialize("json", queryset)
            report_details_data = []
            for queryset_item in json.loads(queryset_items):
                stock_item_dict = queryset_item['fields']
                stock_item_dict['id'] = queryset_item['pk']
                report_details_data.append(stock_item_dict)
            processed_data = posDetailsReports(report_details_data)
            return posDetailsResportConnection(
                items=processed_data[0],
                total_amount=processed_data[-1]
            )
        else:

            return posDetailsResportConnection(
                items=None,
                total_amount=None
            )

    def resolve_payment_mode(self, info, id=None, idList=None):
        queryset = []
        if id:
            queryset = paymentMode.objects.filter(id=id).order_by('id')
        if idList:
            queryset = paymentMode.objects.filter(id__in=idList).order_by('id')
        return PaymentModeConnection(items=queryset)

    @permission_required(models=["Item_Master", ])
    def resolve_categories(self, info, **kwargs):
        queryset = Category.objects.filter(active=True)
        return CategoryConnection(
            items=queryset
        )

    @permission_required(models=["Currency_Master"])
    def resolve_currency_Formate(self, info):
        queryset = CurrencyFormate.objects.all()
        return CurrencyFormateTypeConnection(items=queryset)

    # @permission_required(models=["Contact", "Supplier", "Customer", "POS", "Enquiry"])
    def resolve_contact_detalis(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                                phone_number=None, user_name=None, email=None):
        queryset = ContactDetalis.objects.order_by('-id').all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if phone_number:
            filter_kwargs['phone_number__icontains'] = phone_number
        if user_name:
            filter_kwargs['contact_person_name__icontains'] = user_name
        if email:
            filter_kwargs['email__icontains'] = email
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return ContactDetalisConnection(items=paginated_data.object_list, page_info=page_info)

    def resolve_company_address(self, info, id=None):
        queryset = CompanyAddress.objects.filter(id=id)
        return queryset

    @permission_required(models=["Supplier", "Customer", "Item_Master", "Lead", "SalesOrder_2", "POS","Purchase_Order","Debit Note",
                                 "Receipt Voucher", 'PaymentVoucher',"Credit Note"])
    def resolve_supplier_form_data(self, info, page=1, page_size=20, order_by=None, descending=False, company_name=None,
                                   supplier_no=None, legal_name=None, gstin=None, pan_no=None, contact_person_name=None,
                                   phone_number=None, state=None, supplier=None, customer=None, transporter=None,
                                   address_type=None, city=None, country=None, id=None, source=None, any=None,
                                   is_lead=False, is_lead_search=None,active=None):
        """retun the data with filiter"""
        queryset = SupplierFormData.objects.order_by('-id').all()
        # supplierDataImport.updateSupplier()
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if supplier_no:
            filter_kwargs['supplier_no__icontains'] = supplier_no
        if company_name:
            filter_kwargs['company_name__icontains'] = company_name
        if legal_name:
            filter_kwargs['legal_name__icontains'] = legal_name
        if gstin:
            filter_kwargs['gstin__icontains'] = gstin
        if pan_no:
            filter_kwargs['pan_no__icontains'] = pan_no
        if contact_person_name:
            filter_kwargs['contact__contact_person_name__icontains'] = contact_person_name
            filter_kwargs['contact__default'] = True
        if phone_number:
            filter_kwargs['contact__phone_number__icontains'] = phone_number
            filter_kwargs['contact__default'] = True
        if address_type:
            filter_kwargs['address__address_type__icontains'] = address_type
            filter_kwargs['address__default'] = True
        if city:
            filter_kwargs['address__city__icontains'] = city
            filter_kwargs['address__default'] = True
        if country:
            filter_kwargs['address__country__icontains'] = country
            filter_kwargs['address__default'] = True
        if state:
            filter_kwargs['address__state__icontains'] = state
            filter_kwargs['address__default'] = True
        if supplier:
            filter_kwargs['supplier'] = supplier
        if customer:
            filter_kwargs['customer'] = customer
        if transporter:
            filter_kwargs['transporter'] = transporter
        if not is_lead_search:
            if is_lead != None:
                filter_kwargs['is_lead'] = is_lead
        if active:
            filter_kwargs['active'] = active
        if any:
            pass
        else:
            filter_kwargs['active'] = True
        if source:
            customer_supplier_filter = Q(customer=True, supplier=True)
            if source == 'Customer':
                supplier_filter = Q(customer=True)
            elif source == 'Supplier':
                supplier_filter = Q(supplier=True)
            if customer_supplier_filter and supplier_filter:
                combined_filter = supplier_filter | customer_supplier_filter
                queryset = queryset.filter(combined_filter)
        """Apply sorting"""

        queryset = queryset.filter(**filter_kwargs)

        db_s = {
            'companyName': {"field": 'company_name', "is_text": True},
            'legalName': {"field": 'legal_name', "is_text": True},
            'gstin': {"field": 'gstin', "is_text": True},
            'panNo': {"field": 'pan_no', "is_text": True},
            'contactPersonName': {"field": 'contact__contact_person_name', "is_text": True,
                                  "sub_field": 'contact__default'},
            'phoneNumber': {"field": 'contact__phone_number', "is_text": True, "sub_field": 'contact__default'},
            'addressType': {"field": 'address__address_type', "is_text": True, "sub_field": 'address__default'},
            'city': {"field": 'address__city', "is_text": True, "sub_field": 'address__default'},
            'state': {"field": 'address__state', "is_text": True, "sub_field": 'address__default'},
            'country': {"field": 'address__country', "is_text": True, "sub_field": 'address__default'},
        }
        if order_by:
            order_by_config = db_s.get(order_by)
            if 'sub_field' in order_by_config:
                filter_kwargs[order_by_config['sub_field']] = True
            queryset = queryset.filter(**filter_kwargs)
            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'
            # Apply sorting
            queryset = queryset.order_by(order_by_field)
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return SupplierFormDataConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Account_Group", "Item_Master", "Accounts_Master"])
    def resolve_accounts_group_type(self, info):
        queryset = AccountsgroupType.objects.all()
        return AccountsGroupTypeConnection(
            items=queryset
        )

    @permission_required(models=["Account_Group", "Item_Master", "Accounts_Master"])
    def resolve_accounts_group(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                               accounts_group_name=None, accounts_type=None, group_active=None, accounts_type2=None,
                               any=None):

        queryset = AccountsGroup.objects.all().order_by('-id')

        """Apply filters using Q objects for complex queries"""
        filter_conditions = Q()
        if id:
            filter_conditions &= Q(id=id)
        if accounts_group_name:
            filter_conditions &= Q(accounts_group_name__icontains=accounts_group_name)
        if accounts_type:
            filter_conditions &= Q(accounts_type__name__icontains=accounts_type)
        # To handle multiple account types, you might need to adjust the logic if accounts_type and accounts_type2 should be treated as 'OR'
        if accounts_type2:
            # This line assumes you want to OR accounts_type and accounts_type2 conditions
            # filter_conditions &= Q(accounts_type__name__icontains=accounts_type) | Q(accounts_type__name__icontains=accounts_type2)
            filter_conditions |= Q(accounts_type__name__icontains=accounts_type2)
        if group_active is not None:  # Explicit check for None allows False values
            filter_conditions &= Q(group_active=group_active)
        if any:
            pass
        else:
            filter_conditions &= Q(group_active=True)

        db_s = {
            'accountsGroupName': {"field": 'accounts_group_name', "is_text": True},
            'accountsType': {"field": 'accounts_type', "is_text": False},
            'groupActive': {"field": 'group_active', "is_text": False}
        }
        queryset = queryset.filter(filter_conditions)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return AccountsGroupsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Accounts_Master", "Item_Master", "Store", "Other_Expenses", "Other_Income","POS","PaymentVoucher","ExpenseRequest",
                                 "Receipt Voucher", 'PaymentVoucher'])
    def resolve_accounts_master(self, info, page=1, page_size=20, order_by=None, descending=False, id=None,
                                accounts_name=None, accounts_group_name=None, gst_applicable=None, tds=None,
                                accounts_active=None, accounts_type2=None, accounts_type=None, accounts_type_only=None,
                                account_master_type=None, account_master_type_2=None, allow_receipt=None, any=None,
                                account_choice_type=None,account_type_list = []
                                ):
        """retun the data with filiter"""
        queryset = AccountsMaster.objects.all().order_by('-id')
        # Start with a base Q object for optional chaining of filters
        filter_conditions = Q()
        # Dynamically add filters based on provided values
        if id:
            filter_conditions &= Q(id=id)
        if accounts_name:
            filter_conditions &= Q(accounts_name__icontains=accounts_name)
        if accounts_type_only:
            filter_conditions &= Q(account_type__icontains=accounts_type_only)
        if accounts_group_name:
            filter_conditions &= Q(accounts_group_name__accounts_group_name__icontains=accounts_group_name)
        if accounts_type:
            filter_conditions &= Q(accounts_group_name__accounts_type__name__icontains=accounts_type)
        if account_type_list:  # Pythonic way to check if list has items
            filter_conditions &= Q(account_type__in=account_type_list)
        if accounts_type2:
            filter_conditions |= Q(
                accounts_group_name__accounts_type__name__icontains=accounts_type2)  # OR condition for the second type
        if gst_applicable is not None:
            filter_conditions &= Q(gst_applicable=gst_applicable)
        if account_master_type:
            filter_conditions &= Q(account_type=account_master_type)
        if account_master_type_2:
            filter_conditions |= Q(
                account_type=account_master_type_2)
        if allow_receipt is not None:
            filter_conditions &= Q(allow_receipt=allow_receipt)
        if tds is not None:
            filter_conditions &= Q(tds=tds)
        if accounts_active is not None:
            filter_conditions &= Q(accounts_active=accounts_active)
        if account_choice_type:
            filter_conditions &= Q(account_type=account_choice_type)
        if any:
            pass
        else:
            filter_conditions &= Q(accounts_active=True)

        db_s = {
            'accountsName': {"field": 'accounts_name', "is_text": True},
            'accountType': {"field": 'accounts_group_name', "is_text": False},
            'gstApplicable': {"field": 'gst_applicable', "is_text": False},
            'tds': {"field": 'tds', "is_text": False},
            'accountsActive': {"field": 'accounts_active', "is_text": False},
        }
        queryset = queryset.filter(filter_conditions)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)

        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        # Construct page info
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return AccountsMasterConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_accounts_master_type_with_index(self, info, **kwargs):
        queryset = AccountsMaster.objects.filter(account_type__in=['Bank', 'Cash', 'Swipe'])
        accounts_list = list(queryset)

        # Sort by set_pos_report, assigning a default value of `float('inf')` for empty or None values
        accounts_list.sort(
            key=lambda account: account.set_pos_report if account.set_pos_report is not None else float('inf')
        )
        return accounts_list

    @permission_required(models=["HSN"])
    def resolve_hsn_type(self, info):
        queryset = HsnType.objects.all()
        return HsnType_TypeConnection(
            items=queryset,
        )

    @permission_required(models=["HSN"])
    def resolve_gst_rate(self, info):
        queryset = GstRate.objects.all().exclude(rate__in=[12, 28])
        return GstRate_TypeConnection(
            items=queryset,
        )



    @permission_required(models=["Customer", "Supplier"])
    def resolve_gst_type(self, info,company_master = None):
        queryset = GstType.objects.all()
        if company_master:
            allowed_gst_types = ["REGULAR", "REGULAR-SEZ", "COMPOSITION"]
            queryset = queryset.filter(gst_type__in=allowed_gst_types)
            pass
        return GstTypeConnection(items=queryset)

    @permission_required(models=["HSN"])
    def resolve_numbering_series_linking(self, info):
        queryset = NumberingSeriesLinking.all()
        return GstTypeConnection(items=queryset)

    @permission_required(models=["HSN", "Item_Master", "Other_Expenses", "Other_Income", "Item_Group"])
    def resolve_hsn(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, hsn_types=None,
                    hsn_code=None, description=None, gstRates=None, cess_rate=None, rcm=None,
                    itc=None, any=None):
        
        """retun the data with filiter"""
        queryset = Hsn.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {k: v for k, v in {
            'id': id,
            'hsn_types__name__icontains': hsn_types,
            'hsn_code__icontains': hsn_code,
            'description__icontains': description,
            'cess_rate__icontains': cess_rate,
            'rcm__icontains': rcm,
            'itc__icontains': itc,
        }.items() if v is not None}
        if id:
            filter_kwargs['id'] = id
        if hsn_types:
            filter_kwargs['hsn_types__name__icontains'] = hsn_types
        if description:
            filter_kwargs['description__icontains'] = description

        if gstRates is not None:
            filter_kwargs['gst_rates__rate'] = gstRates
        if cess_rate:
            filter_kwargs['cess_rate__icontains'] = cess_rate
        if rcm:
            filter_kwargs['rcm__icontains'] = rcm
        if itc:
            filter_kwargs['itc__icontains'] = itc

        db_s = {
            'hsnCode': {"field": 'hsn_code', "is_text": False},
            'hsnTypes': {"field": 'hsn_types', "is_text": False},
            'gstRates': {"field": 'gst_rates', "is_text": False},
            "description": {"field": 'description', "is_text": True},
            'cessRate': {"field": 'cess_rate', "is_text": False},
            'rcm': {"field": 'rcm', "is_text": False},
            'itc': {"field": 'itc', "is_text": False},

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

        return HsnConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Store", "Stock_Addition", "Conference", "POS","Purchase_Order", "Purchase Return"])
    def resolve_Store(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, store_name=None,
                      store_account=None, store_incharge=None,
                      matained=None, action=None, any=None,is_conference=None):
        user = info.context.user
        """retun the data with filiter"""
        queryset = Store.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if store_name:
            filter_kwargs['store_name__icontains'] = store_name
        if store_account:
            filter_kwargs['store_account__accounts_name__icontains'] = store_account
        if store_incharge:
            filter_kwargs['store_incharge__username__icontains'] = store_incharge
        if matained is not None:
            filter_kwargs['matained__icontains'] = matained
        if is_conference is not None:
            filter_kwargs['conference'] = is_conference
        if action:
            filter_kwargs['action__icontains'] = action
        if any:
            pass
        else:
            filter_kwargs['action__icontains'] = True

        db_s = {
            'storeName': {"field": 'store_name', "is_text": True},
            'storeAccount': {"field": 'store_account', "is_text": False},
            'storeIncharge': {"field": 'store_incharge', "is_text": False},
            'matained': {"field": 'matained', "is_text": False},
            'action': {"field": 'action', "is_text": False}
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
        return StoreConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_display_group(self, info, id=None, part_code=None):
        if id:
            queryset = display_group.objects.filter(id=id)
        elif part_code:
            queryset = display_group.objects.select_related('part_number').filter(part_number=part_code)
        else:
            queryset = display_group.objects.all()
        return DisplayGroupConnection(items=queryset)

    def resolve_item_combo(self, info, id=None):
        if id is not None:
            # Using filter instead of get to ensure we always return a QuerySet (list-like)
            return Item_Combo.objects.filter(id=id)
        else:
            # Return all items if no ID is specified
            return Item_Combo.objects.all()

    @permission_required(models=["Customer"])
    def resolve_customer_groups(self, info, page=1, page_size=20, order_by=None, descending=False,
                                name=None, name_contains=None):
        """retun the data with filiter"""
        queryset = CustomerGroups.objects.all().order_by('-id')
        filter_kwargs = {}
        if name:
            filter_kwargs['name'] = name
        if name_contains:
            filter_kwargs['name__icontains'] = name_contains
        queryset = queryset.filter(**filter_kwargs)
        """Apply sorting"""
        if order_by:
            if descending:
                order_by = f"-{order_by}"
            queryset = queryset.filter(**filter_kwargs).order_by(order_by)
        else:
            queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return CustomerGroupsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Supplier"])
    def resolve_supplier_groups(self, page=1, page_size=20, order_by=None, descending=False, name=None):
        """retun the data with filiter"""
        queryset = SupplierGroups.objects.all().order_by('-id')
        filter_kwargs = {}
        """Apply sorting"""
        if order_by:
            if descending:
                order_by = f"-{order_by}"
            queryset = queryset.filter(**filter_kwargs).order_by(order_by)
        else:
            if name:
                filter_kwargs['name__icontains'] = name
            queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return SupplierGroupsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(
        models=["User_Management", "Roles", "Store", "ActivityType", "Lead", "Department", "ReportTemplate",
                "Conference", "POS","Customer","Supplier"])
    def resolve_User(self, info, UserName=None, email=None):
        queryset = User.objects.all()
        if UserName:
            queryset = queryset.filter(username__icontains=UserName)
        if email:
            queryset = queryset.filter(email__icontains=email)
        return UserConnection(
            items=queryset)

    def resolve_finished_goods(self, info, id=None, finished_goods_name=None):
        queryset = []

        if id:
            queryset = FinishedGoods.objects.filter(id=id)
        if finished_goods_name:
            queryset = FinishedGoods.objects.filter(part_no__item_name__icontains=finished_goods_name)
        return FinishedGoodsConnection(
            items=queryset
        )

    def resolve_raw_materials(self, info, id=None, id_list=None):
        query_set = []
        if id:
            query_set = RawMaterial.objects.filter(id=id)
        if id_list:
            query_set = RawMaterial.objects.filter(id__in=id_list)
        return RawMaterialConnection(
            items=query_set
        )

    def resolve_scrap(self, info, id=None, id_list=None):
        query_set = []
        if id:
            query_set = Scrap.objects.filter(id=id)
        if id_list:
            query_set = Scrap.objects.filter(id__in=id_list)
        return ScrapConnection(
            items=query_set
        )

    def resolve_routing(self, info, route_name=None, route_name_contains=None):
        querset = Routing.objects.all()
        if route_name:
            querset = Routing.objects.filter(route_name=route_name)
        if route_name_contains:
            querset = Routing.objects.filter(route_name__icontains=route_name_contains)
        return RoutingConnection(
            items=querset
        )

    def resolve_bom_routing(self, info, id=None, id_list=None, order_by=None, descending=None):
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if id_list:
            filter_kwargs['id__in'] = id_list

        db_s = {
            "id": {"field": "id", "is_text": False},
            'serialNumber': {"field": 'serial_number', "is_text": False},
            'route': {"field": 'route__route_name', "is_text": True},
            "work_center": {"field": 'work_center__work_center', "is_text": True},
            "duration": {"field": 'duration', "is_text": False},
        }
        queryset = []
        # Apply case-insensitive sorting
        if id or id_list:
            queryset = BomRouting.objects.filter(**filter_kwargs)
        if order_by and queryset:
            queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        return BomRoutingConnection(items=queryset)

    def resolve_bom_status(self, info):
        return BomStatusConnection(
            items=BomStatus.objects.all()
        )

    def resolve_bom_type_option(self, info):
        bom_type_option = [{'id': 1, 'bomType': 'MANUFACTURE'}, {'id': 2, 'bomType': 'SUBCONTRACT'}]
        return BomTypeOptionConnection(
            items=bom_type_option
        )

    def resolve_bom(self, info, page=1, page_size=20, id=None,
                    id_gt=None, id_lt=None, id_gte=None, id_lte=None,
                    id_start=None, id_end=None, total_raw_material=None,
                    total_raw_material_gt=None, total_raw_material_lt=None,
                    total_raw_material_gte=None, total_raw_material_lte=None,
                    total_raw_material_start=None, total_raw_material_end=None,
                    bom_name=None, updated_at=None, modified_by=None, status=None,
                    finished_goods=None, order_by=None, descending=None,
                    bom_name_contains=None, is_active=None, is_default=None,
                    finished_goods_part_code=None, bom_type=None, bom_no=None,
                    bom_no_contains=None, finished_goods_part_code_list=None,
                    ):
        queryset = Bom.objects.all().order_by('-id')
        filter_kwargs = {}
        if id:
            filter_kwargs['id__icontains'] = id
        if id_gt:
            filter_kwargs['id__gt'] = id_gt
        if id_lt:
            filter_kwargs['id__lt'] = id_lt
        if id_gte:
            filter_kwargs['id__gte'] = id_gte
        if id_lte:
            filter_kwargs['id__lte'] = id_lte
        if id_start and id_end:
            filter_kwargs['id__range'] = (id_start, id_end)
        if total_raw_material:
            filter_kwargs['total_raw_material__icontains'] = total_raw_material
        if total_raw_material_gt:
            filter_kwargs['total_raw_material__gt'] = total_raw_material_gt
        if total_raw_material_lt:
            filter_kwargs['total_raw_material__lt'] = total_raw_material_lt
        if total_raw_material_gte:
            filter_kwargs['total_raw_material__gte'] = total_raw_material_gte
        if total_raw_material_lte:
            filter_kwargs['total_raw_material__lte'] = total_raw_material_lte
        if total_raw_material_start and total_raw_material_end:
            filter_kwargs['total_raw_material__range'] = (total_raw_material_start, total_raw_material_end)
        if bom_name_contains:
            filter_kwargs['bom_name__icontains'] = bom_name_contains
        if bom_name:
            filter_kwargs['bom_name__icontains'] = bom_name
        if modified_by:
            filter_kwargs['modified_by'] = modified_by
        if updated_at:
            start_date, end_date = updated_at.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y')
            if start_date == end_date:
                filter_kwargs['updated_at__date'] = updated_start_date
            else:
                filter_kwargs['updated_at__range'] = (updated_start_date, updated_end_date)
        if status:
            filter_kwargs['status'] = status
        if finished_goods:
            filter_kwargs['finished_goods'] = finished_goods
        if is_active is not None:
            filter_kwargs['is_active'] = is_active
        if is_default is not None:
            filter_kwargs['is_default'] = is_default
        if finished_goods_part_code:
            filter_kwargs['finished_goods__part_no'] = finished_goods_part_code
        if finished_goods_part_code_list:
            filter_kwargs['finished_goods__part_no__in'] = finished_goods_part_code_list
        if bom_type:
            filter_kwargs['bom_type'] = bom_type
        if bom_no:
            filter_kwargs['bom_no'] = bom_no
        if bom_no_contains:
            filter_kwargs['bom_no__icontains'] = bom_no_contains
        db_s = {
            "id": {"field": "id", "is_text": False},
            'bomName': {"field": 'bom_name', "is_text": True},
            'bomNo': {"field": 'bom_no', "is_text": True},
            'modifiedBy': {"field": 'modified_by__username', "is_text": True},
            "updatedAt": {"field": 'updated_at', "is_text": True},
            "finishedGoods": {"field": 'finished_goods__part_no__item_name', "is_text": True},
            "totalRawMaterial": {"field": 'total_raw_material', "is_text": False},
            "status": {"field": 'status__status', "is_text": True}
        }

        if not filter_kwargs:
            clearUnwantedBomData()
        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs)
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return BomConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_stock_history(self, info):
        return StockSerialHistoryConnection(items=StockSerialHistory.objects().all())

    def resolve_batch_number(self, info, page=1, page_size=20, batch_number_name=None, batch_number=None,
                             part_number=None):
        queryset = BatchNumber.objects.all()
        filter_kwargs = {}
        if batch_number_name:
            filter_kwargs['batch_number_name__icontains'] = batch_number_name
        if batch_number:
            filter_kwargs['id'] = batch_number
        if part_number:
            filter_kwargs['part_number'] = part_number

        queryset = queryset.filter(**filter_kwargs)

        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return BatchNumberConnection(
            items=paginated_data.object_list,
            page_info=page_info)

    def resolve_serial_number(self, info, page=1, page_size=20, serial_number=None, id=None, serial_number_list=None):
        queryset = SerialNumbers.objects.all()
        filter_kwargs = {}
        if serial_number:
            filter_kwargs['serial_number__icontains'] = serial_number
        if id:
            filter_kwargs['id'] = id
        if serial_number_list:
            filter_kwargs['serial_number__in'] = serial_number_list
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        return SerialNumberConnection(items=paginated_data.object_list)
    
    def resolve_serial_is_duplicate(self, info, serial_number_list=None, part_number=None):
        serial_number_list = serial_number_list or []
        duplicate_serials = SerialNumbers.objects.filter(
            serial_number__in=serial_number_list,
            itemstock__part_number__id=part_number
        ).values_list("serial_number", flat=True).distinct()

        # Build list of SerialNumberStringType objects
        serial_objs = [SerialNumberStringType(serialNumber=s) for s in duplicate_serials]

        return SerialNumberisDupilicate(
            isDupulicate=bool(serial_objs),
            serial_number=serial_objs
        )

    def resolve_item_stock(self, info, page=1, page_size=20, store=None, part_number=None, batch_number=None,
                           batch_number_string=None,part_code = None,part_name = None):
        queryset = ItemStock.objects.select_related('store', 'unit', 'batch_number', 'part_number').all()
        filter_kwargs = {}
        if part_number:
            filter_kwargs['part_number__id'] = part_number
        if store:
            filter_kwargs['store'] = store
        if batch_number:
            filter_kwargs['batch_number'] = batch_number
        if batch_number_string:
            filter_kwargs['batch_number__batch_number_name'] = batch_number_string
        if part_code : 
            filter_kwargs['part_number__item_part_code__icontains'] = part_code
        if part_name : 
            filter_kwargs['part_number__item_name__icontains'] = part_name
            
        filter_kwargs['current_stock__gt'] = 0
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return ItemStockConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_stock_items(self, info, page=1, page_size=20, stock_ids=[]):
        queryset = ItemStock.objects.filter(
            id__in=stock_ids, 
            # store__matained=True,
        ).select_related(
            'store', 'unit', 'batch_number'
        ).prefetch_related('serial_number').filter(current_stock__gt=0).all()
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return ItemStockConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_stock_ids(self, info, part_number=None, store=None):
        filter = {}
        if part_number:
            filter['part_number'] = part_number
        if store:
            filter['store'] = store
        queryset = ItemStock.objects.filter(**filter).all()
        return QueryStockIdConnection(items=queryset)

    def resolve_stock_statement(self, info, page=1, page_size=20, part_code=None,
                                part_name=None, descending=None,
                                current_stock=None, order_by=None,
                                item_group=None, stores=None):
        filtered_items = ItemStock.objects.all()
        filter_criteria = {}
        aggregated_stock = {}
        if part_code:
            filter_criteria['part_number__item_part_code'] = part_code
        if part_name:
            filter_criteria['part_number__item_name'] = part_name
        if item_group:
            filter_criteria['part_number__item_group__name'] = item_group
        if stores:
            filter_criteria['store__store_name'] = stores
        if current_stock:
            filtered_items = filtered_items.values('part_number').annotate(total_value=Sum('current_stock'))
            filter_criteria['total_value'] = current_stock
        if filter_criteria:
            filtered_items = filtered_items.filter(**filter_criteria)
        sorting_key_dict = {
            "partCode": {"field": "part_number__item_part_code", "is_text": True},
            'partName': {"field": 'part_number__item_name', "is_text": True},
            'currentStock': {"field": 'total_value', "is_text": False},
            "itemGroup": {"field": 'part_number__item_group__name', "is_text": True},
            "stores": {"field": 'store__store_name', "is_text": True},
            "stockId": {"field": 'id', "is_text": False},
        }
        filtered_items = filtered_items.values('part_number').distinct()
        if order_by:
            filtered_items = filtered_items.values('part_number').annotate(total_value=Sum('current_stock'))
            order_by_config = sorting_key_dict.get(order_by)
            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]
                if is_text_field:
                    annotated_field_name = f'{order_by_field}_lower'
                    filtered_items = filtered_items.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name
                if descending:
                    order_by_field = f'-{order_by_field}'
                filtered_items = filtered_items.order_by(order_by_field)
        total_qty = 0
        try:
            part_numbers = list(set([a[0] for a in filtered_items.values_list('part_number')]))
            stock_items_temp = ItemStock.objects.filter(part_number__in=part_numbers).annotate(
                total_stock=Sum('current_stock'))
            if stores:
                stock_items_temp = stock_items_temp.filter(store__store_name=stores)  # Corrected this line
            total_qty = stock_items_temp.aggregate(total_qty=Sum('total_stock', output_field=IntegerField()))[
                            'total_qty'] or 0
        except:
            total_qty = 0
        if filtered_items:
            total_items = len(filtered_items)
            for item_master_item in filtered_items[(page_size * (page - 1)):page_size * page]:
                stock_items = ItemStock.objects.filter(part_number=item_master_item['part_number']).all()
                if stores:
                    stock_items = stock_items.filter(store__store_name=stores)
                stock_items = stock_items.filter(current_stock__gte=0)
                if stock_items:
                    part_number_id = item_master_item['part_number']
                    current_item_stock = sum([item.current_stock for item in stock_items])

                    stock_ids = [item.id for item in stock_items]
                    store_names = ", ".join(list(set([item.store.store_name for item in stock_items])))
                    aggregated_stock[part_number_id] = {
                        'id': part_number_id,
                        'current_stock': current_item_stock,
                        'stores': store_names,
                        'part_code': stock_items[0].part_number.item_part_code,
                        'part_name': stock_items[0].part_number.item_name,
                        'item_group': stock_items[0].part_number.item_group.name if stock_items[
                            0].part_number.item_group else '',
                        'stock_id': stock_ids,
                        'description': stock_items[0].part_number.description,
                        'is_serial': stock_items[0].part_number.serial,
                        'is_batch': stock_items[0].part_number.batch_number
                    }
        else:
            if part_code:
                item_master_data = ItemMaster.objects.filter(item_part_code=part_code)
            if part_name:
                item_master_data = ItemMaster.objects.filter(item_name=part_name)
            if item_master_data:
                total_items = 1
                item_master_data_item = item_master_data[0]
                aggregated_stock[item_master_data_item.id] = {
                    'id': item_master_data_item.id,
                    'current_stock': "0.00",
                    'stores': "",
                    'part_code': item_master_data_item.item_part_code,
                    'part_name': item_master_data_item.item_name,
                    'item_group': item_master_data_item.item_group.name if item_master_data_item.item_group else '',
                    'stock_id': [],
                    'description': item_master_data_item.description,
                    'is_serial': item_master_data_item.serial,
                    'is_batch': item_master_data_item.batch_number
                }
            else:
                total_items = 0
                aggregated_stock[0] = {}
        # Convert aggregated_stock dictionary to a list of dictionaries
        processed_data = list(aggregated_stock.values())
        total_pages = total_items // page_size
        total_pages += 1
        has_next_page = False
        has_previous_page = False
        if page < total_pages:
            has_next_page = True
        if page != 1 and page != 0 and page <= total_pages:
            has_previous_page = True
        page_info = PageInfoType(
            total_items=total_items,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
            total_pages=total_pages,
        )
        return StockStatementConnection(items=processed_data, page_info=page_info, total_qty=total_qty)



    @permission_required(models=["Stock_Statement", "Purchase_Order", "GIN", "GRN", "Purchase Return"])
    def resolve_stock_statement_part_view(self, info, part_id=None):
        if not part_id:
            return {"error": "Part id is required."}

        itemmaster = ItemMaster.objects.filter(id=part_id).first()
        if not itemmaster:
            return {"error": "Item Master not found."}

        combo_qty = 0
        total_qty = 0
        stock_list = []
        history_list = []
        store_list = []
        uom_list = []

        def check_combo_stock(combos):
            qty_list = []
            for combo in combos.all():
                part_id = combo.part_number.id
                required_qty = combo.item_qty
                current_stock = ItemStock.objects.filter(part_number=part_id).aggregate(
                    total=Sum("current_stock")
                ).get("total") or 0
                qty_list.append(current_stock / required_qty)
            return min(qty_list) if qty_list else 0
        
        if not itemmaster.item_combo_bool:
            stock_datas = ItemStock.objects.filter(part_number=part_id).order_by("-id") 
            if not stock_datas.exists():
                return  StockStatementPartView(stock_and_history_data={
                        "part_code": itemmaster.item_part_code,
                        "part_name": itemmaster.item_name,
                       "error": "No stock available",
                    })  
            first_stock = stock_datas.first()
            alternate_uom_instances = first_stock.part_number.alternate_uom.all()
            if alternate_uom_instances:
                for alternate_uom in alternate_uom_instances: 
                    uom_list.append({
                        "value": alternate_uom.addtional_unit.name,
                        "label": alternate_uom.addtional_unit.name,
                        "convertionfactor": str(alternate_uom.conversion_factor),
                        'is_main':False
                    })
            main_uom = first_stock.part_number.item_uom
            if main_uom:
                uom_list.append({
                        "value": main_uom.name,
                        "label": main_uom.name,
                        "convertionfactor": "1",
                        'is_main':True
                    })
            for single_stock in stock_datas:
                if single_stock.store.store_name not in store_list:
                    store_list.append(single_stock.store.store_name)
                 
                   

                serial_list = list(single_stock.serial_number.values_list("serial_number", flat=True))

                stock_list.append({
                    "store": single_stock.store.store_name,
                    "qty": float(single_stock.current_stock),
                    "UOM": single_stock.unit.name,
                    "batch": single_stock.batch_number.batch_number_name if single_stock.batch_number else None,
                    "serial": " ,".join(serial_list) if serial_list else None,
                })

                for history in single_stock.stockhistory_set.all():
                    history_list.append({
                        "id": history.id,
                        'transaction_id': history.transaction_id,
                        'transaction_module': history.transaction_module,
                        'date': str(history.modified_date.strftime('%d/%m/%Y')),
                        'part_code_id': history.part_number.item_name,
                        'start_stock': history.previous_state,
                        'end_stock': history.updated_state,
                        'added': history.added,
                        'reduced': history.reduced,
                        'saved_by': history.saved_by.username,
                        'display_id': history.display_id,
                        "display_name": history.display_name,
                        "is_delete": history.is_delete
                    })

            total_qty = sum([float(s.current_stock) for s in stock_datas])
        else:
            if itemmaster.item_combo_data.exists():
                combo_qty = math.floor(check_combo_stock(itemmaster.item_combo_data))
        history_list = sorted(history_list, key=lambda x: x['id'], reverse=True)

        return StockStatementPartView(stock_and_history_data={
            "part_code": itemmaster.item_part_code,
            "part_name": itemmaster.item_name,
            "qty": str(total_qty),
            "stock_details": stock_list,
            "history_list": history_list,
            "store": store_list,
            "uom_list": uom_list,
            "combo_qty": str(combo_qty) if combo_qty > 0 else "0"
        })



    @permission_required(models=["POS_Stock_Report"])
    def resolve_pos_stock_report(self, info, part_id=None, conference_id=None):
        queryset = StockHistory.objects.filter(conference=conference_id)
        queryset_items = serializers.serialize("json", queryset)
        pos_stock_report_data = []
        for stock_item in json.loads(queryset_items):
            stock_item_dict = stock_item['fields']
            stock_item_dict['id'] = stock_item['pk']
            pos_stock_report_data.append(stock_item_dict)
        processed_data = get_pos_stock_report_data(pos_stock_report_data)

        return posStockReportConnection(items=processed_data)

    

    def resolve_stock_history_log(self, info, stock_id=[]):
        queryset = StockHistory.objects.filter(stock_link__in=stock_id).select_related('part_number').all()
        queryset_items = serializers.serialize("json", queryset)
        stock_history_master_data = []
        for stock_item in json.loads(queryset_items):
            stock_item_dict = stock_item['fields']

            stock_history_master_data.append(stock_item_dict)
        processed_data = get_stock_history_details(stock_history_master_data)
        return StockHistoryConnection(items=processed_data)

    def resolve_stock_history_details(self, info, stock_id=[], transaction_id=None, transaction_module=None):
        filter_criteria = {}
        processed_data = []
        if transaction_id:
            filter_criteria['transaction_id'] = transaction_id
        if transaction_module:
            filter_criteria['transaction_module'] = transaction_module
        if len(stock_id) > 0:
            filter_criteria['stock_link__in'] = stock_id
        if not transaction_id and not transaction_module and len(stock_id) < 1:
            processed_data = []
        else:
            queryset = StockHistory.objects.filter(**filter_criteria).select_related(
                'part_number', "saved_by").order_by('-modified_date').all()
            queryset_items = serializers.serialize("json", queryset)
            stock_history_master_data = []
            for stock_item in json.loads(queryset_items):
                stock_item_dict = stock_item['fields']
                stock_item_dict['id'] = stock_item['pk']
                stock_history_master_data.append(stock_item_dict)
            processed_data = get_stock_history_details(stock_history_master_data)
        return StockHistoryConnection(items=processed_data)

    def resolve_inventory_approval(self, info, page=1, page_size=20,
                                   approval_id=None, item_part_code=None, item_name=None,
                                   qty=None, serial_number_joined=None, batch_number=None, store=None,
                                   qty_gt=None, qty_lt=None, qty_gte=None, qty_lte=None,
                                   qty_start=None, qty_end=None, order_by=None, descending=None, part_number=None):
        queryset = ItemInventoryApproval.objects.filter(id__in=approval_id).prefetch_related('serial_number').all()
        filter_kwargs = {}
        if serial_number_joined:
            filter_kwargs['serial_number__serial_number'] = serial_number_joined
        if batch_number:
            filter_kwargs['batch_number__batch_number_name'] = batch_number
        if store:
            filter_kwargs['store__store_name'] = store
        if item_part_code:
            filter_kwargs['part_number__item_part_code__icontains'] = item_part_code
        if item_name:
            filter_kwargs['part_number__item_name__icontains'] = item_name
        if qty:
            filter_kwargs['qty'] = qty
        if qty_gt:
            filter_kwargs['qty__gt'] = qty_gt
        if qty_lt:
            filter_kwargs['qty__lt'] = qty_lt
        if qty_gte:
            filter_kwargs['qty__gte'] = qty_gte
        if qty_lte:
            filter_kwargs['qty__lte'] = qty_lte
        if qty_start and qty_end:
            filter_kwargs['qty__range'] = (qty_start, qty_end)
        if part_number:
            filter_kwargs['part_number__item_part_code__icontains'] = part_number
        queryset = queryset.filter(**filter_kwargs)
        db_s = {
            "id": {"field": "id", "is_text": False},
            'partNumber': {"field": 'part_number__item_part_code', "is_text": True},
            'qty': {"field": 'qty', "is_text": False},
            "serialNumber": {"field": 'serial_number__serial_number', "is_text": True},
            "batchNumber": {"field": 'batch_number__batch_number_name', "is_text": True},
            "store": {"field": 'store__store_name', "is_text": True}
        }

        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs)
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return InventoryApprovalConnection(
            items=paginated_data.object_list,
            page_info=page_info)

    @permission_required(models=["Currency_Exchange", "Target", 'Conference', "Lead","Currency_Master","Purchase_Order", "Receipt Voucher", 'PaymentVoucher', 'Credit Note'])
    def resolve_currency_exchange_connection(self, info, page=1, page_size=20,
                                             order_by=None,
                                             descending=None, name=None,
                                             rate=None,
                                             rate_gt=None,  # Add id_min argument
                                             rate_lt=None,  # Add id_max argument
                                             rate_gte=None,  # Add id_min argument
                                             rate_lte=None,  # Add id_max argument
                                             rate_start=None,
                                             rate_end=None,
                                             date=None, id=None):
        """retun the data with filiter"""
        queryset = CurrencyExchange.objects.all().order_by('-id')
        """Apply filters"""

        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        # if name:
        #     filter_kwargs['name__icontains'] = name
        if rate:
            filter_kwargs['rate__icontains'] = rate
        if rate_gt:
            filter_kwargs['rate__gt'] = rate_gt
        if rate_lt:
            filter_kwargs['rate__lt'] = rate_lt
        if rate_gte:
            filter_kwargs['rate__gte'] = rate_gte
        if rate_lte:
            filter_kwargs['rate__lte'] = rate_lte
        if rate_start and rate_end:
            filter_kwargs['id__range'] = (rate_start, rate_end)
        if date:
            start_date, end_date = date.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y')

            if start_date == end_date:
                filter_kwargs['date__range'] = (updated_start_date, updated_end_date)
            else:
                filter_kwargs['date__range'] = (updated_start_date, updated_end_date)
        db_s = {
            "id": {"field": "id", "is_text": False},
            'name': {"field": 'name', "is_text": True},
            'rate': {"field": 'rate', "is_text": False},
            'date': {"field": 'date', "is_text": False},
        }
        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs)
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return CurrencyExchangeConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["Currency_Master"])
    def resolve_currency_master(self, info, page=1,
                                page_size=20, order_by=None,
                                descending=None, name=None,
                                currency_symbol=None, active=None,
                                formate=None, id=None, any=None):
        """retun the data with filiter"""
        queryset = CurrencyMaster.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        if currency_symbol:
            filter_kwargs['currency_symbol__icontains'] = currency_symbol
        if active != None:
            filter_kwargs['active'] = active
        if formate:
            filter_kwargs['formate__formate'] = formate
        if any:
            pass
        else:
            filter_kwargs['active'] = True

        db_s = {
            "id": {"field": "id", "is_text": False},
            'name': {"field": 'name', "is_text": True},
            'currencySymbol': {"field": 'currency_symbol', "is_text": True},
            "active": {"field": "active", "is_text": False},
            "formate": {"field": "formate", "is_text": False}
        }
        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs)
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return CurrencyExchangeConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(models=["POS", "Numbering_Series"])
    def resolve_resource_pos_type(self, info):
        queryset = ResourcePosType.objects.all()
        return ResourcePosTypeConnection(
            items=queryset
        )

    @permission_required(models=["Numbering_Series"])
    def resolve_numbering_series(self, info, page=1, page_size=20,
                                 order_by=None, descending=None, id=None, numbering_series_name=None,
                                 resource=None, formate=None,
                                 pos_type=None, current_value=None,
                                 default=None, active=None):
        """retun the data with filiter"""
        queryset = NumberingSeries.objects.all().order_by('-id')
        """Apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if numbering_series_name:
            filter_kwargs['numbering_series_name__icontains'] = numbering_series_name
        if resource:
            filter_kwargs['resource__icontains'] = resource
        if pos_type:
            filter_kwargs['pos_type__ReSourceIsPosType__icontains'] = pos_type
        if formate:
            filter_kwargs['formate__icontains'] = formate
        if current_value:
            filter_kwargs['current_value'] = current_value
        if default is not None:
            filter_kwargs['default'] = default
        if active is not None:
            filter_kwargs['active'] = active

        db_s = {
            "id": {"field": "id", "is_text": False},
            'numberingSeriesName': {"field": 'numbering_series_name', "is_text": True},
            'resource': {"field": 'resource', "is_text": True},
            "posType": {"field": "pos_type", "is_text": True},
            "formate": {"field": "formate", "is_text": True},
            "currentValue": {"field": "current_value", "is_text": False},
            "default": {"field": "default", "is_text": False},
            "active": {"field": "active", "is_text": False},
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
        return NumberingSeriesConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )



    @permission_required(models=["Stock_Addition","Stock_Deletion"])
    def resolve_inventory_handler(self, info, page=1, page_size=20, inventory_handler_id=None, store=None,
                                  saved_by=None, created_at=None, order_by=None, descending=None,
                                  starts_with=None, id=None):
        queryset = InventoryHandler.objects.prefetch_related('inventory_id').all()
        filter_kwargs = {} 
        if id:
            filter_kwargs['id'] = id
        if starts_with:
            filter_kwargs['inventory_handler_id__startswith'] = starts_with
        if inventory_handler_id:
            filter_kwargs['inventory_handler_id__icontains'] = inventory_handler_id
        if store:
            filter_kwargs['store__store_name'] = store
        if saved_by:
            filter_kwargs['saved_by__username'] = saved_by
        if created_at:
            start_date, end_date = created_at.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y')
            if start_date == end_date:
                filter_kwargs['created_at__date'] = updated_start_date
            else:
                filter_kwargs['created_at__range'] = (updated_start_date, updated_end_date)
        queryset = queryset.filter(**filter_kwargs)

        db_s = {
            "inventoryHandlerId": {"field": "inventory_handler_id", "is_text": True},
            'store': {"field": 'store__store_name', "is_text": True},
            'savedBy': {"field": 'saved_by__username', "is_text": True},
            "createdAt": {"field": 'created_at', "is_text": False}
        }

        # Apply case-insensitive sorting
        queryset = queryset.filter(**filter_kwargs).order_by('-inventory_handler_id')
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'
                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        queryset = CalculateInventoryQty(queryset)

        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return InventoryHandlerConnection(
            items=paginated_data.object_list,
            page_info=page_info)

    def resolve_stock_serial_history(self, info):
        return StockSerialHistoryConnection(items=StockSerialHistory.objects.all())

    def resolve_eway_bill_options(self, info, eWayBillUom=None):

        result = [
            {"id": item[0], "eWayBillUom": item[1]} for item in e_way_bill if eWayBillUom.lower() in item[1].lower()
        ]

        return FixedOptionConnection(items=result)

    def resolve_pos_status(self, info, Status=None):
        result = [
            {"id": item[0], "Status": item[1]} for item in PosStatus
        ]
        return posStatusConnection(items=result)

    def resolve_postype_options(self, info, posType=None):

        result = [
            {"id": item[0], "posType": item[1]} for item in Postypes_
        ]

        return PosTypeConnection(items=result)

    def resolve_work_center_master(self, info, page=1, page_size=20, work_center=None):
        queryset = WorkCenter.objects.all()
        if work_center:
            queryset = WorkCenter.objects.filter(work_center__icontains=work_center)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return WorkCenterMasterConnection(items=queryset, page_info=page_info)

    def resolve_stock_history(self, info, page=1, page_size=20):
        queryset = StockHistory.objects.all()
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return StockHistoryConnection(items=queryset, page_info=page_info)

    def resolve_raw_material_bom_link(self, info, raw_material=None, bom=None):
        queryset = RawMaterialBomLink.objects.all()
        filter_kwargs = {}
        if raw_material:
            filter_kwargs['raw_material'] = raw_material
        if bom:
            filter_kwargs['bom'] = bom
        queryset = queryset.filter(**filter_kwargs)
        return RawMaterialBomLinkConnection(items=queryset)

    def resolve_stock_statement_item_combo_qty(self, info, id=None, store=None):
        qty = 0
        if id:
            item_master_instance = ItemMaster.objects.get(id=id)
            item_master_dict = model_to_dict(item_master_instance)
            qty = process_item_combo_stock_statement(item_master_dict, store)
        result = [StockStatementItemComboQtyType(qty)]
        return StockStatementItemComboQtyConnection(items=result)

    def resolve_goods_inward_note_type(self, info, id):
        filter_kwargs = {}
        queryset = GoodsInwardNote.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    def resolve_quality_inspection_report_type(self, info, id):
        filter_kwargs = {}
        queryset = QualityInspectionReport.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    def resolve_goods_receipt_note_type(self, info, id):
        filter_kwargs = {}
        queryset = GoodsReceiptNote.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset

    @permission_required(models=["Other_Expenses"])
    def resolve_other_expenses(self, info, id=None, page=1, page_size=20, order_by=None, descending=False,
                            account=None, active=None, account_group=None):
        filter_kwargs = {}
        queryset = OtherExpenses.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if account:
            filter_kwargs['account__accounts_name__icontains'] = account
        if active != None:
            filter_kwargs['active'] = active
        if account_group:
            filter_kwargs['account__accounts_group_name__accounts_type__name'] = active = account_group
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return OtherExpensesConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
 
    @permission_required(models=["Purchase_Order"])
    def resolve_purchase_order(self, info, id=None, page=1, page_size=20, order_by=None, descending=False, active=None,
                               purchaseOrder_no=None, createdAt=None, status=None, supplierId=None,
                               isSupplierDistinct=None, companyName=None, department=None, isDepartmentDistinct=None,
                               receivingStoreId=None, isreceivingStoreDistinct=None, dueDate=None, netAmount=None,
                               netAmount_gt=None, netAmount_lt=None, netAmount_gte=None, netAmount_lte=None,
                               netAmount_start=None, netAmount_end=None,supplier=None,department_id=None):
        filter_kwargs = {}
        queryset = purchaseOrder.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if purchaseOrder_no:
            filter_kwargs['purchaseOrder_no__linked_model_id__icontains'] = purchaseOrder_no
        if status:
            filter_kwargs['status'] = status
        if supplierId:
            filter_kwargs['supplier_id__supplier_no__icontains'] = supplierId
        if companyName:
            filter_kwargs['supplier_id__company_name__icontains'] = companyName
        if supplier:
           filter_kwargs['supplier_id__id'] = supplier
        if department:
            filter_kwargs['department__name__icontains'] = department
        if department_id:
            filter_kwargs['department__id'] = department_id
        if receivingStoreId:
            filter_kwargs['receiving_store_id__store_name__icontains'] = receivingStoreId
        if netAmount:
            filter_kwargs['net_amount'] = netAmount
        if netAmount_gt:
            filter_kwargs['net_amount__gt'] = netAmount_gt
        if netAmount_lt:
            filter_kwargs['net_amount__lt'] = netAmount_lt
        if netAmount_gte:
            filter_kwargs['net_amount__gte'] = netAmount_gte
        if netAmount_lte:
            filter_kwargs['net_amount__lte'] = netAmount_lte
        if netAmount_start and netAmount_end:
            filter_kwargs['net_amount__range'] = (netAmount_start, netAmount_end)
        if dueDate:
            start_date, end_date = dueDate.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['due_date'] = updated_start_date
            else:
                filter_kwargs['due_date__range'] = (updated_start_date, updated_end_date)
        if createdAt:
            start_date, end_date = createdAt.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['created_at__date'] = updated_start_date
            else:
                filter_kwargs['created_at__range'] = (updated_start_date, updated_end_date)
        if active is not None:
            filter_kwargs['active'] = active
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        if isSupplierDistinct:
            queryset = queryset.filter(**filter_kwargs).order_by('supplier_id').distinct('supplier_id')
        elif isDepartmentDistinct:
            queryset = queryset.filter(**filter_kwargs).order_by('department').distinct('department')
        elif isreceivingStoreDistinct:
            queryset = queryset.filter(**filter_kwargs).order_by('receiving_store_id').distinct('receiving_store_id')
        else:
            queryset = queryset.filter(**filter_kwargs)
        if id:
            version_ids = get_all_related_orders(queryset.first())
        else:
            version_ids = []
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return purchaseOrderConnection(
            items=paginated_data.object_list,
            page_info=page_info,
            version=versionListType(versionList=version_ids),
        )
    
    def resolve_purchase_supplier_update_item_tax(self, info, gst_nature_transaction=None, state=None, itemdetails=[], otherexpenses=[]):
            item_details_update_data = []
            other_expence_update_data = []

            company_obj = company_info()
            if company_obj is None:
                return GraphQLError("Company Not Found.")
            if gst_nature_transaction is None:
                return GraphQLError("Gst Nature Transaction is required.")
            if state is None:
                return GraphQLError("State is required.")
            if not itemdetails:
                return GraphQLError("Item Details are required.")

            gst_transaction = GSTNatureTransaction.objects.filter(id=gst_nature_transaction).first()
            if gst_transaction is None:
                return GraphQLError("GST Transaction not found.")

            itemdetails = ItemMaster.objects.filter(id__in=itemdetails)
            if not itemdetails:
                return GraphQLError("Item Details not found.")

            expenses = OtherExpenses.objects.filter(id__in=otherexpenses)
            is_specify_taxable = gst_transaction.gst_nature_type == "Specify" and gst_transaction.specify_type == "taxable"
            is_intrastate = str(state).lower() == str(company_obj.address.state).lower()

            for item in itemdetails: 
                update_item = {}
                update_item['id'] = str(item.id)
                update_item['sgst'] = "0"
                update_item['cgst'] = "0"
                update_item['igst'] = "0"
                update_item['cess'] = "0"
                update_item['tax'] = "0"
                update_item['after_discount_value_for_per_item'] = "0"
                update_item['discount_percentage'] = "0"
                update_item['discount_value'] = "0"
                update_item['final_value'] = "0" 
                if is_specify_taxable: 
                    if gst_transaction.place_of_supply == "Intrastate":
                        update_item['sgst'] = str(gst_transaction.sgst_rate)
                        update_item['cgst'] = str(gst_transaction.cgst_rate)
                        update_item['cess'] = str(gst_transaction.cess_rate)
                        # update_item['tax'] = str(gst_transaction.sgst_rate + gst_transaction.cgst_rate + gst_transaction.cess_rate)
                        update_item['tax'] = str(gst_transaction.sgst_rate + gst_transaction.cgst_rate)
                    else:
                        update_item['igst'] = str(gst_transaction.igst_rate)
                        update_item['cess'] = str(gst_transaction.cess_rate)
                        # update_item['tax'] =  str(gst_transaction.igst_rate + gst_transaction.cess_rate)
                        update_item['tax'] =  str(gst_transaction.igst_rate)
                elif gst_transaction.gst_nature_type == "As per HSN": 
                    hsn = item.item_hsn
                    if hsn is None:
                        return GraphQLError(f"{item.item_master_id.item_part_code} → HSN not found.")

                    update_item['cess'] =str(hsn.cess_rate)
                    update_item['tax'] = str(hsn.gst_rates.rate)
                    if is_intrastate:
                        rate_half = str(hsn.gst_rates.rate / 2)
                        update_item['sgst'] = str(rate_half)
                        update_item['cgst'] = str(rate_half)
                    else:
                        update_item['igst'] = str(hsn.gst_rates.rate) 

                item_details_update_data.append((update_item)) 
            for expence in expenses:
                update_expence = {}
                update_expence['id'] = expence.id
                update_expence['sgst'] = str(0)
                update_expence['cgst'] = str(0)
                update_expence['igst'] = str(0)
                update_expence['cess'] = str(0)
                update_expence['tax'] = str(0)
                update_expence['after_discount_value'] = str(0)
                update_expence['discount_value'] = str(0)

                if is_specify_taxable: 
                    if gst_transaction.place_of_supply == "Intrastate":
                        update_expence['sgst'] = str(gst_transaction.sgst_rate)
                        update_expence['cgst'] = str(gst_transaction.cgst_rate)
                        update_expence["cgst"] = str(gst_transaction.cess_rate)
                        # update_expence['tax'] =  str(gst_transaction.sgst_rate + gst_transaction.cgst_rate + gst_transaction.cess_rate)
                        update_expence['tax'] =  str(gst_transaction.sgst_rate + gst_transaction.cgst_rate)
                    else:
                        update_expence['igst'] = str(gst_transaction.igst_rate)
                        update_expence['cess'] = str(gst_transaction.cess_rate)
                        # update_expence['tax'] =  str(gst_transaction.igst_rate + gst_transaction.cess_rate)
                        update_expence['tax'] =  str(gst_transaction.igst_rate)
                elif gst_transaction.gst_nature_type == "As per HSN": 
                    hsn = expence.HSN
                    if hsn is None:
                        return GraphQLError(f"{expence.name} → HSN not found.")

                    update_expence['cess'] = hsn.cess_rate
                    update_expence['tax'] = hsn.gst_rates.rate
                    if is_intrastate:
                        rate_half =    str(hsn.gst_rates.rate / 2)
                        update_expence['sgst'] = str(rate_half)
                        update_expence['cgst'] = str(rate_half)
                    else:
                        update_expence['igst'] = hsn.gst_rates.rate

                other_expence_update_data.append((update_expence)) 
            return purchaseSupplierUpdateitemtax(items=item_details_update_data, other_expence=other_expence_update_data)

    def resolve_purchase_time_line(self, info, purchase_id):
        def serialize_debit_note(dn):
            
            return {
                "id": str(dn.id),
                "label": "Debit Note",
                "isShow": True,
                "Number": dn.debit_note_no.linked_model_id,
                "date": str(dn.created_at),
                "status": dn.status.name,
            }

        def serialize_purchase_return(pr):
            return {
                "id": str(pr.id),
                "label": "Purchase Return",
                "isShow": True,
                "Number": pr.purchase_return_no.linked_model_id,
                "date": str(pr.created_at),
                "status": pr.status.name,
                "children": [serialize_debit_note(dn) for dn in pr.debitnote_set.all()],
            }

        def serialize_purchase_invoice(pi):
            return {
                "id": str(pi.id),
                "label": "Purchase Invoice",
                "isShow": True,
                "Number": pi.purchase_invoice_no.linked_model_id,
                "date": str(pi.created_at),
                "status": pi.status.name,
                "children": [serialize_purchase_return(pr) for pr in pi.purchase_retun.all()],
            }

        def serialize_grn(grn):
            children = [serialize_purchase_invoice(pi) for pi in grn.purchase_invoice.all() if grn.purchase_invoice.exists() ]
            children += [serialize_purchase_return(pr) for pr in grn.purchase_retun.all() if grn.purchase_retun.exists()]
            return {
                "id": str(grn.id),
                "label": "Goods Receipt Note",
                "isShow": True,
                "Number": grn.grn_no.linked_model_id,
                "date": str(grn.created_at),
                "status": grn.status.name,
                "children": children,
            }

        def get_gin_grn(gin):
            
            children = []
            if gin.quality_inspection_report_id:
                qir = gin.quality_inspection_report_id
                qir_children = []
                if gin.grn:
                    qir_children.append(serialize_grn(gin.grn))
                if qir.rework_received:
                    qir_children.append({
                        "id": str(qir.rework_received.id),
                        "label": "Rework Delivery Challan",
                        "isShow": True,
                        "Number": qir.rework_received.dc_no.linked_model_id,
                        "date": str(qir.rework_received.created_at),
                        "status": qir.rework_received.status.name,
                         "children": [
                                {
                                    "id": str(gin.id),
                                    "label": "Goods Inward Note",
                                    "isShow": True,
                                    "Number": gin.gin_no.linked_model_id,
                                    "date": str(gin.created_at),
                                    "status": gin.status.name,
                                    "children": get_gin_grn(gin),
                                }
                                for gin in purchase_obj.gin.all()
                                if   gin.rework_delivery_challan
                ]
                    })
                children.append({
                    "id": str(qir.id),
                    "label": "Quality Inspection Report",
                    "isShow": True,
                    "Number": qir.qir_no.linked_model_id,
                    "date": str(qir.created_at),
                    "status": qir.status.name,
                    "children": qir_children,
                })
            elif gin.grn:
                children.append(serialize_grn(gin.grn))
            return children
        
        if not purchase_id:
            return None

        purchase_obj = purchaseOrder.objects.filter(id=purchase_id).first()
        if not purchase_obj:
            return None

        return PurchaseTimeLine(
            item={
                "id": str(purchase_obj.id),
                "label": "Purchase Order",
                "isShow": True,
                "Number": purchase_obj.purchaseOrder_no.linked_model_id,
                "date": str(purchase_obj.created_at),
                "status": purchase_obj.status.name,
                "children": [
                    {
                        "id": str(gin.id),
                        "label": "Goods Inward Note",
                        "isShow": True,
                        "Number": gin.gin_no.linked_model_id,
                        "date": str(gin.created_at),
                        "status": gin.status.name,
                        "children": get_gin_grn(gin),
                    }
                    for gin in purchase_obj.gin.all()
                    if not gin.rework_delivery_challan
                ],
            }
        )

    @permission_required(models=["GIN"])
    def resolve_gin_initial_fetch(self, info, id=None, parent_module=None, rework_id=None):
         
        gin_item_details = []
        gin_data ={}
        try:
            if id:
                if parent_module == "Purchase":
                    queryset = purchaseOrder.objects.get(id=id) 
                    if queryset:
                        if queryset.status.name in ["Inward", "Cancelled"]:
                            raise GraphQLError("Cannot create GIN for a purchase order that is either already inwarded or cancelled.")
                        gin_data['supplier_no'] = queryset.supplier_id.supplier_no
                        gin_data['supplier_name'] = queryset.supplier_id.company_name
                        gin_data['purchase_data'] = {"purchase_no":queryset.purchaseOrder_no.linked_model_id,
                                                    "purchase_id":queryset.id}
                        gin_data['due_date'] = queryset.due_date.strftime("%d-%m-%Y") if queryset.due_date else None
                        gin_data['department'] = queryset.department.name
                        gin_data['receiving_store'] = queryset.receiving_store_id.store_name
                        # gin_data['scrap_reject_store'] = queryset.scrap_reject_store_id.store_name
                        if queryset.item_details.exists():
                            for index, item in enumerate(queryset.item_details.all(), start=1): 

                                if (item.received or 0) < (item.po_qty or 0) and item.item_master_id.item_types.name not in ['Service']:
                                    gin_item_details.append({
                                        "id":"",
                                        "index":index,
                                        "itemmaster_id":item.item_master_id.id,
                                        "itemPartCode": item.item_master_id.item_part_code, 
                                        "itemName" : item.item_master_id.item_name,
                                        "description" : item.item_master_id.description,
                                        "accepted": "0",
                                        "received": str((item.po_qty or 0) - (item.received or 0)),
                                        "qc": item.item_master_id.item_qc,
                                        "purchaseOrderParent" : item.id,
                                        "poQty" : str(item.po_qty),
                                        "uom": item.po_uom.name
                                    })
                        gin_data['itemdetails'] = gin_item_details
                        return GinInitialFetch(items=gin_data)
                    else:
                        return GraphQLError(f'Purchase Not Found.')
            elif rework_id:
                queryset = ReworkDeliveryChallan.objects.filter(id=rework_id).first()
                if not queryset:
                    return GraphQLError(f'Rework Delivery Challan Not Found.')
                if queryset.status.name not in ["Dispatch"]:
                    return GraphQLError("Cannot create GIN for a Rework Delivery Challan Must be Dispatch.")
                purchase = queryset.purchase_order_no
                
                gin_data['supplier_no'] = purchase.supplier_id.supplier_no
                gin_data['supplier_name'] = purchase.supplier_id.company_name
                gin_data['purchase_data'] = {"purchase_no":purchase.purchaseOrder_no.linked_model_id,
                                            "purchase_id":purchase.id}
                gin_data['due_date'] = purchase.due_date.strftime("%d-%m-%Y") if purchase.due_date else None
                gin_data['department'] = purchase.department.name
                gin_data['receiving_store'] = purchase.receiving_store_id.store_name
                # gin_data['scrap_reject_store'] = purchase.scrap_reject_store_id.store_name
                gin_data['rework_delivery_challan'] = queryset.id

                if queryset.rework_delivery_challan_item_details.exists():

                    for index, item in enumerate(queryset.rework_delivery_challan_item_details.all(), start=1):
                        blance_rework_qty = (item.rework_qty or 0) - (item.received_qty or 0)
                        if blance_rework_qty > 0: 
                            gin_item_details.append({
                                    "id":"",
                                    "index":index,
                                    "itemmaster_id":item.purchase_item.item_master_id.id, 
                                    "itemPartCode": item.purchase_item.item_master_id.item_part_code,
                                    "itemName" : item.purchase_item.item_master_id.item_name,
                                    "description" : item.purchase_item.item_master_id.description,
                                    "accepted": "0",
                                    "received": str(blance_rework_qty),
                                    "reword_delivery_challan_item" : str(item.id),
                                    "qc": item.purchase_item.item_master_id.item_qc,
                                    "purchaseOrderParent" : item.purchase_item.id,
                                    "poQty" : str(item.purchase_item.po_qty),
                                    "uom": item.purchase_item.po_uom.name
                                })
                        
                gin_data['itemdetails'] = gin_item_details 
                if len(gin_item_details) <=0:
                    return GraphQLError("All items in this Rework Delivery Challan have already been received into GIN.")

                return GinInitialFetch(items=gin_data)

        except Exception as e: 
            return GraphQLError(f'An exception occurred->', e)
    
    @permission_required(models=["GIN"])
    def resolve_gin_edit_fetch(self, info, id):
        gin_item_details = []
        gin_data ={}
        try:
            if id:
                gin_obj = GoodsInwardNote.objects.filter(id=id).first()
                gin_data['created_by'] = gin_obj.created_by.username
                gin_data['updated_at'] = str(gin_obj.updated_at) if gin_obj.updated_at else str(gin_obj.created_at)
                gin_data['id'] = gin_obj.id
                gin_data['gin_no'] = gin_obj.gin_no.linked_model_id
                gin_data['gin_date'] = str(gin_obj.gin_date)
                gin_data['gin_status'] = gin_obj.status.name
                gin_data['qc_status'] = None
                gin_data['grn_status'] = None
                gin_data['rework_delivery_challan'] = gin_obj.rework_delivery_challan.id if gin_obj.rework_delivery_challan and  gin_obj.rework_delivery_challan.id else None
                if gin_obj.quality_inspection_report_id:
                    gin_data['qc_status'] = gin_obj.quality_inspection_report_id.status.name
                
                if gin_obj.grn:
                    gin_data['grn_status'] = gin_obj.grn.status.name
                
                if gin_obj.purchase_order_id:
                    gin_data['supplier_no'] = gin_obj.purchase_order_id.supplier_id.supplier_no
                    gin_data['supplier_name'] = gin_obj.purchase_order_id.supplier_id.company_name
                    gin_data['purchase_data'] = {"purchase_no":gin_obj.purchase_order_id.purchaseOrder_no.linked_model_id,
                                            "purchase_id":gin_obj.purchase_order_id.id}
                    gin_data['due_date'] = gin_obj.purchase_order_id.due_date.strftime("%d-%m-%Y") if gin_obj.purchase_order_id.due_date else None

                    gin_data['department'] = gin_obj.purchase_order_id.department.name
                    receiving_store = gin_obj.purchase_order_id.receiving_store_id.store_name
                    gin_data['receiving_store'] = receiving_store
                    # gin_data['scrap_reject_store'] = gin_obj.purchase_order_id.scrap_reject_store_id.store_name
                    
                if gin_obj.goods_receipt_note_item_details_id.exists():
                    for index, item in enumerate(gin_obj.goods_receipt_note_item_details_id.all(), start=1):
                        purchase_item_cf  = (item.purchase_order_parent.conversion_factor or 1)
                        item_data = {
                            "id":item.id,
                            "index":str(index),
                            "itemmaster_id":str(item.item_master.id),
                            "itemPartCode": item.item_master.item_part_code,
                            "accepted": str((item.qualityinspectionsreportitemdetails_set.first().accepted * purchase_item_cf or 0))
                                if item.qualityinspectionsreportitemdetails_set.first() and item.qualityinspectionsreportitemdetails_set.first().accepted else "0",
                            "itemName" : item.item_master.item_name,
                            "description" : item.item_master.description,
                            "received":str(item.received),
                            "reword_delivery_challan_item" : str(item.reword_delivery_challan_item.id) if item.reword_delivery_challan_item and  item.reword_delivery_challan_item.id else None,
                            "qc": item.qc
                        }
                        
                        if gin_obj.purchase_order_id:
                            item_data['purchaseOrderParent'] = str(item.purchase_order_parent.id)
                            item_data['poQty'] = str(item.purchase_order_parent.po_qty)
                            item_data['uom'] = item.purchase_order_parent.po_uom.name

                        gin_item_details.append(item_data)
                gin_data['itemdetails'] = gin_item_details
                return GinInitialFetch(items=gin_data)

        except Exception as e:
            return GraphQLError(f"An exception occurred {e}")
    
    @permission_required(models=["QIR"])
    def resolve_qir_initial_fetch(self, info, id):
        gir_item_details = []
        gir_data = {}
        try:
            if id:
                queryset = GoodsInwardNote.objects.filter(id=id).first()
                if not queryset:
                    raise GraphQLError("GIN in not Found.")
                if queryset.status.name in ["Pending", "Cancelled"]:
                        raise GraphQLError("Cannot create Qir for a GIN that is either already pending or cancelled.")
                gir_data['gin_id'] = str(queryset.id)
                gir_data['gin_no'] = queryset.gin_no.linked_model_id
                gir_data['gin_date'] = str(queryset.gin_date)
                for item in queryset.goods_receipt_note_item_details_id.all():
                    if item.qc:
                        data = {
                            "id":"",
                            "gin_id" : str(item.id),
                            "itemName":item.item_master.item_name,
                            "itemPartCode":item.item_master.item_part_code,
                            "itemMasterId":item.item_master.id,
                            "description" : item.item_master.description
                            }
                        if item.purchase_order_parent:
                            data["received"] = f"{item.received / item.purchase_order_parent.conversion_factor:.3f}"
                            data['uom']= item.purchase_order_parent.uom.name
                            data['poQty'] =  str(item.received or 0)
                            data['conversion_factor'] =str(item.purchase_order_parent.conversion_factor)
                            data['pouom'] = item.purchase_order_parent.uom.name
                            # data['pouom'] = item.purchase_order_parent.po_uom.name

                        gir_item_details.append(data)
                gir_data['item'] = gir_item_details
                return getGinDataForQir(items =gir_data)
        except Exception as e:
            return GraphQLError(f'An exception occurred--{e}.')

    @permission_required(models=["QIR"])
    def resolve_qir_edit_fetch(self, info, id):
        qir_item_details = []
        qir_data = {}
        try:
            if id:
                queryset = QualityInspectionReport.objects.filter(id=id).first()
                if queryset is None:
                    return GraphQLError("Qc not Found.") 
                qir_data['id'] = queryset.id
                qir_data['qir_no'] = queryset.qir_no.linked_model_id
                qir_data['qir_date'] = str(queryset.qir_date)
                qir_data['gin_id'] = str(queryset.goods_inward_note.id)
                qir_data['gin_no'] = queryset.goods_inward_note.gin_no.linked_model_id
                qir_data['gin_date'] = str(queryset.goods_inward_note.gin_date)
                qir_data['remark'] = queryset.remarks
                qir_data['created_by'] = queryset.created_by.username
                qir_data['created_at'] = str(queryset.updated_at) if queryset.updated_at else str(queryset.created_at)
                qir_data['status'] = queryset.status.name
                qir_data['purchase_order_id'] = queryset.goods_inward_note.purchase_order_id.id
                qir_data['rework_dc'] = True if queryset.rework_received != None else False

                employee_obj =  None
                for item in queryset.quality_inspections_report_item_detail_id.all():
                    if employee_obj is None:
                        employee_obj = Employee.objects.filter(user__user__id=item.checked_by.id).first()
                        if not employee_obj:
                            return GraphQLError("User did not Found.")
                    data = {
                            "id" : str(item.id),
                            "gin_id" : str(item.goods_inward_note_item.id),
                            "itemName":item.goods_inward_note_item.item_master.item_name,
                            "itemPartCode":item.goods_inward_note_item.item_master.item_part_code,
                            "itemMasterId":item.goods_inward_note_item.item_master.id,
                            "description" : item.goods_inward_note_item.item_master.description,
                            "rejectedQty":str(item.rejected or 0),
                            "acceptedQty":str(item.accepted or 0),
                            "reworkQty":str(item.rework or 0),
                        }
                    if item.goods_inward_note_item.purchase_order_parent:
                        data["received"] = f"{item.goods_inward_note_item.received / item.goods_inward_note_item.purchase_order_parent.conversion_factor :.3f}"
                        data['uom']= item.goods_inward_note_item.purchase_order_parent.uom.name
                        data['poQty'] = str(item.goods_inward_note_item.received)
                        data['conversion_factor'] = str(item.goods_inward_note_item.purchase_order_parent.conversion_factor)
                        data['pouom'] = item.goods_inward_note_item.purchase_order_parent.uom.name
                    qir_item_details.append(data)
                qir_data["checked_by"] = {"emp_id":employee_obj.employee_id,
                                        "user_id":item.checked_by.id,
                                        "emp_name":employee_obj.employee_name,
                                        "imge_url": employee_obj.user_profile.image if employee_obj.user_profile and employee_obj.user_profile.image else None
                                        }
                qir_data['item'] = qir_item_details
                return getGinDataForQir(items=qir_data)
        except Exception as e:
            return GraphQLError(f'An exception occurred--{str(e)}.')

    @permission_required(models=["GRN"])
    def resolve_grn_initial_fetch(self, info, id):
        grn_item_details = []
        grn_data = {}
        try:
            if id:
                queryset = GoodsInwardNote.objects.filter(id=id).first()
                if not queryset:
                    raise GraphQLError("GIN in not Found.") 
                if queryset.grn:
                    raise GraphQLError(f"A GRN (No: {queryset.grn.grn_no.linked_model_id}) already exists for the selected GIN.")
                if queryset.status.name in ["Pending", "Cancelled"]:
                        raise GraphQLError("Cannot create GRN for a GIN that is either already pending or cancelled.")
                grn_data['grn_no'] = ""
                grn_data['grn_date'] = ""
                grn_data['gin_id'] = str(queryset.id)
                grn_data['gin_no'] = str(queryset.gin_no.linked_model_id)
                grn_data['gin_date'] = str(queryset.gin_date)
                grn_data['status'] = ""
                grn_data['created_by'] = ""
                grn_data['updated_at'] = ""
                if queryset.purchase_order_id:
                    grn_data['supplier_code'] = str(queryset.purchase_order_id.supplier_id.supplier_no)
                    grn_data['supplier_name'] = str(queryset.purchase_order_id.supplier_id.company_name)
                    grn_data['purchase_no'] = str(queryset.purchase_order_id.purchaseOrder_no.linked_model_id)
                    grn_data['due_date'] = str(queryset.purchase_order_id.due_date)
                    grn_data['department'] = str(queryset.purchase_order_id.department.name)
                    grn_data['receving_store'] = str(queryset.purchase_order_id.receiving_store_id.store_name)
                    
                for item in queryset.goods_receipt_note_item_details_id.all():
                    inward = (
                                (
                                    (item.qualityinspectionsreportitemdetails_set.last().accepted * item.purchase_order_parent.conversion_factor)
                                    if item.purchase_order_parent
                                    else item.qualityinspectionsreportitemdetails_set.last().accepted
                                )
                                if (
                                    item.qualityinspectionsreportitemdetails_set.last()
                                    and item.qualityinspectionsreportitemdetails_set.last().accepted is not None
                                )
                                else (item.received or 0)
                            )

                    
                    if inward <= 0:
                        continue
                    data = {
                                "id":"",
                                "gin_id" : str(item.id),
                                "itemMasterId":str(item.item_master.id),
                                "itemPartCode":str(item.item_master.item_part_code),
                                "itemName":str(item.item_master.item_name),
                                "description" : str(item.item_master.description),
                                "po_qty":str(item.purchase_order_parent.po_qty) if item.purchase_order_parent else None,
                                "po_uom" : str(item.purchase_order_parent.po_uom.name) if item.purchase_order_parent else None,
                                "inward" : f"{inward:.3f}",
                                "qc" : item.qc,
                                "conversion_factor":str(item.purchase_order_parent.conversion_factor) if item.purchase_order_parent.conversion_factor else None,
                                "base_qty":f"{inward / item.purchase_order_parent.conversion_factor :.3f}",
                                "base_uom":f"{item.purchase_order_parent.uom.name}"
                            }
                    if item.item_master.batch_number:
                            data['is_batch'] = True
                            "batch_number"
                    elif item.item_master.serial:
                        data['is_serial'] = True
                        data['serial_auto_gentrate'] = item.item_master.serial_auto_gentrate
                        data['serial_format'] = item.item_master.serial_format
                        data['serial_starting'] = item.item_master.serial_starting
                    data['stock_added'] = False
                    grn_item_details.append(data)
                grn_data['item'] = grn_item_details 
            return getGinDataForQir(items=grn_data)
        except Exception  as e:
            return GraphQLError(f'An exception occurred {e}')
    
    @permission_required(models=["GRN"])
    def resolve_grn_edit_fetch(self, info, id):
        grn_item_details = []
        grn_data = {}
        try:
            if id:
                queryset = GoodsReceiptNote.objects.filter(id=id).first()
                if not queryset:
                    raise GraphQLError("GRN in not Found.")
                grn_data['id'] = str(queryset.id)
                grn_data['grn_no'] = str(queryset.grn_no.linked_model_id)
                grn_data['grn_date'] = str(queryset.grn_date)
                grn_data['gin_id'] = str(queryset.goods_inward_note.id)
                grn_data['gin_no'] = str(queryset.goods_inward_note.gin_no.linked_model_id)
                grn_data['gin_date'] = str(queryset.goods_inward_note.gin_date)
                grn_data['status'] = str(queryset.status.name)
                grn_data['created_by'] = queryset.created_by.username
                grn_data['updated_at'] = str(queryset.updated_at) if queryset.updated_at else str(queryset.created_at)
            
                if queryset.goods_inward_note.purchase_order_id:
                    grn_data['supplier_code'] = str(queryset.goods_inward_note.purchase_order_id.supplier_id.supplier_no)
                    grn_data['supplier_name'] = str(queryset.goods_inward_note.purchase_order_id.supplier_id.company_name)
                    grn_data['purchase_no'] = str(queryset.goods_inward_note.purchase_order_id.purchaseOrder_no.linked_model_id)
                    grn_data['purchase_id'] = str(queryset.goods_inward_note.purchase_order_id.id)
                    grn_data['due_date'] = str(queryset.goods_inward_note.purchase_order_id.due_date)
                    grn_data['department'] = str(queryset.goods_inward_note.purchase_order_id.department.name)
                    grn_data['receving_store'] = str(queryset.goods_inward_note.purchase_order_id.receiving_store_id.store_name)
 
                for item in queryset.goods_receipt_note_item_details.all(): 
                    data = {
                                "id":str(item.id),
                                "gin_id" : str(item.gin.id),
                                "itemMasterId":str(item.gin.item_master.id),
                                "itemName":str(item.gin.item_master.item_name),
                                "itemPartCode":str(item.gin.item_master.item_part_code),
                                "description" : str(item.gin.item_master.description),
                                "po_qty": str(item.gin.purchase_order_parent.po_qty) if item.gin.purchase_order_parent else None,
                                "po_uom": str(item.gin.purchase_order_parent.po_uom) if item.gin.purchase_order_parent else None,
                                "base_qty" : str(item.base_qty),
                                "base_uom" : str(item.gin.purchase_order_parent.uom.name) if item.gin.purchase_order_parent else None ,
                                "inward" : str(item.qty) ,
                                "qc" : item.gin.qc,
                                "conversion_factor":str(item.gin.purchase_order_parent.conversion_factor) if item.gin.purchase_order_parent.conversion_factor else None,
                                "invoiceQty":str(item.purchase_invoice_qty) if item.purchase_invoice_qty else None,
                                "returnQty":str(item.purchase_return_qty) if item.purchase_return_qty else None,
                            }
                    if item.gin.item_master.batch_number:
                        data['is_batch'] = True
                        data['batch'] = item.batch_number
                    elif item.gin.item_master.serial:
                        data['is_serial'] = True
                        data['serial'] = str(item.serial_number).split(",") if item.serial_number else ""
                        data['serial_auto_gentrate'] = item.gin.item_master.serial_auto_gentrate
                        data['serial_format'] = item.gin.item_master.serial_format
                        data['serial_starting'] = item.gin.item_master.serial_starting
                
                    data['stock_added'] = item.stock_added
                    grn_item_details.append(data)
                grn_data['item'] = grn_item_details 
                return getGinDataForQir(items=grn_data)
        except Exception as e:
            return GraphQLError(f"An exception occurred {str(e)}")

    def resolve_rework_delivery_challan_initial_fetch(self, info, id):
        rework_delivery_challan_data = {}
        itemdetail = []
        try:
            if id:
                queryset =  QualityInspectionReport.objects.filter(id=id).first()
                if not queryset:
                    return GraphQLError("Quality Inspection Report in not Found.")
                if queryset.rework_received:
                    return GraphQLError("Already rework is exists.")
                
                purchase_instance = queryset.goods_inward_note.purchase_order_id
                rework_delivery_challan_data = {
                    "id":"",
                    "reworkDCNo":  "",
                    "reworkDCDate": "",
                    "purchaseOrderNo": purchase_instance.purchaseOrder_no.linked_model_id,
                    "purchaseOrderID": purchase_instance.id,
                    "reason": "",
                    "qirNo": queryset.qir_no.linked_model_id,
                    "qirId": queryset.id,
                    "supplierNumber": purchase_instance.supplier_id.supplier_no,
                    "supplierName": purchase_instance.supplier_id.company_name,
                    "addressList": [ 
                         {
                            "value": addres.id,
                            "label": addres.address_type,
                            "fullAddress": {
                                "id": addres.id,
                                "addressType": addres.address_type,
                                "addressLine1": addres.address_line_1,
                                "addressLine2": addres.address_line_2,
                                "city": addres.city,
                                "state": addres.state,
                                "country": addres.country,
                                "pincode": addres.pincode,
                            }
                        }
                        for addres in purchase_instance.supplier_id.address.all()
                    ],
                    "addressType": {
                        "value": purchase_instance.address.id,
                        "label": purchase_instance.address.address_type,
                        "fullAddress": {
                            "id": purchase_instance.address.id,
                            "addressType": purchase_instance.address.address_type,
                            "addressLine1": purchase_instance.address.address_line_1,
                            "addressLine2": purchase_instance.address.address_line_2,
                            "city": purchase_instance.address.city,
                            "state": purchase_instance.address.state,
                            "country": purchase_instance.address.country,
                            "pincode": purchase_instance.address.pincode,
                        }
                        
                    },
                    "contactPerson": {
                        "value": purchase_instance.contact.id,
                        "label": purchase_instance.contact.contact_person_name,
                        "mobile": purchase_instance.contact.phone_number,
                        "Email":purchase_instance.contact.email,
                        "whatsappNo": purchase_instance.contact.whatsapp_no
                    },
                    "gstinType": purchase_instance.gstin_type,
                    "gstin": purchase_instance.gstin,
                    "placeOfSupply": {
                        "value": purchase_instance.place_of_supply,
                        "label": purchase_instance.place_of_supply
                    },
                    "currency":{
                            "value": str(purchase_instance.currency.id), 
                            "label": purchase_instance.currency.Currency.name, 
                            "rate":  str(purchase_instance.currency.rate), 
                            "symbol": purchase_instance.currency.Currency.currency_symbol, 
                    },
                }

                for index, item in enumerate(queryset.quality_inspections_report_item_detail_id.all()):
                    purchase_cf = (item.goods_inward_note_item.purchase_order_parent.conversion_factor or 1)
                    qty = Decimal(f"{item.rework/purchase_cf : .3f}")
                    if qty > 0:
                        amount = item.goods_inward_note_item.purchase_order_parent.po_rate*qty

                        itemdetail.append({
                            "index": index,
                            "id": "",
                            "qirId": item.id,
                            "uom":{
                                "value":item.goods_inward_note_item.purchase_order_parent.uom.id,
                                "label":item.goods_inward_note_item.purchase_order_parent.uom.name
                            },
                            "rate": str(item.goods_inward_note_item.purchase_order_parent.rate),
                            'po_uom' : {
                                "value":item.goods_inward_note_item.purchase_order_parent.po_uom.id,
                                "label":item.goods_inward_note_item.purchase_order_parent.po_uom.name
                            },
                            "po_rate": str(item.goods_inward_note_item.purchase_order_parent.po_rate),
                            "hsnCode":item.goods_inward_note_item.purchase_order_parent.hsn_id.hsn_code,
                            "hsnCode": {
                                "value": item.goods_inward_note_item.purchase_order_parent.hsn_id.id,
                                "label": item.goods_inward_note_item.purchase_order_parent.hsn_id.hsn_code
                            },
                            "description": item.goods_inward_note_item.purchase_order_parent.item_master_id.description,
                            "amount": str(amount),
                            "tax": str(item.goods_inward_note_item.purchase_order_parent.tax),
                            "partCode": {
                                "value":str(item.goods_inward_note_item.purchase_order_parent.item_master_id.id),
                                "label":str(item.goods_inward_note_item.purchase_order_parent.item_master_id.item_part_code)
                            },
                            "partName": {
                                "value":str(item.goods_inward_note_item.purchase_order_parent.item_master_id.id),
                                "label":str(item.goods_inward_note_item.purchase_order_parent.item_master_id.item_name)
                            },
                            "sgst":str(item.goods_inward_note_item.purchase_order_parent.sgst) if  item.goods_inward_note_item.purchase_order_parent.sgst else None,
                            "cgst":str(item.goods_inward_note_item.purchase_order_parent.cgst) if  item.goods_inward_note_item.purchase_order_parent.cgst else None,
                            "igst": str(item.goods_inward_note_item.purchase_order_parent.igst) if item.goods_inward_note_item.purchase_order_parent.igst else None,
                            "cess":str(item.goods_inward_note_item.purchase_order_parent.cess) if item.goods_inward_note_item.purchase_order_parent.cess else None,
                            "reworkQty": str(qty),
                            "purchase_rework_QTY" : str(item.rework * item.goods_inward_note_item.purchase_order_parent.conversion_factor),
                            "purchaseItem":str(item.goods_inward_note_item.purchase_order_parent.id) if item.goods_inward_note_item.purchase_order_parent.id else None
                        }) 
                    
                rework_delivery_challan_data['item_details'] = itemdetail
                return getGinDataForQir(items=rework_delivery_challan_data)
        except Exception as e:
            return GraphQLError(f"Unexpeted error occurred {str(e)}")
        
    @permission_required(models=["Rework DC"])
    def resolve_rework_delivery_challan(self, info, id):
        rework_delivery_challan_data = {}
        itemdetail = []
        try:
            if id:
                queryset = ReworkDeliveryChallan.objects.filter(id=id).first()
                if not queryset:
                    return GraphQLError("Rework Delivery Challan in not Found.")
                
                rework_delivery_challan_data = {
                    "id":queryset.id,
                    "reworkDCNo": queryset.dc_no.linked_model_id,
                    "reworkDCDate": str(queryset.dc_date),
                    "purchaseOrderNo": queryset.purchase_order_no.purchaseOrder_no.linked_model_id,
                    "purchaseOrderID": queryset.purchase_order_no.id,
                    "reason": queryset.remarks,
                    "qirNo": queryset.qualityinspectionreport_set.last().qir_no.linked_model_id,
                    "qirId": queryset.qualityinspectionreport_set.last().id,
                    "supplierNumber": queryset.purchase_order_no.supplier_id.supplier_no,
                    "supplierName": queryset.purchase_order_no.supplier_id.company_name, 
                    "addressList": [ 
                         {
                            "value": addres.id,
                            "label": addres.address_type,
                            "fullAddress": {
                                "id": addres.id,
                                "addressType": addres.address_type,
                                "addressLine1": addres.address_line_1,
                                "addressLine2": addres.address_line_2,
                                "city": addres.city,
                                "state": addres.state,
                                "country": addres.country,
                                "pincode": addres.pincode,
                            }
                        }
                        for addres in queryset.purchase_order_no.supplier_id.address.all()
                    ],
                    "addressType": {
                        "value": queryset.address.id,
                        "label": queryset.address.address_type,
                        "fullAddress": {
                            "id": queryset.address.id,
                            "addressType": queryset.address.address_type,
                            "addressLine1": queryset.address.address_line_1,
                            "addressLine2": queryset.address.address_line_2,
                            "city": queryset.address.city,
                            "state": queryset.address.state,
                            "country": queryset.address.country,
                            "pincode": queryset.address.pincode,
                        }
                    },
                    "contactPerson": {
                        "value": queryset.purchase_order_no.contact.id,
                        "label": queryset.purchase_order_no.contact.contact_person_name,
                        "mobile": queryset.purchase_order_no.contact.phone_number,
                        "Email":queryset.purchase_order_no.contact.email,
                        "whatsappNo": queryset.purchase_order_no.contact.whatsapp_no
                    },
                    "gstinType": queryset.purchase_order_no.gstin_type,
                    "gstin": queryset.purchase_order_no.gstin,
                    "placeOfSupply": {
                        "value": queryset.purchase_order_no.place_of_supply,
                        "label": queryset.purchase_order_no.place_of_supply
                    },
                    "currency":{ 
                            "value": str(queryset.purchase_order_no.currency.id), 
                            "label": queryset.purchase_order_no.currency.Currency.name, 
                            "rate":  str(queryset.purchase_order_no.currency.rate), 
                            "symbol": queryset.purchase_order_no.currency.Currency.currency_symbol, 
                    },
                    "createdBy" :queryset.created_by.username,
                    "updatedAt" : str(queryset.updated_at) if queryset.updated_at else str(queryset.created_at),
                    "status":str(queryset.status.name),
                    "termsCondition":{
                        "value":str(queryset.terms_conditions.id),
                        "label":str(queryset.terms_conditions.name),
                    },
                    "termsConditionText":queryset.terms_conditions_text,
                    "vehicleNo": queryset.vehicle_no if queryset.vehicle_no else None,
                    "transport": {
                        "value": queryset.transport.id if queryset.transport and queryset.transport.id else None,
                        "label": queryset.transport.company_name if queryset.transport and queryset.transport.company_name else None
                    },
                    "docketDate": str(queryset.docket_date) if queryset.docket_date else None,
                    "docketNo": queryset.docket_no if queryset.docket_no else None,
                    "otherModel": queryset.other_model if queryset.other_model else None,
                    "driverName": queryset.driver_name if queryset.driver_name else None, 
                    "eWayBill": queryset.e_way_bill if queryset.e_way_bill else None,
                    "eWayBillDate": str(queryset.e_way_bill_date) if queryset.e_way_bill_date else None,
                    "roundOffMethod": queryset.round_off_method if queryset.round_off_method  else None
                } 
                for index,  item in enumerate(queryset.rework_delivery_challan_item_details.all()):
                    itemdetail.append({
                        "index": index,
                        "id": item.id,
                        "qirId": item.qc_item.id,
                        "uom":item.qc_item.goods_inward_note_item.purchase_order_parent.uom.id,
                        "uom":{
                            "value":item.qc_item.goods_inward_note_item.purchase_order_parent.uom.id,
                            "label":item.qc_item.goods_inward_note_item.purchase_order_parent.uom.name
                        },
                        'po_uom' : {
                            "value":item.qc_item.goods_inward_note_item.purchase_order_parent.po_uom.id,
                            "label":item.qc_item.goods_inward_note_item.purchase_order_parent.po_uom.name
                        },
                        "po_rate": str(item.qc_item.goods_inward_note_item.purchase_order_parent.po_rate),
                        "hsnCode":item.qc_item.goods_inward_note_item.purchase_order_parent.hsn_id.hsn_code,
                        "hsnCode": {
                                    "value": item.qc_item.goods_inward_note_item.purchase_order_parent.hsn_id.id,
                                    "label": item.qc_item.goods_inward_note_item.purchase_order_parent.hsn_id.hsn_code
                        },
                        "rate": str(item.qc_item.goods_inward_note_item.purchase_order_parent.rate),
                        "description": item.qc_item.goods_inward_note_item.purchase_order_parent.item_master_id.description,
                        "amount": str(item.amount),
                        "tax": str(item.qc_item.goods_inward_note_item.purchase_order_parent.tax),
                        "partCode": {
                            "value":str(item.qc_item.goods_inward_note_item.purchase_order_parent.item_master_id.id),
                            "label":str(item.qc_item.goods_inward_note_item.purchase_order_parent.item_master_id.item_part_code)
                        },
                        "partName": {
                            "value":str(item.qc_item.goods_inward_note_item.purchase_order_parent.item_master_id.id),
                            "label":str(item.qc_item.goods_inward_note_item.purchase_order_parent.item_master_id.item_name)
                        },
                        "sgst":str(item.qc_item.goods_inward_note_item.purchase_order_parent.sgst) if  item.qc_item.goods_inward_note_item.purchase_order_parent.sgst else None,
                        "cgst":str(item.qc_item.goods_inward_note_item.purchase_order_parent.cgst) if  item.qc_item.goods_inward_note_item.purchase_order_parent.cgst else None,
                        "igst": str(item.qc_item.goods_inward_note_item.purchase_order_parent.igst) if item.qc_item.goods_inward_note_item.purchase_order_parent.igst else None,
                        "cess":str(item.qc_item.goods_inward_note_item.purchase_order_parent.cess,) if item.qc_item.goods_inward_note_item.purchase_order_parent.cess else None,
                        "reworkQty": str(item.rework_qty),
                        "purchase_rework_QTY" : str(item.rework_qty * item.qc_item.goods_inward_note_item.purchase_order_parent.conversion_factor),
                        "reworkDoneQty":str(item.received_qty) if item.received_qty else None,
                        "purchaseItem":str(item.purchase_item.id) if item.purchase_item.id else None
                    })
            rework_delivery_challan_data['item_details'] = itemdetail
            return getGinDataForQir(items=rework_delivery_challan_data)
        except Exception as e:
            return GraphQLError(f"An exception occurred {str(e)}")

    @permission_required(models=["Terms_Conditions", "Quotation", "SalesOrder_2","Purchase Return","Purchase Invoice","Rework DC","Purchase_Order", "Credit Note"])
    def resolve_terms_conditions(self, info, id=None, page=1, page_size=20, order_by=None, descending=False,
                                name=None, module=None):
        filter_kwargs = {}
        queryset = TermsConditions.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        # if module:
        #     filter_kwargs['module__icontains'] = module
        if module:
            filter_kwargs['module'] = module
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return TermsConditionsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    @permission_required(
        models=["Department", "Numbering_Series", "User_Management", "Quotation", "SalesOrder_2", "Employee",
                "Purchase_Order", "Debit Note"])
    def resolve_department(self, info, id=None, page=1, page_size=20, order_by=None,
                            descending=False, name=None):
        filter_kwargs = {}
        queryset = Department.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        db_s = {
            "id": {"field": "id", "is_text": False},
            'name': {"field": 'name', "is_text": True},

        }
        queryset = queryset.filter(**filter_kwargs)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)

        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        ) 
        return DepartmentConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_other_expenses_purchase_order(self, info, id=None):
        queryset = OtherExpensespurchaseOrder.objects.all()
        if id:
            queryset = queryset.filter(id=id)
        return OtherExpensespurchaseOrderConnection(items=queryset)

    @permission_required(models=["Purchase Invoice"])
    def resolve_purchase_invoice_selete_multi_purchase(self, info, supplier_id=None, department_id=None):
        filter = {}
        full_query = []

        if supplier_id:
            filter['supplier_id'] = supplier_id
        if department_id:
            filter['department_id'] = department_id
        filter['status__name__in'] = ['Submit']
        filter['active'] = True

        purchases = purchaseOrder.objects.filter(**filter).order_by("-created_at")
        purchase_index = 0
        for purchase in purchases:
            grn_datas =[]
            grn_index = 0
            for gin in purchase.gin.all():
                if gin.grn and gin.grn.status and gin.grn.status.name == "Received":
                    grn_item_details = []
                    for item in gin.grn.goods_receipt_note_item_details.all():
                        if item.purchaseinvoiceitemdetails_set.exists():
                            continue
                        rate = (item.gin.purchase_order_parent.rate or 0) if item.gin.purchase_order_parent.rate else (item.gin.purchase_order_parent.after_discount_value_for_per_item or 0)
                        amount = str(rate * (item.qty or 0))
                        item_json = {
                            "part_code" : item.gin.item_master.item_part_code,
                            "part_name" : item.gin.item_master.item_name,
                            "qty" : str(item.qty),
                            "rate" : str(rate),
                            "amount" : str(amount),
                            "conversion_factor" : str(item.conversion_factor),
                            "is_invoised":item.purchaseinvoiceitemdetails_set.exists(),
                        }
                        grn_item_details.append(item_json)
                    if len(grn_item_details)> 0:
                        grn_data ={
                            "grn_no" : gin.grn.grn_no.linked_model_id,
                            "grn_id" : str(gin.grn.id),
                            "gin_id" : str(gin.id),
                            "is_grn_selected":False,
                            "itemdetails": grn_item_details,
                            "index": grn_index
                        }
                        grn_index+=1
                        grn_datas.append(grn_data)
            
            if grn_datas:
                single_purchase = {
                    "purchaseOrder_no" : purchase.purchaseOrder_no.linked_model_id,
                    "is_purchase_selected":False,
                    "address_type":purchase.address.address_type,
                    "contact_person":purchase.contact.contact_person_name,
                    "gstin_type":purchase.gstin_type,
                    "gstin":purchase.gstin,
                    "state":purchase.address.state,
                    "place_of_supply":purchase.place_of_supply,
                    "gst_nature":purchase.gst_nature_transaction.nature_of_transaction,
                    "currency":purchase.currency.Currency.name,
                    "grn" : grn_datas,
                    "index":purchase_index,
                }
                purchase_index +=1
                full_query.append(single_purchase)

                 
        return getGinDataForQir(items=full_query)
    
    @permission_required(models=["Purchase Invoice"])
    def resolve_purchase_invoice_initial_fetch(self, info, grn_id=[]):

        grns = GoodsReceiptNote.objects.filter(id__in=grn_id)
        if not grns.exists():
            return GraphQLError("No GRN found.")

        first_grn = grns.first()
        purchase = first_grn.goods_inward_note.purchase_order_id
        supplier = purchase.supplier_id

        # --- Credit period ---
        purchase_list, purchase_order_no, grn_instances, transactions = [], [], [], []
        credit_period = 0
        for grn in grns:
            po = grn.goods_inward_note.purchase_order_id
            if po not in purchase_list:
                 purchase_list.append(po)
            if grn.status.name == "Received":
               
                credit_period = min(credit_period or po.credit_period or 0, po.credit_period or 0)

                linked_id = getattr(po.purchaseOrder_no, "linked_model_id", None)
                if linked_id not in purchase_order_no:
                    purchase_order_no.append(str(linked_id))

                grn_instances.append(grn)
            transactions.append(po.gst_nature_transaction)

        if len(set(transactions)) > 1:
            return GraphQLError("Different gst_nature_transaction found. Cannot make purchase invoice.")

        # --- Supplier TDS/TCS ---
        tds = None
        tcs = None
        if supplier.tds:
            tds = "P" if "P" in (supplier.pan_no or "") else "O"
        if supplier.tcs in ["SALES", "BOTH"]:
            if supplier.pan_no:
                tcs = "WP" if "P" in supplier.pan_no else "WO"
            else:
                tcs = "WOO"

        # --- Purchase Invoice Base ---
        purchase_invoice = {
            "invoice_no": "",
            "invoice_date": "",
            "supplier_code": supplier.supplier_no,
            "supplier_name": supplier.company_name,
            "supplier_pan_no": supplier.pan_no,
            "supplier_tcs": supplier.tcs,
            "supplier_tds": supplier.tds,
            "credit_period": str(credit_period),
            "payment_terms": purchase.payment_terms,
            "supplier_ref": purchase.supplier_ref,
            "department": purchase.department.name,
            "remaks": "",
            "due_date": str(purchase.due_date),
            "gst_type": purchase.gstin_type,
            "gstin": purchase.gstin,
            "state": purchase.address.state,
            "place_of_supply": purchase.place_of_supply,
            "eway_bill_no": ",".join([g.e_way_bill for g in grn_instances if g.e_way_bill]),
            "eway_bill_date": ",".join([str(g.e_way_bill_date) for g in grn_instances if g.e_way_bill_date]),
            "purchase_order_no": ",".join(purchase_order_no),
            "grn_no": ",".join([str(g.grn_no.linked_model_id) for g in grn_instances]),
            "gst_nature_type": purchase.gst_nature_type,
            "nature_of_transaction": getattr(purchase.gst_nature_transaction, "nature_of_transaction", ""),
            "igst": purchase.igst,
            "sgst": purchase.sgst,
            "cgst": purchase.cgst,
            "cess": purchase.cess,
            "currency": {
                "name": str(purchase.currency.Currency.name),
                "rate": str(purchase.exchange_rate) if purchase.exchange_rate else None,
                "currencySymbol": str(purchase.currency.Currency.currency_symbol),
            },
            "address": {
                "id": str(purchase.address.id or ""),
                "address_type": str(purchase.address.address_type or ""),
                "address_line_1": str(purchase.address.address_line_1 or ""),
                "address_line_2": str(purchase.address.address_line_2 or ""),
                "city": str(purchase.address.city or ""),
                "pincode": str(purchase.address.pincode or ""),
                "state": str(purchase.address.state or ""),
                "country": str(purchase.address.country or ""),
                "default": str(purchase.address.default),
            },
            "contact": {
                "id": str(purchase.contact.id or ""),
                "contact_person_name": str(purchase.contact.contact_person_name or ""),
                "email": str(purchase.contact.email or ""),
                "phone_number": str(purchase.contact.phone_number or ""),
                "whatsapp_no": str(purchase.contact.whatsapp_no or ""),
            },
        }

        # --- Item Grouping ---
        grouped_items, errors = {}, []
        for grn in grns:
            for item in grn.goods_receipt_note_item_details.exclude(
                Q(purchaseinvoiceitemdetails__isnull=False)
            ):
                gin_item, itemmaster, po_item = item.gin, item.gin.item_master, item.gin.purchase_order_parent 
                allow_qty = (item.qty or 0) - (item.purchase_return_qty or 0) - (item.purchase_invoice_qty or 0)
                if allow_qty <= 0:
                    continue

                rate, base_qty, po_rate = po_item.rate or 0, item.base_qty or 0, po_item.po_rate or 0
                po_qty = (item.qty or 0) - (item.purchase_return_qty or 0)
                po_amount, amount = po_rate * po_qty, base_qty 

                # TDS/TCS %
                tds_percentage = (
                    itemmaster.tds_link.percent_individual_with_pan
                    if tds == "P" and itemmaster.tds_link
                    else itemmaster.tds_link.percent_other_with_pan
                    if tds == "O" and itemmaster.tds_link
                    else 0
                ) 
                tcs_percentage = 0
                if itemmaster.tcs_link:
                    if tcs == "WP":
                        tcs_percentage = itemmaster.tcs_link.percent_individual_with_pan
                    elif tcs == "WO":
                        tcs_percentage = itemmaster.tcs_link.percent_other_with_pan
                    elif tcs == "WOO":
                        tcs_percentage = itemmaster.tcs_link.percent_other_without_pan 
                # Group by itemmaster
                data = grouped_items.setdefault(itemmaster.id, {
                    "grnItem": [],
                    "partCode": itemmaster.item_part_code,
                    "partName": itemmaster.item_name,
                    "description": itemmaster.description,
                    "po_rate": str(po_rate),
                    "po_qty": "0",
                    "po_uom": po_item.po_uom.name,
                    "po_amount": "0",
                    "rate": str(rate),
                    "qty": "0",
                    "uom": po_item.uom.name,
                    "amount": "0",
                    "conversion_factor": [],
                    "category": itemmaster.category.name,
                    "hsn": po_item.hsn_id.hsn_code,
                    "igst": str(po_item.igst or 0),
                    "cgst": str(po_item.cgst or 0),
                    "sgst": str(po_item.sgst or 0),
                    "cess": str(po_item.cess or 0),
                    "tdsLink": {
                        "percentOtherWithPan": str(getattr(itemmaster.tds_link, "percent_other_with_pan", "") or ""),
                        "percentIndividualWithPan": str(getattr(itemmaster.tds_link, "percent_individual_with_pan", "") or ""),
                    },
                    "tcsLink": {
                        "percentIndividualWithPan": str(getattr(itemmaster.tcs_link, "percent_individual_with_pan", "") or ""),
                        "percentOtherWithPan": str(getattr(itemmaster.tcs_link, "percent_other_with_pan", "") or ""),
                        "percentOtherWithoutPan": str(getattr(itemmaster.tcs_link, "percent_other_without_pan", "") or ""),
                    },
                    "tds_percentage": str(tds_percentage) if tds_percentage else None,
                    "tcs_percentage": str(tcs_percentage) if tcs_percentage else None,
                    "tax": str(po_item.tax or 0),
                    "is_submited_purchase_invoice": item.is_submited_purchase_invoice or None,
                    "is_draft_purchase_invoice": item.is_draft_purchase_invoice or None,
                })

                # update grouped values
                data["grnItem"].append(str(item.id))
                data["conversion_factor"].append(str(item.conversion_factor))
                data["po_qty"] = str(Decimal(data["po_qty"]) + po_qty)
                data["po_amount"] = str(Decimal(data["po_amount"]) + po_amount)
                data["qty"] = str(Decimal(data["qty"]) + base_qty)
                data["amount"] = str(Decimal(data["amount"]) + amount)
 
        # conversion factor validation
        for item_data in grouped_items.values():
            if len(set(item_data["conversion_factor"])) > 1:
                errors.append(f"{item_data['description']} has different conversion factors. Not allowed.")
            item_data['conversion_factor'] =item_data["conversion_factor"][0]
        if errors:
            return GraphQLError(", ".join(errors))
        service_item = []
        for item in purchase.item_details.filter(item_master_id__item_types__name="Service"):
            if item.purchaseinvoiceitemdetails_set.exists():
                continue
            itemmaster  = item.item_master_id
            # TDS/TCS %
            tds_percentage = (
                itemmaster.tds_link.percent_individual_with_pan
                if tds == "P" and itemmaster.tds_link
                else itemmaster.tds_link.percent_other_with_pan
                if tds == "O" and itemmaster.tds_link
                else 0
            ) 
            tcs_percentage = 0
            if itemmaster.tcs_link:
                if tcs == "WP":
                    tcs_percentage = itemmaster.tcs_link.percent_individual_with_pan
                elif tcs == "WO":
                    tcs_percentage = itemmaster.tcs_link.percent_other_with_pan
                elif tcs == "WOO":
                    tcs_percentage = itemmaster.tcs_link.percent_other_without_pan 
            
            data = {"grnItem": [],
                    "po_item" :str(item.id),
                    "partCode": itemmaster.item_part_code,
                    "partName": itemmaster.item_name,
                    "description": item.description,
                    "po_rate": str(item.po_rate),
                    "po_qty": str(item.po_qty),
                    "po_uom": item.po_uom.name,
                    "po_amount": str(item.po_amount),
                    "rate": str(item.rate),
                    "qty": str(item.qty),
                    "uom": item.uom.name,
                    "amount": str(item.amount),
                    "conversion_factor": 1,
                    "category": itemmaster.category.name,
                    "hsn": item.hsn_id.hsn_code,
                    "igst": str(item.igst or 0),
                    "cgst": str(item.cgst or 0),
                    "sgst": str(item.sgst or 0),
                    "cess": str(item.cess or 0),
                    "tdsLink": {
                        "percentOtherWithPan": str(getattr(itemmaster.tds_link, "percent_other_with_pan", "") or ""),
                        "percentIndividualWithPan": str(getattr(itemmaster.tds_link, "percent_individual_with_pan", "") or ""),
                    },
                    "tcsLink": {
                        "percentIndividualWithPan": str(getattr(itemmaster.tcs_link, "percent_individual_with_pan", "") or ""),
                        "percentOtherWithPan": str(getattr(itemmaster.tcs_link, "percent_other_with_pan", "") or ""),
                        "percentOtherWithoutPan": str(getattr(itemmaster.tcs_link, "percent_other_without_pan", "") or ""),
                    },
                    "tds_percentage": str(tds_percentage) if tds_percentage else None,
                    "tcs_percentage": str(tcs_percentage) if tcs_percentage else None,
                    "tax": str(item.tax or 0),
                }
            service_item.append(data)
 
        # purchase_invoice["item_details"] = list(grouped_items.values()) 
        purchase_invoice['item_details'] = list(grouped_items.values()) + service_item


        if not purchase_invoice["item_details"]:
            raise GraphQLError("All GRN items are already invoiced/returned.")

        # --- Other Expenses ---
        other_expense_list = []
        for po in purchase_list:
            for oe in po.other_expenses.all():
                if not OtherExpensespurchaseOrder.objects.filter(parent=oe.id).exists():
                    other_expense_list.append({
                        "otherIncomeChargesId": {
                            "label": str(oe.other_expenses_id.name),
                            "value": str(oe.other_expenses_id.id),
                            "hsn": {
                                "id": str(getattr(oe.other_expenses_id.HSN, "id", "") or ""),
                                "hsnCode": str(getattr(oe.other_expenses_id.HSN, "hsn_code", "") or ""),
                            },
                        },
                        "amount": str(oe.amount or 0),
                        "igst": str(oe.igst or ""),
                        "sgst": str(oe.sgst or ""),
                        "cgst": str(oe.cgst or ""),
                        "cess": str(oe.cess or ""),
                        "tax": str(oe.tax or ""),
                        "parent": str(oe.id or ""),
                    })
        purchase_invoice["other_expence"] = other_expense_list

        return getGinDataForQir(items=purchase_invoice)

    @permission_required(models=["Purchase Invoice"])
    def resolve_purchase_invoice_edit_fetch(self, info, id=None):
        purchase_invoice = {}
        itemdetails=[]
        other_expence_list =[]
        
        if id:
            purchase_invoice_instance = PurchaseInvoice.objects.filter(id=id).first()
            if not purchase_invoice_instance:
                return GraphQLError(" Purchase Invoice Not found.")
            
            grn_instances = GoodsReceiptNote.objects.filter(purchase_invoice=purchase_invoice_instance)

            purchase_nos = (
                    GoodsReceiptNote.objects.filter(purchase_invoice=purchase_invoice_instance)
                    .exclude(goods_inward_note__purchase_order_id__purchaseOrder_no__linked_model_id__isnull=True)
                    .values_list("goods_inward_note__purchase_order_id__purchaseOrder_no__linked_model_id", flat=True)
                )

            purchase = (grn.goods_inward_note.purchase_order_id 
                        if (grn := purchase_invoice_instance.goodsreceiptnote_set.first()) and grn.goods_inward_note 
                        else None)
            if not purchase:
                return GraphQLError(" Purchase Not found.")
            
            grn_nos = (
                GoodsReceiptNote.objects.filter(purchase_invoice=purchase_invoice_instance)
                .exclude(grn_no__linked_model_id__isnull=True)
                .values_list("grn_no__linked_model_id", flat=True)
            )

            purchase_nos = (
                GoodsReceiptNote.objects.filter(purchase_invoice=purchase_invoice_instance)
                .exclude(goods_inward_note__purchase_order_id__purchaseOrder_no__linked_model_id__isnull=True)
                .values_list("goods_inward_note__purchase_order_id__purchaseOrder_no__linked_model_id", flat=True)
            )
            purchase_invoice = {
                "id":str(purchase_invoice_instance.id),
                "invoice_no": str(purchase_invoice_instance.purchase_invoice_no.linked_model_id),
                "invoice_date": str(purchase_invoice_instance.purchase_invoice_date),
                "purchase_order_no":','.join(purchase_nos),
                "grn_no":",".join(grn_nos), 
                "supplier_code": purchase.supplier_id.supplier_no,
                "supplier_name": purchase.supplier_id.company_name,   # you might want purchase.supplier_id.name here
                "supplier_pan_no": purchase.supplier_id.pan_no,
                "supplier_tcs": purchase.supplier_id.tcs,
                "supplier_tds": purchase.supplier_id.tds,
                "payment_terms": purchase_invoice_instance.payment_terms,
                "supplier_ref": purchase.supplier_ref,
                "department": purchase.department.name,
                "grn_no":",".join([grn_instance.grn_no.linked_model_id for grn_instance in grn_instances if grn_instance.grn_no and grn_instance.grn_no.linked_model_id ]), 
                "eway_bill_no": ",".join([grn_instance.e_way_bill for grn_instance in grn_instances if grn_instance.e_way_bill]),
                "eway_bill_date":",".join([grn_instance.e_way_bill_date for grn_instance in grn_instances  if grn_instance.e_way_bill_date ]) ,
                "purchase_order_no" : ",".join(purchase_nos),
                "purchase_order_id":str(purchase.id),
                "remaks": purchase_invoice_instance.remarks,
                "due_date": str(purchase_invoice_instance.due_date),
                "credit_date": str(purchase_invoice_instance.credit_date),
                "credit_period": str(purchase_invoice_instance.credit),
                "gst_type": purchase.gstin_type,
                "gstin": purchase.gstin,
                "state": purchase.address.state,
                "place_of_supply": purchase.place_of_supply, 
                "gst_nature_type":purchase.gst_nature_type,
                "nature_of_transaction":purchase.gst_nature_transaction.nature_of_transaction if purchase.gst_nature_transaction.nature_of_transaction else "",
                "igst":str(purchase_invoice_instance.igst),
                "sgst":str(purchase_invoice_instance.sgst),
                "cgst":str(purchase_invoice_instance.cgst),
                "cess":str(purchase_invoice_instance.cess),
                "igst_value":str(purchase_invoice_instance.igst_value),
                "sgst_value":str(purchase_invoice_instance.sgst_value),
                "cgst_value":str(purchase_invoice_instance.cgst_value),
                "cess_value":str(purchase_invoice_instance.cess_value),
                "tds_bool": purchase_invoice_instance.tds_bool,
                "tcs_bool": purchase_invoice_instance.tcs_bool,
                "tds_total":str(purchase_invoice_instance.tds_total),
                "tcs_total":str(purchase_invoice_instance.tcs_total),
                "item_total_befor_tax" : str(purchase_invoice_instance.item_total_befor_tax),
                "other_charges_befor_tax" : str(purchase_invoice_instance.other_charges_befor_tax),
                "taxable_value": str(purchase_invoice_instance.taxable_value),
                "tax_total" : str(purchase_invoice_instance.tax_total),
                "round_off" : str(purchase_invoice_instance.round_off),
                "roundOffMethod":purchase_invoice_instance.round_off_method if purchase_invoice_instance.round_off_method else None,
                "net_amount" :str(purchase_invoice_instance.net_amount),
                "created_by" :purchase_invoice_instance.created_by.username if purchase_invoice_instance.created_by else None,
                "modified_by" :purchase_invoice_instance.modified_by.username if purchase_invoice_instance.created_by else None,
                "created_at": str(purchase_invoice_instance.created_at),
                "updated_at" :str( purchase_invoice_instance.updated_at),
                "currency":{
                    "name":str(purchase.currency.Currency.name),
                    "rate":str(purchase.exchange_rate) if purchase.exchange_rate else None,
                    "currencySymbol":str(purchase.currency.Currency.currency_symbol),
                },
                "terms_conditions":{
                    "value":str(purchase_invoice_instance.terms_conditions.id),
                    "label":purchase_invoice_instance.terms_conditions.name,
                },
                "terms_conditions_text":purchase_invoice_instance.terms_conditions_text,
                "status":purchase_invoice_instance.status.name,
                "purchase_invoice_import" : {},
                "date" : str(datetime.now().date())
            }
            purchaseinvoiceimport = PurchaseInvoiceImport.objects.filter(purchase_invoice=purchase_invoice_instance).first()
            if purchaseinvoiceimport:
                purchase_invoice_import_line = []
                purchase_invoice_import = purchaseinvoiceimport
                purchase_invoice['purchase_invoice_import'] =  {
                                                                "bill_of_entry_no" : purchase_invoice_import.bill_of_entry_no,
                                                                "bill_of_entry_date":str(purchase_invoice_import.bill_of_entry_date),
                                                                "port_code": str(purchase_invoice_import.port_code),
                                                                "total_duty" :str(purchase_invoice_import.total_duty),
                                                                "id":str(purchase_invoice_import.id),
                                                                }
                
                for index, item in enumerate(PurchaseInvoiceImportLine.objects.filter(import_header=purchaseinvoiceimport)):
                     
                    purchase_item = item.item.grn_item.first().gin.purchase_order_parent
                    purchase_invoice_import_line.append({
                    "index":str(index),
                    "hsn":purchase_item.hsn_id.hsn_code,
                    "description":purchase_item.description,
                    "po_rate":str(purchase_item.po_rate),
                    "po_qty":str(purchase_item.po_qty),
                    "po_amount":str(purchase_item.po_amount),
                    "assessableHsn" : {
                        "value":str(item.assessable_hsn.id),
                        "label":item.assessable_hsn.hsn_code
                    },
                    "assessableValue" : str(item.assessable_value),
                    "igst" : str(item.igst),
                    })
                purchase_invoice['purchase_invoice_import']['purchase_invoice_import_line'] = purchase_invoice_import_line
  
            address_obj = purchase.address
            purchase_invoice["address"] = {
                "id": str(address_obj.id or ""),
                "address_type": str(address_obj.address_type or ""),
                "address_line_1": str(address_obj.address_line_1 or ""),
                "address_line_2": str(address_obj.address_line_2 or ""),
                "city": str(address_obj.city or ""),
                "pincode": str(address_obj.pincode or ""),
                "state": str(address_obj.state or ""),
                "country": str(address_obj.country or ""),
                "default": str(address_obj.default),  # True/False → "True"/"False"
            }
            contact_obj = purchase.contact
            purchase_invoice["contact"] = {
                "id":str(contact_obj.id or ""),
                "contact_person_name": str(contact_obj.contact_person_name or ""),
                "email": str(contact_obj.email or ""),
                "phone_number":str(contact_obj.phone_number or ""),
                "whatsapp_no":str(contact_obj.whatsapp_no or ""),
            }
        
            for item in purchase_invoice_instance.item_detail.all():
               
                rate= 0
                base_qty = 0
                grn_item_ids= []
                if item.grn_item.exists():
                    grn_item_ids = [str(grn_item.id) for grn_item in item.grn_item.all()]
                    base_qty = sum((grn_item.base_qty or 0) for grn_item in item.grn_item.all())
                    grn_item = item.grn_item.first()
                    gin_item = grn_item.gin
                    itemmaster = grn_item.gin.item_master if grn_item and grn_item.gin else None
                    rate = gin_item.purchase_order_parent.rate
                elif item.po_item:
                    itemmaster = item.po_item.item_master_id
                    
                
                data = {
                    "grnItem": grn_item_ids,
                    "po_item" :str(item.po_item.id) if item.po_item else None,
                    "partCode": itemmaster.item_part_code,
                    "partName": itemmaster.item_name,   # maybe use name instead of code
                    "description": itemmaster.description,
                    "category": itemmaster.category.name,
                    "po_rate" : str(item.po_rate) ,
                    "po_qty" : str(item.po_qty),
                    "po_uom": gin_item.purchase_order_parent.po_uom.name,
                    "po_amount": str(item.po_amount),
                    "rate":str(rate)  if rate else str(item.po_rate),
                    "qty": str(base_qty) if base_qty else str(item.po_qty) ,
                    "uom": gin_item.purchase_order_parent.uom.name,
                    "conversion_factor" : str(item.conversion_factor),
                    "hsn": gin_item.purchase_order_parent.hsn_id.hsn_code,
                    "assessableHsn":{
                        "value":str(gin_item.purchase_order_parent.hsn_id.id),
                        "label":gin_item.purchase_order_parent.hsn_id.hsn_code,
                        "tax":str(gin_item.purchase_order_parent.hsn_id.gst_rates.rate),
                    },
                    "igst": str(item.igst or 0)if item.igst else None,
                    "cgst": str(item.cgst or 0)if item.cgst else None,
                    "sgst": str(item.sgst or 0)if item.sgst else None,
                    "cess": str(item.cess or 0)if item.cess else None, 
                    "tdsLink": {
                        "percentOtherWithPan": str(itemmaster.tds_link.percent_other_with_pan) if itemmaster.tds_link and itemmaster.tds_link.percent_other_with_pan is not None else "",
                        "percentIndividualWithPan": str(itemmaster.tds_link.percent_individual_with_pan) if itemmaster.tds_link and itemmaster.tds_link.percent_individual_with_pan is not None else "",
                    },
                    "tcsLink": {
                        "percentIndividualWithPan": str(itemmaster.tcs_link.percent_individual_with_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_individual_with_pan is not None else "",
                        "percentOtherWithPan": str(itemmaster.tcs_link.percent_other_with_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_other_with_pan is not None else "",
                        "percentOtherWithoutPan": str(itemmaster.tcs_link.percent_other_without_pan) if itemmaster.tcs_link and itemmaster.tcs_link.percent_other_without_pan is not None else "",
                    },
                    "tds_percentage":str(item.tds_percentage) if item.tds_percentage else None,
                    "tcs_percentage":str(item.tcs_percentage) if item.tcs_percentage else None,
                    "tds_value":str(item.tds_value) if item.tds_value else None,
                    "tcs_value":str(item.tcs_value) if item.tcs_value else None,
                    "tax": str(gin_item.purchase_order_parent.tax or 0),
                    "id":str(item.id or 0),
                }
                itemdetails.append(data)

            for expence in purchase_invoice_instance.other_expence_charge.all():
                    other_expence_data = {
                        "id" : str(expence.id),
                        "otherIncomeChargesId":{
                            "label": str(expence.other_expenses_id.name),
                            "value": str(expence.other_expenses_id.id),
                            "hsn": {
                                "id":str(expence.other_expenses_id.HSN.id) if expence.other_expenses_id.HSN and expence.other_expenses_id.HSN.id else None,
                                "hsnCode":str(expence.other_expenses_id.HSN.hsn_code) if expence.other_expenses_id.HSN and expence.other_expenses_id.HSN.hsn_code else None,
                            },
                            },
                        "amount": str(expence.amount),
                        "igst": str(expence.igst or ""),
                        "sgst":str(expence.sgst or ""),
                        "cgst":str(expence.cgst or ""),
                        "cess":str(expence.cess or ""),
                        "tax" :str(expence.tax or ""),
                        "parent": str(expence.parent.id) if expence.parent and expence.parent.id else None,
                    }
                    other_expence_list.append(other_expence_data)

            purchase_invoice["item_details"] = itemdetails
            purchase_invoice["other_expence"] = other_expence_list
            
        return getGinDataForQir(items=purchase_invoice)

    def resolve_purchase_return_multi_select(self,info,supplier_id=None, department_id=None,module=None):
        filter = {}
        full_query = []
        if not module : 
            return GraphQLError("Module is required")
        
        if supplier_id:
            filter['supplier_id'] = supplier_id
        if department_id:
            filter['department_id'] = department_id
        filter['status__name__in'] = ['Submit']
        filter['active'] = True

        purchases = purchaseOrder.objects.filter(**filter).order_by("-created_at")
        purchase_invoice_list = []
        purchase_index = 0
        grn_index = 0 
        
        if module == "GRN":
            for purchase in purchases:
                grn_datas =[] 
                
                for gin in purchase.gin.all():
                    if gin.grn and gin.grn.status and gin.grn.status.name == "Received":
                        grn_item_details = []
                        item_index = 0

                        for item in gin.grn.goods_receipt_note_item_details.all():
                            qty =  (item.qty or 0) - (item.purchase_return_qty or 0) - (item.purchase_invoice_qty or 0)
                            if qty > 0:
                                rate = (item.gin.purchase_order_parent.rate or 0)
                                uom =  item.gin.purchase_order_parent.uom
                                amount = str(rate * qty) 
                                item_json = {
                                    "part_code" : item.gin.item_master.item_part_code,
                                    "part_name" : item.gin.item_master.item_name,
                                    "qty" : str(qty),
                                    "rate" : str(rate),
                                    "uom" : uom.name,
                                    "conversion_factor" : str(item.conversion_factor), 
                                    "amount" : str(amount),
                                    "is_already_purchase_returned":"",
                                    "is_selected":False,
                                    "id":str(item.id),
                                    "index":item_index
                                }
                                item_index += 1
                                grn_item_details.append(item_json)

                        if len(grn_item_details)> 0:
                            grn_data ={
                                "grn_no" : gin.grn.grn_no.linked_model_id,
                                "grn_id" : gin.grn.id, 
                                "is_grn_selected":False,
                                "itemdetails": grn_item_details,
                                "is_already_purchase_returned":"",
                                "index": grn_index
                            }
                            grn_datas.append(grn_data)
                            grn_index +=1
                if grn_datas:
                    single_purchase = {
                        "purchaseOrder_no" : purchase.purchaseOrder_no.linked_model_id,
                        "purchaseOrder_id" : purchase.id,
                        "is_purchase_selected":False,
                        "is_already_purchase_returned":"",
                        "address_type":purchase.address.address_type,
                        "contact_person":purchase.contact.contact_person_name,
                        "gstin_type":purchase.gstin_type,
                        "gstin":purchase.gstin,
                        "state":purchase.address.state,
                        "place_of_supply":purchase.place_of_supply,
                        "gst_nature":purchase.gst_nature_transaction.nature_of_transaction,
                        "currency":purchase.currency.Currency.name,
                        "grn" : grn_datas,
                        "index":purchase_index,
                    }
                    purchase_index+=1
                            
                    full_query.append(single_purchase)

        if module == "Purchase Invoice":
            purchases = purchaseOrder.objects.filter(**filter).order_by("-created_at")
            purchase_index = 0
            invoice_index = 0   

            for purchase in purchases:
                
                invoice_datas = [] 
                for gin in purchase.gin.all():
                    if gin.grn and gin.grn.status and gin.grn.status.name == "Received": 
                        for invoice in gin.grn.purchase_invoice.all():
                            if invoice in purchase_invoice_list:
                                continue
                            purchase_invoice_list.append(invoice)
                            invoice_item_details = []
                            item_index = 0
                            for item in invoice.item_detail.all():
                                grn_items = item.grn_item.all()
                                
                                qty  = sum((grn_item.qty or 0)  - (grn_item.purchase_return_qty or 0)  for grn_item in grn_items) 
                                if qty>0:
                                    rate = (item.po_rate or 0)
                                    amount = (rate * qty)
                                    item_json = {
                                        "part_code" : item.grn_item.first().gin.item_master.item_part_code,
                                        "part_name" : item.grn_item.first().gin.item_master.item_part_code,
                                        "qty" : str(qty),
                                        "rate" : str(rate),
                                        "amount" : str(amount),  
                                        "conversion_factor" : str(item.grn_item.first().conversion_factor),
                                        "is_selected": False,
                                        "is_already_purchase_returned": "",
                                        "id":str(item.id),
                                        "index":item_index
                                    }
                                    invoice_item_details.append(item_json) 
                                    item_index += 1
                            if len(invoice_item_details) > 0:
                                invoice_data = {
                                    "invoice_no" : invoice.purchase_invoice_no.linked_model_id,
                                    "invoice_id" : invoice.id, 
                                    "itemdetails": invoice_item_details,
                                    "index": invoice_index,   
                                    "is_already_purchase_returned": "",
                                    "is_invoice_selected":False,
                                }
                                
                                invoice_datas.append(invoice_data)
                                invoice_index += 1   
                        
                if len(invoice_datas) > 0:
                    single_purchase = {
                        "purchaseOrder_no" : purchase.purchaseOrder_no.linked_model_id,
                        "is_purchase_selected": False,
                        "address_type": purchase.address.address_type,
                        "contact_person": purchase.contact.contact_person_name,
                        "gstin_type": purchase.gstin_type,
                        "gstin": purchase.gstin,
                        "state": purchase.address.state,
                        "place_of_supply": purchase.place_of_supply,
                        "gst_nature": purchase.gst_nature_transaction.nature_of_transaction,
                        "currency": purchase.currency.Currency.name,
                        "invoice_data": invoice_datas,
                        "index": purchase_index,
                        "is_already_purchase_returned": "", 
                    }
                    purchase_index += 1
                    full_query.append(single_purchase)

        
        return getGinDataForQir(items=full_query)
    
    def resolve_initial_purchase_return_fetch(self, info, grn_item_id=None, purchase_invoice_item_ids=None):
        """
        Fetches initial data for Purchase Return, based on either GRN item(s) or Purchase Invoice item(s).
        Handles validation, grouping, and prepares response payload for QIR/Gin.
        """

        grn_item_id = grn_item_id or []
        purchase_invoice_item_ids = purchase_invoice_item_ids or []

        # --- Base Validations ---
        if not grn_item_id and not purchase_invoice_item_ids:
            return GraphQLError("GRN Item ID(s) or Purchase Invoice Item ID(s) must be provided.")

        # --- Setup containers ---
        grouped_items = {}
        purchase_orders = set() 
        grn_list, purchase_invoice_list = [], []
        errors, transactions = [], []
        credit_period, first_grn = 0, None

        # =====================================================================================
        # 1️ Flow: Based on GRN Item(s)
        # =====================================================================================
        if grn_item_id:
            grn_items = GoodsReceiptNoteItemDetails.objects.filter(id__in=grn_item_id)
            if not grn_items.exists():
                return GraphQLError("No GRN Item found.")

            # Collect unique GRNs
            for grn_item in grn_items:
                grn = grn_item.goodsreceiptnote_set.first()
                if grn and grn not in grn_list:
                    grn_list.append(grn)

            # Validate GRN statuses
            for grn in grn_list:
                if grn.status.name not in ["Received"]:
                    errors.append(f"{grn.grn_no.linked_model_id} -> status {grn.status.name} not allowed")

            if errors:
                return GraphQLError(", ".join(errors))

            # Collect purchase order + credit period + transaction type
            for grn in grn_list:
                po = grn.goods_inward_note.purchase_order_id
                credit_period = min(credit_period or po.credit_period or 0, po.credit_period or 0)
                purchase_orders.add(po)
                transactions.append(po.gst_nature_transaction)

            # Validate gst_nature_transaction consistency
            if len(set(transactions)) > 1:
                return GraphQLError("Different gst_nature_transaction found. Cannot make sales invoice.")

            first_grn = grn_items.first().goodsreceiptnote_set.first()

        # =====================================================================================
        # 2️ Flow: Based on Purchase Invoice Item(s)
        # =====================================================================================
        elif purchase_invoice_item_ids:
            purchase_invoice_items = PurchaseInvoiceItemDetails.objects.filter(id__in=purchase_invoice_item_ids)
            if not purchase_invoice_items.exists():
                return GraphQLError("No Purchase Invoice Item found.")
           
            # Collect unique purchase invoices
            for item in purchase_invoice_items: 
                
                if item.po_item: 
                    continue 
                pi = item.purchaseinvoice_set.first()
                if pi and pi not in purchase_invoice_list:
                    purchase_invoice_list.append(pi)
                
                if (item.grn_item.first() and item.grn_item.first().gin.goodsinwardnote_set.first() and
                    item.grn_item.first().gin.goodsinwardnote_set.first().purchase_order_id):
                    purchase_orders.add(item.grn_item.first().gin.goodsinwardnote_set.first().purchase_order_id)
                
    
            if len(purchase_invoice_list) > 1:
                return GraphQLError("More than one purchase invoice is not allowed.")
            
            if purchase_invoice_list[0].status.name != "Submit": 
                return GraphQLError(
                    f"{purchase_invoice_list[0].purchase_invoice_no.linked_model_id} "
                    f"{purchase_invoice_list[0].status.name} is not allowed"
                )
            # invoice_no = purchase_invoice_list[0].purchase_invoice_no.linked_model_id if purchase_invoice_list[0] else None
            first_grn = (
                purchase_invoice_items.first()
                .purchaseinvoice_set.first()
                .goodsreceiptnote_set.first()
            )
            
        # =====================================================================================
        # 3️ Common purchase return structure
        # =====================================================================================
        purchase = first_grn.goods_inward_note.purchase_order_id
        
        purchase_return = {
            "return_no": "",
            "return_date": "",
            "invoice_no":  "",
            "supplier_code": purchase.supplier_id.supplier_no,
            "supplier_name": purchase.supplier_id.company_name,
            "supplier_pan_no": purchase.supplier_id.pan_no,
            "department": purchase.department.name,
            "remaks": "",
            "due_date": str(purchase.due_date),
            "gst_type": purchase.gstin_type,
            "gstin": purchase.gstin,
            "state": purchase.address.state,
            "place_of_supply": purchase.place_of_supply,
            "eway_bill_no": "",
            "eway_bill_date": "",
            "purchase_order_no": ",".join(po.purchaseOrder_no.linked_model_id for po in purchase_orders),
            "purchase_order_id":str(purchase.id),
            "grn_no": ",".join(grn.grn_no.linked_model_id for grn in grn_list),
            "purchaseInvoiceNo":purchase_invoice_list[0].purchase_invoice_no.linked_model_id if purchase_invoice_list else None,
            "isInvoiced":True if purchase_invoice_list else None,
            "gst_nature_type": purchase.gst_nature_type,
            "nature_of_transaction": (
                purchase.gst_nature_transaction.nature_of_transaction
                if purchase.gst_nature_transaction and purchase.gst_nature_transaction.nature_of_transaction
                else ""
            ),
            "igst": purchase.igst,
            "sgst": purchase.sgst,
            "cgst": purchase.cgst,
            "cess": purchase.cess,
            "currency": {
                "label": str(purchase.currency.Currency.name),
                "rate": str(purchase.exchange_rate) if purchase.exchange_rate else None,
                "currencySymbol": str(purchase.currency.Currency.currency_symbol),
            },
        }

         
        # --- Address & Contact ---
        address_obj, contact_obj = purchase.address, purchase.contact
        purchase_return["address"] = {
            "value": str(address_obj.id or ""),
            "label": str(address_obj.address_type or ""),
            "address_line_1": str(address_obj.address_line_1 or ""),
            "address_line_2": str(address_obj.address_line_2 or ""),
            "city": str(address_obj.city or ""),
            "pincode": str(address_obj.pincode or ""),
            "state": str(address_obj.state or ""),
            "country": str(address_obj.country or ""),
            "default": str(address_obj.default),
        }
        purchase_return["contact"] = {
            "value": str(contact_obj.id or ""),
            "label": str(contact_obj.contact_person_name or ""),
            "email": str(contact_obj.email or ""),
            "phone_number": str(contact_obj.phone_number or ""),
            "whatsapp_no": str(contact_obj.whatsapp_no or ""),
        }

         
        # =====================================================================================
        # 4️ Helpers
        # =====================================================================================
        def get_available_serials(grn_items, itemmaster):
            """Return available serial numbers still in stock for a given itemmaster."""
            total_serials = [] 
            for grn_item in grn_items:  
                delimiter = ',' if ',' in grn_item.serial_number else '\n'
                 
                serial = (grn_item.serial_number or "") 
                # Split, strip whitespace, and remove empty strings
                numbers = [s.strip() for s in serial.split(delimiter) if s.strip()]
             
                serial_instances = SerialNumbers.objects.filter(
                    serial_number__in=numbers
                ).values_list("id", "serial_number")
               
                current_serial_ids = {
                    id
                    for stock in ItemStock.objects.filter(part_number=itemmaster)
                    for id in stock.serial_number.values_list("id", flat=True)
                }
            
                total_serials.extend(
                    {"value": sid, "label": s_num}
                    for sid, s_num in serial_instances
                    if sid in current_serial_ids
                )
            return total_serials

        # =====================================================================================
        # 5️ Populate Item Details
        # =====================================================================================
        item_details = [] 
        if grn_item_id:
            for index, item in enumerate(grn_items):
                grn_no = item.goodsreceiptnote_set.first().grn_no.linked_model_id if item.goodsreceiptnote_set.first() and item.goodsreceiptnote_set.first().grn_no.linked_model_id else None
                gin_item, itemmaster = item.gin, item.gin.item_master
                purchase_item = gin_item.purchase_order_parent
 
                po_rate = (purchase_item.po_rate or 0) 
                allowed_qty = (item.qty or 0) - (item.purchase_invoice_qty or 0) - (item.purchase_return_qty or 0)
                base_qty = Decimal(f"{allowed_qty/item.conversion_factor:.3f}")

                if allowed_qty <= 0:
                    # errors.append(
                    #     f"{itemmaster.item_part_code} - {itemmaster.item_name} has already been invoiced or returned."
                    # )
                    continue

                batch_info, serials , no_batch_no_serial_info, is_no_batch_no_serial_info = [], [], [], False
                if itemmaster.batch_number:
                    batch_info.append({"value": str(item.id), "label": item.batch_number, "qty": str(base_qty),"grn_no":str(grn_no) , "uom" :purchase_item.uom.name})
                elif itemmaster.serial:
                    serials = get_available_serials([item], itemmaster) 
                else:
                    is_no_batch_no_serial_info= True
                    no_batch_no_serial_info.append({"value": str(item.id), "label": grn_no, "qty": str(base_qty), "uom" : purchase_item.uom.name})
 
                if itemmaster.id not in grouped_items:
                    grouped_items[itemmaster.id] = {
                        "grnItem": [str(item.id)],
                        "itemMasterId":itemmaster.id,
                        "partCode": itemmaster.item_part_code,
                        "partName": itemmaster.item_name, 
                        "description": itemmaster.description,
                        "po_uom": purchase_item.po_uom.name,
                        "po_qty" : str(allowed_qty or 0),
                        "po_rate" : str(po_rate),
                        "base_uom":purchase_item.uom.name,
                        "base_qty": str(base_qty or 0),
                        "base_rate": str(purchase_item.rate),
                        "conversion_factor" : str(item.conversion_factor),
                        "category": itemmaster.category.name,
                        "hsn": purchase_item.hsn_id.hsn_code,
                        "igst": str(purchase_item.igst or 0),
                        "cgst": str(purchase_item.cgst or 0),
                        "sgst": str(purchase_item.sgst or 0),
                        "cess": str(purchase_item.cess or 0),
                        "po_amount": str(po_rate * allowed_qty),
                        "isBatch": itemmaster.batch_number,
                        "batch_list": batch_info,
                        "isSerial": itemmaster.serial,
                        "batch":"",
                        "serial":"",
                        "serial_list": serials,
                        "isNoBatchSerial" : is_no_batch_no_serial_info,
                        "no_batch_no_serial_list" : no_batch_no_serial_info,
                        "noBatchSerial":"",
                        "returnQty":"",
                        "tax": str(purchase_item.tax or 0),
                        "index":index+1,
                    }
                else:
                    grouped_items[itemmaster.id]["grnItem"].append(str(item.id))
                    if batch_info:
                        grouped_items[itemmaster.id]["batch_list"].extend(batch_info)
                    if serials:
                        grouped_items[itemmaster.id]["serial_list"].extend(serials)
                    if is_no_batch_no_serial_info:
                        grouped_items[itemmaster.id]["no_batch_no_serial_list"].extend(no_batch_no_serial_info)
                    grouped_items[itemmaster.id]["po_qty"] = str(
                        Decimal(grouped_items[itemmaster.id]["po_qty"]) + allowed_qty
                    )
                    
                    grouped_items[itemmaster.id]["base_qty"] = str(
                        Decimal(grouped_items[itemmaster.id]["base_qty"]) + base_qty
                    )
                    grouped_items[itemmaster.id]["po_amount"] = str(
                        Decimal(grouped_items[itemmaster.id]["po_amount"]) + (po_rate * allowed_qty)
                    )

            item_details = list(grouped_items.values())

        elif purchase_invoice_item_ids: 
            for idx,item in enumerate(purchase_invoice_items):
               
                if item.po_item:
                    continue
                first_grn_item = item.grn_item.first()
                if not first_grn_item:
                    continue
                
                gin_item, itemmaster = first_grn_item.gin, first_grn_item.gin.item_master
                purchase_item = gin_item.purchase_order_parent
                po_rate = (purchase_item.po_rate or 0)
                
                purchase_return_item_total_qty = sum((prc_item.po_return_qty or 0) for prc_item in item.purchasereturnchallanitemdetails_set.all())
                allowed_qty = (item.po_qty or 0)
                if purchase_return_item_total_qty:
                    allowed_qty = allowed_qty - (purchase_return_item_total_qty or 0) 
                
                base_qty = Decimal(f"{allowed_qty/item.conversion_factor:.3f}")
                
                batch_list, serials , no_batch_no_serial_info, is_no_batch_no_serial_info = [], [], [], False
                print("base_qty",itemmaster.batch_number, itemmaster.serial)
                if itemmaster.batch_number:
                    batch_list = [
                        {"value": str(grn.id), "label": grn.batch_number, "qty": str(base_qty),
                        "grn_no":grn.goodsreceiptnote_set.first().grn_no.linked_model_id,  "uom":purchase_item.uom.name}
                        for grn in item.grn_item.all()
                    ]
                elif itemmaster.serial:
                    serials = get_available_serials(item.grn_item.all(), itemmaster)
                    print("serials", serials)
                else:
                    is_no_batch_no_serial_info = True
                    no_batch_no_serial_info = [
                        {"value": str(grn.id), "label": grn.goodsreceiptnote_set.first().grn_no.linked_model_id, 
                        "uom":purchase_item.uom.name, "qty": str(base_qty)}
                        for grn in item.grn_item.all()
                    ]
                
                item_details.append({
                    "purchase_invoice": str(item.id),
                    "itemMasterId":itemmaster.id,
                    "partCode": itemmaster.item_part_code,
                    "partName": itemmaster.item_name,
                    "itemMasterId":str(itemmaster.id),
                    "description": itemmaster.description,
                    "category": itemmaster.category.name,
                    "po_uom": purchase_item.po_uom.name,
                    "po_qty" : str(allowed_qty or 0),
                    "po_rate" : str(po_rate),
                    "base_uom": purchase_item.uom.name,
                    "base_qty": str(base_qty),
                    "base_rate": str(purchase_item.rate),
                    "conversion_factor" : str(first_grn_item.conversion_factor),
                    "hsn": purchase_item.hsn_id.hsn_code,
                    "igst": str(purchase_item.igst or 0),
                    "cgst": str(purchase_item.cgst or 0),
                    "sgst": str(purchase_item.sgst or 0),
                    "cess": str(purchase_item.cess or 0),
                    "po_amount": str(po_rate * allowed_qty),
                    "isBatch": itemmaster.batch_number,
                    "batch_list": batch_list,
                    "isSerial": itemmaster.serial,
                    "serial":"",
                    "batch":"",
                    "serial_list": serials,
                    "isNoBatchSerial" : is_no_batch_no_serial_info,
                    "no_batch_no_serial_list" : no_batch_no_serial_info,
                    "noBatchSerial":"",
                    "returnQty":"",
                    "tax": str(purchase_item.tax or 0),
                    "index":idx+1
                })
        print("item_details", item_details)
        purchase_return["item_details"] = item_details

        # =====================================================================================
        # 6️⃣ Final Validations
        # =====================================================================================
        if errors:
            raise GraphQLError(", ".join(errors))
        if not purchase_return["item_details"]:
            raise GraphQLError("All GRN items are already invoiced.")
        
        return getGinDataForQir(items=purchase_return)

    def resolve_edit_purchase_return_fetch(self, info, purchase_return_id=None):
        grn_instance = None
        purchase_orders = []

        if not purchase_return_id:
            return GraphQLError("Purchase Return is required.")
        
        purchase_return_object = PurchaseReturnChallan.objects.filter(id=purchase_return_id).first()
        
        if not purchase_return_object:
            return GraphQLError("Purchase Return is not required.")
            
        
        purchase_invoice = purchase_return_object.purchaseinvoice_set.all() if purchase_return_object.purchaseinvoice_set else None
        goods_receipt_note = purchase_return_object.goodsreceiptnote_set.all() if purchase_return_object.goodsreceiptnote_set else None
        
        if purchase_invoice:
            first_invoice = purchase_invoice.first()
            grn_instance = first_invoice.item_detail.first().grn_item.first().goodsreceiptnote_set.first()
            
            
            purchase_orders.append(grn_instance.goods_inward_note.purchase_order_id)
            
        else:
            grn_instance = goods_receipt_note.first()
            for grn in purchase_return_object.goodsreceiptnote_set.all():
                purchase = grn.goods_inward_note.purchase_order_id
                if purchase not in purchase_orders:
                    purchase_orders.append(purchase)
        
        """Common purchase return structure"""
        
        purchase = grn_instance.goods_inward_note.purchase_order_id 
        purchase_return = {
            "return_no": purchase_return_object.purchase_return_no.linked_model_id,
            "return_date": str(purchase_return_object.purchase_return_date),
            "supplier_code": purchase.supplier_id.supplier_no,
            "supplier_name": purchase.supplier_id.company_name,
            "supplier_pan_no": purchase.supplier_id.pan_no,
            "department": purchase.department.name,
            "remaks": purchase_return_object.remarks,
            "gst_type": purchase.gstin_type,
            "gstin": purchase.gstin,
            "state": purchase.address.state,
            "place_of_supply": purchase.place_of_supply, 
            "purchase_order_no": ",".join(po.purchaseOrder_no.linked_model_id for po in purchase_orders),
            "purchase_order_id":str(purchase.id),
            "purchaseInvoiceNo": ", ".join( pi.purchase_invoice_no.linked_model_id for pi in purchase_invoice),
            "isInvoiced": True if purchase_invoice else False,
            "grn_no": ",".join(grn.grn_no.linked_model_id for grn in goods_receipt_note),
            "gst_nature_type": purchase.gst_nature_type,
            "nature_of_transaction": (
                purchase.gst_nature_transaction.nature_of_transaction
                if purchase.gst_nature_transaction and purchase.gst_nature_transaction.nature_of_transaction
                else ""
            ),
            "igst": purchase.igst,
            "sgst": purchase.sgst,
            "cgst": purchase.cgst,
            "cess": purchase.cess,
            "currency": {
                "label": str(purchase.currency.Currency.name),
                "rate": str(purchase.exchange_rate) if purchase.exchange_rate else None,
                "currencySymbol": str(purchase.currency.Currency.currency_symbol),
            },
            "termsConditions": {
                "value": str(purchase_return_object.terms_conditions.id) if purchase_return_object.terms_conditions and purchase_return_object.terms_conditions.id else "",
                "label": str(purchase_return_object.terms_conditions.name) if purchase_return_object.terms_conditions and purchase_return_object.terms_conditions.name else "",
            },
            "termsConditionText": purchase_return_object.terms_conditions_text or "",
            "vehicleNo": purchase_return_object.vehicle_no if purchase_return_object.vehicle_no else None,
            "transport": {
                "value": purchase_return_object.transport.id if purchase_return_object.transport and purchase_return_object.transport.id else None,
                "label": purchase_return_object.transport.company_name if purchase_return_object.transport and purchase_return_object.transport.company_name else None
            },
            "docketDate": str(purchase_return_object.docket_date) if purchase_return_object.docket_date else None,
            "docketNo": purchase_return_object.docket_no if purchase_return_object.docket_no else None,
            "otherModel": purchase_return_object.other_model if purchase_return_object.other_model else None,
            "driverName": purchase_return_object.driver_name if purchase_return_object.driver_name else None, 
            "eWayBill": str(purchase_return_object.eway_bill_no) if purchase_return_object.eway_bill_no else None,
            "eWayBillDate": str(purchase_return_object.eway_bill_date) if purchase_return_object.eway_bill_date else None,
            "created_by":purchase_return_object.created_by.username if purchase_return_object.created_by else "",
            "created_at": str(purchase_return_object.created_at),
            "updated_at" :str( purchase_return_object.updated_at),
            "roundOffMethod":purchase_return_object.round_off_method if purchase_return_object.round_off_method else None,
            "status": purchase_return_object.status.name if purchase_return_object.status else "",
            "id": str(purchase_return_object.id or ""),
        } 
        """Address & Contact"""
        address_obj, contact_obj = purchase.address, purchase.contact
        purchase_return["address"] = {
            "value": str(address_obj.id or ""),
            "label": str(address_obj.address_type or ""),
            "address_line_1": str(address_obj.address_line_1 or ""),
            "address_line_2": str(address_obj.address_line_2 or ""),
            "city": str(address_obj.city or ""),
            "pincode": str(address_obj.pincode or ""),
            "state": str(address_obj.state or ""),
            "country": str(address_obj.country or ""),
            "default": str(address_obj.default),
        }
        purchase_return["contact"] = {
            "value": str(contact_obj.id or ""),
            "label": str(contact_obj.contact_person_name or ""),
            "email": str(contact_obj.email or ""),
            "phone_number": str(contact_obj.phone_number or ""),
            "whatsapp_no": str(contact_obj.whatsapp_no or ""),
        } 
        itemdetails = []
        
        def get_serial(grn_items,  itemmaster):
            """Return available serial numbers still in stock for a given itemmaster."""
            total_serials = []
            for grn_item in grn_items:
                numbers = (grn_item.serial_number or "").split(",")
                numbers = [ number.strip() for number in numbers]
                serial_instances = SerialNumbers.objects.filter(
                    serial_number__in=numbers
                ).values_list("id", "serial_number")
                 
                current_serial_ids = {
                    id
                    for stock in ItemStock.objects.filter(part_number=itemmaster)
                    for id in stock.serial_number.values_list("id", flat=True)
                }

                total_serials.extend(
                    {"value": sid, "label": s_num}
                    for sid, s_num in serial_instances
                    if sid in current_serial_ids
                )
            return total_serials
        
 
        try:
            for index, item in enumerate(purchase_return_object.purchase_return_challan_item_Details.all()):
                batch = item.batch.all()
                serial_instances = item.serial.all()
                nobatch_noserial_instances = item.nobatch_noserial.all()
                all_batch_list = []
                serial = []
                serial_list =[]
                nobatch_noserial_list =[]
                seen = set() 
                no_batch_serial_seen = set()
                if batch:
                    for single_batch in batch:
                        allowed_qty= 0
                        grn_no = single_batch.batch.goodsreceiptnote_set.first().grn_no.linked_model_id
                        if item.grn_item.all():
                            allowed_qty = (single_batch.batch.qty or 0) - (single_batch.batch.purchase_return_qty or 0) - (single_batch.batch.purchase_invoice_qty or 0)
                        else:
                            allowed_qty = (single_batch.batch.qty or 0) - (single_batch.batch.purchase_return_qty or 0)
                        
                        all_batch_list.append({
                            "id": str(single_batch.id),
                            "value": str(single_batch.batch.id),
                            "label": single_batch.batch.batch_number,
                            "qty": f"{allowed_qty/single_batch.batch.conversion_factor:.3f}",
                            "returnQty": str(single_batch.qty),
                            "is_stock_reduce" : single_batch.is_stock_reduce,
                            "grn_no":str(grn_no)
                        })
                        seen.add(single_batch.batch.id)
                elif serial_instances:
                    for single_serial in serial_instances:
                        serial.append(
                            {
                            "value": single_serial.id,
                            "label": single_serial.serial_number,
                            }
                        )
                else:
                    for nobatch_noserial_instance in nobatch_noserial_instances:
                        grn_item = nobatch_noserial_instance.nobatch_noserial
                        grn_no = grn_item.goodsreceiptnote_set.first().grn_no.linked_model_id
                        allowed_qty= 0
                        if item.grn_item.all():
                            allowed_qty = (grn_item.qty or 0) - (grn_item.purchase_return_qty or 0) - (grn_item.purchase_invoice_qty or 0)
                        else:
                            allowed_qty = (grn_item.qty or 0) - (grn_item.purchase_return_qty or 0)
                        nobatch_noserial_list.append(
                            {
                            "id": str(nobatch_noserial_instance.id),
                            "value": str(grn_item.id),
                            "label": grn_no,
                            "qty": f"{allowed_qty/grn_item.conversion_factor:.3f}",
                            "returnQty": str(nobatch_noserial_instance.qty),
                            "is_stock_reduce" : nobatch_noserial_instance.is_stock_reduce,
                            }
                        )
                        no_batch_serial_seen.add(grn_item.id)
 
                if item and item.purchase_invoice_item:
                    grn_item = item.purchase_invoice_item.grn_item.first()
                    grn_no = grn_item.goodsreceiptnote_set.first().grn_no.linked_model_id
                    itemmaster = grn_item.gin.item_master
                    purchase_item = grn_item.gin.purchase_order_parent
                    if itemmaster.batch_number:
                        for grn in item.purchase_invoice_item.grn_item.all():
                            if grn.id not in seen:
                                allowed_qty=  (grn.qty or 0) - (grn.purchase_return_qty or 0)
                                base_qty = allowed_qty/(grn.conversion_factor or 0)
                                all_batch_list.append({
                                    "id": None,
                                    "value": str(grn.id),
                                    "label": grn.batch_number,
                                    "qty": str(base_qty),
                                    "returnQty": "", 
                                    "grn_no":grn_no
                                })
                                seen.add(grn.id)

                    elif itemmaster.serial:
                        serial_list =get_serial(item.purchase_invoice_item.grn_item.all(),   itemmaster)
                    
                    else:
                        for grn in item.purchase_invoice_item.grn_item.all():
                            if grn.id not in no_batch_serial_seen:
                                new_allowed_qty = (grn.qty or 0) - (grn.purchase_return_qty or 0) - (grn.purchase_invoice_qty or 0)
                                grn_no = grn.goodsreceiptnote_set.first().grn_no.linked_model_id
                                base_qty = new_allowed_qty/grn.conversion_factor
                                
                                nobatch_noserial_list.append(
                                    {
                                    "id":  "",
                                    "value": str(grn.id),
                                    "label": grn_no,
                                    "qty": str(base_qty),
                                    "returnQty": "",
                                    "is_stock_reduce" :  "",
                                    })
                    allowed_qty = (item.purchase_invoice_item.po_qty or 0)
                    po_rate =  (grn_item.gin.purchase_order_parent.po_rate or 0)
                   
                    data = {
                        "purchase_invoice": str(item.purchase_invoice_item.id),
                        "partCode": itemmaster.item_part_code,
                        "partName": itemmaster.item_name,
                        "itemMasterId":str(itemmaster.id),
                        "description": itemmaster.description,
                        "category": itemmaster.category.name,
                        "hsn": grn_item.gin.purchase_order_parent.hsn_id.hsn_code,
                        "po_qty":str(allowed_qty),
                        "po_uom" : grn_item.gin.purchase_order_parent.po_uom.name,
                        "po_return_qty": str(item.po_return_qty or 0),
                        "po_amount" : str((item.po_return_qty or 0)*po_rate),
                        "po_rate" : str(po_rate),
                        "base_uom": grn_item.gin.purchase_order_parent.uom.name,
                        "base_qty" : f"{allowed_qty / grn_item.conversion_factor:.3f}",
                        "base_rate": str(grn_item.gin.purchase_order_parent.rate), 
                        "po_return_qty": str(item.po_return_qty or 0),
                        "returnQty":str(item.base_return_qty),
                        "conversion_factor" : str(grn_item.conversion_factor),
                        "igst": str(purchase_item.igst or 0),
                        "cgst": str(purchase_item.cgst or 0),
                        "sgst": str(purchase_item.sgst or 0),
                        "cess": str(purchase_item.cess or 0),
                        "isBatch": itemmaster.batch_number,
                        "batch": all_batch_list if all_batch_list else None,
                        "isSerial":itemmaster.serial,
                        "serial": serial,
                        "serial_list": serial_list,
                        "isNoBatchSerial" : True if nobatch_noserial_list else False,
                        "noBatchSerial" : nobatch_noserial_list, 
                        "is_stock_reduce" : item.is_stock_reduce,
                        "tax": str(purchase_item.tax or 0),
                        "index":index+1,
                        "id":item.id,
                    }
                    itemdetails.append(data)
                elif item.grn_item.all():
                    grn_item = item.grn_item.first()
                    itemmaster = grn_item.gin.item_master
                    purchase_item = grn_item.gin.purchase_order_parent
                    
                    if itemmaster.batch_number:
                        for grn in item.grn_item.all():
                            if grn.id not in seen:
                                allowed_qty=  (grn.qty or 0) - (grn.purchase_return_qty or 0)
                                base_qty = allowed_qty/(grn.conversion_factor or 0)
                                grn_no = grn.goodsreceiptnote_set.first().grn_no.linked_model_id 
                                all_batch_list.append({
                                    "id": None,
                                    "value": str(grn.id),
                                    "label": grn.batch_number,
                                    "qty": str(base_qty),
                                    "returnQty": "",
                                    "grn_no":str(grn_no)
                                })
                                seen.add(grn.id)
                    elif itemmaster.serial:
                        serial_list =get_serial(item.grn_item.all(),  itemmaster)
                    else:
                        for grn in item.grn_item.all():
                            if grn.id not in no_batch_serial_seen:
                                new_allowed_qty = (grn.qty or 0) - (grn.purchase_return_qty or 0) - (grn.purchase_invoice_qty or 0)
                                grn_no = grn.goodsreceiptnote_set.first().grn_no.linked_model_id
                                base_qty = new_allowed_qty/grn.conversion_factor
                                nobatch_noserial_list.append(
                                    {
                                    "id":  "",
                                    "value": str(grn.id),
                                    "label": grn_no,
                                    "qty": str(base_qty),
                                    "returnQty": "",
                                    "is_stock_reduce" :  "",
                                    })
                    allowed_qty = sum((grn_instance.qty or 0) - (grn_instance.purchase_invoice_qty or 0)  for grn_instance in item.grn_item.all())
                    po_rate = grn_item.gin.purchase_order_parent.po_rate
                    
                    data = {
                        "grnItem": [grn_item.id for grn_item in item.grn_item.all()],
                        "partCode": itemmaster.item_part_code,
                        "partName": itemmaster.item_name,
                        "itemMasterId":str(itemmaster.id),
                        "description": itemmaster.description,
                        "category": itemmaster.category.name,
                        "po_uom" : grn_item.gin.purchase_order_parent.po_uom.name,
                        "po_return_qty": str(item.po_return_qty or 0),
                        "po_rate": str(po_rate),
                        "po_amount" : str(item.po_amount),
                        "base_uom": grn_item.gin.purchase_order_parent.uom.name,
                        "base_qty" : f"{allowed_qty/grn_item.conversion_factor:.3f}",
                        "base_rate": str(grn_item.gin.purchase_order_parent.rate), 
                        "po_qty":str(item.po_return_qty),
                        "conversion_factor" : str(grn_item.conversion_factor),
                        "hsn": grn_item.gin.purchase_order_parent.hsn_id.hsn_code,
                        "igst": str(purchase_item.igst or 0),
                        "cgst": str(purchase_item.cgst or 0),
                        "sgst": str(purchase_item.sgst or 0),
                        "cess": str(purchase_item.cess or 0),
                        "isBatch": itemmaster.batch_number,
                        "batch": all_batch_list if all_batch_list else None,
                        "isSerial":itemmaster.serial,
                        "serial": serial,
                        "serial_list" : serial_list,
                        "isNoBatchSerial" : True if nobatch_noserial_list else False,
                        "noBatchSerial" : nobatch_noserial_list, 
                        "tax": str(purchase_item.tax or 0),
                        "is_stock_reduce" : item.is_stock_reduce,
                        "index":index+1,
                        "returnQty":str(item.base_return_qty),
                        "id":item.id,
                    }   
                    itemdetails.append(data)
        except Exception as e:
                return GraphQLError(f"An exception occurred {str(e)}")
        
        purchase_return['item_details'] = itemdetails
        
        return getGinDataForQir(items=purchase_return)

    def resolve_initial_debit_note_fetch(self, info, purchase_return_id=None):
        try:
            grn_instance = None 
            purchase = None

            if not purchase_return_id:
                return GraphQLError("Purchase Return id is required.")
            
            purchase_return_object = PurchaseReturnChallan.objects.filter(id=purchase_return_id).first()
            
            if not purchase_return_object:
                return GraphQLError("Purchase Return is not found.")
            
            if purchase_return_object.status.name == "Draft" or purchase_return_object.status.name == "Canceled" :
                return GraphQLError("Purchase Return is not submitted or dispatched.")


            purchase_invoice = purchase_return_object.purchaseinvoice_set.all() if purchase_return_object.purchaseinvoice_set else None
 
            if purchase_invoice is None:
                return GraphQLError("Purchase invoice is not Found.")
            
            
            if purchase_invoice:
                first_invoice = purchase_invoice.first()
                grn_instance = first_invoice.goodsreceiptnote_set.first()
                if not grn_instance:
                    return GraphQLError("GRN is not Found.")
                purchase = grn_instance.goods_inward_note.purchase_order_id

 
            tds = None
            tcs = None 
            supplier = purchase.supplier_id
            if supplier.tds and "P" in supplier.pan_no:
                tds =  "P"
            elif supplier.tds and "P" not in supplier.pan_no:
                    tds =  "O"
            if supplier.tcs in ['PURCHASE', "BOTH"]:
                if supplier.pan_no and "P" in supplier.pan_no:
                    tcs =  "WP"
                elif supplier.pan_no and "P" not in supplier.pan_no:
                    tcs =  "WO"
                elif supplier.pan_no and "P" not in supplier.pan_no:
                    tcs =  "WOO"

            debit_data = {
                "id":"",
                "status" : "",
                "debitNoteNo": "",
                "debitNoteDate":  "",
                "department": {
                    "value": purchase.department.id,
                    "label":  purchase.department.name
                },
                "supplierRef":purchase.supplier_ref,
                "remarks": "",
                "purchaseOrderNo": {
                        "id" : purchase.id,
                        "purchase_order" :purchase.purchaseOrder_no.linked_model_id
                }, 
                "invoiceNo":first_invoice.purchase_invoice_no.linked_model_id if first_invoice and first_invoice.purchase_invoice_no else "",
                "supplierName": {
                    "value": str(purchase.supplier_id.id),
                    "label": purchase.supplier_id.company_name,
                },
                "gstType": purchase.gstin_type,
                "gstin": purchase.gstin,
                "currency": {
                    "value": str(purchase.currency.id),
                    "label": purchase.currency.Currency.name,
                    "rate": str(purchase.exchange_rate) if purchase.exchange_rate else None,
                    "symbol": purchase.currency.Currency.currency_symbol,
                },
                "placeOfSupply": {
                    "value": purchase.place_of_supply, 
                    "label":purchase.place_of_supply, 
                },
                "gstNatureOfTransaction": {
                    "natureOfTransaction": {
                        "value": str(purchase.gst_nature_transaction.id),
                        "label": purchase.gst_nature_transaction.nature_of_transaction,
                    }, 
                }, 
                "address": {
                    "value": str(purchase.address.id or ""),
                    "label": str(purchase.address.address_type or ""),
                    "state": str(purchase.address.state or ""),
                    "fullAddredd": {
                        "id": str(purchase.address.id or ""),
                        "addressType":  str(purchase.address.address_type or ""),
                        "addressLine1":str(purchase.address.address_line_1 or ""),
                        "addressLine2": str(purchase.address.address_line_2 or ""),
                        "city": str(purchase.address.city or ""),
                        "state":  str(purchase.address.state or ""),
                        "country":str(purchase.address.country or ""),
                        "pincode": str(purchase.address.pincode or ""),
                    }
                },   
                "tdsEnable": True if purchase.supplier_id.tcs and purchase.supplier_id.tcs == "BOTH" or purchase.supplier_id.tcs == "PURCHASE"  else False,
                "tcsEnable":purchase.supplier_id.tds if purchase.supplier_id.tds else False,
                "purchaseReturnChallan": {
                        "id" : purchase_return_object.id,
                        "purchase_return_no": purchase_return_object.purchase_return_no.linked_model_id
                },
                "ewayBill":purchase_return_object.eway_bill_no if purchase_return_object.eway_bill_no  else None,
                "ewayDate":str(purchase_return_object.eway_bill_date) if purchase_return_object.eway_bill_date else None,
                "noteNo": "",
                "noteDate":"",
                "state": purchase.address.state,
                "contactPerson": {
                    "value": str(purchase.contact.id or ""),
                    "label": str(purchase.contact.contact_person_name or ""),
                    "mobile": str(purchase.contact.phone_number or ""),
                    "whatsappNo":str(purchase.contact.whatsapp_no or ""),
                    "Email": str(purchase.contact.email or ""),
                },
                "supplierNumber": {
                    "value":str(purchase.supplier_id.id),
                    "label":purchase.supplier_id.supplier_no
                },   
            }
            
            itemdetails = []
            try:
                for index, item in enumerate(purchase_return_object.purchase_return_challan_item_Details.all()):
                    purchase_invoice_item = item.purchase_invoice_item
                    grn_item = purchase_invoice_item.grn_item.first()
                    gin_item = grn_item.gin
                    purchase_order_item = gin_item.purchase_order_parent
                    itemmaster = gin_item.item_master 

                
                    data = {
                        "index": str(index +1),
                        "id": "",
                        "qty": str(item.po_return_qty),
                        "uom": {
                            "value": str(purchase_order_item.po_uom.id),
                            "label": str(purchase_order_item.po_uom.name),
                        },
                        "category": itemmaster.category.name,
                        "hsnCode": {
                            "value":  purchase_order_item.hsn_id.id,
                            "label":  purchase_order_item.hsn_id.hsn_code
                        },
                        "rate":  str(purchase_invoice_item.po_rate),
                        "description": itemmaster.description,
                        "amount": str(item.po_return_qty * purchase_invoice_item.po_rate),
                        "tax":  str(purchase_order_item.tax or 0),
                        "partCode": {
                            "value": str(itemmaster.id),
                            "label": str(itemmaster.item_part_code),
                        },
                        "partName": {
                            "value": str(itemmaster.id),
                            "label": str(itemmaster.item_name),
                        },
                        "accountName": "",
                        "itemType": "Item Master",  
                        "isItemMaster": True,
                        "igst": str(purchase_order_item.igst or 0),
                        "cgst": str(purchase_order_item.cgst or 0),
                        "sgst": str(purchase_order_item.sgst or 0),
                        "cess": str(purchase_order_item.cess or 0),
                        "tdsLink": {
                            "percentOtherWithPan": str(getattr(itemmaster.tds_link, "percent_other_with_pan", "") or ""),
                            "percentIndividualWithPan": str(getattr(itemmaster.tds_link, "percent_individual_with_pan", "") or ""),
                        } if itemmaster.tds_link else None,
                        "tcsLink":{
                            "percentIndividualWithPan": str(getattr(itemmaster.tcs_link, "percent_individual_with_pan", "") or ""),
                            "percentOtherWithPan": str(getattr(itemmaster.tcs_link, "percent_other_with_pan", "") or ""),
                            "percentOtherWithoutPan": str(getattr(itemmaster.tcs_link, "percent_other_without_pan", "") or ""),
                        } if itemmaster.tcs_link else None, 
                        "baseAmount":str(item.base_return_qty*purchase_order_item.rate),
                        "baseQty":str(item.base_return_qty),
                        "baseRate":str(purchase_order_item.rate),
                        "baseUom":{
                            "value": str(purchase_order_item.uom.id),
                            "label": str(purchase_order_item.uom.name),
                        },
                        "conversionFactor":str(grn_item.conversion_factor),
                        "purchase_return_item" : str(item.id),
                    } 
                    # TDS
                    if  tds == "P" and itemmaster.tds_link:
                        data['tdsPercentage'] = str(itemmaster.tds_link.percent_individual_with_pan)
                        data['tdsValue'] = str((item.po_amount*itemmaster.tds_link.percent_individual_with_pan)/100)
                    elif tds == "O" and itemmaster.tds_link:
                        data['tdsPercentage'] = str(itemmaster.tds_link.percent_other_with_pan)
                        data['tdsValue'] = str((item.po_amount*itemmaster.tds_link.percent_other_with_pan)/100)
                    
                    # TCS
                    if tcs == "WP" and itemmaster.tcs_link:
                        data['tcsPercentage'] = str(itemmaster.tcs_link.percent_individual_with_pan)
                        data['tcsValue'] = str((item.po_amount*itemmaster.tcs_link.percent_individual_with_pan)/100)
                    elif tcs == "WO" and itemmaster.tcs_link:
                        data['tcsPercentage'] = str(itemmaster.tcs_link.percent_other_with_pan)
                        data['tcsValue'] = str((item.po_amount*itemmaster.tcs_link.percent_other_with_pan)/100)
                    elif tcs == "WOO" and itemmaster.tcs_link:
                        data['tcsPercentage'] = str(itemmaster.tcs_link.percent_other_without_pan)
                        data['tcsValue'] = str((item.po_amount*itemmaster.tcs_link.percent_other_without_pan)/100)

                    itemdetails.append(data)
            except Exception as e:
                return GraphQLError(f"An exception occurred {str(e)}")
            debit_data['item_details'] = itemdetails
            return getGinDataForQir(items=debit_data)
        except Exception as e:
            return GraphQLError(f"Unexpeted error occurred on debit note initial fetch {str(e)}")

    def resolve_edit_debit_note_fetch(self, info, debit_note_id=None):
        try:
    
            if not debit_note_id:
                return GraphQLError("Debit Note ID is required.")
        
            debit_note_instance = DebitNote.objects.filter(id=debit_note_id).first()

            if not debit_note_instance:
                return GraphQLError("Debit Note not Found.")
            
 
            po_invoice_nombers = None
            if debit_note_instance.return_invoice:
                po_invoice_nombers = ", ".join(po.purchase_invoice_no.linked_model_id for po in  debit_note_instance.return_invoice.purchaseinvoice_set.all())
            debit_data = {
                "id":str(debit_note_instance.id),
                "status" : debit_note_instance.status.name,
                "debitNoteNo": debit_note_instance.debit_note_no.linked_model_id,
                "debitNoteDate":  str(debit_note_instance.debit_note_date),
                "department": {
                    "value": debit_note_instance.department.id,
                    "label":  debit_note_instance.department.name,
                },
                "supplierRef":debit_note_instance.supplier_ref,
                "remarks": debit_note_instance.remarks,
                "purchaseOrderNo": {
                        "id" : str(debit_note_instance.purchase_order_no.id) if debit_note_instance.purchase_order_no and debit_note_instance.purchase_order_no.id else None,
                        "purchase_order" : debit_note_instance.purchase_order_no.purchaseOrder_no.linked_model_id if debit_note_instance.purchase_order_no and debit_note_instance.purchase_order_no.purchaseOrder_no.linked_model_id else None
                }, 
                "invoiceNo": po_invoice_nombers, 
                "supplierName": {
                    "value": str(debit_note_instance.supplier.id),
                    "label": debit_note_instance.supplier.company_name, 
                },
                "supplierPanNo":debit_note_instance.supplier.pan_no,
                "gstType": debit_note_instance.gstin_type,
                "gstin": debit_note_instance.gstin,
                "currency": {
                    "value":str(debit_note_instance.currency.id),
                    "label": debit_note_instance.currency.Currency.name,
                    "rate": str(debit_note_instance.exchange_rate) if debit_note_instance.exchange_rate else None,
                    "symbol": str(debit_note_instance.currency.Currency.currency_symbol),
                },
                "placeOfSupply": {
                    "value": debit_note_instance.address.state,
                    "label":debit_note_instance.address.state,
                },
                "gstNatureOfTransaction": {
                    "natureOfTransaction": {
                        "value": str(debit_note_instance.gst_nature_transaction.id),
                        "label": debit_note_instance.gst_nature_transaction.nature_of_transaction,
                    }, 
                }, 
                "address": {
                    "value": str(debit_note_instance.address.id or ""),
                    "label": str(debit_note_instance.address.address_type or ""),
                    "state":  debit_note_instance.address.state,
                    "fullAddredd": {
                        "id": str(debit_note_instance.address.id),
                        "addressType": str(debit_note_instance.address.address_type or ""),
                        "addressLine1":debit_note_instance.address.address_line_1,
                        "addressLine2": debit_note_instance.address.address_line_2,
                        "city": debit_note_instance.address.city,
                        "state":  debit_note_instance.address.state,
                        "country": debit_note_instance.address.country,
                        "pincode": debit_note_instance.address.pincode,
                    }
                }, 
                "edit": True, 
                "tdsEnable": debit_note_instance.tds_bool if debit_note_instance.tds_bool else None,
                "tcsEnable": debit_note_instance.tcs_bool if debit_note_instance.tcs_bool else None,
                "purchaseReturnChallan": {
                        "id" : str(debit_note_instance.return_invoice.id) if debit_note_instance.return_invoice and debit_note_instance.return_invoice.id else None,
                        "purchase_return_no": debit_note_instance.return_invoice.purchase_return_no.linked_model_id if debit_note_instance.return_invoice and debit_note_instance.return_invoice.purchase_return_no.linked_model_id else None
                },
                "noteNo": debit_note_instance.note_no if debit_note_instance.note_no else None,
                "noteDate": str(debit_note_instance.note_date) if debit_note_instance.note_date else None, 
                "state": debit_note_instance.address.state,
                "contactPerson": {
                    "value":str(debit_note_instance.contact.id or ""),
                    "label": str(debit_note_instance.contact.contact_person_name or ""),
                    "mobile": debit_note_instance.contact.phone_number,
                    "whatsappNo":str(debit_note_instance.contact.whatsapp_no or ""),
                    "Email": debit_note_instance.contact.email,
                },
                "supplierNumber": {
                    "value": str(debit_note_instance.supplier.id),
                    "label":debit_note_instance.supplier.supplier_no, 
                },   
                "totaltax": str(debit_note_instance.tax_total) if debit_note_instance.tax_total else None,
                "roundOff":str(debit_note_instance.round_off) if debit_note_instance.round_off else None,
                "roundOffType":debit_note_instance.round_off_method,
                "item_details_value": str(debit_note_instance.item_total_befor_tax),
                "other_income_value": str(debit_note_instance.other_charges_befor_tax),
                "netAmount": str(debit_note_instance.net_amount), 
                "sgst": str(debit_note_instance.sgst),
                "cgst": str(debit_note_instance.cgst),
                "igst": str(debit_note_instance.igst),
                "cess": str(debit_note_instance.cess), 
                "TDS" : str(debit_note_instance.tds_total) if debit_note_instance.tds_total else None,
                "TCS" : str(debit_note_instance.tcs_total) if debit_note_instance.tcs_total else None,
                "directDebitNote":False if debit_note_instance.return_invoice and  debit_note_instance.return_invoice.id else True,
                "createdBy":debit_note_instance.created_by.username,
                "createdAt":str(debit_note_instance.updated_at) if debit_note_instance.updated_at else str(debit_note_instance.created_at)
            }
            itemdetails = []
            other_income_charges =[]
            account = [] 
            
            for index, item in enumerate(debit_note_instance.debitnoteitemdetail_set.all()):
               
                itemmaster = item.item_master 
                data = {
                    "index": str(item.index),
                    "id": str(item.id),
                    "qty": str(item.po_qty),
                    "uom": {
                        "value": str(item.po_uom.id),
                        "label": str(item.po_uom.name),
                    },
                    "category": itemmaster.category.name,
                    "hsnCode": {
                        "value":  item.hsn.id,
                        "label": item.hsn.hsn_code
                    },
                    "rate": str(item.po_rate),
                    "description": itemmaster.description,
                    "amount": str(item.po_amount),
                    "baseAmount":str(item.amount),
                    "baseQty":str(item.qty),
                    "baseRate":str(item.rate),
                    "baseUom":{
                        "value": str(item.uom.id),
                        "label": str(item.uom.name),
                    },
                    "tax": str(item.tax or 0) if item.tax else ""
                    ,
                    "partCode": {
                        "value": str(itemmaster.id),
                        "label": str(itemmaster.item_part_code),
                    },
                    "partName": {
                        "value": str(itemmaster.id),
                        "label": str(itemmaster.item_name),
                    },
                    "accountName": "",
                    "itemType": "Item Master",  
                    "isItemMaster": True,
                    "igst": str(item.igst or 0) if item.igst else None,
                    "cgst": str(item.cgst or 0) if item.cgst else None,
                    "sgst": str(item.sgst or 0) if item.sgst else None,
                    "cess": str(item.cess or 0) if item.cess else None, 
                    "tdsPercentage": str(item.tds_percentage or 0) if item.tds_percentage else None,
                    "tcsPercentage": str(item.tcs_percentage or 0) if item.tcs_percentage else None, 
                    "purchase_return_item" : str(item.purchase_return_item.id) if item.purchase_return_item and  item.purchase_return_item.id else None,
                }

                itemdetails.append(data)
            
            

            for item in debit_note_instance.debitnoteaccount_set.all():  
                data = {
                    "index": str(item.index),
                    "id": str(item.id),
                    "qty": None,
                    "uom": None,
                    "category": None,
                    "hsnCode": {
                        "value":  str(item.hsn.id),
                        "label": item.hsn.hsn_code
                    } if item.hsn else item.hsn,
                    "rate": None,
                    "description": item.description,
                    "amount": str(item.amount),
                    "tax": str(item.tax) if item.tax else None,
                    "partCode": None,
                    "partName": None,
                    "accountName": {
                        "value":str(item.account_master.id),
                        "label":item.account_master.accounts_name
                    },
                    "itemType": "Account Master",  
                    "isItemMaster": False,
                    "sgst" : str(item.sgst) if item.sgst else None,
                    "cgst" : str(item.cgst) if item.cgst else None,
                    "igst" : str(item.igst) if item.igst else None,
                    "cess" : str(item.cess) if item.cess else None,
                    "tdsPercentage": str(item.tds_percentage or 0) if item.tds_percentage else None,
                    "tcsPercentage": str(item.tcs_percentage or 0) if item.tcs_percentage else None, 
                }
                account.append(data)

            for index, charge in enumerate(debit_note_instance.debitnoteotherincomecharge_set.all()): 
                other_income_data = {
                        "index": index+1,
                        "id" : str(charge.id),
                        "otherIncomeChargesId": {
                            "value": str(charge.other_income_charges.id),
                            "label":  str(charge.other_income_charges.name),
                            "tax":str(charge.tax or 0),
                            "hsn": str(charge.other_income_charges.hsn.id),
                            "hsnCode": str(charge.other_income_charges.hsn.hsn_code), 
                        },
                        "amount" : str(charge.amount),
                        "tax":str(charge.tax or 0),
                        "hsnCode": str(charge.other_income_charges.hsn.hsn_code), 
                        "igst": str(charge.igst or 0),
                        "cgst": str(charge.cgst or 0),
                        "sgst": str(charge.sgst or 0),
                        "cess": str(charge.cess or 0), 
                    }
                other_income_charges.append(other_income_data)
            combined_list = itemdetails + account
            combined_list = sorted(combined_list, key=lambda x: int(x["index"])) 
            debit_data['other_income_charges'] = other_income_charges
            debit_data['item_details'] = combined_list
 
            return getGinDataForQir(items=debit_data)
        except Exception as e:
            return GraphQLError(f'An exception occurred {str(e)}')

    def resolve_direct_purchase_invoice(self, info, id=None):

        direct_invoice_instance = None
        filter ={}
        if id :
            filter['id'] = id
        direct_invoice_instance = DirectPurchaseinvoice.objects.filter(**filter)
        return direct_invoice_instance

    def resolve_CommonStatus_type(self, info, table=None):
        query = None
        if table:
            query = CommanStatus.objects.filter(table=table)
        return query

    @permission_required(models=["UserGroup","User_Management"])
    def resolve_all_UserGroup_type(self, info, id=None, group_name=None):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if group_name:
            filter_kwargs['group_name__icontains'] = group_name
        query = UserGroup.objects.all()
        queryset = query.filter(**filter_kwargs)
        return queryset

    @permission_required(models=["Department", "User_Management", "Credit Note"])
    def resolve_allDepartment_type(self, info, id=None,name=None):
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['name__icontains'] = name
        query = Department.objects.all()
        queryset = query.filter(**filter_kwargs)        

        
        return queryset
    
    @permission_required(models=["Company Master"])
    def resolve_all_company_master(self, info,id=None):
        filter_kwargs = {}
        query = CompanyMaster.objects.all()
        if id:
            filter_kwargs['id'] = id

        return query.filter(**filter_kwargs)

    @permission_required(models=["Accounts General Ledger"])
    def resolve_accounts_general_ledger_filter_options(self, info, account_name=None,
                                                   payment_voucher_no=None,
                                                   customer_supplier=None,
                                                   employee=None,voucher_type=None,
                                                   voucher_no=None, purchase_account=None,  ):
        try:
            filters = Q()

            if account_name:
                filters &= Q(account__accounts_name__icontains=account_name)
            if payment_voucher_no:
                filters &= Q(payment_voucher_no__payment_voucher_no__linked_model_id__icontains=payment_voucher_no)
            if customer_supplier:
                filters &= Q(customer_supplier__company_name__icontains=customer_supplier)
            if employee:
                filters &= Q(employee__employee_name__icontains=employee)
            if voucher_type:
                filters &= Q(voucher_type__icontains=voucher_type)
            if purchase_account:
                filters &= Q(purchase_account__accounts_name__icontains=purchase_account)

            if voucher_no:
                filters &= (
                    Q(payment_voucher_no__payment_voucher_no__linked_model_id__icontains=voucher_no) |
                    Q(sales_dc_voucher_no__dc_no__linked_model_id__icontains=voucher_no) |
                    Q(sales_invoice_voucher_no__sales_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(direct_sales_voucher_no__direct_sales_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(goods_receipt_note_no__grn_no__linked_model_id__icontains=voucher_no) |
                    Q(debit_note__debit_note_no__linked_model_id__icontains=voucher_no) |
                    Q(purchase_return_challan__purchase_return_no__linked_model_id__icontains=voucher_no) |
                    Q(direct_purchase_invoice__direct_purchase_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(purchase_invoice__purchase_invoice_no__linked_model_id__icontains=voucher_no) 

                ) 

            queryset = AccountsGeneralLedger.objects.select_related(
                "payment_voucher_no", "account", "customer_supplier", "employee"
            ).filter(filters)

            # Use sets to ensure uniqueness
            account_names = set()
            payment_voucher_nos = set()
            customer_suppliers = set()
            employees = set()
            voucher_types = set()
            voucher_no = set()
            purchase_accounts= set()

            for item in queryset:
                if item.account:
                    account_names.add(item.account.accounts_name)
                if item.payment_voucher_no and item.payment_voucher_no.payment_voucher_no:
                    payment_voucher_nos.add(item.payment_voucher_no.payment_voucher_no.linked_model_id)
                if item.customer_supplier:
                    customer_suppliers.add(item.customer_supplier.company_name)
                if item.employee:
                    employees.add(item.employee.employee_name)
                if item.voucher_type:
                    voucher_types.add(item.voucher_type)
                if item.payment_voucher_no and item.payment_voucher_no.payment_voucher_no:
                    voucher_no.add(item.payment_voucher_no.payment_voucher_no.linked_model_id)

                if item.sales_dc_voucher_no and item.sales_dc_voucher_no.dc_no:
                    voucher_no.add(item.sales_dc_voucher_no.dc_no.linked_model_id)

                if item.sales_invoice_voucher_no and item.sales_invoice_voucher_no.sales_invoice_no:
                    voucher_no.add(item.sales_invoice_voucher_no.sales_invoice_no.linked_model_id)
                if item.direct_sales_voucher_no and item.direct_sales_voucher_no.direct_sales_invoice_no:
                    voucher_no.add(item.direct_sales_voucher_no.direct_sales_invoice_no.linked_model_id)

                if item.debit_note and item.debit_note.debit_note_no:
                    voucher_no.add(item.debit_note.debit_note_no.linked_model_id)

                if item.purchase_return_challan and item.purchase_return_challan.purchase_return_no:
                    voucher_no.add(item.purchase_return_challan.purchase_return_no.linked_model_id)

                if item.direct_purchase_invoice and item.direct_purchase_invoice.direct_purchase_invoice_no:
                    voucher_no.add(item.direct_purchase_invoice.direct_purchase_invoice_no.linked_model_id)
                
                if item.purchase_invoice and item.purchase_invoice.purchase_invoice_no:
                    voucher_no.add(item.purchase_invoice.purchase_invoice_no.linked_model_id)

                if item.purchase_account:
                    purchase_accounts.add(item.purchase_account)

                    # purchase_invoice__purchase_invoice_no__linked_model_id__icontains
                
                


        except Exception as e:
            return GraphQLError(f"Error occurred while resolving filter options: {str(e)}")

        return AccountsGeneralLedgerFilterOptionListType(
            account_names=sorted(account_names) if account_names else [],
            payment_voucher_nos=sorted(payment_voucher_nos) if payment_voucher_nos else [],
            customer_suppliers=sorted(customer_suppliers) if customer_suppliers else [],
            employees=sorted(employees) if employees else [],
            voucher_types=sorted(voucher_types) if voucher_types else [],
            voucher_no=sorted(voucher_no) if voucher_no else [],
            purchase_account = sorted(purchase_accounts) if purchase_accounts else []
        )

    @permission_required(models=["Accounts General Ledger"])
    def resolve_accounts_general_ledger(self, info, page=1, page_size=10, order_by=None, descending=False,date=None,
                                        amount_filter=None, employee=None,voucher_type=None,
                                        account_name=None, remark=None,customer_supplier=None, voucher_no=None, purchase_account=None,
                                        purchase_amount=None):
        try:
            filter_kwargs = {}
            query = AccountsGeneralLedger.objects.all()
            if date:
                try:
                    date_dict = json.loads(date)
                    updated_start_date = date_dict.get("startDate")
                    updated_end_date = date_dict.get("endDate")
                    if updated_start_date == updated_end_date:
                        filter_kwargs['date'] = updated_start_date
                    else:
                        filter_kwargs['date__range'] = (updated_start_date, updated_end_date)
                except json.JSONDecodeError:
                    raise Exception("Invalid JSON format for date")
            if employee:
                filter_kwargs['employee__employee_name__icontains']  = employee
            amount_filter = json.loads(amount_filter) if amount_filter else None
            if amount_filter:
                field = amount_filter.get("field")  # "debit" or "credit"
                operator = amount_filter.get("operator")
                value = amount_filter.get("value")
                range_vals = amount_filter.get("range")

                if field and operator:
                    if operator == "equal":
                        filter_kwargs[f"{field}"] = value
                    elif operator == "approx":
                        filter_kwargs[f"{field}__icontains"] = value
                    elif operator == "lt":
                        filter_kwargs[f"{field}__lt"] = value
                    elif operator == "lte":
                        filter_kwargs[f"{field}__lte"] = value
                    elif operator == "gt":
                        filter_kwargs[f"{field}__gt"] = value
                    elif operator == "gte":
                        filter_kwargs[f"{field}__gte"] = value
                    elif operator == "between" and isinstance(range_vals, list) and len(range_vals) == 2:
                        filter_kwargs[f"{field}__range"] = tuple(range_vals)

           
            if voucher_type:
                filter_kwargs['voucher_type'] = voucher_type

            if account_name:
                filter_kwargs['account__accounts_name__icontains'] = account_name
            if remark:
                filter_kwargs['remark__icontains'] = remark
            if customer_supplier:
                filter_kwargs['customer_supplier__company_name__icontains'] = customer_supplier
            if purchase_account:
                filter_kwargs['purchase_account__accounts_name__icontains'] = purchase_account
            if filter_kwargs:
                query = query.filter(**filter_kwargs)
            if voucher_no:
                query = query.filter(
                    Q(payment_voucher_no__payment_voucher_no__linked_model_id__icontains=voucher_no) |
                    Q(sales_dc_voucher_no__dc_no__linked_model_id__icontains=voucher_no) |
                    Q(sales_invoice_voucher_no__sales_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(direct_sales_voucher_no__direct_sales_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(goods_receipt_note_no__grn_no__linked_model_id__icontains=voucher_no) |
                    Q(debit_note__debit_note_no__linked_model_id__icontains=voucher_no) |
                    Q(purchase_return_challan__purchase_return_no__linked_model_id__icontains=voucher_no) |
                    Q(direct_purchase_invoice__direct_purchase_invoice_no__linked_model_id__icontains=voucher_no) |
                    Q(purchase_invoice__purchase_invoice_no__linked_model_id__icontains=voucher_no) 
                )
            if order_by:
                try:
                    query = query.order_by(('-' if descending else '') + order_by)
                
                except Exception as e:
                    return GraphQLError(f"Error occurred while ordering query:{str(e)}")
                
            paginator = Paginator(query, page_size)
            paginated_data = paginator.get_page(page)
            page_info = PageInfoType(
                total_items=paginator.count,
                has_next_page=paginated_data.has_next(),
                has_previous_page=paginated_data.has_previous(),
                total_pages=paginator.num_pages,
            )
            totals = query.aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
            # totals = paginated_data.object_list.aggregate(
            #         total_debit=Sum('debit'),
            #         total_credit=Sum('credit')
            #     )
            return AccountsGeneralLedgerTypeConnection(
                items=paginated_data.object_list,
                page_info=page_info,
                total_debit=totals.get("total_debit") or None,
                total_credit=totals.get("total_credit") or None,
            )
        except Exception as e: 
            return AccountsGeneralLedgerTypeConnection(items=[], page_info=PageInfoType(total_items=0, has_next_page=False, has_previous_page=False, total_pages=0))
    
    def resolve_child_general_ledger_account_list(self, info, account_name):
        if not account_name:
            raise GraphQLError("account_name is required.")

        gl_accounts = AccountsGeneralLedger.objects.filter(
            account__accounts_name__icontains=account_name
        ).values("id", "account__accounts_name").order_by("account__accounts_name", "id")\
        .distinct("account__accounts_name")
            

        return [
            ChildGeneralLedgerAccountList(
                id=str(acc["id"]),
                account_names=acc["account__accounts_name"]
            )
            for acc in gl_accounts
        ]
    
    def resolve_child_account_general_ledger(self, info, page=1, page_size=10, id=None):
        if not id:
            raise GraphQLError("Account id is required.")
        print(id)
       
        qs = AccountsGeneralLedger.objects.filter(
            account__id=id).values(
            "date",
            "voucher_type",
            "account__accounts_name",
            "account__accounts_group_name__accounts_type__name",
            "debit",
            "credit",
            "payment_voucher_no__id",
            "payment_voucher_no__payment_voucher_no__linked_model_id",
            "sales_dc_voucher_no__id",
            "sales_dc_voucher_no__dc_no__linked_model_id",
            "sales_invoice_voucher_no__id",
            "sales_invoice_voucher_no__sales_invoice_no__linked_model_id",
            "direct_sales_voucher_no__id",
            "direct_sales_voucher_no__direct_sales_invoice_no__linked_model_id",
            "sales_return_voucher_no__id",
            "sales_return_voucher_no__sr_no__linked_model_id",
            "credit_note_voucher_no__id",
            "credit_note_voucher_no__cn_no__linked_model_id",
            "goods_receipt_note_no__id",
            "goods_receipt_note_no__grn_no__linked_model_id",
            "purchase_invoice__id",
            "purchase_invoice__purchase_invoice_no__linked_model_id",
            "direct_purchase_invoice__id",
            "direct_purchase_invoice__direct_purchase_invoice_no__linked_model_id",
            "purchase_return_challan__id",
            "purchase_return_challan__purchase_return_no__linked_model_id",
            "debit_note__id",
            "debit_note__debit_note_no__linked_model_id",
        ).order_by("-date")
 
        total_records = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        paginated = qs[start:end]

        items = []
        total_debit = 0
        total_credit = 0

        for row in paginated:
            
            voucher_id = (
                row["payment_voucher_no__id"]
                or row["sales_dc_voucher_no__id"]
                or row["sales_invoice_voucher_no__id"]
                or row["direct_sales_voucher_no__id"]
                or row["sales_return_voucher_no__id"]
                or row["credit_note_voucher_no__id"]
                or row["goods_receipt_note_no__id"]
                or row["purchase_invoice__id"]
                or row["direct_purchase_invoice__id"]
                or row["purchase_return_challan__id"]
                or row["debit_note__id"]
            )

            voucher_no = (
                row["payment_voucher_no__payment_voucher_no__linked_model_id"]
                or row["sales_dc_voucher_no__dc_no__linked_model_id"]
                or row["sales_invoice_voucher_no__sales_invoice_no__linked_model_id"]
                or row["direct_sales_voucher_no__direct_sales_invoice_no__linked_model_id"]
                or row["sales_return_voucher_no__sr_no__linked_model_id"]
                or row["credit_note_voucher_no__cn_no__linked_model_id"]
                or row["goods_receipt_note_no__grn_no__linked_model_id"]
                or row["purchase_invoice__purchase_invoice_no__linked_model_id"]
                or row["direct_purchase_invoice__direct_purchase_invoice_no__linked_model_id"]
                or row["purchase_return_challan__purchase_return_no__linked_model_id"]
                or row["debit_note__debit_note_no__linked_model_id"]
            )
            debit= 0
            credit= 0
            if row['account__accounts_group_name__accounts_type__name'] == "Expenses":
                debit = (row["debit"] or row["credit"])
            elif row['account__accounts_group_name__accounts_type__name'] == "Income":
                credit = (row["debit"] or row["credit"])
            elif row['account__accounts_group_name__accounts_type__name'] == "Asset":
                debit = (row["debit"] or row["credit"])
            elif row['account__accounts_group_name__accounts_type__name'] == "Liabilities":
                credit = (row["debit"] or row["credit"])


            total_debit += debit
            total_credit += credit

            items.append(
                ChildAccountGeneralLedgertype(
                    date=row["date"],
                    account=row["account__accounts_name"],
                    voucher_type=row["voucher_type"],
                    voucher_id=voucher_id,
                    voucher_no=voucher_no,
                    debit=str(debit),
                    credit=str(credit),
                )
            )

        # page_info = PageInfoType(
        #     total=total_records,
        #     page=page,
        #     page_size=page_size,
        #     has_next=end < total_records,
        #     has_previous=start > 0,
        # )

        return ChildAccountGeneralLedgertypeConnection(
            items=items,
            total_debit=str(total_debit),
            total_credit=str(total_credit),
            # page_info=page_info
        )



        