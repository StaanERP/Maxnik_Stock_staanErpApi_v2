from rest_framework import serializers
from .models import *

"""Activites"""


class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = "__all__"


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = "__all__"


class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = "__all__"


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = "__all__"


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activites
        fields = "__all__"


class EmailTempleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplete
        fields = "__all__"


class EmailRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailRecord
        fields = "__all__"

"""Lead"""


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = "__all__"


"""Quotations"""


class OtherIncomeChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherIncomeCharges
        fields = "__all__"


class QuotationsItemComboItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationsItemComboItemDetails
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class QuotationsItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationsItemDetails
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class QuotationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotations
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class QuotationsOtherIncomeChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationsOtherIncomeCharges
        fields = "__all__"
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


"""SalesOrder_2"""


class SalesOrder_2_temComboItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_temComboItemDetails
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class SalesOrder_2Serializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)


class SalesOrder_2_ItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_ItemDetails
        fields = "__all__"
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

# This is only for sales moduals
class SalesOrder_2_otherIncomeChargesSerializer_qs(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_otherIncomeCharges
        fields = "__all__"


class SalesOrder_2_otherIncomeChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_otherIncomeCharges
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class SalesOrder_2_DeliverChallanItemComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_DeliverChallanItemCombo
        # fields = "__all__"
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

class SalesOrder_2_DeliveryChallanItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_DeliveryChallanItemDetails
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

class SalesOrder_2_DeliveryChallanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder_2_DeliveryChallan
        # fields = "__all__"
        exclude = ['created_by', 'modified_by','dc_no']
        read_only_fields = ['created_by', 'modified_by','dc_no']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user 
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

"""Traget """
class TargetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Target
        fields = "__all__"

class SalesInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoice
        exclude = ['created_by', 'modified_by']
        read_only_fields = ['created_by', 'modified_by']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        # print("validated_data---------",validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return super().update(instance, validated_data)

class SalesInvoiceItemDetailSerialzer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItemDetail
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

class SalesInvoiceItemComboSerialzer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItemCombo
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

class DirectSalesInvoiceItemDetailsSerialzer(serializers.ModelSerializer):
    class Meta:
        model = DirectSalesInvoiceItemDetails
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

class DirectSalesInvoiceSerialzer(serializers.ModelSerializer):
    class Meta:
        model = DirectSalesInvoice
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

class SalesReturnBatch_itemSerialzer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturnBatch_item
        fields = "__all__"

class SalesReturnItemComboSerialzer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturnItemCombo
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

class SalesReturnOtherIncomeChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturnOtherIncomeCharges
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

class SalesReturnItemDetailsSerialzer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturnItemDetails
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

class SalesReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturn
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

class ReceiptVoucherAdvanceDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptVoucherAdvanceDetails
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

class ReceiptVoucherAgainstInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptVoucherAgainstInvoice
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

class ReceiptVoucherLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptVoucherLine
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

class SalesPaidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPaidDetails
        exclude = ['created_by']
        read_only_fields = ['created_by']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

# 
 
class ReceiptVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptVoucher
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
    
class CreditNoteOtherIncomeChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteOtherIncomeCharges
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

class CreditNoteAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteAccount
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

class CreditNoteComboItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteComboItemDetails
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

class CreditNoteItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteItemDetails
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

class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
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