from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import *
from django.contrib.auth.models import User
from rest_framework.authtoken.views import Token
from rest_framework.response import Response


class CompanyMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMaster
        # fields = "__all__"
        exclude = ['created_by', 'modified_by',"address" ]
        read_only_fields = ['created_by', 'modified_by',]

    def create(self, validated_data):
        user = self.context['request'].user
        address = self.context['address']
        validated_data['address_id'] = address
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        address = self.context['address']
        validated_data['address'] = address
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class LocalizedDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return super().to_representation(value)

class ReportTempletedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"
class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = "__all__"
class ItemMasterHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMasterHistory
        fields = "__all__"


class EditListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditListView
        fields = "__all__"


class HsnSerializer(serializers.ModelSerializer):
    gst_rate = serializers.ChoiceField(choices=gst_rate, required=False, allow_null=True)

    class Meta:
        model = Hsn
        fields = "__all__"


class HsnEffectiveDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsnEffectiveDate
        fields = "__all__"


class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item_Groups_Name
        fields = "__all__"


class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class AccountsGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountsGroup
        fields = "__all__"


class AccountsMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountsMaster
        fields = "__all__"

class GSTNatureTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTNatureTransaction
        # fields = "__all__"
        exclude = ['created_by', 'modified_by']
        read_only_fields = ['created_by', 'modified_by']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class AccountsGeneralLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountsGeneralLedger
        fields = "__all__"

class Alternate_unitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternate_unit
        fields = "__all__"


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = "__all__"


class BatchNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchNumber
        fields = "__all__"


class StockSerialHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockSerialHistory
        fields = "__all__"


class StockHistoryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistoryLog
        fields = "__all__"

class TDSMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TDSMaster
        fields = "__all__"

class TCSMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCSMaster
        fields = "__all__"

class ItemMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMaster
        fields = "__all__"




class SerialNumbersSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerialNumbers
        fields = "__all__"


class ItemStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemStock
        fields = "__all__"


class StockHistorySerializer(serializers.ModelSerializer):
    modified_date = LocalizedDateTimeField()

    class Meta:
        model = StockHistory
        fields = "__all__"


class ItemInventoryApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInventoryApproval
        fields = "__all__"


class InventoryHandlerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryHandler
        fields = "__all__"


class displayGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = display_group
        fields = "__all__"


class ItemComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item_Combo
        fields = "__all__"


class CustomerGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroups
        fields = "__all__"


class SupplierGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierGroups
        fields = "__all__"

class SupplierFormGstEffectiveDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierFormGstEffectiveDate
        fields = "__all__"

class ItemContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactDetalis
        fields = "__all__"


class ItemAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        fields = "__all__"

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = "__all__"


class ItemSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierFormData
        fields = "__all__"

    # def validate_gstin(self, value):
    #     if value == "URP":
    #         # If value is UDP, uniqueness is not checked
    #         return value

    #     # Check for uniqueness if value is not UDP
    #     if SupplierFormData.objects.filter(gstin=value).exists():
    #         raise serializers.ValidationError("This value is not unique.")

    #     return value

    # def validate_Legal_Name(self, value):
    #     """
    #     Validate that Legal_Name is unique.
    #     """
    #     existing_supplier = Supplier_Form_Data.objects.filter(Legal_Name=value).first()
    #
    #     if existing_supplier:
    #         raise serializers.ValidationError("Legal_Name must be unique.")
    #
    #     return value


class CurrencyMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyMaster
        fields = "__all__"


class CurrencyExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyExchange
        fields = "__all__"
        
    def validate(self, attrs):
        currency = attrs.get("Currency")
        instance = getattr(self, "instance", None)

        if currency:
            qs = CurrencyExchange.objects.filter(Currency=currency, is_delete=False)
            if instance:
                qs = qs.exclude(id=instance.id)

            if qs.exists():
                raise serializers.ValidationError(
                    {"Currency": f"Currency '{currency}' already has an exchange rate record."}
                )

        return attrs


class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = "__all__"


class SalesOrderItemComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItemCombo
        fields = "__all__"

class posOtherIncomeChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = posOtherIncomeCharges
        fields = "__all__"


class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = paymentMode
        fields = "__all__"


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"

 


class NumberingSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberingSeries
        fields = '__all__'


class BomCostVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomCostVariation
        fields = '__all__'


class FinishedGoodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishedGoods
        fields = '__all__'


class RawMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterial
        fields = '__all__'


class RawMaterialBomLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterialBomLink
        fields = '__all__'


class ScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = "__all__"


class RoutingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routing
        fields = "__all__"


class BomRoutingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomRouting
        fields = "__all__"


class BomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bom
        fields = "__all__"


class MrpMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MrpMaster
        fields = "__all__"


class MrpItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MrpItem
        fields = "__all__"


class ProductionOrderSerialNumbersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderSerialNumbers
        fields = "__all__"


class ProductionOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderStatus
        fields = "__all__"


class POItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderItem
        fields = "__all__"


class SubProductionOrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubProductionOrders
        fields = "__all__"


class ProductionOrderFinishedGoodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderFinishedGoods
        fields = "__all__"


class ProductionOrderRawMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderRawMaterials
        fields = "__all__"


class ProductionOrderScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderScrap
        fields = "__all__"


class ProductionOrderOtherChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderOtherCharges
        fields = "__all__"


class ProductionOrderProcessRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderProcessRoute
        fields = "__all__"         
        
        
class ProductionOrderMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderMaster
        fields = "__all__"


class ProductionOrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderItemDetail
        fields = "__all__"


class ProductionOrderLinkingTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrderLinkingTable
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class TermsConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsConditions
        fields = '__all__'


class OtherExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherExpenses
        fields = '__all__'


class purchaseOrderItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = purchaseOrderItemDetails
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]

    def create(self, validated_data):
        user = self.context['request'].user
        print("user", user)
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class purchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = purchaseOrder
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class GoodsInwardNoteItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsInwardNoteItemDetails
        fields = '__all__'
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class GoodsInwardNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsInwardNote
        fields = '__all__'
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class GoodsReceiptNoteItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptNoteItemDetails
        fields = '__all__'
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class OtherExpensespurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherExpensespurchaseOrder
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data): 
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class QualityInspectionsReportItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityInspectionsReportItemDetails
        fields = '__all__'
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class QualityInspectionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityInspectionReport
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class ReworkDeliveryChallanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReworkDeliveryChallan
        fields = '__all__' 
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class ReworkDeliveryChallanItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReworkDeliveryChallanItemDetails
        fields = '__all__'
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class PurchaseRetunBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRetunBatch
        fields = "__all__"

class PurchaseRetunNobatchNoserialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRetunNobatchNoserial
        fields = "__all__"

class PurchaseReturnChallanItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseReturnChallanItemDetails
        exclude = ['created_by', 'modified_by']
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)


    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)

class PurchaseReturnChallanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseReturnChallan
        exclude = ['created_by', 'modified_by', ]
        read_only_fields = ['created_by', 'modified_by', ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)


    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)


class PurchaseInvoiceItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceItemDetails
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)


    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)

class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoice
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',"dc_no"]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class PurchaseInvoiceImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceImport
        fields = "__all__"
        
class PurchaseInvoiceImportLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceImportLine
        fields = "__all__"

class DirectPurchaseInvoiceItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectPurchaseInvoiceItemDetails
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)


    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)

class DirectPurchaseInvoiceAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectPurchaseInvoiceAccount
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)


    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)


class DirectPurchaseinvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectPurchaseinvoice
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',"dc_no"]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class DebitNoteOtherIncomeChargesSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebitNoteOtherIncomeCharge
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',"dc_no"]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class DebitNoteItemDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebitNoteItemDetail
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by',"dc_no"]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class DebitNoteAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebitNoteAccount
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class DebitNoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebitNote
        exclude = ['created_by', 'modified_by',]
        read_only_fields = ['created_by', 'modified_by' ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class PurchasePaidDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchasePaidDetails
        exclude = ['created_by']
        read_only_fields = ['created_by']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user 
        return super().create(validated_data)
        
class MaterialRequestMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialRequestMaster
        fields = "__all__"
        
class MaterialRequestItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialRequestItemDetails
        fields = "__all__"    
        
class MaterialRequestForSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialRequestFor
        fields = "__all__"   


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
class ReportTemplateSerializer(serializers.ModelSerializer):
    share_report = UserSerializer(many=True)
    class Meta:
        model = ReportTemplate
        fields = '__all__'
        

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "username", "password"]
#         extra_kwargs = {
#             'password': {
#                 'write_only': True,
#                 'required': True
#             }
#         }

# def create(self, validated_data):
#     username = validated_data.get('username')
#     password = validated_data.get('password')
#
#     # Check if a user with the provided username already exists
#     existing_user = User.objects.filter(username=username).first()
#     if existing_user:
#         # If the user exists, return the existing user's token
#         token, created = Token.objects.get_or_create(user=existing_user)
#         return Response({'token': token.key})
#
#     # If the user doesn't exist, create a new user and return the token
#     user = User.objects.create_user(username=username, password=password)
#     token = Token.objects.create(user=user)
#
#     return Response({'token': token.key})
