from django.urls import path, include
from itemmaster2.views import *

urlpatterns = [
    path('sales_order2_rerport',  SalesOrder2Rerport.as_view()),
    path('sales_order_1',  test_report.as_view()),
]




# "customer__company_name",
