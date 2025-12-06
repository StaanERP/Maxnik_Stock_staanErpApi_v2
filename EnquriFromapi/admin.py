from django.contrib import admin

from .models import *



# @admin.register(enquiryDatas)
# class enquiryDatasAdmin(admin.ModelAdmin):
#     fields = ['Name', 'OrganizationName', 'Email', 'status', 'MobileNumber', 'Location', 'message',
#               'Interesteds', 'conferencedata', 'salesPerson', 'Remarks', 'followup',"profile_image"]

# admin.site.register(enquiryDatas, enquiryDatasAdmin)

admin.site.register(enquiryDatas)
admin.site.register(product)
admin.site.register(Conferencedata)
admin.site.register(UserPermission)


