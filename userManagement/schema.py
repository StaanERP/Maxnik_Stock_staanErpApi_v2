import graphene
from itemmaster2.Utils.ItemMasterComman import *
from .models import *
from itemmaster.schema import *
from itemmaster2.models import *
from datetime import date
import calendar

role_type = create_graphene_type(Roles)


class RollConnection(graphene.ObjectType):
    items = graphene.List(role_type)
    page_info = graphene.Field(PageInfoType)

class UserHierarchical(graphene.ObjectType):
    user_hierarchical = graphene.JSONString()


user_management_type = create_graphene_type(UserManagement)


class UserManagementConnection(graphene.ObjectType):
    items = graphene.List(user_management_type)
    page_info = graphene.Field(PageInfoType)


"""permission table type"""
permission_options_type = create_graphene_type(PermissionOptions)
permission_Model_type = create_graphene_type(PermissionModel)
allowed_permission_type = create_graphene_type(AllowedPermission)
Profile_type = create_graphene_type(Profile)


class ProfileConnection(graphene.ObjectType):
    items = graphene.List(Profile_type)
    page_info = graphene.Field(PageInfoType)

class UserAllowedPermission(graphene.ObjectType):
    permission_list = graphene.List(graphene.String)
    name = graphene.String()
    email = graphene.String()
    is_sales_person = graphene.Boolean()
    is_admin = graphene.Boolean()
    is_service =  graphene.Boolean()
    is_sales_coordinator = graphene.Boolean()
    is_service_coordinator = graphene.Boolean()

"""Employee"""
Employee_type = create_graphene_type(Employee)


class EmployeeConnection(graphene.ObjectType):
    items = graphene.List(Employee_type)
    page_info = graphene.Field(PageInfoType)


"""ExpenseRequest"""
ExpenseRequest_type = create_graphene_type(ExpenseRequest)


class ExpenseRequestConnection(graphene.ObjectType):
    items = graphene.List(ExpenseRequest_type)
    page_info = graphene.Field(PageInfoType)


"""expense_categories"""
ExpenseCategories_type = create_graphene_type(ExpenseCategories)


class ExpenseCategoriesConnection(graphene.ObjectType):
    items = graphene.List(ExpenseCategories_type)
    page_info = graphene.Field(PageInfoType)


"""ExpenseClaimDetails"""
ExpenseClaimDetails_type = create_graphene_type(ExpenseClaimDetails)


class ExpenseClaimDetailsConnection(graphene.ObjectType):
    items = graphene.List(ExpenseClaimDetails_type)
    page_info = graphene.Field(PageInfoType)


class ExpenseClaimDetailInput(graphene.InputObjectType):
    id = graphene.ID()
    date_of_exp = graphene.Date(required=True)
    expense_categories = graphene.Int(required=True)
    descriptions = graphene.String(required=True)
    claim_amount = graphene.Decimal(required=False)
    approved_amount = graphene.Decimal(required=False)
    gst_in = graphene.Boolean(required=False)
    pdf_url = graphene.List(graphene.Int, required=False)
    


"""ExpenseClaim"""
ExpenseClaim_type = create_graphene_type(ExpenseClaim)


class ExpenseClaimConnection(graphene.ObjectType):
    items = graphene.List(ExpenseClaim_type)
    page_info = graphene.Field(PageInfoType)

 
"""PaymentVoucherAdvanceDetails"""
PaymentVoucherAdvanceDetails_type = create_graphene_type(PaymentVoucherAdvanceDetails)
PaymentVoucherAgainstInvoice_type = create_graphene_type(PaymentVoucherAgainstInvoice)

"""PaymentVoucher"""
PaymentVoucher_type = create_graphene_type(PaymentVoucher)
class PaymentVoucherConnection(graphene.ObjectType):
    items = graphene.List(PaymentVoucher_type)
    page_info = graphene.Field(PageInfoType)

