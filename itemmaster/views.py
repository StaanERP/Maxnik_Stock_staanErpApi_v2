import json

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from datetime import date, datetime, timezone, timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from itemmaster2.models import *
from userManagement.models import UserManagement
from .serializer import *
from django.http import JsonResponse
from django.forms.models import model_to_dict
from decimal import Decimal
from collections import defaultdict
from django.db import connection
from django.core.serializers import serialize
from django.db.models import Prefetch
from itemmaster import Report_json_data
from django.db.models import Q, Count, Sum, Avg, Min, Max
from rest_framework.response import Response
from .Utils.CommanUtils import *
from django.core.cache import cache
from django.db.models.functions import TruncMonth, TruncYear, ExtractMonth, ExtractYear,TruncWeek
from django.db.models import Sum, Count, Avg, Min, Max, Q, F, Case, When, Value, CharField
from datetime import datetime

predefind_model_status = {
    "SalesOrder_2": "status__name",
    "Quotations": "status__name",
    "enquiryDatas": "status",
    "Leads": "status__name",
    "SalesOrder": "status",
    "Activites": "status__name",
    "GoodsInwardNote" : "status__name",
    "GoodsReceiptNote" : "status__name",
    "purchaseOrder" : "status__name",
    "QualityInspectionReport" : "status__name",
    "ReworkDeliveryChallan":"status__name",
    "SalesOrder_2_DeliveryChallan":"status__name",
    "PurchaseInvoice":"status__name",
    "PurchaseReturnChallan":"status__name",
    "DebitNote":"status__name",
    "DirectPurchaseinvoice":"status__name",
    "SalesReturn":"status__name",
    "PaymentVoucher":"status__name"
}

model_data_fields = {"SalesOrder_2": "sales_order", "Leads": "lead", "Quotations": "quotations",
                    "enquiryDatas": "enquiry",
                    "SalesOrder_2_DeliveryChallan":"dc",
                    "SalesInvoice":"sales_invoice",
                    "purchaseOrder":"purchaseOrder",
                    "GoodsInwardNote":"GoodsInwardNote",
                    "QualityInspectionReport":"QualityInspectionReport",
                    "GoodsReceiptNote":"GoodsReceiptNote",
                    "PurchaseReturnChallan":"PurchaseReturnChallan",
                    "PurchaseInvoice":"PurchaseInvoice",
                    "DebitNote":"DebitNote",
                    "ReworkDeliveryChallan":"ReworkDeliveryChallan"
                     }

Tables = [{"sales_order": {"app": "itemmaster2", "model_name": "SalesOrder_2", "label": "Sales Order"}},
          {"lead": {"app": "itemmaster2", "model_name": "Leads", "label": "Leads"}}
        , {"quotations": {"app": "itemmaster2", "model_name": "Quotations", "label": "Quotations"}},
          {"enquiry": {"app": "EnquriFromapi", "model_name": "enquiryDatas", "label": "Enquiry"}},
           {"dc": {"app": "itemmaster2", "model_name": "SalesOrder_2_DeliveryChallan", "label": "Delivery Challan"}},
           {"sales_invoice": {"app": "itemmaster2", "model_name": "SalesInvoice", "label": "Sales Invoice"}},
           {"purchaseOrder": {"app": "itemmaster", "model_name": "purchaseOrder", "label": "Purchase Order"}},
           {"GoodsInwardNote": {"app": "itemmaster", "model_name": "GoodsInwardNote", "label": "Goods Inward Note"}},
           {"QualityInspectionReport": {"app": "itemmaster", "model_name": "QualityInspectionReport", "label": "Quality Inspection Report"}},
           {"GoodsReceiptNote": {"app": "itemmaster", "model_name": "GoodsReceiptNote", "label": "Goods Receipt Note"}},
            {"PurchaseReturnChallan": {"app": "itemmaster", "model_name": "PurchaseReturnChallan", "label": "Purchase Return Challan"}},
            {"PurchaseInvoice": {"app": "itemmaster", "model_name": "PurchaseInvoice", "label": "Purchase Invoice"}},
            {"DebitNote": {"app": "itemmaster", "model_name": "DebitNote", "label": "Debit Note"}},
            {"ReworkDeliveryChallan": {"app": "itemmaster", "model_name": "ReworkDeliveryChallan", "label": "Rework Delivery Challan"}}

          ]

active_model_list = ["SalesOrder_2", "Quotations","purchaseOrder"]

created_at_fields = {"SalesOrder_2":"CreatedAt", "Leads":"created_at","Quotations":"CreatedAt","enquiryDatas":"created_at","SalesOrder_2_DeliveryChallan":"created_at",
                     "SalesInvoice":"created_at","purchaseOrder":"created_at","PurchaseReturnChallan":"created_at","PurchaseInvoice":"created_at","DebitNote":"created_at","ReworkDeliveryChallan":"created_at"}

permission_table_list={"enquiryDatas":"Enquiry"}

def applyFilter(modelname, appname, pageNumber, pageSize, static_filter, fixFilterObjects, selected_filed_, sort_by,
                user_id, subordinates):
    ModelClass = None
    # Dynamically get the model
    status_list = []
    try:
        ModelClass = apps.get_model(app_label=appname, model_name=modelname)
        ModelClass_ = ModelClass
        ModelClass = ModelClass.objects.all().order_by('-id')
        if len(selected_filed_) > 0:
            if modelname in predefind_model_status and predefind_model_status[modelname]:
                selected_filed_.append(predefind_model_status[modelname])
            ModelClass = ModelClass.values(*selected_filed_)

        normal_filters = {}
        exclude_filters = {}
        isnull_filters = []
        not_isnull_filters = []
        if modelname in predefind_model_status and predefind_model_status[modelname]:
            field_name = str(predefind_model_status[modelname]).split("__")[0]
            try:
                status_ = ModelClass.values(predefind_model_status[modelname]).order_by(field_name).distinct(field_name)
                status_list.append(status_)
            except Exception as e:
                print("e", e)

        if fixFilterObjects:
            for key, value in fixFilterObjects.items():
                if key.endswith("__noticontains"):
                    exclude_key = key.replace("__noticontains", "__icontains")
                    exclude_filters[exclude_key] = value
                elif key.endswith("__notin"):
                    exclude_key = key.replace("__notin", "__in")
                    exclude_filters[exclude_key] = value
                elif key.endswith("__isempty"):
                    field_name = key.replace("__isempty", "")
                    isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                elif key.endswith("__isnotempty"):  # Handle "is not empty"
                    field_name = key.replace("__isnotempty", "")
                    not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                elif key.endswith('__group'):
                    field_name = key.replace("__group", "")
                    users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
                    field_name = str(field_name).split("__")[0]
                    normal_filters[f"{field_name}__in"] = users_ids_list
                elif key.endswith("__default"):
                    exclude_key = key.replace("__default", "")
                    normal_filters[str(exclude_key).split("__")[0]] = user_id
                else:
                    normal_filters[key] = value

        if static_filter:
            for key, value in static_filter.items():
                normal_filters[key] = value

        UserData = UserManagement.objects.filter(user_id=user_id).first()
        if  not UserData.admin and not UserData.sales_executive  and modelname in ['Leads',"enquiryDatas","Quotations","SalesOrder_2"]:
                normal_filters[f"sales_person__in"] = subordinates
        
        try:
            # Apply normal filters
            if normal_filters:
                ModelClass = ModelClass.filter(**normal_filters)
            # apply exclude filters
            if exclude_filters:
                ModelClass = ModelClass.exclude(**exclude_filters)
                # Apply isnull (empty) filters
            for isnull_filter in isnull_filters:
                ModelClass = ModelClass.filter(isnull_filter)

                # Apply isnotnull (not empty) filters
            for not_isnull_filter in not_isnull_filters:
                ModelClass = ModelClass.filter(not_isnull_filter)
            if sort_by:
                valid_fields = [f.name for f in ModelClass_._meta.fields]  # Get model field names
                validated_sort_fields = []
                field_name = sort_by.lstrip("-")
                field_name = str(field_name).split("__")[0]
                if field_name in valid_fields:
                    validated_sort_fields.append(sort_by)
                if len(validated_sort_fields) > 0:
                    ModelClass = ModelClass.order_by(*validated_sort_fields)
                else:
                    return {"success": True, "error": f"Invalid sort field: {field_name}", "data": ModelClass,
                            "status": status_list}
                
            if ModelClass_.__name__ == "enquiryDatas":
                ModelClass = ModelClass.exclude(status="Converted To Lead")
            return {"success": True, "error": None, "data": ModelClass, "status": status_list}
        except Exception as e:
            return {"success": False, "error": e, "data": None, "status": None}

    except Exception as e:
        return {"success": True, "error": e, "data": ModelClass, "status": status_list}


def get_date_range(condition_value):
    """Returns start and end dates based on condition value."""
    today = now().date()

    if condition_value == "week":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week

    elif condition_value == "month":
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1) - timedelta(days=1))
        return start_of_month, end_of_month

    elif condition_value == "financially":
        current_year = today.year
        if today.month < 4:
            start_of_financial_year = datetime(current_year - 1, 4, 1).date()
            end_of_financial_year = datetime(current_year, 3, 31).date()
        else:
            start_of_financial_year = datetime(current_year, 4, 1).date()
            end_of_financial_year = datetime(current_year + 1, 3, 31).date()
        return start_of_financial_year, end_of_financial_year

    return None, None  # Default case

def get_subordinate(user_id):
    """Recursively get all subordinate user IDs of a user."""
    from django.db.models import Q

    visited = set()  # To avoid circular references

    def getsubordinate_ids(uid):
        if uid in visited:
            return []
        visited.add(uid)
        try:
            user_obj = UserManagement.objects.get(user=uid)
        except UserManagement.DoesNotExist:
            return []

        direct_subordinates = UserManagement.objects.filter(
            Q(role__report_to=user_obj.user) | Q(role_2__report_to=user_obj.user)
        )
        all_subordinate_ids = []
        for subordinate in direct_subordinates:
            sub_id = subordinate.user.id
            all_subordinate_ids.append(sub_id)
            all_subordinate_ids.extend(getsubordinate_ids(sub_id))  # Recursive

        return all_subordinate_ids
    cache_key = f"subordinates_of_user_{user_id}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    result =  getsubordinate_ids(user_id)
    result.append(user_id)
    cache.set(cache_key, result, timeout=43200)# cache for 12 hours
    return result

