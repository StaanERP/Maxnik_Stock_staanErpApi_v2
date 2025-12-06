from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Leads)  
admin.site.register(SalesOrder_2) 
admin.site.register(SalesOrder_2_ItemDetails)
admin.site.register(SalesOrder_2_temComboItemDetails)
admin.site.register(SalesOrder_2_DeliveryChallanItemDetails)
admin.site.register(SalesOrder_2_DeliveryChallan)
admin.site.register(SalesOrder_2_DeliverChallanItemCombo)
admin.site.register(SalesOrder_2_otherIncomeCharges)
admin.site.register(SalesInvoice)
admin.site.register(SalesInvoiceItemDetail)
admin.site.register(SalesInvoiceItemCombo)

admin.site.register(Quotations)
admin.site.register(QuotationsItemDetails)
admin.site.register(QuotationsItemComboItemDetails)
admin.site.register(QuotationsOtherIncomeCharges)
admin.site.register(SalesOrder_2_RetunBatch)

admin.site.register(DirectSalesInvoice)


admin.site.register(EmailTemplete)
admin.site.register(EmailResource)

admin.site.register(SalesReturnBatch_item)
admin.site.register(SalesReturnItemCombo)
admin.site.register(SalesReturnItemDetails)
admin.site.register(SalesReturn)


admin.site.register(ReceiptVoucherAdvanceDetails)
admin.site.register(ReceiptVoucherAgainstInvoice)
admin.site.register(ReceiptVoucher)