"""ExpenseReconciliation"""
expense_reconciliation_details_type = create_graphene_type(ExpenseReconciliationDetails)

"""Holiday"""
holiday_type = create_graphene_type(Holidays)
leave_type_type=create_graphene_type(LeaveType)
leave_alloted_type=create_graphene_type(LeaveAlloted)
leave_modal_type=create_graphene_type(Leave)
attendance_type=create_graphene_type(AttendanceRegister)

class leave_alloted_employee_type(graphene.ObjectType):
    id = graphene.Int()
    employee_id = graphene.String()
    employee_name = graphene.String()
    employee_Group = graphene.String()
    employee_image_url = graphene.String()
    allotted_days=graphene.Decimal()
    taken_leave=graphene.Decimal()

def createAttendanceRegister():
    today = date.today()
    errors = []
    try:
        # Get default statuses as objects
        status_map = {
            "Absent": None,
            "Holiday": None,
            "Leave": None,
            "Half Day Leave": None,
            "Week Off": None
        }
        # Fetch status objects for AttendanceRegister table
        for status_name in status_map.keys():
            status_object = CommanStatus.objects.filter(name=status_name, table="AttendanceRegister").first()
            if status_object:
                status_map[status_name] = status_object  # Store object instead of ID

        # Ensure all required statuses exist
        if None in status_map.values():
            missing_statuses = [name for name, obj in status_map.items() if obj is None]
            errors.append(f"Missing required statuses in CommanStatus table: {', '.join(missing_statuses)}")
            return {"success": False, "errors": errors}
    except Exception as e:
        print("Error fetching status objects:", e)
        return {"success": False, "errors": ["Error fetching status objects"]}

    employees = Employee.objects.all()

    try:
        attendance_entries = []

        holiday_entry = Holidays.objects.filter(from_date__lte=today, to_date__gte=today).first()
        if holiday_entry:
            try:
                status = status_map["Holiday"]
                print("holiday_entry",holiday_entry)
                attendance_records = [
                    AttendanceRegister(employee_id=employee, status=status, holidays=holiday_entry,date=today)
                    for employee in employees
                ]
                print("attendance_records",attendance_records)
                AttendanceRegister.objects.bulk_create(attendance_records)
                return 
            except Exception as e:
                print("ee->",e)
        
        else:
            for employee in employees:
                status = status_map["Absent"]  # Default to Absent
                leave_entry = None 
                # 2. Check if employee has leave on this day
                # print("status_map[Leave]",status_map["Leave"])
                leave_entry = Leave.objects.filter(
                    employee_id=employee,
                    from_date__lte=today,
                    to_date__gte=today,
                    status__name="Approved"
                ).first()

                if leave_entry:
                    if leave_entry.leave_day_type == "Full Day":
                        status = status_map["Leave"]
                    elif leave_entry.leave_day_type == "Half Day":
                        status = status_map["Half Day Leave"]

                # 3. Check if today is a week off for this employee
                week_off_days = employee.week_off_days.split(",") if employee.week_off_days else []
                if calendar.day_name[today.weekday()] in week_off_days:
                    status = status_map["Week Off"]

                # Create attendance entry with objects instead of IDs

                attendance_entries.append(
                    AttendanceRegister(
                        employee_id=employee,  # Store as an Employee object
                        date=today,
                        check_in=None,
                        check_out=None,
                        work_hours=None,
                        over_time_hours=None,
                        break_hours=None,
                        late_in_hours=None,
                        late_out_hours=None,
                        status=status,  # Store full status object
                        leave=leave_entry if status in [status_map["Leave"], status_map["Half Day Leave"]] else None,
                    )
                )
            print("attendance_entries", attendance_entries)
            # Bulk create attendance records for performance
            AttendanceRegister.objects.bulk_create(attendance_entries)
            return {"success": True, "errors": []}

    except Exception as e:
        print("Error creating attendance entries:", e)
        return {"success": False, "errors": ["Error creating attendance entries"]}