# @method_decorator(csrf_exempt, name='dispatch')
class InitialDataForTables(APIView):
    """depence on model filter get data used for list view"""
    def put(self, request):
        model_name = request.data.get("model_name", None)
        table_name = request.data.get("table_name", None)
        app_name = request.data.get("app_name", None)
        permission_name = request.data.get("permission_name",None)
        user_id = request.data.get("user_id", None)
        pageNumber = request.data.get('pageNumber', 1)
        pageSize = request.data.get('pageSize', 10)
        static_filter = request.data.get("static", None)
        subordinates = get_subordinate(user_id)
        # Validate inputs
        required_fields = ["model_name", "table_name", "app_name", "user_id","permission_name"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]

        allowed = False
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_management = UserManagement.objects.filter(user=user_id).first()
        if user_management and user_management.profile:
            allowed_perms = user_management.profile.allowed_permission.filter(
                model_name=permission_name
            )
            for perm in allowed_perms:
                if perm.permission_options.filter(options_name__iexact="View").exists():
                    allowed = True
        if allowed:
            # Base query
            query = Q(table=table_name) & (
                    Q(visible_to="Myself", created_by=user_id) |
                    Q(visible_to="All User") |
                    Q(visible_to="Select Users", visible_to_user__in=[user_id])
            )
            # Filter records based on the query
            records = EditListView.objects.filter(query)

            # Filter by the latest update time
            default_table_filter = records.filter(default_update_date_time__isnull=False).order_by('-default_update_date_time')
            if len(default_table_filter) > 0:
                filter_condition = {}
                selected_filed_ = []
                filter_object = default_table_filter[0]
                serialized_filter_object = model_to_dict(filter_object) 
                if 'visible_to_user' in serialized_filter_object:
                    serialized_filter_object['visible_to_user'] = [
                        {"id": u.id, "username": u.username, "email": u.email}
                        for u in serialized_filter_object['visible_to_user']
                    ]
                # serialized_filter_object = serializer.data  # This is now JSON serializable
                sort_by = filter_object.default_sort_order

                filter_conditions = filter_object.filiter_conditions
                selected_fields = filter_object.coloumn_to_display
                for condition in filter_conditions:
                    if condition['type'] == "Date":
                        condition_value = condition['conditionOption']['value']
                        field_name = condition['field']
                        if condition_value in ["week", "month", "financially"]:
                            start_date, end_date = get_date_range(condition_value)
                            filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                        elif condition_value == "today":
                            # start_date, end_date = get_date_range(condition_value)
                            if condition["isDate"]:
                                filter_condition.update({f"{field_name}__date": datetime.now().date()})
                            else:
                                filter_condition.update({f"{field_name}": datetime.now().date()})

                        elif condition_value == "custom":
                            start_date = condition['conditionApplied']['start']
                            end_date = condition['conditionApplied']['end']
                            if start_date == end_date:
                                # Apply direct match instead of range if dates are the same
                                filter_condition.update({field_name: start_date})
                            else:
                                filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                        elif condition_value == "empty":
                            filter_condition.update({f"{condition['field']}": True})
                    elif condition['type'] == "Bool":
                        # Convert string to boolean
                        value_str = str(condition['conditionApplied']['value']).strip().lower()
                        if value_str == 'true':
                            bool_value = True
                        elif value_str == 'false':
                            bool_value = False
                        else:
                            raise ValueError(f"Invalid boolean value: {value_str}")
                        filter_condition.update({condition['field']: bool_value})
                    elif condition['type'] == "text" and ("isMulti" in condition and not condition['isMulti']):
                        if type(condition['conditionApplied']) == dict:
                            condition['conditionApplied'] = condition['conditionApplied']['value']
                        else:
                            condition['conditionApplied'] = condition['conditionApplied']
                        if condition['conditionOption']['value'] == "equal":
                            filter_condition.update({f"{condition['field']}__icontains": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "notEqual":
                            filter_condition.update({f"{condition['field']}__noticontains": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "isEmpty":
                            filter_condition.update({f"{condition['field']}__isempty": ""})
                        if condition['conditionOption']['value'] == "isNotEmpty":
                            filter_condition.update({f"{condition['field']}__isnotempty": ""})
                        if condition['conditionOption']['value'] == "userGroup":
                            filter_condition.update(
                                {f"{condition['field']}__group": condition['conditionApplied']['value']})
                        if condition['conditionOption']['value'] == "default":
                            filter_condition.update({f"{condition['field']}__default": user_id})
                    elif condition['type'] == "text" and ("isMulti" in condition and condition['isMulti']):
                        if condition['conditionOption']['value'] == "equal":
                            filter_condition.update(
                                {f"{condition['field']}__in": [data['value'] for data in condition['conditionApplied']]})
                        if condition['conditionOption']['value'] == "notEqual":
                            filter_condition.update(
                                {f"{condition['field']}__notin": [data['value'] for data in condition['conditionApplied']]})
                        if condition['conditionOption']['value'] == "isEmpty":
                            filter_condition.update({f"{condition['field']}__isempty": ""})
                        if condition['conditionOption']['value'] == "isNotEmpty":
                            filter_condition.update({f"{condition['field']}__isnotempty": ""})
                        if condition['conditionOption']['value'] == "userGroup":
                            filter_condition.update(
                                {f"{condition['field']}__group": condition['conditionApplied']['value']})
                        if condition['conditionOption']['value'] == "default":
                            filter_condition.update({f"{condition['field']}__default": user_id})

                    elif condition['type'] == "number":
                        if condition['conditionOption']['value'] == "lessThan":
                            filter_condition.update({f"{condition['field']}__lt": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "greaterThan":
                            filter_condition.update({f"{condition['field']}__gt": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "lessThanEqual":
                            filter_condition.update({f"{condition['field']}__lte": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "greaterThanEqual":
                            filter_condition.update({f"{condition['field']}__gte": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "between":
                            split_data = condition['conditionApplied'].split(',')
                            start = int(split_data[0].replace("'", ""))
                            end = int(split_data[1].replace("'", ""))
                            filter_condition.update({f"{condition['field']}__range": (start, end)})
                for selected_field in selected_fields:
                    selected_filed_.append(selected_field.get("field"))
                if "id" not in selected_filed_:
                    selected_filed_.append("id")
                
                result = applyFilter(model_name, app_name, pageNumber, pageSize, static_filter, filter_condition,
                                    selected_filed_, sort_by, user_id, subordinates)
                
                if result['success']:
                    try:
                        paginator = Paginator(result['data'], pageSize)
                        paginated_data = paginator.get_page(pageNumber)
                        status_rerquest = result.get('status', [])

                        if isinstance(status_rerquest, list) and len(status_rerquest) > 0:
                            status_data = [status_ for status_ in status_rerquest[0] if
                                        status_.get('status__name') not in [None, ""] or status_.get('status') not in [
                                            None, ""]]
                        else:
                            status_data = [] 
                        response_data = {
                            'count': paginator.count,  # Total number of records
                            'num_pages': paginator.num_pages,  # Total number of pages
                            'has_next': paginated_data.has_next(),  # Check if there is a next page
                            'has_previous': paginated_data.has_previous(),  # Check if there is a previous page
                            'current_page': pageNumber,
                            'page_size': pageSize,
                            'results': list(paginated_data),  # The paginated data
                            "editlistview": (serialized_filter_object),
                            "status": status_data
                        }
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                    return Response(response_data)
                else:
                    return Response({"error": result['error']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "No data Available"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": f"You don't have permission to view the data of {table_name}"}, status=status.HTTP_400_BAD_REQUEST)



class commanFetchQuery(APIView):
    """depence on model filter get data,  used for list view"""
    def put(self, request):
        model_name = request.data.get("model_name", None)
        app_name = request.data.get("app_name", None)
        permission_name = request.data.get("permission_name",None)
        fields = request.data.get("selectedData")
        user_id = request.data.get("user_id", None)
        pageNumber = request.data.get('pageNumber', 1)
        pageSize = request.data.get('pageSize', 10)
        filterData = request.data.get("filterData", None)
        fixedfields = request.data.get("fixedselectedData", None)
        fixedfilterData = request.data.get("fixedfilterData", None)
        distinct_data = request.data.get("distinct", [])
        static_filter = request.data.get("static", None)
        sort_by = request.data.get("sort_by", [])
        errors = []
        required_fields = ["model_name", "app_name", "selectedData","permission_name","user_id"]
        allowed = False
        subordinates = get_subordinate(user_id)
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_management = UserManagement.objects.filter(user=user_id).first()
        if user_management and user_management.profile:
            allowed_perms = user_management.profile.allowed_permission.filter(
                model_name=permission_name
            )
            for perm in allowed_perms:
                if perm.permission_options.filter(options_name__iexact="View").exists():
                    allowed = True

        if allowed:
            ModelClass = apps.get_model(app_label=app_name, model_name=model_name)
            ModelClass_ = ModelClass
            ModelClass = ModelClass.objects.all().order_by('-id')
            if fixedfields:
                if "id" not in fixedfields:
                    fixedfields.append("id")
                ModelClass = ModelClass.values(*fixedfields)
            else:
                if "id" not in fields:
                    fields.append("id")
                ModelClass = ModelClass.values(*fields)
            if fixedfilterData:
                normal_filters = {}
                exclude_filters = {}
                isnull_filters = []
                not_isnull_filters = []
                for key, value in fixedfilterData.items():
                    if key.endswith("__noticontains"):
                        exclude_key = key.replace("__noticontains", "__icontains")
                        exclude_filters[exclude_key] = value
                    if key.endswith("__isnull"):
                        normal_filters[f"{key}"] = True
                    elif key.endswith("__notin"):
                        exclude_key = key.replace("__notin", "__in")
                        exclude_filters[exclude_key] = value
                    elif key.endswith("__isempty"):  # Handle "is empty"
                        field_name = key.replace("__isempty", "")
                        isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                    elif key.endswith("__isnotempty"):
                        field_name = key.replace("__isnotempty", "")
                        not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                    elif key.endswith("__default"):
                        exclude_key = key.replace("__default", "")
                        normal_filters[str(exclude_key).split("__")[0]] = user_id
                    elif key.endswith('__group'):
                        field_name = key.replace("__group", "")
                        users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
                        field_name = str(field_name).split("__")[0]
                        normal_filters[f"{field_name}__in"] = users_ids_list
                    elif any(period in key for period in ["_today", "_week", "_month", "_financially"]):
                        # Handling date-based filters with correct key formatting

                        if "__isnull" in key:
                            date_field = key.replace("__isdate__isnull", "")

                        if key.endswith("__isdate"):
                            # Convert "_today__isdate", "_week__isdate", etc., to "_date"
                            date_field = key.replace("_today__isdate", "__date").replace("_week__isdate", "__date") \
                                .replace("_month__isdate", "__date").replace("_financially__isdate", "__date")
                        else:
                            # Remove "_today", "_week", "_month", "_financially" completely
                            date_field = key.replace("_today", "").replace("_week", "").replace("_month", "").replace(
                                "_financially", "")

                        today = timezone.now().date()
                        if value:  # If value is provided, use it as the filter
                            normal_filters[date_field] = value

                        elif "_today" in key:
                            normal_filters[date_field] = today

                        elif "_week" in key:
                            start_of_week = today - timedelta(days=today.weekday())
                            normal_filters[f"{date_field}__range"] = [start_of_week, today]

                        elif "_month" in key:
                            start_of_month = today.replace(day=1)
                            # Calculate last day of the month
                            end_of_month = (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1) - timedelta(
                                days=1))
                            normal_filters[f"{date_field}__range"] = [start_of_month, end_of_month]

                        elif "_financially" in key:
                            current_year = today.year
                            if today.month < 4:
                                start_of_financial_year = datetime(current_year - 1, 4, 1).date()
                                end_of_financial_year = datetime(current_year, 3, 31).date()
                            else:
                                start_of_financial_year = datetime(current_year, 4, 1).date()
                                end_of_financial_year = datetime(current_year + 1, 3, 31).date()
                            normal_filters[f"{date_field}__range"] = [start_of_financial_year, end_of_financial_year]
                    
                    elif key.endswith("__in")  and type(value) == list:
                  
                        value_multi = []
                        if any(isinstance(single_val, dict) and single_val.get("value") for single_val in value):
                            value_multi = [single_val.get("value") for single_val in value if single_val.get("value")]
                        else:
                            value_multi = value


                        normal_filters[key] = value_multi
                    else:
                        normal_filters[key] = value
               
                try:
                    # Apply normal filters
                    if normal_filters:
                        ModelClass = ModelClass.filter(**normal_filters)

                    # Apply to exclude filters
                    if exclude_filters:
                        ModelClass = ModelClass.exclude(**exclude_filters)

                    # Apply isnull (empty) filters
                    for isnull_filter in isnull_filters:
                        ModelClass = ModelClass.filter(isnull_filter)

                    # Apply isnotnull (not empty) filters
                    for not_isnull_filter in not_isnull_filters:
                        ModelClass = ModelClass.filter(not_isnull_filter)

                except Exception as e:
                    errors.append(e)
            if static_filter:
                for key, value in static_filter.items():
                    filterData[key] = value
            try:
                user_management_data = UserManagement.objects.filter(user_id=user_id).first()
                if not user_management_data.admin and not user_management_data.sales_executive and model_name in ['Leads',"enquiryDatas","Quotations","SalesOrder_2"]:
                    filterData[f"sales_person__in"] = subordinates
                if filterData:
                    try:
                        ModelClass = ModelClass.filter(**filterData)
                    except Exception as e:
                        print(e)
                if len(distinct_data) > 0:
                    distinct_data = [field.split('__')[0] for field in distinct_data]  # Extract field names
                    distinct_data = set(distinct_data)

                    # Validate against model fields
                    valid_fields = [f.name for f in ModelClass_._meta.fields]
                    distinct_data = [field for field in distinct_data if field in valid_fields]
                    try:
                        ModelClass = ModelClass.order_by(*distinct_data).distinct(*distinct_data)
                    except Exception as e:
                        errors.append(e)
                        # Validate and apply multi-field sorting

                if sort_by:
                    if not isinstance(sort_by, list):
                        return Response({"error": "sort_by should be a list of fields"}, status=status.HTTP_400_BAD_REQUEST)

                    valid_fields = [f.name for f in ModelClass_._meta.fields]  # Get model field names
                    validated_sort_fields = []

                    for field in sort_by:
                        field_name = field.lstrip("-")  # Remove '-' to validate the base field name
                        field_name = field_name.split("__")[0]
                        field_ = field.split("__")[0]

                        if field_name in valid_fields:
                            validated_sort_fields.append(field_)
                        else:
                            return Response({"error": f"Invalid sort field: {field_name}"},
                                            status=status.HTTP_400_BAD_REQUEST)
                    ModelClass = ModelClass.order_by(*validated_sort_fields)

                if ModelClass_.__name__ == "enquiryDatas":
                    ModelClass = ModelClass.exclude(status="Converted To Lead")
            except Exception as e:
                errors.append(e)
            paginator = Paginator(ModelClass, pageSize)
            paginated_data = paginator.get_page(pageNumber)
            response_data = {
                "errors": errors,
                'count': paginator.count,  # Total number of records
                'num_pages': paginator.num_pages,  # Total number of pages
                'has_next': paginated_data.has_next(),  # Check if there is a next page
                'has_previous': paginated_data.has_previous(),  # Check if there is a previous page,
                'results': list(paginated_data)  # The paginated data
            }
            return Response(response_data)
        else:
            response_data = {
                "errors": ["You don't have permission to view the data"],
                'count': 0,  # Total number of records
                'num_pages': 0,  # Total number of pages
                'has_next': False,  # Check if there is a next page
                'has_previous': False,  # Check if there is a previous page,
                'results': []
            }
            return Response(response_data)
            # return Response({"error": f"You don't have permission to view the data"})


class GetFieldsModels(APIView):
    # @api_permission_required(models=["ReportTemplate"], action="view")
    def get(self, model):
        try:
            data = Tables
            if data is None:
                raise Exception(f"Model not found.")
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class GetFieldsSubModels(APIView):
    """it reten the model fields"""

    def get(self, request, model):
        # Fetch the data using getattr to access the model data
        model_key = model_data_fields.get(model, None)
        if not model_key:
            raise Exception(f"Model {model} not found in model_data_fields.")

        processed_fields = {}
        data = getattr(Report_json_data, model_key, None)
        if data is None:
            raise Exception(f"Model {model} not found.")

        # Process link_type fields
        def process_fields(fields):
            updated_fields = []  # Create a new list to store processed fields
            for field in fields:
                field = field.copy()  # Prevent modifying the original dictionary
                # field.pop('group_by', None)  # Remove group_by if present
                if 'link_type' in field and (
                        field['link_type'] == 'ForeignKey' or field['link_type'] == 'ManyToManyField'):
                    link_table = field.get('link_table', [])
                    field['link_table'] = process_fields(link_table)  # Recurse
                    processed_fields[field['visible_name']] = field['link_table']
                updated_fields.append(field)
            return updated_fields

        # Remove child objects (those with 'link_type') and store others
        def remove_child_objects(fields):
            processed_fields[model] = [field for field in fields if 'link_type' not in field]

        remove_child_objects(data)
        process_fields(data)
        # Generate group_by fields
        group_by = {}
        for table, fields in processed_fields.items():
            group_by[table] = []
            for field in fields:
                if field.get('group_by'):
                    group_by[table].append({
                        "label": field['visible_name'],
                        "value": field['field_links'],
                        "type": field['type']
                    })
        # Generate calculation fields
        calculation_fields = {
            table: [
                {"label": field['visible_name'], "value": field['field_links'], "functions": func}
                for field in fields if field.get('number')
                for func in ["Sum", "Avg"]  # Iterate over both functions for each field
            ]
            for table, fields in processed_fields.items()
        }
        for table in processed_fields:
            processed_fields[table] = [dict(field) for field in processed_fields[table]]  # Create new copies
            for file in processed_fields[table]:
                file.pop('group_by', None)  # Remove safely from the copied version
                file.pop('number', None)
        return Response({
            "column_fields": processed_fields,
            "group_by": group_by,
            "calculation": calculation_fields,
            "module_list": Tables
        })


class GetReportData(APIView):
    """depence on param send with report data"""
    # @api_permission_required(models=["ReportTemplate"], action="view")
    def put(self, request):
        group_by = request.data.get("group_by", [])
        annotations = request.data.get("annotations", {})
        order_by = request.data.get('order_by', None)
        model_name = request.data.get("model_name", None)
        app_name = request.data.get("app_name", None)
        limit = request.data.get("limit", None)
        filterData = request.data.get("filterData", None)

        # Check for missing required fields
        required_fields = ["model_name", "app_name", "group_by"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Dynamically build the annotations
        annotation_args = {}
        for alias, annotation_info in annotations.items():
            if annotation_info.get("type") == "Sum":
                annotation_args[alias] = Sum(annotation_info["field"])
            elif annotation_info.get("type") == "Count":
                annotation_args[alias] = Count(annotation_info["field"])
            elif annotation_info.get("type") == "Avg":
                annotation_args[alias] = Avg(annotation_info["field"])
            elif annotation_info.get("type") == "Min":
                annotation_args[alias] = Min(annotation_info["field"])
            elif annotation_info.get("type") == "Max":
                annotation_args[alias] = Max(annotation_info["field"])

        # Get the model class dynamically
        ModelClass = apps.get_model(app_label=app_name, model_name=model_name)

        # Start the query on ModelClass (not a QuerySet yet)
        queryset = ModelClass.objects.all()  # Create the base queryset

        # Apply filtering if provided
        if filterData:
            queryset = queryset.filter(**filterData)

        try:
            # Perform the query with dynamic group_by and annotations
            query = queryset.values(*group_by)  # Group by fields dynamically
            if annotation_args:
                query = query.annotate(**annotation_args)  # Apply dynamic annotations if present

            summary_data = query

            # Apply ordering if provided
            if order_by:
                summary_data = query.order_by(*order_by)

            # Apply limit if provided
            if limit and isinstance(limit, int):
                summary_data = summary_data[:limit]

            return Response(summary_data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# class GetChartData(APIView):
#     """depence on param send with report chart datas"""
#     @api_permission_required(models=["ReportTemplate"], action="view")
#     def put(self, request):
#         model_name = request.data.get("model_name", None)
#         app_name = request.data.get("app_name", None)
#         id = request.data.get("id", None)
#         if id:
#             report_model = ReportTemplate.objects.get(id=id)
#         group_by = request.data.get("group_by", [])
#         annotations = request.data.get("annotations", {})
#         filter_condition_report = request.data.get('filterData', None)
#         user_id = request.data.get("user_id", None)
#         if id:
#             ModelClass = apps.get_model(app_label=report_model.app, model_name=report_model.primary_model)
#         else:
#             ModelClass = apps.get_model(app_label=app_name, model_name=model_name)
            
#         annotation_args = {}
#         view_list = []  # List of fields for which we want to get aggregated data
#         label = []  # To store values of the group_by field (like months, salespersons, etc.)
#         filter_condition = {}

#         # Process annotations (Sum, Count, Avg, Min, Max)
#         for alias, annotation_info in annotations.items():
#             view_list.append(alias)
#             if annotation_info.get("type") == "Sum":
#                 annotation_args[alias] = Sum(annotation_info["field"])
#             elif annotation_info.get("type") == "Count":
#                 annotation_args[alias] = Count(annotation_info["field"])
#             elif annotation_info.get("type") == "Avg":
#                 annotation_args[alias] = Avg(annotation_info["field"])
#             elif annotation_info.get("type") == "Min":
#                 annotation_args[alias] = Min(annotation_info["field"])
#             elif annotation_info.get("type") == "Max":
#                 annotation_args[alias] = Max(annotation_info["field"])

#         try:
#             # Start querying the database
#             query = ModelClass.objects.all()
#             for condition in filter_condition_report:
#                 if condition['type'] == "date":
#                     condition_value = condition['conditionOption']['value']
#                     field_name = condition['field']
#                     if condition_value in ["week", "month", "financially"]:
#                         start_date, end_date = get_date_range(condition_value)
#                         filter_condition.update({f"{field_name}__range": [start_date, end_date]})
#                     elif condition_value == "today":
#                         # start_date, end_date = get_date_range(condition_value)
#                         if condition["isDate"]:
#                             filter_condition.update({f"{field_name}__date": datetime.now().date()})
#                         else:
#                             filter_condition.update({f"{field_name}": datetime.now().date()})

#                     elif condition_value == "custom":
#                         start_date = condition['conditionApplied']['start']
#                         end_date = condition['conditionApplied']['end']
#                         if start_date == end_date:
#                             # Apply direct match instead of range if dates are the same
#                             filter_condition.update({field_name: start_date})
#                         else:
#                             filter_condition.update({f"{field_name}__range": [start_date, end_date]})
#                     elif condition_value == "empty":
#                         filter_condition.update({f"{condition['field']}": True})

#                 elif condition['type'] == "bool":
#                     # Convert string to boolean
#                     value_str = str(condition['conditionApplied']['value']).strip().lower()
#                     if value_str == 'true':
#                         bool_value = True
#                     elif value_str == 'false':
#                         bool_value = False
#                     else:
#                         raise ValueError(f"Invalid boolean value: {value_str}")
#                     filter_condition.update({condition['field']: bool_value})
#                 elif condition['type'] == "text" and ("isMulti" in condition and not condition['isMulti']):
#                     if type(condition['conditionApplied']) == dict:
#                         condition['conditionApplied'] = condition['conditionApplied']['value']
#                     else:
#                         condition['conditionApplied'] = condition['conditionApplied']
#                     if condition['conditionOption']['value'] == "equal":
#                         filter_condition.update({f"{condition['field']}__icontains": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "notEqual":
#                         filter_condition.update({f"{condition['field']}__noticontains": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "isEmpty":
#                         filter_condition.update({f"{condition['field']}__isempty": ""})
#                     if condition['conditionOption']['value'] == "isNotEmpty":
#                         filter_condition.update({f"{condition['field']}__isnotempty": ""})
#                     if condition['conditionOption']['value'] == "userGroup":
#                         filter_condition.update(
#                             {f"{condition['field']}__group": condition['conditionApplied']['value']})
#                     if condition['conditionOption']['value'] == "default":
#                         filter_condition.update({f"{condition['field']}__default": user_id})
#                 elif condition['type'] == "text" and ("isMulti" in condition and condition['isMulti']):
#                     if condition['conditionOption']['value'] == "equal":
#                         filter_condition.update(
#                             {f"{condition['field']}__in": [data['value'] for data in condition['conditionApplied']]})
#                     if condition['conditionOption']['value'] == "notEqual":
#                         filter_condition.update(
#                             {f"{condition['field']}__notin": [data['value'] for data in condition['conditionApplied']]})
#                     if condition['conditionOption']['value'] == "isEmpty":
#                         filter_condition.update({f"{condition['field']}__isempty": ""})
#                     if condition['conditionOption']['value'] == "isNotEmpty":
#                         filter_condition.update({f"{condition['field']}__isnotempty": ""})
#                     if condition['conditionOption']['value'] == "userGroup":
#                         filter_condition.update(
#                             {f"{condition['field']}__group": condition['conditionApplied']['value']})
#                     if condition['conditionOption']['value'] == "default":
#                         filter_condition.update({f"{condition['field']}__default": user_id})

#                 elif condition['type'] == "number":
#                     if condition['conditionOption']['value'] == "lessThan":
#                         filter_condition.update({f"{condition['field']}__lt": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "greaterThan":
#                         filter_condition.update({f"{condition['field']}__gt": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "lessThanEqual":
#                         filter_condition.update({f"{condition['field']}__lte": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "greaterThanEqual":
#                         filter_condition.update({f"{condition['field']}__gte": condition['conditionApplied']})
#                     if condition['conditionOption']['value'] == "between":
#                         split_data = condition['conditionApplied'].split(',')
#                         start = int(split_data[0].replace("'", ""))
#                         end = int(split_data[1].replace("'", ""))
#                         filter_condition.update({f"{condition['field']}__range": (start, end)})
            
#             if ModelClass.__name__ in  active_model_list:
#                 query = query.filter(active=True)
#             if filter_condition:
#                 try:
#                     normal_filters = {}
#                     exclude_filters = {}
#                     isnull_filters = []
#                     not_isnull_filters = []
#                     for key, value in filter_condition.items():
#                         if key.endswith("__noticontains"):
#                             exclude_key = key.replace("__noticontains", "__icontains")
#                             exclude_filters[exclude_key] = value
#                         if key.endswith("__isnull"):
#                             normal_filters[f"{key}"] = True
#                         elif key.endswith("__isempty"):  # Handle "is empty"
#                             field_name = key.replace("__isempty", "")
#                             isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
#                         elif key.endswith("__isnotempty"):  # Handle "is not empty"
#                             field_name = key.replace("__isnotempty", "")
#                             not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
#                         elif key.endswith("__default"):
#                             exclude_key = key.replace("__default", "")
#                             normal_filters[str(exclude_key).split("__")[0]] = user_id
#                         elif key.endswith('__group'):
#                             field_name = key.replace("__group", "")
#                             users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
#                             field_name = str(field_name).split("__")[0]
#                             normal_filters[f"{field_name}__in"] = users_ids_list
#                         else:
#                             normal_filters[key] = value
#                         # Apply normal filters
#                         # active_model_list = ["SalesOrder_2","Leads","Quotations"]

            
#                     if normal_filters:
#                         query = query.filter(**normal_filters)

#                     # Apply exclude filters (for __noticontains)
#                     if exclude_filters:
#                         query = query.exclude(**exclude_filters)

#                     # Apply isnull (empty) filters
#                     for isnull_filter in isnull_filters:
#                         ModelClass = ModelClass.filter(isnull_filter)

#                     # Apply isnotnull (not empty) filters
#                     for not_isnull_filter in not_isnull_filters:
#                         ModelClass = ModelClass.filter(not_isnull_filter)
#                 except Exception as e:
#                     print("e--------->",e)
                

#             query = query.values(*group_by)
#             # Annotate query if annotations are specified
#             if annotation_args:
#                 query = query.annotate(**annotation_args)

#             # Initialize a list to store values for each field in view_list
#             combined_values = [[] for _ in view_list]

#             # Iterate over the query results
#             for data in query:
#                 # Extract the value for the group_by field
#                 for key, value in data.items():
#                     if key in group_by:
#                         label.append(value)

#                     # Now process the values for each annotation in view_list
#                     for idx, view_data in enumerate(view_list):
#                         if view_data == key:
#                             combined_values[idx].append(value)
#             value = {}
#             for index, edit in enumerate(view_list):
#                 value.update({edit: combined_values[index]})
#             result = {"label": label, "values": value}

#             return Response(result, status=200)

#         except Exception as e:
#             # In case of an error, return the exception details
#             return Response(str(e), status=500)



class GetChartData(APIView):
    """depence on param send with report chart datas"""
    @api_permission_required(models=["ReportTemplate"], action="view")
    def put(self, request):
        model_name = request.data.get("model_name", None)
        app_name = request.data.get("app_name", None)
        id = request.data.get("id", None)
        if id:
            report_model = ReportTemplate.objects.get(id=id)
        group_by = request.data.get("group_by", [])
        chart_date_format = request.data.get("chart_date_format", None)
        annotations = request.data.get("annotations", {})
        filter_condition_report = request.data.get('filterData', None)
        user_id = request.data.get("user_id", None)
        
        if id:
            ModelClass = apps.get_model(app_label=report_model.app, model_name=report_model.primary_model)
        else:
            ModelClass = apps.get_model(app_label=app_name, model_name=model_name)
            
        annotation_args = {}
        view_list = []
        label = []
        filter_condition = {}
        print("annotations", annotations)
        # Process annotations (Sum, Count, Avg, Min, Max)
        for alias, annotation_info in annotations.items():
            view_list.append(alias)
            if annotation_info.get("type") == "Sum":
                annotation_args[alias] = Sum(annotation_info["field"])
            elif annotation_info.get("type") == "Count":
                annotation_args[alias] = Count(annotation_info["field"])
            elif annotation_info.get("type") == "Avg":
                annotation_args[alias] = Avg(annotation_info["field"])
            elif annotation_info.get("type") == "Min":
                annotation_args[alias] = Min(annotation_info["field"])
            elif annotation_info.get("type") == "Max":
                annotation_args[alias] = Max(annotation_info["field"]) 
        
        try:
            # Start querying the database
            query = ModelClass.objects.all()
            
            # Apply filter conditions (same as your existing code)
            for condition in filter_condition_report:
                if condition['type'] == "date":
                    condition_value = condition['conditionOption']['value']
                    field_name = condition['field']
                    if condition_value in ["week", "month", "financially"]:
                        start_date, end_date = get_date_range(condition_value)
                        filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                    elif condition_value == "today":
                        if condition["isDate"]:
                            filter_condition.update({f"{field_name}__date": datetime.now().date()})
                        else:
                            filter_condition.update({f"{field_name}": datetime.now().date()})
                    elif condition_value == "custom":
                        start_date = condition['conditionApplied']['start']
                        end_date = condition['conditionApplied']['end']
                        if start_date == end_date:
                            filter_condition.update({field_name: start_date})
                        else:
                            filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                    elif condition_value == "empty":
                        filter_condition.update({f"{condition['field']}": True})

                elif condition['type'] == "bool":
                    value_str = str(condition['conditionApplied']['value']).strip().lower()
                    if value_str == 'true':
                        bool_value = True
                    elif value_str == 'false':
                        bool_value = False
                    else:
                        raise ValueError(f"Invalid boolean value: {value_str}")
                    filter_condition.update({condition['field']: bool_value})
                    
                elif condition['type'] == "text" and ("isMulti" in condition and not condition['isMulti']):
                    if type(condition['conditionApplied']) == dict:
                        condition['conditionApplied'] = condition['conditionApplied']['value']
                    else:
                        condition['conditionApplied'] = condition['conditionApplied']
                    if condition['conditionOption']['value'] == "equal":
                        filter_condition.update({f"{condition['field']}__icontains": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "notEqual":
                        filter_condition.update({f"{condition['field']}__noticontains": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "isEmpty":
                        filter_condition.update({f"{condition['field']}__isempty": ""})
                    if condition['conditionOption']['value'] == "isNotEmpty":
                        filter_condition.update({f"{condition['field']}__isnotempty": ""})
                    if condition['conditionOption']['value'] == "userGroup":
                        filter_condition.update(
                            {f"{condition['field']}__group": condition['conditionApplied']['value']})
                    if condition['conditionOption']['value'] == "default":
                        filter_condition.update({f"{condition['field']}__default": user_id})
                        
                elif condition['type'] == "text" and ("isMulti" in condition and condition['isMulti']):
                    if condition['conditionOption']['value'] == "equal":
                        filter_condition.update(
                            {f"{condition['field']}__in": [data['value'] for data in condition['conditionApplied']]})
                    if condition['conditionOption']['value'] == "notEqual":
                        filter_condition.update(
                            {f"{condition['field']}__notin": [data['value'] for data in condition['conditionApplied']]})
                    if condition['conditionOption']['value'] == "isEmpty":
                        filter_condition.update({f"{condition['field']}__isempty": ""})
                    if condition['conditionOption']['value'] == "isNotEmpty":
                        filter_condition.update({f"{condition['field']}__isnotempty": ""})
                    if condition['conditionOption']['value'] == "userGroup":
                        filter_condition.update(
                            {f"{condition['field']}__group": condition['conditionApplied']['value']})
                    if condition['conditionOption']['value'] == "default":
                        filter_condition.update({f"{condition['field']}__default": user_id})

                elif condition['type'] == "number":
                    if condition['conditionOption']['value'] == "lessThan":
                        filter_condition.update({f"{condition['field']}__lt": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "greaterThan":
                        filter_condition.update({f"{condition['field']}__gt": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "lessThanEqual":
                        filter_condition.update({f"{condition['field']}__lte": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "greaterThanEqual":
                        filter_condition.update({f"{condition['field']}__gte": condition['conditionApplied']})
                    if condition['conditionOption']['value'] == "between":
                        split_data = condition['conditionApplied'].split(',')
                        start = int(split_data[0].replace("'", ""))
                        end = int(split_data[1].replace("'", ""))
                        filter_condition.update({f"{condition['field']}__range": (start, end)})
            
            if ModelClass.__name__ in active_model_list:
                query = query.filter(active=True)
                
            if filter_condition:
                try:
                    normal_filters = {}
                    exclude_filters = {}
                    isnull_filters = []
                    not_isnull_filters = []
                    for key, value in filter_condition.items():
                        if key.endswith("__noticontains"):
                            exclude_key = key.replace("__noticontains", "__icontains")
                            exclude_filters[exclude_key] = value
                        if key.endswith("__isnull"):
                            normal_filters[f"{key}"] = True
                        elif key.endswith("__isempty"):
                            field_name = key.replace("__isempty", "")
                            isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                        elif key.endswith("__isnotempty"):
                            field_name = key.replace("__isnotempty", "")
                            not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                        elif key.endswith("__default"):
                            exclude_key = key.replace("__default", "")
                            normal_filters[str(exclude_key).split("__")[0]] = user_id
                        elif key.endswith('__group'):
                            field_name = key.replace("__group", "")
                            users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
                            field_name = str(field_name).split("__")[0]
                            normal_filters[f"{field_name}__in"] = users_ids_list
                        else:
                            normal_filters[key] = value

                    if normal_filters:
                        query = query.filter(**normal_filters)

                    if exclude_filters:
                        query = query.exclude(**exclude_filters)

                    for isnull_filter in isnull_filters:
                        query = query.filter(isnull_filter)

                    for not_isnull_filter in not_isnull_filters:
                        query = query.filter(not_isnull_filter)
                except Exception as e:
                    print("e--------->", e)

            # Handle date-based grouping
            date_field_annotation = {}
            modified_group_by = []
            
            if chart_date_format and group_by:
                for field in group_by:
                    # Check if this field is a date field that needs special grouping
                    field_obj = ModelClass._meta.get_field(field.split('__')[0])
                    
                    if field_obj.get_internal_type() in ['DateTimeField', 'DateField']:
                        # Add date truncation/extraction based on date_format
                        if chart_date_format == 'week':
                            # For Sunday-Saturday weeks, we need to extract week info differently
                            # Store the original date field for custom week calculation
                            date_field_annotation[f'{field}_date'] = F(field)
                            modified_group_by.append(f'{field}_date')
                        # Add date truncation/extraction based on chart_date_format
                        if chart_date_format == 'month':
                            # Group by Month and Year (e.g., "November 2025")
                            date_field_annotation[f'{field}_month'] = TruncMonth(field)
                            modified_group_by.append(f'{field}_month')
                        elif chart_date_format == 'year':
                            # Group by Year only
                            date_field_annotation[f'{field}_year'] = TruncYear(field)
                            modified_group_by.append(f'{field}_year')
                        elif chart_date_format == 'financial':
                            # Financial year grouping (April start)
                            # We'll extract year and month, then calculate FY in Python
                            date_field_annotation[f'{field}_year'] = ExtractYear(field)
                            date_field_annotation[f'{field}_month'] = ExtractMonth(field)
                            modified_group_by.extend([f'{field}_year', f'{field}_month'])
                    else:
                        # Non-date field, keep as is
                        modified_group_by.append(field)
            else:
                modified_group_by = group_by

            print("date_field_annotation",date_field_annotation)
            # Annotate with date truncation if needed
            if date_field_annotation:
                query = query.annotate(**date_field_annotation)

            # Group by the modified fields
            query = query.values(*modified_group_by)
            
            # Annotate query if annotations are specified
            if annotation_args:
                query = query.annotate(**annotation_args)

            # Initialize a list to store values for each field in view_list
            combined_values = [[] for _ in view_list]

            # Helper function to calculate Sunday-based week start
            def get_sunday_week_start(date_obj):
                """Get the Sunday of the week for a given date"""
                if isinstance(date_obj, datetime):
                    date_obj = date_obj.date() 
                # Get day of week (0=Monday, 6=Sunday)
                day_of_week = date_obj.weekday() 
                # Calculate days to subtract to get to Sunday
                # If Sunday (weekday=6), days_to_subtract=0
                # If Monday (weekday=0), days_to_subtract=1
                # If Saturday (weekday=5), days_to_subtract=6
                if day_of_week == 6:  # Sunday
                    days_to_subtract = 0
                else:
                    days_to_subtract = day_of_week + 1
                
                week_start = date_obj - timedelta(days=days_to_subtract)
                return week_start
            
            # Helper function to format date labels
            def format_date_label(data, field, date_format_type):
                if date_format_type == 'week':
                    date_value = data.get(f'{field}_date')
                    if date_value:
                        # Calculate Sunday-based week start and Saturday end
                        week_start = get_sunday_week_start(date_value)
                        week_end = week_start + timedelta(days=6)
                        
                        # Format as "Week 11/02 - 11/08, 2025"
                        return f"Week {week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}, {week_start.year}"
                if date_format_type == 'month':
                    date_value = data.get(f'{field}_month')
                    if date_value:
                        return date_value.strftime('%B %Y')  # e.g., "November 2025"
                elif date_format_type == 'year':
                    date_value = data.get(f'{field}_year')
                    if date_value:
                        return str(date_value.year)
                elif date_format_type == 'financial':
                    year = data.get(f'{field}_year')
                    month = data.get(f'{field}_month')
                    if year and month:
                        # Financial year starts in April (month 4)
                        if month >= 4:
                            return f"FY {year}-{year + 1}"
                        else:
                            return f"FY {year - 1}-{year}"
                return None

            # Iterate over the query results
            seen_labels = set()  # To avoid duplicate labels
            
            for data in query:  
                # Extract the value for the group_by field
                label_value = None
                
                if chart_date_format and group_by:
                    # Format date label based on chart_date_format
                    for field in group_by:
                        field_obj = ModelClass._meta.get_field(field.split('__')[0])
                        if field_obj.get_internal_type() in ['DateTimeField', 'DateField']:
                            label_value = format_date_label(data, field, chart_date_format)
                            break
                    
                    # If no date field found, use regular field value
                    if not label_value:
                        for key, value in data.items():
                            if key in group_by:
                                label_value = value
                                break
                else:
                    # Regular grouping (non-date)
                    for key, value in data.items():
                        if key in group_by or key in modified_group_by:
                            if key not in [f'{f}_month' for f in group_by] and \
                                key not in [f'{f}_year' for f in group_by]:
                                label_value = value
                                break

                # Add label only if it's unique (for financial year grouping)
                if label_value and label_value not in seen_labels:
                    label.append(label_value)
                    seen_labels.add(label_value)
                    
                    # Process the values for each annotation in view_list
                    for idx, view_data in enumerate(view_list):
                        if view_data in data:
                            combined_values[idx].append(data[view_data])
                elif label_value and label_value in seen_labels:
                    # Aggregate values for duplicate labels (financial year case)
                    label_idx = label.index(label_value)
                    for idx, view_data in enumerate(view_list):
                        if view_data in data:
                            # Sum up values for the same label
                            if label_idx < len(combined_values[idx]):
                                combined_values[idx][label_idx] += data[view_data]

            value = {}
            for index, edit in enumerate(view_list):
                value.update({edit: combined_values[index]})
            result = {"label": label, "values": value}

            return Response(result, status=200)

        except Exception as e:
            # In case of an error, return the exception details
            return Response(str(e), status=500)



class fetchFilterConditions(APIView):
    @api_permission_required(models=["ReportTemplate"], action="view")
    def put(self, request):
        model_name = request.data.get("model_name", None)
        app_name = request.data.get("app_name", None)
        id = request.data.get("id", None)
        if id:
            report_model = ReportTemplate.objects.get(id=id)
        fields = request.data.get("selectedData")
        limit = request.data.get('limit', 1)
        filterData = request.data.get("filterData", None)
        distinct_data = request.data.get("distinct", [])
        errors = []
        required_fields = ["selectedData"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if id:
            ModelClass = apps.get_model(app_label=report_model.app, model_name=report_model.primary_model)
        else:
            ModelClass = apps.get_model(app_label=app_name, model_name=model_name)
        ModelClass_ = ModelClass
        queryset = ModelClass.objects.all()
        # active_model_list = ["SalesOrder_2","Leads","Quotations"]
        if ModelClass.__name__ in active_model_list:
            queryset = queryset.filter(active=True)
        if "id" not in fields:
            fields.append("id")
        queryset = queryset.values(*fields)
        try:
            if filterData:
                try:
                    # Apply the filter by unpacking the dictionary
                    queryset = queryset.filter(**filterData)
                    if len(distinct_data) > 0:
                        distinct_data = [field.split('__')[0] for field in distinct_data]  # Extract field names
                        valid_fields = [f.name for f in ModelClass_._meta.fields]
                        distinct_data = [field for field in distinct_data if field in valid_fields]
                        try:
                            queryset = queryset.order_by(*distinct_data).distinct(*distinct_data)
                        except Exception as e:
                            errors.append(e)
                except Exception as e:
                    print(e)
            page_number = 1
            paginator = Paginator(queryset, limit)
            paginated_data = paginator.get_page(page_number)
            response_data = {
                "errors": errors,
                'results': list(paginated_data)  # The paginated data
            }
            return Response(response_data)
        except Exception as e:
            errors.append(e)


class GetReportEditData(APIView):
    """get report edit data"""
    @api_permission_required(models=["ReportTemplate"], action="view")
    def put(self, request):
        model_name = request.data.get("model_name", None)
        app_name = request.data.get("app_name", None)
        limit = request.data.get("limit", None)
        user_id = request.data.get("user_id", None)
        id = request.data.get("id")

        try:
            report_model = ReportTemplate.objects.get(id=id)
            if id:
                ModelClass = apps.get_model(app_label=report_model.app, model_name=report_model.primary_model)
            else:
                ModelClass = apps.get_model(app_label=app_name, model_name=model_name)
            select_data_value = report_model.select_data
            filter_condition_report = request.data.get("filter_condition", report_model.filter_conditions)
            filter_condition = {}
            processed_fields = {}
            def process_fields(fields):
                try:
                    updated_fields = []  # Create a new list to store processed fields
                    for field in fields:
                        field = field.copy()  # Prevent modifying the original dictionary
                        # field.pop('group_by', None)  # Remove group_by if present
                        if 'link_type' in field and (
                                field['link_type'] == 'ForeignKey' or field['link_type'] == 'ManyToManyField'):
                            link_table = field.get('link_table', [])
                            field['link_table'] = process_fields(link_table)  # Recurse
                            processed_fields[field['visible_name']] = field['link_table']
                        updated_fields.append(field)
                    return updated_fields
                except Exception as e:
                    print(e)

            # Remove child objects (those with 'link_type') and store others
            def remove_child_objects(fields):
                try:

                    processed_fields[model_data_fields[report_model.primary_model]] = [field for field in fields if
                                                                                       'link_type' not in field]

                except Exception as e:
                    print(e, "-----<<<")

            if id:
                models_fileds = getattr(Report_json_data, model_data_fields[report_model.primary_model], None)
            else:
                models_fileds = getattr(Report_json_data, model_data_fields[model_name], None)
            remove_child_objects(models_fileds)
            process_fields(models_fileds)
            for table in processed_fields:
                processed_fields[table] = [dict(field) for field in processed_fields[table]]  # Create new copies
                for file in processed_fields[table]:
                    file.pop('group_by', None)  # Remove safely from the copied version
                    file.pop('number', None)
            if isinstance(select_data_value, list):
                fields_array = [item.get('field') for item in select_data_value if 'field' in item]
            # if grouped_by : 
            #     fields_array.append(grouped_by.get('value')) 
            if fields_array:
                if "id" not in fields_array:
                    fields_array.append("id")

            queryset = ModelClass.objects.all()
            if ModelClass.__name__ in  active_model_list:
                queryset = queryset.filter(active=True)
            try:
                for condition in filter_condition_report:
                    if condition['type'] == "date":
                        condition_value = condition['conditionOption']['value']
                        field_name = condition['field']
                        if condition_value in ["week", "month", "financially"]:
                            start_date, end_date = get_date_range(condition_value)
                            filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                        elif condition_value == "today":
                            # start_date, end_date = get_date_range(condition_value)
                            if condition["isDate"]:
                                filter_condition.update({f"{field_name}__date": datetime.now().date()})
                            else:
                                filter_condition.update({f"{field_name}": datetime.now().date()})

                        elif condition_value == "custom":
                            start_date = condition['conditionApplied']['start']
                            end_date = condition['conditionApplied']['end']
                            if start_date == end_date:
                                # Apply direct match instead of range if dates are the same
                                filter_condition.update({field_name: start_date})
                            else:
                                filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                        elif condition_value == "empty":
                            filter_condition.update({f"{condition['field']}": True})

                    elif condition['type'] == "bool":
                        # Convert string to boolean
                        value_str = str(condition['conditionApplied']['value']).strip().lower()
                        if value_str == 'true':
                            bool_value = True
                        elif value_str == 'false':
                            bool_value = False
                        else:
                            raise ValueError(f"Invalid boolean value: {value_str}")
                        filter_condition.update({condition['field']: bool_value})

                    elif condition['type'] == "text" and ("isMulti" in condition and not condition['isMulti']):
                        if type(condition['conditionApplied']) == dict:
                            condition['conditionApplied'] = condition['conditionApplied']['value']
                        else:
                            condition['conditionApplied'] = condition['conditionApplied']
                        if condition['conditionOption']['value'] == "equal":
                            filter_condition.update({f"{condition['field']}__icontains": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "notEqual":
                            filter_condition.update(
                                {f"{condition['field']}__noticontains": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "isEmpty":
                            filter_condition.update({f"{condition['field']}__isempty": ""})
                        if condition['conditionOption']['value'] == "isNotEmpty":
                            filter_condition.update({f"{condition['field']}__isnotempty": ""})
                        if condition['conditionOption']['value'] == "userGroup":
                            filter_condition.update(
                                {f"{condition['field']}__group": condition['conditionApplied']['value']})
                        if condition['conditionOption']['value'] == "default":
                            filter_condition.update({f"{condition['field']}__default": user_id})
                    elif condition['type'] == "text" and ("isMulti" in condition and condition['isMulti']):
                        if condition['conditionOption']['value'] == "equal":
                            filter_condition.update(
                                {f"{condition['field']}__in": [data['value'] for data in
                                                               condition['conditionApplied']]})
                        if condition['conditionOption']['value'] == "notEqual":
                            filter_condition.update(
                                {f"{condition['field']}__notin": [data['value'] for data in
                                                                  condition['conditionApplied']]})
                        if condition['conditionOption']['value'] == "isEmpty":
                            filter_condition.update({f"{condition['field']}__isempty": ""})
                        if condition['conditionOption']['value'] == "isNotEmpty":
                            filter_condition.update({f"{condition['field']}__isnotempty": ""})
                        if condition['conditionOption']['value'] == "userGroup":
                            filter_condition.update(
                                {f"{condition['field']}__group": condition['conditionApplied']['value']})
                        if condition['conditionOption']['value'] == "default":
                            filter_condition.update({f"{condition['field']}__default": user_id})

                    elif condition['type'] == "number":
                        if condition['conditionOption']['value'] == "lessThan":
                            filter_condition.update({f"{condition['field']}__lt": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "greaterThan":
                            filter_condition.update({f"{condition['field']}__gt": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "lessThanEqual":
                            filter_condition.update({f"{condition['field']}__lte": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "greaterThanEqual":
                            filter_condition.update({f"{condition['field']}__gte": condition['conditionApplied']})
                        if condition['conditionOption']['value'] == "between":
                            split_data = condition['conditionApplied'].split(',')
                            start = int(split_data[0].replace("'", ""))
                            end = int(split_data[1].replace("'", ""))
                            filter_condition.update({f"{condition['field']}__range": (start, end)})

                if filter_condition:
                    normal_filters = {}
                    exclude_filters = {}
                    isnull_filters = []
                    not_isnull_filters = []
                    for key, value in filter_condition.items():
                        if key.endswith("__noticontains"):
                            exclude_key = key.replace("__noticontains", "__icontains")
                            exclude_filters[exclude_key] = value
                        elif key.endswith("__isempty"):  # Handle "is empty"
                            field_name = key.replace("__isempty", "")
                            isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                        elif key.endswith("__isnotempty"):  # Handle "is not empty"
                            field_name = key.replace("__isnotempty", "")
                            not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                        elif key.endswith("__default"):
                            exclude_key = key.replace("__default", "")
                            normal_filters[str(exclude_key).split("__")[0]] = user_id
                        elif key.endswith('__group'):
                            field_name = key.replace("__group", "")
                            users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
                            field_name = str(field_name).split("__")[0]
                            normal_filters[f"{field_name}__in"] = users_ids_list
                        else:
                            normal_filters[key] = value
                        # Apply normal filters
                    try:
                        if normal_filters:
                            queryset = queryset.filter(**normal_filters)

                    except  Exception as e:
                        print(e, "---")

                    # Apply exclude filters (for __noticontains)
                    if exclude_filters:
                        queryset = queryset.exclude(**exclude_filters)
                    # active_model_list = ["SalesOrder_2","Quotations","Lead"]
                    if ModelClass.__name__ in active_model_list:
                        queryset = queryset.filter(active=True)
            except Exception as e:
                print("Exception------", e)

            if limit:
                queryset = queryset[:int(limit)]
            else:
                queryset = queryset
            queryset = queryset.values(*fields_array)

            report_model_dict = json.loads(serialize('json', [report_model]))[0][
                'fields']  # Extract fields from serialized JSON
            report_model_dict['selected_row_data'] = list(queryset)
            report_model_dict['selected_row_data_length'] = len(queryset)
            # print("processed_fields",processed_fields)
            report_model_dict['model_fields'] = processed_fields
            report_model_dict['model_list'] = Tables  

            return Response(report_model_dict, status=status.HTTP_200_OK)
        except ReportTemplate.DoesNotExist:
            return Response({"error": "ReportTemplate not found."}, status=404)  # If report not found, return 404
        except Exception as e:
            print(e, "---->>")
            return Response({"error": "An error occurred."}, status=500)


def build_filter_conditions(filter_conditions, user_id):
    filter_condition = {}
    for condition in filter_conditions:
        if "sales_person" not in condition['field']:
           if condition['type'] == "date":
                   condition_value = condition['conditionOption']['value']
                   field_name = condition['field']
                   if condition_value in ["week", "month", "financially"]:
                       start_date, end_date = get_date_range(condition_value)
                       filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                   elif condition_value == "today":
                       # start_date, end_date = get_date_range(condition_value)
                       if condition["isDate"]:
                           filter_condition.update({f"{field_name}__date": datetime.now().date()})
                       else:
                           filter_condition.update({f"{field_name}": datetime.now().date})
                   elif condition_value == "custom":
                       start_date = condition['conditionApplied']['start']
                       end_date = condition['conditionApplied']['end']
                       if start_date == end_date:
                           # Apply direct match instead of range if dates are the same
                           filter_condition.update({field_name: start_date})
                       else:
                           filter_condition.update({f"{field_name}__range": [start_date, end_date]})
                   elif condition_value == "empty":
                       filter_condition.update({f"{condition['field']}": True})
               
           elif condition['type'] == "bool":
               # Convert string to boolean
               value_str = str(condition['conditionApplied']['value']).strip().lower()
               if value_str == 'true':
                   bool_value = True
               elif value_str == 'false':
                   bool_value = False
               else:
                   raise ValueError(f"Invalid boolean value: {value_str}")
               filter_condition.update({condition['field']: bool_value})
           
           elif condition['type'] == "text" and ("isMulti" in condition and not condition['isMulti']):
               if type(condition['conditionApplied']) == dict:
                   condition['conditionApplied'] = condition['conditionApplied']['value']
               else:
                   condition['conditionApplied'] = condition['conditionApplied']
               if condition['conditionOption']['value'] == "equal":
                   filter_condition.update({f"{condition['field']}__icontains": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "notEqual":
                   filter_condition.update({f"{condition['field']}__noticontains": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "isEmpty":
                   filter_condition.update({f"{condition['field']}__isempty": ""})
               if condition['conditionOption']['value'] == "isNotEmpty":
                   filter_condition.update({f"{condition['field']}__isnotempty": ""})
               if condition['conditionOption']['value'] == "userGroup":
                   filter_condition.update(
                       {f"{condition['field']}__group": condition['conditionApplied']['value']})
               if condition['conditionOption']['value'] == "default":
                   filter_condition.update({f"{condition['field']}__default": user_id})
           elif condition['type'] == "text" and ("isMulti" in condition and condition['isMulti']):
               if condition['conditionOption']['value'] == "equal":
                   filter_condition.update(
                       {f"{condition['field']}__in": [data['value'] for data in condition['conditionApplied']]})
               if condition['conditionOption']['value'] == "notEqual":
                   filter_condition.update(
                       {f"{condition['field']}__notin": [data['value'] for data in condition['conditionApplied']]})
               if condition['conditionOption']['value'] == "isEmpty":
                   filter_condition.update({f"{condition['field']}__isempty": ""})
               if condition['conditionOption']['value'] == "isNotEmpty":
                   filter_condition.update({f"{condition['field']}__isnotempty": ""})
               if condition['conditionOption']['value'] == "userGroup":
                   filter_condition.update(
                       {f"{condition['field']}__group": condition['conditionApplied']['value']})
               if condition['conditionOption']['value'] == "default":
                   filter_condition.update({f"{condition['field']}__default": user_id})
           elif condition['type'] == "number":
               if condition['conditionOption']['value'] == "lessThan":
                   filter_condition.update({f"{condition['field']}__lt": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "greaterThan":
                   filter_condition.update({f"{condition['field']}__gt": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "lessThanEqual":
                   filter_condition.update({f"{condition['field']}__lte": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "greaterThanEqual":
                   filter_condition.update({f"{condition['field']}__gte": condition['conditionApplied']})
               if condition['conditionOption']['value'] == "between":
                   split_data = condition['conditionApplied'].split(',')
                   start = int(split_data[0].replace("'", ""))
                   end = int(split_data[1].replace("'", ""))
                   filter_condition.update({f"{condition['field']}__range": (start, end)})

    return filter_condition       


class GetDashboardChartData(APIView):
    def put(self, request):
        try:
            report_folder_name = request.data.get("report_folder", None)
            user_id = request.data.get("user_id",None)
            filter_condition_apply =request.data.get("filterConditionData",None)
            if not report_folder_name:
                return Response({"error": "Missing 'report_folder' parameter."}, status=status.HTTP_400_BAD_REQUEST)

            if not user_id:
                return Response({"error": "Missing 'user_id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

            user_manaagement = UserManagement.objects.filter(user=user_id).first()
            templates = ReportTemplate.objects.filter(report_folder=report_folder_name)
            results = []

            for template in templates:
                app_label = template.app
                model_name = template.primary_model
                group_by = template.x_axis.get("value") if template.x_axis else None
                filter_conditions =template.filter_conditions if template.filter_conditions else None

                try:
                    ModelClass = apps.get_model(app_label=app_label, model_name=model_name)
                except LookupError as le:
                    print(f"Model lookup failed: {le}")
                    continue
               
                # 1. Prepare annotations and view_list
                annotations = {}
                view_list = []
                filter_condition = {}

                for field in template.y_axis:
                    field_name = field.get("value")
                    function = field.get("functions")
                    if field_name and function:
                        alias = f"{field_name}_{function.lower()}"
                        annotations[alias] = {
                            "type": function,
                            "field": field_name
                        }

                annotation_args = {}

                for alias, annotation_info in annotations.items():
                    view_list.append(alias)
                    func_type = annotation_info.get("type")
                    target_field = annotation_info.get("field")
                    if func_type == "Sum":
                        annotation_args[alias] = Sum(target_field)
                    elif func_type == "Count":
                        annotation_args[alias] = Count(target_field)
                    elif func_type == "Avg":
                        annotation_args[alias] = Avg(target_field)
                    elif func_type == "Min":
                        annotation_args[alias] = Min(target_field)
                    elif func_type == "Max":
                        annotation_args[alias] = Max(target_field)

                # 2. Query the data
                queryset = ModelClass.objects.all()

                if not user_manaagement or (not user_manaagement.sales_person and not user_manaagement.admin):
                    return Response(
                        {"error": "You have No Permission to View Dashboard Details"})
                # Apply filter if the user is a sales person
                if user_manaagement and user_manaagement.sales_person:
                    queryset = queryset.filter(sales_person__id=user_id)

                if filter_conditions :
                    filter_condition = build_filter_conditions(filter_conditions, user_id)

                if ModelClass.__name__ in  active_model_list:
                    queryset = queryset.filter(active=True)

                if filter_condition:
                    normal_filters = {}
                    exclude_filters = {}
                    isnull_filters = []
                    not_isnull_filters = []
                    for key, value in filter_condition.items():
                        if key.endswith("__noticontains"):
                            exclude_key = key.replace("__noticontains", "__icontains")
                            exclude_filters[exclude_key] = value
                        if key.endswith("__isnull"):
                            normal_filters[f"{key}"] = True
                        elif key.endswith("__isempty"):  # Handle "is empty"
                            field_name = key.replace("__isempty", "")
                            isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                        elif key.endswith("__isnotempty"):  # Handle "is not empty"
                            field_name = key.replace("__isnotempty", "")
                            not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                        elif key.endswith("__default"):
                            exclude_key = key.replace("__default", "")
                            normal_filters[str(exclude_key).split("__")[0]] = user_id
                        elif key.endswith('__group'):
                            field_name = key.replace("__group", "")
                            users_ids_list = [user.user.id for user in UserManagement.objects.filter(user_group=value)]
                            field_name = str(field_name).split("__")[0]
                            normal_filters[f"{field_name}__in"] = users_ids_list
                        else:
                            normal_filters[key] = value
                    try:
                        if normal_filters:
                            queryset = queryset.filter(**normal_filters)

                        # Apply exclude filters (for __noticontains)
                        if exclude_filters:
                            queryset = queryset.exclude(**exclude_filters)
                            # print("result",result)

                        # Apply isnull (empty) filters
                        for isnull_filter in isnull_filters:
                            ModelClass = ModelClass.filter(isnull_filter)

                        # Apply isnotnull (not empty) filters
                        for not_isnull_filter in not_isnull_filters:
                            ModelClass = ModelClass.filter(not_isnull_filter)

                    except Exception as e:
                        print(e)
                if filter_condition_apply:
                    created_at_field = created_at_fields.get(ModelClass.__name__, None)
                    if created_at_field:
                        try:
                            # If monthValue exists, apply it and skip financialYearValue
                            month_data = filter_condition_apply.get("monthValue", {})
                            fy_data = filter_condition_apply.get("financialYearValue", {})

                            month_start = month_data.get("start")
                            month_end = month_data.get("end")
                            fy_start = fy_data.get("fromDate")
                            fy_end = fy_data.get("toDate")

                            # Validate and prioritize month range
                            if month_start and month_end:
                                queryset = queryset.filter(**{
                                    f"{created_at_field}__range": [month_start, month_end]
                                })
                            elif fy_start and fy_end:
                                queryset = queryset.filter(**{
                                    f"{created_at_field}__range": [fy_start, fy_end]
                                })

                            # Apply salespersonValue only for admin users
                            if user_manaagement and  user_manaagement.admin:
                                salesperson_value = filter_condition_apply.get("salespersonValue", {}).get("value")
                                if salesperson_value:
                                    queryset = queryset.filter(sales_person__id=salesperson_value)
                        except Exception as e:
                            print("e--------->",e)
                    else:
                        return Response({"error": f"Missing created_at_field for '{template.primary_model}'."})

                if group_by:
                    query = queryset.values(group_by).annotate(**annotation_args)
                else:
                    query = queryset.aggregate(**annotation_args)
                    results.append({
                        "report_name": template.report_name,
                        "chart":template.chart,
                        "app_name":app_label,
                        "model_name": model_name,
                        "aggregates": query,
                    })
                    continue
                # 3. Organize results for grouped view
                label = []
                combined_values = [[] for _ in view_list]
                for row in query:
                    # Group label
                    label.append(row.get(group_by))

                    # Values per aggregation field
                    for idx, view_data in enumerate(view_list):
                        combined_values[idx].append(row.get(view_data))

                values = {view_list[i]: combined_values[i] for i in range(len(view_list))}
                result = {
                    "report_name": template.report_name,
                    "app_name":app_label,
                    "model_name":model_name,
                    "chart":template.chart,
                    "id":template.id,
                    "label": label,
                    "values": values,
                }

                results.append(result)

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            print("Exception ---->", e)
            return Response({"error": "Error in Dashboard Fetch", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetDashboardTargetData(APIView):
    def put(self, request):
        try:
            user_id = request.data.get("user_id", None)
            filter_condition_apply = request.data.get("filterConditionData", {})
            fy_data = filter_condition_apply.get("financialYearValue", {})
            fy_start = fy_data.get("fromDate")
            fy_end = fy_data.get("toDate")

            user_mgmt = UserManagement.objects.filter(user=user_id).first()
            if not user_mgmt or (not user_mgmt.sales_person and not user_mgmt.admin):
                    return Response(
                        {"error": "You have No Permission to View Dashboard Details"})
            
            # Fallback to current financial year if not provided
            if not fy_start or not fy_end:
                today = date.today()
                current_year = today.year
                if today.month < 4:
                    fy_start = date(current_year - 1, 4, 1)
                    fy_end = date(current_year, 3, 31)
                else:
                    fy_start = date(current_year, 4, 1)
                    fy_end = date(current_year + 1, 3, 31)
            else:
                fy_start = datetime.strptime(fy_start, "%Y-%m-%d").date()
                fy_end = datetime.strptime(fy_end, "%Y-%m-%d").date()

            # Extract selected month (1 to 12) from 'value'
            month_data = filter_condition_apply.get("monthValue", {})
            selected_month = int(month_data.get("value")) if month_data.get("value") else None

            salesperson_id = filter_condition_apply.get("salespersonValue", {}).get("value")
            target_achievement_list = []

            if user_mgmt and user_mgmt.sales_person:
                # Regular Salesperson
                target_instance = Target.objects.filter(
                    target_sales_person__sales_person__id=user_id,
                    financial_year_start=fy_start,
                    financial_year_end=fy_end
                ).first()

                if not target_instance:
                    return Response([], status=200)

                for sp in target_instance.target_sales_person.all():
                    if sp.sales_person.id != user_id:
                        continue

                    target_achievement_month = []
                    for tm in sp.target_months.all():
                        if selected_month and tm.month != selected_month:
                            continue
                        achievement = tm.target_achievement or Decimal("0.00")
                        target_achievement_month.append({
                            "month": tm.month,
                            "target_value": float(tm.target_value),
                            "target_achievement": float(achievement),
                        })

                    target_achievement_list.append({
                        "salesperson_name": sp.sales_person.username,
                        "salesperson_id":sp.sales_person.id,
                        "role": sp.role.role_name,
                        "ishead": sp.is_head,
                        "financial_year_start":fy_start,
                        "financial_year_end":fy_end,
                        "target": target_achievement_month
                    })

            elif user_mgmt and user_mgmt.admin:
                # Admin
                monthly_summary = {month: {
                    "month": month,
                    "target_value": 0.0,
                    "target_achievement": 0.0
                } for month in range(1, 13)}

                targets = Target.objects.filter(
                    financial_year_start=fy_start,
                    financial_year_end=fy_end
                ).prefetch_related("target_sales_person__target_months")

                for target in targets:
                    for sp in target.target_sales_person.all():
                        if salesperson_id and str(sp.sales_person.id) != str(salesperson_id):
                            continue
                        for tm in sp.target_months.all():
                            if selected_month and tm.month != selected_month:
                                continue
                            monthly_summary[tm.month]["target_value"] += float(tm.target_value or 0.0)
                            monthly_summary[tm.month]["target_achievement"] += float(tm.target_achievement or 0.0)

                monthly_target_list = sorted(
                    [v for v in monthly_summary.values() if not selected_month or v["month"] == selected_month],
                    key=lambda x: x["month"]
                )

                target_achievement_list.append({
                    "salesperson_name": "All Salespersons",
                    "role": "Admin",
                    "ishead": False,
                    "financial_year_start":fy_start,
                    "financial_year_end":fy_end,
                    "target": monthly_target_list
                })

            return Response(target_achievement_list, status=200)

        except Exception as e:
            print("Error:", e)
            return Response({"error": str(e)}, status=500)


class HsnCreateView(APIView):
    def get(self, request):
        article = Hsn.objects.all().order_by('-id')
        serialzer = HsnSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = HsnSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HsnDetails(APIView):
    def get_object(self, pk):
        try:
            return Hsn.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = HsnSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = HsnSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemGroupCreateView(APIView):
    def get(self, request):
        article = Item_Groups_Name.objects.all().order_by('-id').filter(is_delete=False)
        serialzer = ItemGroupSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemGroupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemGroupDetails(APIView):
    def get_object(self, pk):
        try:
            return Item_Groups_Name.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemGroupSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemGroupSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UOMCreateView(APIView):
    def get(self, request):
        article = UOM.objects.all().order_by('-id').filter(is_delete=False)
        serialzer = UOMSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = UOMSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UOMDetails(APIView):
    def get_object(self, pk):
        try:
            return UOM.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = UOMSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = UOMSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryCreateView(APIView):
    def get(self, request):
        article = Category.objects.all().order_by('-id')
        serialzer = CategorySerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountsGroupCreateView(APIView):
    def get(self, request):
        article = AccountsGroup.objects.all().order_by('-id').filter(is_delete=False)
        serialzer = AccountsGroupSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = AccountsGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountsGroupDetails(APIView):
    def get_object(self, pk):
        try:
            return AccountsGroup.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = AccountsGroupSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = AccountsGroupSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # If the deletion is protected, handle the exception
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountsMasterCreateView(APIView):
    def get(self, request):
        article = AccountsMaster.objects.all().order_by('-id').filter(is_delete=False)
        serialzer = AccountsMasterSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = AccountsMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountsMasterDetails(APIView):
    def get_object(self, pk):
        try:
            return AccountsMaster.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = AccountsMasterSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = AccountsMasterSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlternateUnitCreateView(APIView):
    def get(self, request):
        article = Alternate_unit.objects.all().order_by('-id')
        serialzer = Alternate_unitSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = Alternate_unitSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlternateUnitDetails(APIView):
    def get_object(self, pk):
        try:
            return Alternate_unit.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = Alternate_unitSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = Alternate_unitSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemMasterCreateView(APIView):
    def get(self, request):
        article = ItemMaster.objects.all().order_by('-id')
        serialzer = ItemMasterSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemMasterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemMasterDetails(APIView):
    def get_object(self, pk):
        try:
            return ItemMaster.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemMasterSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemMasterSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""Store"""


class StoreCreateView(APIView):

    def get(self, request):
        article = Store.objects.all().order_by('-id').filter(is_delete=False)
        serialzer = StoreSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDetails(LoginRequiredMixin, APIView):
    def get_object(self, pk):
        try:
            return Store.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = StoreSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = StoreSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockSerialHistoryCreateView(APIView):
    def get(self, request):
        article = StockSerialHistory.objects.all().order_by('-id')
        serialzer = StockSerialHistorySerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = StockSerialHistorySerializer(data=request.data)
        # print(serializer, '---->>>')
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockSerialHistoryDetails(APIView):
    def get_object(self, pk):
        try:
            return StockSerialHistory.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = StockSerialHistorySerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = StockSerialHistorySerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchNumberCreateView(APIView):
    def get(self, request):
        article = BatchNumber.objects.all().order_by('id')
        serialzer = BatchNumberSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = BatchNumberSerializer(data=request.data)
        # print(serializer)
        #
        if serializer.is_valid():
            serializer.save()
            serializer.save()

            return Response(serializer.data, )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BatchNumberDetails(APIView):
    def get_object(self, pk):
        try:
            return BatchNumber.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = BatchNumberSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = BatchNumberSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SerialNumbersCreateView(APIView):
    def get(self, request):
        article = SerialNumbers.objects.all().order_by('id')
        serialzer = SerialNumbersSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = SerialNumbersSerializer(data=request.data)
        # print(serializer)

        if serializer.is_valid():
            serializer.save()
            serializer.save()

            return Response(serializer.data, )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SerialNumbersDetails(APIView):
    def get_object(self, pk):
        try:
            return SerialNumbers.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = SerialNumbersSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = SerialNumbersSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemStockCreateView(APIView):
    def get(self, request):
        article = ItemStock.objects.all().order_by('-id')
        serialzer = ItemStockSerializer(article, many=True)

        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemStockSerializer(data=request.data)
        # print(serializer.is_valid())
        # print(serializer.errors)
        # print(serializer)

        if serializer.is_valid():
            serializer.save()
            serializer.save()

            return Response(serializer.data, )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockDetails(APIView):
    def get_object(self, pk):
        try:
            return ItemStock.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemStockSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemStockSerializer(article, data=request.data)
        # print(serializer)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockHistoryLogCreateView(APIView):
    def get(self, request):
        article = StockHistoryLog.objects.all().order_by('-id')
        serialzer = StockHistoryLogSerializer(article, many=True)

        return Response(serialzer.data)


class ItemInventoryApprovalCreateView(APIView):
    def get(self, request):
        article = ItemInventoryApproval.objects.all().order_by('id')
        serialzer = ItemInventoryApprovalSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemInventoryApprovalSerializer(data=request.data)
        # print(serializer)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryHandlerCreateView(APIView):
    def get(self, request):
        article = InventoryHandler.objects.all().order_by('-id')
        serialzer = InventoryHandlerSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = InventoryHandlerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryHandlerDetails(APIView):
    def get_object(self, pk):
        try:
            return InventoryHandler.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = InventoryHandlerSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = InventoryHandlerSerializer(article, data=request.data)
        # print(serializer)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class displayGroupCreateView(APIView):
    def get(self, request):
        article = display_group.objects.all().order_by('-id')
        serialzer = displayGroupSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = displayGroupSerializer(data=request.data)
        # print(serializer)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class displayGroupDetails(APIView):
    def get_object(self, pk):
        try:
            return display_group.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = displayGroupSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = displayGroupSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemComboCreateView(APIView):
    def get(self, request):
        article = Item_Combo.objects.all().order_by('-id')
        serialzer = ItemComboSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemComboSerializer(data=request.data)
        # print(serializer)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemComboDetails(APIView):
    def get_object(self, pk):
        try:
            return Item_Combo.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemComboSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemComboSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerGroupCreateView(APIView):
    def get(self, request):
        article = CustomerGroups.objects.all().order_by('-id')
        serialzer = CustomerGroupsSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = CustomerGroupsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerGroupDetails(APIView):
    def get_object(self, pk):
        try:
            return CustomerGroups.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = CustomerGroupsSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = CustomerGroupsSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierGroupCreateView(APIView):
    def get(self, request):
        article = SupplierGroups.objects.all().order_by('-id')
        serialzer = SupplierGroupsSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = SupplierGroupsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierGroupDetails(APIView):
    def get_object(self, pk):
        try:
            return SupplierGroups.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = SupplierGroupsSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = SupplierGroupsSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemContactCreateView(APIView):
    def get(self, request):
        article = ContactDetalis.objects.all().order_by('-id')
        serialzer = ItemContactSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemContactDetails(APIView):
    def get_object(self, pk):
        try:
            return ContactDetalis.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemContactSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemContactSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemAddressCreateView(APIView):
    def get(self, request):
        article = CompanyAddress.objects.all().order_by('-id')
        serialzer = ItemAddressSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ItemAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemAddressDetails(APIView):
    def get_object(self, pk):
        try:
            return CompanyAddress.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemAddressSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemAddressSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            # print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemSupplierFormCreateView(APIView):

    def get(self, request):
        articles = SupplierFormData.objects.all().order_by('-id')
        serializer = ItemSupplierSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ItemSupplierSerializer(data=request.data)
        # print(serializer.is_valid())
        # print(serializer.errors)
        # print(serializer)

        if serializer.is_valid():
            # try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # except Exception as e:
        #     print(e)
        #
        #
        #     return Response(error, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemSupplierFormDetails(APIView):
    def get_object(self, pk):
        try:
            return SupplierFormData.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemSupplierSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ItemSupplierSerializer(article, data=request.data)
        # print(serializer.is_valid())
        # print(serializer.errors)
        # print(serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrencyMasterCreateView(APIView):
    def get(self, request):
        article = CurrencyMaster.objects.all().order_by('-id')
        serialzer = CurrencyMasterSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = CurrencyMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrencyMasterDetails(APIView):
    def get_object(self, pk):
        try:
            return CurrencyMaster.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = CurrencyMasterSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = CurrencyMasterSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrencyExchangeCreateView(APIView):
    def get(self, request):
        article = CurrencyExchange.objects.all().order_by('-id')
        serialzer = CurrencyExchangeSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = CurrencyExchangeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrencyExchangeDetails(APIView):
    def get_object(self, pk):
        try:
            Currency = CurrencyExchange.objects.get(pk=pk)
            # print(Currency,)
            return Currency
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = CurrencyExchangeSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = CurrencyExchangeSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesOrderItemCreateView(APIView):
    def get(self, request):
        article = SalesOrderItem.objects.all().order_by('-id')
        serialzer = SalesOrderItemSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = SalesOrderItemSerializer(data=request.data)
        # print(serializer)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalesOrderItemDetails(APIView):
    def get_object(self, pk):
        try:
            return SalesOrderItem.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = SalesOrderItemSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = SalesOrderItemSerializer(article, data=request.data)
        # print(serializer)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            # print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentModeCreateView(APIView):
    def get(self, request):
        article = paymentMode.objects.all().order_by('-id')
        serialzer = PaymentModeSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = PaymentModeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentModeDetails(APIView):
    def get_object(self, pk):
        try:
            # print(pk)
            # print("try")
            return paymentMode.objects.get(pk=pk)
        except Exception as e:
            print(e)
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = PaymentModeSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = PaymentModeSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            # print(pk)
            # print(article)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ProtectedError as e:
            print("=====>", e)
            error_message = "This data is linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("=====>", e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesOrderCreateView(APIView):
    def get(self, request):
        article = SalesOrder.objects.all().order_by('-id').values("OrderDate", "IsPOS")
        paginator = Paginator(article, 10)
        paginated_data = paginator.get_page(1)
        # Prepare the response data
        response_data = {
            'count': paginator.count,  # Total number of records
            'num_pages': paginator.num_pages,  # Total number of pages
            'has_next': paginated_data.has_next(),  # Check if there is a next page
            'has_previous': paginated_data.has_previous(),  # Check if there is a previous page
            'results': list(paginated_data)  # The paginated data
        }
        return Response(response_data)

    def post(self, request):
        # print(request.data)
        serializer = SalesOrderSerializer(data=request.data)
        # print(serializer.is_valid())
        # print(serializer.errors)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalesOrderDetails(APIView):
    def get_object(self, pk):
        try:
            return SalesOrder.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = SalesOrderSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):

        article = self.get_object(pk)
        serializer = SalesOrderSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk) 
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 

class NumberingSeriesCreateView(APIView):

    def get(self, request):
        article = NumberingSeries.objects.all().order_by('-id')
        serialzer = NumberingSeriesSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):

        for singleSeries in NumberingSeries.objects.all().filter(
                resource=request.data['resource']):
            if singleSeries.resource == "Pos":
                if singleSeries.pos_type__ReSourceIsPosType == "Sample":
                    if singleSeries.Default:
                        singleSeries.Default = False
                        singleSeries.save()
                elif singleSeries.pos_type__ReSourceIsPosType == "Sales":
                    if singleSeries.Default:
                        singleSeries.Default = False
                        singleSeries.save()

        article = NumberingSeries.objects.all().order_by('-id').filter(is_delete=False)
        Change_Data = NumberingSeriesSerializer(article, many=True)
        serializer = NumberingSeriesSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(Change_Data.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NumberingSeriesDetails(APIView):
    def get_object(self, pk):
        try:
            return NumberingSeries.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = NumberingSeriesSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = NumberingSeriesSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinishedGoodsCreateView(APIView):
    def get(self, request):
        article = FinishedGoods.objects.all().order_by('-id')
        # print(article)
        serialzer = FinishedGoodsSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = FinishedGoodsSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinishedGoodsDetails(APIView):
    def get_object(self, pk):
        try:
            return FinishedGoods.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = FinishedGoodsSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = FinishedGoodsSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RawMaterialCreateView(APIView):
    def get(self, request):
        article = RawMaterial.objects.all().order_by('-id')
        serialzer = RawMaterialSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = RawMaterialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RawMaterialDetails(APIView):
    def get_object(self, pk):
        try:
            return RawMaterial.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = RawMaterialSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk=None, id_list=None):
        if pk:
            article = self.get_object(pk)
            serializer = RawMaterialSerializer(article, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        if id_list:
            print(id_list)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScrapCreateView(APIView):
    def get(self, request):
        article = Scrap.objects.all().order_by('-id')
        serialzer = ScrapSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = ScrapSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScrapDetails(APIView):
    def get_object(self, pk):
        try:
            return Scrap.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ScrapSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = ScrapSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoutingCreateView(APIView):
    def get(self, request):
        article = Routing.objects.all().order_by('-id')
        serialzer = RoutingSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = RoutingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BomCreateView(APIView):
    def get(self, request):
        article = Bom.objects.all().order_by('-id')
        serialzer = BomSerializer(article, many=True)
        return Response(serialzer.data)

    def post(self, request):
        serializer = BomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BomDetails(APIView):
    def get_object(self, pk):
        try:
            return Bom.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = BomSerializer(article)
        return Response(serialzer.data)

    def put(self, request, pk):
        article = self.get_object(pk)
        serializer = BomSerializer(article, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            article = self.get_object(pk)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            print(e)
            error_message = "This data Linked with other modules"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #         # Handle other exceptions
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def process_stock_statement(store_id=None, group_id=None):
    item_master_data = list(ItemMaster.objects.values('id', 'Item_PartCode', 'Item_name', 'Item_Group'))
    store_data = {item['id']: item['StoreName'] for item in list(Store.objects.values('id', 'StoreName'))}
    stock_data = list(ItemStock.objects.values('id', 'part_no', 'currentStock', 'store'))
    item_group_data = {item['id']: item['name'] for item in list(Item_Groups_Name.objects.values('id', 'name'))}
    filtered_master_items = []
    for item in item_master_data:
        part_no = item['id']
        data_result = {
            'part_no': part_no,
            'part_code': item['Item_PartCode'],
            'part_name': item['Item_name'],
            'item_group': item_group_data[item['Item_Group']]
        }
        if store_id is None:
            filtered_data = [(int(stock_item['currentStock']), stock_item['store']) for stock_item in stock_data if
                             stock_item['part_no'] == part_no]
        else:
            filtered_data = [(int(stock_item['currentStock']), stock_item['store']) for stock_item in stock_data if
                             stock_item['part_no'] == part_no and int(stock_item['store']) == int(store_id)]
        sum_of_stocks_in_store = 0
        stores = ''
        store_ids = []
        if filtered_data:
            sum_of_stocks_in_store = sum(item[0] for item in filtered_data if len(item) > 1)
            store_ids = list(set([item[1] for item in filtered_data if len(item) > 1]))
            try:
                stores = ', '.join(list(set([store_data[item[1]] for item in filtered_data])))
            except:
                stores = ''
        data_result['qty'] = sum_of_stocks_in_store
        data_result['stores'] = stores
        data_result['store_ids'] = store_ids
        filtered_master_items.append(data_result)
    if group_id:
        filtered_master_items = [item for item in filtered_master_items if
                                 item['item_group'] == item_group_data[int(group_id)]]
    return filtered_master_items


# def get_stock_statement_by_all_store(request):
#
#     if request.method == 'GET':
#         filtered_data = process_stock_statement()
#         return JsonResponse(filtered_data, safe=False)
#
#
# def get_stock_statement_by_given_store(request, store_id):
#
#     if request.method == 'GET':
#         filtered_data = process_stock_statement(store_id=store_id)
#         return JsonResponse(filtered_data, safe=False)


def process_stock_statement_for_single_item(part_no, store_id=None, group_id=None):
    item_master_instance = ItemMaster.objects.get(id=part_no)
    if group_id:
        item_master_instance = ItemMaster.objects.get(id=part_no, Item_Group=int(group_id))
    item_master_dict = model_to_dict(item_master_instance)
    store_data = {item['id']: item['StoreName'] for item in list(Store.objects.values('id', 'StoreName'))}
    item_group_data = {item['id']: item['name'] for item in list(Item_Groups_Name.objects.values('id', 'name'))}
    stock_data = list(ItemStock.objects.values('id', 'part_no', 'currentStock', 'store', 'BatchNumber', 'Serialnum'))
    is_serial = item_master_dict['serial']
    is_batch = item_master_dict['Batch_number']
    if store_id is None:
        filtered_data = [stock_item for stock_item in stock_data if stock_item['part_no'] == int(part_no)]
    else:
        filtered_data = [stock_item for stock_item in stock_data if
                         stock_item['part_no'] == int(part_no) and int(stock_item['store']) == int(store_id)]
    stock_statement_data = []
    if is_serial:
        for filtered_item in filtered_data:
            serial_number = model_to_dict(SerialNumbers.objects.get(id=filtered_item['Serialnum']))['SerialNumber']
            result_data = {
                'part_no': part_no,
                'part_code': item_master_dict['Item_PartCode'],
                'part_name': item_master_dict['Item_name'],
                'Serialnum': serial_number,
                'Batch Number': None,
                'Qty': 1,
                'Store': store_data[filtered_item['store']],
                'store_ids': [filtered_item['store']],
                'item_group': item_group_data[item_master_dict['Item_Group']]
            }
            stock_statement_data.append(result_data)
    elif is_batch:
        # Use a defaultdict to store the aggregated data
        aggregated_data = defaultdict(Decimal)

        # Aggregate the data based on BatchNumber and store
        for item in filtered_data:
            key = (item['BatchNumber'], item['store'])
            aggregated_data[key] += item['currentStock']

        # Convert the defaultdict to a list of dictionaries
        for key, value in aggregated_data.items():
            batch_number = model_to_dict(BatchNumber.objects.get(id=key[0]))['BatchNumberName']
            result_data = {
                'part_no': part_no,
                'part_code': item_master_dict['Item_PartCode'],
                'part_name': item_master_dict['Item_name'],
                'Serialnum': None,
                'Batch Number': batch_number,
                'Qty': value,
                'Store': store_data[key[1]],
                'store_ids': [key[1]],
                'item_group': item_group_data[item_master_dict['Item_Group']]
            }
            stock_statement_data.append(result_data)
    else:
        try:
            sum_of_stocks_in_store = sum(item['currentStock'] for item in filtered_data)
        except:
            sum_of_stocks_in_store = 0
        try:
            stores = ', '.join(list(set([store_data[item['store']] for item in filtered_data])))
        except:
            stores = ''
        try:
            store_ids = list(set([item['store'] for item in filtered_data]))
        except:
            store_ids = []
        result_data = {
            'part_no': part_no,
            'part_code': item_master_dict['Item_PartCode'],
            'part_name': item_master_dict['Item_name'],
            'Serialnum': None,
            'Batch Number': None,
            'Qty': sum_of_stocks_in_store,
            'Store': stores,
            'store_ids': store_ids,
            'item_group': item_group_data[item_master_dict['Item_Group']]
        }
        stock_statement_data.append(result_data)
    return stock_statement_data


# def get_stock_statement_by_all_store_for_single_part_number(request, part_no):
#
#     if request.method == 'GET':
#         filtered_data = process_stock_statement_for_single_item(part_no)
#         return JsonResponse(filtered_data, safe=False)
#
#
# def get_stock_statement_by_given_store_for_single_part_number(request, part_no, store_id):
#
#     if request.method == 'GET':
#         filtered_data = process_stock_statement_for_single_item(part_no, store_id=store_id)
#         return JsonResponse(filtered_data, safe=False)


def get_stock_history_details(part_no, StockHistoryMasterData):
    processed_data = []
    for date_key in StockHistoryMasterData:
        data = {
            'part_no': part_no,
            'start_stock': int(Decimal(StockHistoryMasterData[date_key][0]['PreviousState'])),
            'end_stock': int(Decimal(StockHistoryMasterData[date_key][-1]['UpdatedState'])),
            'date': date_key
        }
        total_item_added = 0
        total_item_deleted = 0
        for history_item in StockHistoryMasterData[date_key]:
            modified_data = int(Decimal(history_item['UpdatedState'])) - int(Decimal(history_item['PreviousState']))
            if modified_data < 0:
                total_item_deleted += modified_data
            elif modified_data > 0:
                total_item_added += modified_data
        data['added'] = total_item_added
        data['reduced'] = total_item_deleted
        processed_data.append(data)
    return processed_data


def getStockHistory(request):
    store_id = request.GET.get('store')
    part_id = request.GET.get('part_id')
    if store_id == 'null' or store_id == 'all':
        store_id = None
    if part_id == 'null' or part_id == 'all':
        part_id = None
    if store_id is None:
        stockData = StockHistoryLog.objects.filter(PartNumber=int(part_id), ColumnName="currentStock")
    else:
        stockData = StockHistoryLog.objects.filter(PartNumber=int(part_id), ColumnName="currentStock",
                                                   StoreLink=int(store_id))

    StockHistoryMasterData = {}
    for StockItem in stockData:
        StockItem = model_to_dict(StockItem)
        timestamp = datetime.fromisoformat(str(StockItem['modifiedDate']))
        formatted_date = timestamp.strftime("%d-%m-%Y")
        if formatted_date in StockHistoryMasterData.keys():
            temp_list = StockHistoryMasterData[formatted_date]
            temp_list.append(StockItem)
            StockHistoryMasterData[formatted_date] = temp_list
        else:
            StockHistoryMasterData[formatted_date] = [StockItem]
    processed_data = get_stock_history_details(part_id, StockHistoryMasterData)
    return JsonResponse(processed_data, safe=False)


# def getStockHistoryWithStore(request, partCode, store_id):
#     stockData = StockHistoryLog.objects.all()
#     StockHistoryMasterData = {}
#     for StockItem in stockData:
#         StockItem = model_to_dict(StockItem)
#         if str(partCode) == str(StockItem['PartNumber']) and str(StockItem['ColumnName']) == "currentStock" and str(store_id) == str(StockItem['StoreLink']):
#             timestamp = datetime.fromisoformat(str(StockItem['modifiedDate']))
#             formatted_date = timestamp.strftime("%Y-%m-%d")
#             if formatted_date in StockHistoryMasterData.keys():
#                 temp_list = StockHistoryMasterData[formatted_date]
#                 temp_list.append(StockItem)
#                 StockHistoryMasterData[formatted_date] = temp_list
#             else:
#                 StockHistoryMasterData[formatted_date] = [StockItem]
#     processed_data = get_stock_history_details(partCode, StockHistoryMasterData)
#     return JsonResponse(processed_data, safe=False)


class getItemMasterHistory(APIView):
    def get_object(self, pk):
        try:
            return ItemMasterHistory.objects.get(pk=pk)
        except Exception as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        article = self.get_object(pk)
        serialzer = ItemMasterHistorySerializer(article)
        return Response(serialzer.data)


def stock_statement_store_group_filter(request):
    if request.method == 'GET':
        try:
            store_id = request.GET.get('store')
            group_id = request.GET.get('group')
            part_id = request.GET.get('part_id')
            if store_id == 'null' or store_id == 'all':
                store_id = None
            if group_id == 'null' or group_id == 'all':
                group_id = None
            if part_id == 'null' or part_id == 'all':
                part_id = None

            if part_id:
                filtered_data = process_stock_statement_for_single_item(part_id, store_id, group_id)
            else:
                filtered_data = process_stock_statement(store_id, group_id)

            return JsonResponse(filtered_data, safe=False)
        except Exception as e:
            print(e)


def get_item_combo_(request):
    if request.method == 'GET':
        item_combo_ids = request.GET.getlist('ids', [])[0].split(',')
        item_combo_ids = [int(a) for a in item_combo_ids]
        filtered_objects = Item_Combo.objects.filter(id__in=item_combo_ids).values('id', 'part_number', 'item_qty',
                                                                                   'item_display', 'is_mandatory')
        # print(filtered_objects)
        if filtered_objects:
            # filtered_objects = serialize('json', filtered_objects)
            filtered_objects = list(filtered_objects.values())
        return JsonResponse(filtered_objects, safe=False)


def pos_report_data_filter(event_name, user, start_date, end_date):
    start_date_obj = datetime.strptime(start_date, "%d-%m-%Y")
    end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")
    formatted_start_date = start_date_obj.strftime("%Y-%m-%d")
    formatted_end_date = end_date_obj.strftime("%Y-%m-%d")

    payment_prefetch = Prefetch('payments', queryset=paymentMode.objects.filter(
        UpdatedAt__gte=start_date,
        UpdatedAt__lte=end_date))
    if not event_name and not user:
        pos_with_payments = SalesOrder.objects.filter(
            marketingEvent__name=event_name,
            date__range=(start_date, end_date)
        ).prefetch_related(payment_prefetch)
    elif event_name and not user:
        pos_with_payments = SalesOrder.objects.filter(
            marketingEvent=event_name,
            order_date__gte=start_date,
            order_date__lte=end_date
        ).prefetch_related('payment').all()
    elif not event_name and user:
        pos_with_payments = SalesOrder.objects.filter(
            marketingEvent=event_name,
            order_date__gte=start_date,
            order_date__lte=end_date
        ).prefetch_related('payment').all()
    else:
        pos_with_payments = SalesOrder.objects.filter(
            marketingEvent=event_name,
            order_date__gte=start_date,
            order_date__lte=end_date
        ).prefetch_related('payment').all()

    # print(pos_with_payments)
    instance_dict = model_to_dict(pos_with_payments[0])
    # print(instance_dict)
    pass


def get_report_details(request):
    if request.method == 'GET':
        try:
            # event_name = request.GET.get('eventname')
            event_name = 1
            user = request.GET.get('user')
            start_date = request.GET.get('startdate')
            end_date = request.GET.get('enddate')
            if event_name == 'null' or event_name == 'all':
                event_name = None
            if user == 'null' or user == 'all':
                user = None
            pos_report_data_filter(event_name, user, start_date, end_date)
            return JsonResponse([], safe=False)
        except Exception as e:
            print(e)
    pass
