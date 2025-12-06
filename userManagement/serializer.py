from rest_framework import serializers
from .models import *


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = "__all__"


class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserManagement
        fields = "__all__"


class AllowedPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedPermission
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"


class ExpenseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRequest
        fields = "__all__"


class ExpenseCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategories
        fields = "__all__"

class ExpenseClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseClaim
        fields = "__all__"

class ExpenseClaimDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseClaimDetails
        fields = "__all__"

class PaymentVoucherAgainstInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVoucherAgainstInvoice
        exclude = ["created_by", "modified_by"]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['modified_by'] = user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        
        return super().update(instance, validated_data)


class PaymentVoucherAdvanceDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVoucherAdvanceDetails
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

class PaymentVoucherLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVoucherLine
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

class PaymentVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVoucher
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


class ExpenseReconciliationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseReconciliationDetails
        fields = "__all__"

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holidays
        fields = "__all__"
    
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"
    
class LeaveAllotedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAlloted
        fields = "__all__"

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = "__all__"

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRegister
        fields = "__all__"