class CommanInitialFetch(graphene.ObjectType):
    items = graphene.JSONString()

class Query(ObjectType):
    all_role = graphene.Field(RollConnection, page=graphene.Int(), page_size=graphene.Int(),
                              order_by=graphene.String(), descending=graphene.Boolean(),id=graphene.Int(),  roleName=graphene.String()
                              , descriptions=graphene.String())
    user_hierarchical = graphene.Field(UserHierarchical)
    all_UserManagement = graphene.Field(UserManagementConnection, page=graphene.Int(), page_size=graphene.Int(),
                                        order_by=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                        role=graphene.Int(),role_name=graphene.String(),head_of_role=graphene.Int(),
                                        isadmin=graphene.Boolean(),  issales_person=graphene.Boolean(), isservice=graphene.Boolean(),
                                        userid=graphene.Int(),userName = graphene.String())
    all_permission_model = graphene.List(permission_Model_type)
    all_Profile = graphene.Field(ProfileConnection, page=graphene.Int(), page_size=graphene.Int(),
                                 order_by=graphene.String(), descending=graphene.Boolean(),
                                 profile_name=graphene.String(),
                                 descriptions=graphene.String(), id=graphene.Int())
    all_UserAllowed_permission = graphene.Field(UserAllowedPermission, user_id=graphene.Int())
    all_employee = graphene.Field(EmployeeConnection, page=graphene.Int(), page_size=graphene.Int(),
                                  order_by=graphene.String(), descending=graphene.Boolean(),
                                  id=graphene.Int(), employee_id=graphene.String(), employee_name=graphene.String(),
                                  designation=graphene.String(), department=graphene.String(),role=graphene.String(),is_user_id=graphene.Boolean())
    all_expense_request = graphene.Field(ExpenseRequestConnection, page=graphene.Int(), page_size=graphene.Int(),
                                         order_by=graphene.String(), descending=graphene.Boolean(),
                                         id=graphene.Int(), expense_request_no=graphene.String(),
                                         expense_request_date=graphene.String(),
                                         employee_name=graphene.String(), request_amount=graphene.Int(),
                                         request_amount_gt=graphene.Int(),
                                         request_amount_lt=graphene.Int(), request_amount_gte=graphene.Int(),
                                         request_amount_lte=graphene.Int(),
                                         request_amount_start=graphene.Int(), request_amount_end=graphene.Int(), )
    all_expense_categories = graphene.Field(ExpenseCategoriesConnection, page=graphene.Int(), page_size=graphene.Int(),
                                            order_by=graphene.String(), descending=graphene.Boolean(),
                                            id=graphene.Int(), expenseCategoryName=graphene.String())
    all_expense_claim = graphene.Field(ExpenseClaimConnection, page=graphene.Int(), page_size=graphene.Int(),
                                       order_by=graphene.String(), descending=graphene.Boolean(),
                                       id=graphene.Int())
    all_payment_voucher = graphene.Field(PaymentVoucherConnection, 
                                         page=graphene.Int(), page_size=graphene.Int(),
                                         order_by=graphene.String(), 
                                         descending=graphene.Boolean(),
                                         id=graphene.Int(),
                                         name=graphene.String())
 
    
    
    all_holidays = graphene.List(holiday_type, id=graphene.Int(), name=graphene.String())
    all_leave_type = graphene.List(leave_type_type, id=graphene.Int(), name=graphene.String())
    all_leave_alloted_type = graphene.List(leave_alloted_type, id=graphene.Int(),financial_year=graphene.Boolean(),employee_id=graphene.Int())
    all_leave=graphene.List(leave_modal_type,id=graphene.Int(), name=graphene.String())
    alloted_employee_list = graphene.List(leave_alloted_employee_type,id=graphene.Int())
    employee_education_details_options = graphene.Field(FixedOptionConnection)
    all_attendance=graphene.List(attendance_type,id=graphene.Int())
    payment_voucher_edit_fetch = graphene.Field(CommanInitialFetch, id=graphene.Int())
    unpaid_purchase_invoice = graphene.Field(CommanInitialFetch, supplier_id=graphene.Int())

    @permission_required(models=["Roles", "User_Management","Target"])
    def resolve_all_role(self, info, page=1, page_size=20, order_by=None, descending=False, roleName=None,
                         descriptions=None, id=None):
        queryset = Roles.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if roleName:
            filter_kwargs['role_name__icontains'] = roleName
        if descriptions:
            filter_kwargs['descriptions__icontains'] = descriptions
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        # 
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
        return RollConnection(items=paginated_data.object_list,
                              page_info=page_info)
    
    @permission_required(models=["Roles", "User_Management"])
    def resolve_user_hierarchical(self, info):
        user_hierarchical = get_department_view_hierarchical()
        return UserHierarchical(user_hierarchical=user_hierarchical)
    
    @permission_required(models=["User_Management","Target","Target_Summary","Employee"])
    def resolve_all_UserManagement(self, info, page=1, page_size=20, order_by=None, descending=False, id=None, role=None,role_name=None,head_of_role=None,
                                   isadmin = None,  issales_person= None , isservice=None,userid=None,userName=None):
        queryset = UserManagement.objects.all().order_by('-id')

        # update_state_city_in_supplier()
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if head_of_role:
            roles = Roles.objects.filter(report_to=head_of_role)
            roles = [roledata.id for roledata in roles]
            if len(roles):
                filter_kwargs["role__in"] = roles
        if  userid:
            filter_kwargs['user__id'] = userid
        if userName:
            filter_kwargs['user__username__icontains'] = userName
        if role:
            filter_kwargs['role'] = role

        # Apply role_name filter using Q object for role and role_2
        if role_name:
            queryset = queryset.filter(Q(role__role_name__icontains=role_name) | Q(role_2__role_name__icontains=role_name))
        if isadmin:
            filter_kwargs['admin'] = isadmin
        if issales_person:
            filter_kwargs['sales_person'] = issales_person
        if isservice:
            filter_kwargs['service'] = isservice
        db_s = {
            "id": {"field": "id", "is_text": False},
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
        return UserManagementConnection(items=paginated_data.object_list,
                                        page_info=page_info)
 
    def resolve_all_permission_model(self, info):
        queryset = PermissionModel.objects.all()
        return queryset

    @permission_required(models=["Profile", "User_Management"])
    def resolve_all_Profile(self, info, page=1, page_size=20, order_by=None, descending=False, profile_name=None,
                            descriptions=None, id=None):
        queryset = Profile.objects.all().order_by('-id')

        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if profile_name:
            filter_kwargs['profile_name__icontains'] = profile_name
        if descriptions:
            filter_kwargs['description__icontains'] = descriptions
        db_s = {
            "id": {"field": "id", "is_text": False},
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
        return ProfileConnection(items=paginated_data.object_list,
                                 page_info=page_info)

    @permission_required(models=["Employee","Leave","LeaveType","ExpenseClaim","PaymentVoucher","ExpenseRequest","QIR", "Receipt Voucher", 'PaymentVoucher'])
    def resolve_all_employee(self, info, page=1, page_size=20, order_by=None, descending=False, employee_id=None,
                             employee_name=None, id=None, designation=None, department=None,role=None,is_user_id=None):
        queryset = Employee.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if employee_id:
            filter_kwargs['employee_id__icontains'] = employee_id
        if employee_name:
            filter_kwargs['employee_name__icontains'] = employee_name
        if designation:
            filter_kwargs['designation__icontains'] = designation
        if department:
            filter_kwargs['department__name__icontains'] = department
        if role:
            filter_kwargs['user__role__role_name'] = role 
            
        db_s = {
            "id": {"field": "id", "is_text": False},
            "employee_id": {"field": "employeeId", "is_text": True},
        }
        queryset = queryset.filter(**filter_kwargs)
        if is_user_id is True:
            queryset = queryset.filter(user__isnull=False)
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return EmployeeConnection(items=paginated_data.object_list,
                                  page_info=page_info)
    
    @permission_required(models=["ExpenseRequest"])
    def resolve_all_expense_request(self, info, page=1, page_size=20, order_by=None, descending=False,
                                    id=None, expense_request_no=None, expense_request_date=None, employee_name=None,
                                    request_amount=None,
                                    request_amount_lt=None, request_amount_gt=None, request_amount_gte=None,
                                    request_amount_lte=None,
                                    request_amount_start=None, request_amount_end=None):
        queryset = ExpenseRequest.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if expense_request_no:
            filter_kwargs['expense_request_no__icontains'] = expense_request_no
        if employee_name:
            filter_kwargs['employee_name__employee_name__icontains'] = employee_name
        if expense_request_date:
            start_date, end_date = expense_request_date.split(' - ')
            updated_start_date = datetime.strptime(start_date, '%d-%m-%Y')
            updated_end_date = datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-1)
            if start_date == end_date:
                filter_kwargs['expense_request_date__range'] = (updated_start_date, updated_end_date)
            else:
                filter_kwargs['expense_request_date__range'] = (updated_start_date, updated_end_date)
        if request_amount:
            filter_kwargs['request_amount__icontains'] = request_amount
        if request_amount_lt:
            filter_kwargs['request_amount__lt'] = request_amount_lt
        if request_amount_gt:
            filter_kwargs['request_amount__gt'] = request_amount_gt
        if request_amount_gte:
            filter_kwargs['request_amount__gte'] = request_amount_gte
        if request_amount_lte:
            filter_kwargs['request_amount__lte'] = request_amount_lte
        if request_amount_start and request_amount_end:
            filter_kwargs['request_amount__range'] = (request_amount_start, request_amount_end)
        db_s = {
            "id": {"field": "id", "is_text": False},
            "expenseRequestNo": {"field": "expense_request_no", "is_text": True},
            "employeeName": {"field": "employee_name__employee_name", "is_text": True},
            "requestAmount": {"field": "request_amount", "is_text": False},
            "expenseRequestDate": {"field": "expense_request_date", "is_text": False},
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
        return ExpenseRequestConnection(items=paginated_data.object_list,
                                        page_info=page_info)


    @permission_required(models=["ExpenseClaim"])
    def resolve_all_expense_categories(self, info, page=1, page_size=20, order_by=None, descending=False, roleName=None,
                                       descriptions=None, id=None, expenseCategoryName=None):
        queryset = ExpenseCategories.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if expenseCategoryName:
            filter_kwargs['expense_category_name__icontains'] = expenseCategoryName
        queryset = queryset.filter(**filter_kwargs)
        db_s = {
            "id": {"field": "id", "is_text": False},
        }
        queryset = apply_case_insensitive_sorting(queryset, order_by, descending, db_s)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return ExpenseCategoriesConnection(items=paginated_data.object_list,
                                           page_info=page_info)
    @permission_required(models=["ExpenseClaim"])
    def resolve_all_expense_claim(self, info, page=1, page_size=20, order_by=None, descending=False, id=None):
        queryset = ExpenseClaim.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        db_s = {
            "id": {"field": "id", "is_text": False},
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
        return ExpenseClaimConnection(items=paginated_data.object_list,
                                      page_info=page_info)

    @permission_required(models=["PaymentVoucher"])
    def resolve_all_payment_voucher(self, info, page=1, page_size=20, order_by=None, descending=False, roleName=None,
                                    descriptions=None, id=None,name=None):
        queryset = PaymentVoucher.objects.all().order_by('-id')
        """apply filters"""
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if name:
            filter_kwargs['payment_voucher_no__linked_model_id__icontains']=name
        db_s = {
            "id": {"field": "id", "is_text": False},
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
        return PaymentVoucherConnection(items=paginated_data.object_list,
                                        page_info=page_info)
 

 
    
    @permission_required(models=["Holidays"])
    def resolve_all_holidays(self, info, id=None, name=None):
        filter_kwargs = {}
        queryset = Holidays.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        elif name:
            filter_kwargs['name__icontains'] = name
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    
    @permission_required(models=["LeaveType","LeaveAlloted"])
    def resolve_all_leave_type(self, info, id=None, name=None):
        filter_kwargs = {}
        queryset = LeaveType.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        elif name:
            filter_kwargs['name__icontains'] = name
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    
    @permission_required(models=["LeaveAlloted"])
    def resolve_all_leave_alloted_type(self, info, id=None, name=None,financial_year=False,employee_id=None):
        filter_kwargs = {}
        queryset = LeaveAlloted.objects.all().order_by('-id')
        if id:
            filter_kwargs['id'] = id
        if financial_year:
            today = date.today()
            current_year = today.year

            # Financial year range: Previous year's March 1st → Current year's April 30th
            # start_of_financial_year = date(current_year - 1, 3, 1)  # March 1st of last year
            # end_of_financial_year = date(current_year, 4, 30)  # April 30th of this year

            start_of_financial_year = date(current_year - 1, 4, 1)  # April 1st of last year
            end_of_financial_year = date(current_year, 3, 31)  # March 31st of this year


            print(f"Filtering from {start_of_financial_year} to {end_of_financial_year}")

            queryset = queryset.filter(from_date__gte=start_of_financial_year, to_date__lte=end_of_financial_year)
        if employee_id:
            filter_kwargs['employee_id__id'] = employee_id
            print(filter_kwargs)
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)

        return queryset
    
    def resolve_all_leave(self, info, id=None, name=None):
        filter_kwargs = {}
        queryset = Leave.objects.all().order_by('-id')
        # createAttendanceRegister()
        if id:
            filter_kwargs['id'] = id
        elif name:
            filter_kwargs['name__icontains'] = name
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    
    def resolve_all_attendance(self, info, id=None):
        filter_kwargs = {}
        print("Function triggered")
        queryset = AttendanceRegister.objects.all().order_by('-id')
        print("queryset",queryset)
        if id:
            filter_kwargs['id'] = id
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
            print("Final queryset:", queryset)
        return queryset
    

    @permission_required(models=["LeaveAlloted"])
    def resolve_alloted_employee_list(self, info, id=None):
        employe_list =[]
        try:
            employees = Employee.objects.all()
            filter_kwargs = {}
            if id: 
                filter_kwargs['id'] = id 
                print(filter_kwargs)
            employees = employees.filter(**filter_kwargs)
            for employe in  employees:
                user =  UserManagement.objects.filter(user=employe.user_id).first()
                leave_alloted =  LeaveAlloted.objects.filter(employee_id__id=employe.id)
                
                if leave_alloted.exists():
                    # total_allotted_days = sum(leave_a.allotted_days for leave_a in leave_alloted if leave_a and leave_a.allotted_days)
                    total_taken_leave = sum(leave_a.taken_leave for leave_a in leave_alloted if leave_a and leave_a.taken_leave)
                    latest_leave = leave_alloted.order_by('-id').first()  
                    leave_type_list = [leave_a for leave_a in leave_alloted if leave_a and leave_a.leave_type]                    
                    # employe_list.append({"id" :employe.id, "employee_id":employe.employee_id, "employee_name":employe.employee_name 
                    #                     , "employee_Group":user.user_group if user and user.user_group else None,
                    #                     "employee_image_url":employe.user_profile.image if employe.user_profile and employe.user_profile.image 
                    #                     else None,"allotted_days": Decimal(total_allotted_days),"taken_leave":Decimal(total_taken_leave),"leave_type":leave_type_list})
                    # employe_list.append({"id" :employe.id, "employee_id":employe.employee_id, "employee_name":employe.employee_name 
                    #                     , "employee_Group":user.user_group if user and user.user_group else None,
                    #                     "employee_image_url":employe.user_profile.image if employe.user_profile and employe.user_profile.image 
                    #                     else None, "allotted_days": Decimal(latest_leave.allotted_days) if latest_leave and latest_leave.allotted_days else Decimal(0)
                    #                     ,"taken_leave": Decimal(latest_leave.taken_leave) if latest_leave and latest_leave.taken_leave else Decimal(0),"leave_type":leave_type_list})
                    employe_list.append({"id" :employe.id, "employee_id":employe.employee_id, "employee_name":employe.employee_name 
                        , "employee_Group":user.user_group if user and user.user_group else None,
                        "employee_image_url":employe.user_profile.image if employe.user_profile and employe.user_profile.image 
                        else None, "allotted_days": Decimal(latest_leave.allotted_days) if latest_leave and latest_leave.allotted_days else Decimal(0)
                        ,"taken_leave":Decimal(total_taken_leave),"leave_type":leave_type_list})
                else:
                
                    employe_list.append({"id" :employe.id, "employee_id":employe.employee_id, "employee_name":employe.employee_name 
                                        , "employee_Group":user.user_group if user and user.user_group else None,
                                        "employee_image_url":employe.user_profile.image if employe.user_profile and employe.user_profile.image 
                                        else None,"allotted_days": None,"taken_leave":None,"leave_type":None}) 
        except Exception as e:
            print(e)
        

        return employe_list

    def resolve_employee_education_details_options(self, info):
        result = [
            {"id": item[0]} for item in employee_education_details if item[1].lower()
        ]

        return FixedOptionConnection(items=result)

    def resolve_all_UserAllowed_permission(self, info,user_id ):
        permission_list = []
        if user_id:
            user_management_instance = UserManagement.objects.get(user=user_id)
            for allow in user_management_instance.profile.allowed_permission.all():
                model_name = allow.permission_model.model_name
                # Collect permission options for each allowed_permission
                for allow_options in allow.permission_options.all():
                    # Append formatted permission details to the list
                    permission_list.append(f"{allow_options.options_name}_{model_name}")
        return UserAllowedPermission(permission_list=permission_list, name=user_management_instance.user.username,
                                     email=user_management_instance.user.email,is_sales_person = user_management_instance.sales_person,
                                     is_admin = user_management_instance.admin ,is_service = user_management_instance.service,
                                     is_sales_coordinator = user_management_instance.sales_executive, 
                                     is_service_coordinator = user_management_instance.service_executive,
                                     )
    
    @permission_required(models=["PaymentVoucher"])
    def resolve_payment_voucher_edit_fetch(self, info, id):
        try:
            pv_line_data = []
            payment_voucher = PaymentVoucher.objects.filter(id=id).first()
            if not payment_voucher:
                return GraphQLError("Payment Voucher did'n found.")
            if payment_voucher.pay_by != "Supplier & Customer":
                return GraphQLError("Pay by Supplier & Customer should only be allowed to fetch the relevant records.")
            
            sales_exists_id = None
            for pv_line in payment_voucher.paymentvoucherline_set.all():
                sales_exists_id = pv_line.receiptvoucheragainstinvoice_set.value_list("purchase_invoice__id",  flat=True)

                supplier_invoices = []
                if pv_line.cus_sup:
                    supplier_invoices = PurchaseInvoice.objects\
                        .filter(goodsreceiptnote__goodsinwardnote__purchase_order_id__supplier_id__id =pv_line.cus_sup.id).exclude(id__in=sales_exists_id)

                exists_against_invoice_details = []
            
                for index, rvai in enumerate(pv_line.receiptvoucheragainstinvoice_set.all()):
                    balance_amt = ( (rvai.purchase_invoice.net_amount or 0) -
                            (
                                rvai.purchase_invoice.purchasepaiddetails_set
                                .aggregate(total=Sum("amount"))["total"] or 0
                            )
                        )
                    
                        
                    exists_against_invoice_details.append(
                        {"id": str(rvai.id),
                        "invoice_no" : rvai.purchase_invoice.purchase_invoice_no.linked_model_id,
                        "invoice_id": str(rvai.purchase_invoice.id),
                        "bill_date": rvai.purchase_invoice.purchase_invoice_date.strftime("%d/%m/%Y") if rvai.purchase_invoice.purchase_invoice_date else None,
                        "due_date": rvai.purchase_invoice.due_date.strftime("%d/%m/%Y") if rvai.purchase_invoice.due_date else None,
                        "balance": str(balance_amt),
                        "amount": str(rvai.adjusted or 0),
                        "remarks": rvai.remarks if rvai.remarks else "",
                        "index": index+1})
                
                for idx,supplier_invoice in enumerate(supplier_invoices):
                    total_adjusted = supplier_invoice.purchasepaiddetails_set\
                    .aggregate(total=Sum("amount"))["total"] or 0
                    blance = (supplier_invoice.net_amount or 0) - total_adjusted
                    if blance > 0:
                        continue

                    exists_against_invoice_details.append({
                        "sales_invoice" : supplier_invoice.purchase_invoice_no.linked_model_id,
                        "invoice_id" : supplier_invoice.id,
                        "bill_date": supplier_invoice.purchase_invoice_date.strftime("%d/%m/%Y") if supplier_invoice.purchase_invoice_date else "",
                        "due_date": supplier_invoice.due_date.strftime("%d/%m/%Y") if supplier_invoice.due_date else "",
                        "balance" :  str(blance),
                        "amount":"",
                        "index": idx + 1
                    }) 
                
                pv_data = {
                        "id" : pv_line.id,
                        "account" : {"value":pv_line.account.id, "lable":pv_line.account.accounts_name},
                        "cus_sup" : {"value":pv_line.cus_sup.id, "lable":pv_line.account.company_name},
                        "employee" : {"value":pv_line.employee.id, "lable":pv_line.employee.employee_name},
                        "pay_for" : {"value":pv_line.pay_for.id, "lable":pv_line.pay_for.accounts_name},
                        "amount" : str(pv_line.amount),
                        "against_invoice_details" : exists_against_invoice_details
                }
                
                pv_line_data.append(pv_data)


         
            return CommanInitialFetch(items = pv_line_data)
        except Exception as e:
            return GraphQLError(f"An exception occurred: {str(e)}")
    
    @permission_required(models=["PaymentVoucher"])
    def resolve_unpaid_purchase_invoice(self, info, supplier_id):
        if not supplier_id:
            return GraphQLError(f"Supplier is mandatory.")
        try:
            invoice_datas= []
            supplier_invoices = PurchaseInvoice.objects.filter(goodsreceiptnote__goodsinwardnote__purchase_order_id__supplier_id__id =supplier_id) 
            
            for idx,supplier_invoice in enumerate(supplier_invoices):
                total_adjusted = supplier_invoice.purchasepaiddetails_set\
                .aggregate(total=Sum("amount"))["total"] or 0
               
                balance_amt = (supplier_invoice.net_amount or 0) - total_adjusted
                if balance_amt <= 0:
                    continue
                invoice_datas.append({
                    "invoice_no" : supplier_invoice.purchase_invoice_no.linked_model_id,
                    "invoice_id" : str(supplier_invoice.id),
                    "bill_date": supplier_invoice.purchase_invoice_date.strftime("%d/%m/%Y") if supplier_invoice.purchase_invoice_date else None,
                    "due_date" : supplier_invoice.due_date.strftime("%d/%m/%Y") if supplier_invoice.due_date else None,
                    "balance" : str((supplier_invoice.net_amount or 0) - total_adjusted), 
                    "index": idx + 1
                })
            return CommanInitialFetch(items = invoice_datas)
        except Exception as e:
            return GraphQLError(f"An exception occurred: {str(e)}")