from django.contrib import admin
from .models import *


admin.site.register(Roles)
admin.site.register(UserManagement)
admin.site.register(PermissionOptions)
admin.site.register(PermissionModel)
admin.site.register(PaymentVoucherAgainstInvoice)
admin.site.register(AllowedPermission)
admin.site.register(Profile)
admin.site.register(ExpenseReconciliationDetails) 
admin.site.register(Employee)
admin.site.register(PaymentVoucherAdvanceDetails)
admin.site.register(PaymentVoucher)
admin.site.register(ExpenseClaim)
admin.site.register(ExpenseClaimDetails)
admin.site.register(Holidays)
admin.site.register(LeaveType)
admin.site.register(Leave)
admin.site.register(LeaveAlloted)
admin.site.register(ExpenseRequest)
admin.site.register(AttendanceRegister)