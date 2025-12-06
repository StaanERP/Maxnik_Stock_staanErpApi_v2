import json

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, Min, Max
from EnquriFromapi.models import *

# class GetSummaryData(APIView):
#     def put(self, request):
#         # Extract grouping and annotations from the request
#         group_by = request.data.get("group_by",[])
#         annotations = request.data.get("annotations", {})
#         order_by = request.data.get('order_by', None)
#         if not group_by :
#             return Response({"error": "'group_by'  is required."}, status=400)
#         # Dynamically build the annotations
#         annotation_args = {}
#         for alias, annotation_info in annotations.items():
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
#         # Perform the query with dynamic group_by and annotations
#         try:
#             query = SalesOrder_2.objects.values(*group_by)  # Group by fields dynamically
#             if annotation_args:
#                 query = query.annotate(**annotation_args)  # Apply dynamic annotations if present
#             summary_data = query
#             # Apply ordering if provided
#             if order_by:
#                 summary_data = query.order_by(*order_by)
#             return Response(summary_data, status=200)
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

# class GetSummaryData(APIView):
#     def put(self, request):
#         # Extract grouping and annotations from the request
#         group_by = request.data.get("group_by", [])
#         annotations = request.data.get("annotations", {})
#         order_by = request.data.get("order_by", [])
#
#         if not group_by:
#             return Response({"error": "'group_by' is required."}, status=400)
#
#         # Dynamically build the annotations
#         annotation_args = {}
#         for alias, annotation_info in annotations.items():
#             if annotation_info.get("type") == "Sum":
#                 annotation_args[alias] = Sum(annotation_info["field"])
#             elif annotation_info.get("type") == "Count":
#                 annotation_args[alias] = Count(annotation_info["field"])
#             elif annotation_info.get("type") == "Avg":
#                 annotation_args[alias] = Avg(annotation_info["field"])
#             elif annotation_info.get("type") == "F":
#                 annotation_args[alias] = F(annotation_info["field"])
#
#         try:
#             # Perform the grouped query
#             query = SalesOrder_2.objects.values(*group_by)
#             if annotation_args:
#                 query = query.annotate(**annotation_args)
#
#             summary_data = list(query)
#
#             # Calculate overall totals
#             overall_totals = {}
#             if annotation_args:
#                 overall_totals = SalesOrder_2.objects.aggregate(**annotation_args)
#
#             # Apply ordering if provided
#             if order_by:
#                 query = query.order_by(*order_by)
#
#             # Return both grouped data and overall totals
#             return Response({
#                 "summary_data": summary_data,
#                 "overall_totals": overall_totals,
#             }, status=200)
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)


class test_report(APIView):
    def get(self, request):
        # grouped_data = SalesOrder_2.objects.values(
        #     'status__name',  # Group by this field
        #     'currency__Currency__name',
        #     'currency__rate',
        #     'currency__Currency__currency_symbol',
        #     'currency__Currency__formate'
        # ).order_by('status__name')

        sales_summary = (
            SalesOrder_2.objects.values('sales_person__username', "net_amount")  # Group by 'sales_person'
            .annotate(total_sales=Sum('net_amount'), order_count=Count('id'))  # Calculate totals
        )
        # for summary in sales_summary:
        #     print(
        #         f"Sales Person: {summary['sales_person__username']}, Total Sales: {summary['total_sales']}, Orders: {summary['order_count']}")

        response_data = {"model": list(sales_summary)}
        return Response(response_data)


class SalesOrder2Rerport(APIView):

    def put(self, request):
        fields = request.data.get("selectedData")
        pageNumber = request.data.get('pageNumber', 1)
        pageSize = request.data.get('pageSize', 10)
        filterData = request.data.get("filterData", None)
        fixedfields = request.data.get("fixedselectedData", None)
        fixedfilterData = request.data.get("fixedfilterData", None)
        distinct_data = request.data.get("distinct", [])
        sort_by = request.data.get("sort_by", [])
        if not fields:
            return Response({"error": "No fields provided"}, status=status.HTTP_400_BAD_REQUEST)
        SalesOrder2 = SalesOrder_2.objects.all().order_by('-id')

        if fixedfields:
            SalesOrder2 = SalesOrder2.values(*fixedfields)
        else:
            SalesOrder2 = SalesOrder2.values(*fields)
        if fixedfilterData:
            normal_filters = {}
            exclude_filters = {}
            isnull_filters = []
            not_isnull_filters = []

            for key, value in fixedfilterData.items():
                if key.endswith("__noticontains"):
                    exclude_key = key.replace("__noticontains", "__icontains")
                    exclude_filters[exclude_key] = value
                elif key.endswith("__isempty"):  # Handle "is empty"
                    field_name = key.replace("__isempty", "")
                    isnull_filters.append(Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""}))
                elif key.endswith("__isnotempty"):  # Handle "is not empty"
                    field_name = key.replace("__isnotempty", "")
                    not_isnull_filters.append(Q(**{f"{field_name}__isnull": False}) & ~Q(**{field_name: ""}))
                else:
                    normal_filters[key] = value

            try:
                # Apply normal filters
                if normal_filters:
                    SalesOrder2 = SalesOrder2.filter(**normal_filters)

                # Apply exclude filters
                if exclude_filters:
                    SalesOrder2 = SalesOrder2.exclude(**exclude_filters)

                # Apply isnull (empty) filters
                for isnull_filter in isnull_filters:
                    SalesOrder2 = SalesOrder2.filter(isnull_filter)

                # Apply isnotnull (not empty) filters
                for not_isnull_filter in not_isnull_filters:
                    SalesOrder2 = SalesOrder2.filter(not_isnull_filter)

            except Exception as e:
                print(e)
        try:
            if filterData:
                try:
                    # Apply the filter by unpacking the dictionary
                    SalesOrder2 = SalesOrder2.filter(**filterData)
                except Exception as e:
                    print(e)
            if len(distinct_data) > 0:
                distinct_data = [field.split('__')[0] for field in distinct_data]  # Extract field names
                distinct_data = set(distinct_data)

                # Validate against model fields
                valid_fields = [f.name for f in SalesOrder2.model._meta.fields]
                distinct_data = [field for field in distinct_data if field in valid_fields]

                try:
                    SalesOrder2 = SalesOrder2.order_by(*distinct_data).distinct(*distinct_data)
                except Exception as e:
                    print(e)

                    # Validate and apply multi-field sorting
            if sort_by:
                if not isinstance(sort_by, list):
                    return Response({"error": "sort_by should be a list of fields"}, status=status.HTTP_400_BAD_REQUEST)

                valid_fields = [f.name for f in SalesOrder_2._meta.fields]  # Get model field names
                validated_sort_fields = []

                for field in sort_by:
                    field_name = field.lstrip("-")  # Remove '-' to validate the base field name

                    if field_name in valid_fields:
                        validated_sort_fields.append(field)
                    else:
                        return Response({"error": f"Invalid sort field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
                print("validated_sort_fields", validated_sort_fields)
                SalesOrder2 = SalesOrder2.order_by(*validated_sort_fields)
        except Exception as e:
            print(e)
        paginator = Paginator(SalesOrder2, pageSize)
        paginated_data = paginator.get_page(pageNumber)
        response_data = {
            'count': paginator.count,  # Total number of records
            'num_pages': paginator.num_pages,  # Total number of pages
            'has_next': paginated_data.has_next(),  # Check if there is a next page
            'has_previous': paginated_data.has_previous(),  # Check if there is a previous page
            'results': list(paginated_data)  # The paginated data
        }
        return Response(response_data)