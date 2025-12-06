import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from ..serializer import *
from ..schema import *
from itemmaster.mutations.Item_master_mutations import *
from itemmaster.Utils.CommanUtils import *
from ..services.serivece_class import *


class RoleCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        role_name = graphene.String()
        report_to = graphene.Int()
        descriptions = graphene.String()
        share_data_with = graphene.List(graphene.Int)
        parent_role = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int(required = True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    role_instance = graphene.Field(role_type)

    @mutation_permission("Roles", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = None
        role_instance = None
        success = False
        errors = []
        share_data_with_ids = kwargs.pop('share_data_with', None)
        if "parent_role" in kwargs and kwargs['parent_role'] == None:
            errors.append("Parent Role is required.")
            return RoleCreateMutation(
            role_instance=role_instance, success=success,
            errors=errors)
        if "id" in kwargs and kwargs['id']:
            role_instance = Roles.objects.filter(id=kwargs['id']).first()
            if not role_instance:
                errors.append("Role not found.")
            else:
                serializer = RoleSerializer(role_instance, data=kwargs, partial=True)
        else:
            serializer = RoleSerializer(data=kwargs)
        if serializer and serializer.is_valid():
            try:
                serializer.save()
                role_instance = serializer.instance
                if share_data_with_ids is not None:
                    users = User.objects.filter(id__in=share_data_with_ids)
                    role_instance.share_data_with.set(users)
                success = True
            except Exception as e:
                print(e)
                errors.append(e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
            print(errors)
        return RoleCreateMutation(
            role_instance=role_instance, success=success,
            errors=errors)


class RoleDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Roles", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            roles_instance = Roles.objects.get(id=id)
            roles_instance.delete()
            success = True
        except Roles.DoesNotExist:
            errors.append('Roles  query does not exist.')
        except ProtectedError:
            errors.append('Roles is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return RoleDeleteMutation(success=success, errors=errors)


class UserManagementCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        user = graphene.Int()
        firstName = graphene.String()
        lastName = graphene.String()
        department = graphene.Int()
        role = graphene.Int()
        role_2 = graphene.Int()
        user_group = graphene.Int()
        profile = graphene.Int()
        admin = graphene.Boolean()
        sales_person = graphene.Boolean()
        service = graphene.Boolean()
        sales_executive = graphene.Boolean()
        service_executive = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int(required = True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("User_Management", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = None

        success = False
        errors = []
        try:
            useradata = User.objects.get(id=kwargs['user'])

            # Update fields if they are provided
            if 'firstName' in kwargs:
                useradata.first_name = kwargs['firstName']
            if 'lastName' in kwargs:
                useradata.last_name = kwargs['lastName']

            useradata.save()  # Save the updated user object
        except User.DoesNotExist:
            errors.append("User not found")
            return UserManagementCreateMutation(success=success, errors=errors)
        except Exception as e:
            errors.append(str(e))
            return UserManagementCreateMutation(success=success, errors=errors)
        try:
            roles = Roles.objects.filter(id__in=[kwargs['role'], kwargs['role_2']])
            for role_ in roles:
                if role_.report_to and role_.report_to.id == useradata.id:
                    return UserManagementCreateMutation(
                        success=success,
                        errors=["“As this user is the head of the role, the role assignment needs to be updated.”"])
        except Exception as e:
            print(e)

        if "id" in kwargs and kwargs['id']:
            user_management_instance = UserManagement.objects.filter(id=kwargs['id']).first()
            if UserManagement.objects.exclude(pk=kwargs['id']).filter(id=kwargs['user']).exists():
                errors.append("User must be unique in User Management ")
                UserManagementCreateMutation(
                    success=success, errors=errors)
            if not user_management_instance:
                errors.append("User Management not found")
            else:
                serializer = UserManagementSerializer(user_management_instance, data=kwargs, partial=True)
        else:
            serializer = UserManagementSerializer(data=kwargs)
            if UserManagement.objects.filter(user=kwargs['user']).exists():
                errors.append("User must be unique in User Management ")
                return UserManagementCreateMutation(
                    success=success,
                    errors=errors)
        if serializer and serializer.is_valid():
            try:
                serializer.save()
                success = True
            except Exception as e:
                errors.append(e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return UserManagementCreateMutation(
            success=success,
            errors=errors)


class UserManagementDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("User_Management", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            user_management_instance = UserManagement.objects.get(id=id)
            user_management_instance.delete()
            success = True
        except UserManagement.DoesNotExist:
            errors.append('User Management  query does not exist.')
        except ProtectedError:
            errors.append('User Management is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return RoleDeleteMutation(success=success, errors=errors)


class AllowedPermissionCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        model_name = graphene.String()
        permission_model = graphene.Int()
        permission_options = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    allowed_permission_instance = graphene.Field(allowed_permission_type)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        allowed_permission_instance = None

        if "id" in kwargs and kwargs['id']:
            allowed_permission_instance = AllowedPermission.objects.filter(id=kwargs['id']).first()

            if not allowed_permission_instance:
                errors.append("allowed permission not found")
            else:
                serializer = AllowedPermissionSerializer(allowed_permission_instance, data=kwargs, partial=True)
        else:
            serializer = AllowedPermissionSerializer(data=kwargs)

        if serializer and serializer.is_valid():
            try:
                serializer.save()
                allowed_permission_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return AllowedPermissionCreateMutation(
            allowed_permission_instance=allowed_permission_instance,
            success=success,
            errors=errors)


def ProfilePreValidations(kwargs):
    errors = []
    Profile_instance = None
    if "id" in kwargs and kwargs['id']:
        Profile_instance = Profile.objects.filter(id=kwargs['id']).first()
        if not Profile_instance:
            errors.append("allowed permission not found")
    if kwargs.get("allowed_permission", []) and len(kwargs.get('allowed_permission', [])) > 0:

        allowed_permission_error = validate_with_serializer_with_out_related_model(kwargs.get('allowed_permission', []),
                                                                                   AllowedPermission,
                                                                                   AllowedPermissionSerializer,
                                                                                   "model_name", "model_name")
        errors.extend(allowed_permission_error)
    else:
        errors.append("At leas All one permission.")
    if kwargs.get("profile_name", None) is None:
        errors.append("Profile Name is required.")
    if kwargs.get("created_by", None) is None:
        errors.append("created By is required.")
    success = len(errors) == 0
    return {"success": success, "error": errors, "instance": Profile_instance}


def saveProfilePerssion(data):
    return save_items(data,
                      AllowedPermission,
                      AllowedPermissionSerializer, "Allowed Permission")


class AllowedPermissionInput(graphene.InputObjectType):
    id = graphene.ID()
    model_name = graphene.String()
    permission_model = graphene.Int()
    permission_options = graphene.List(graphene.Int)
    modified_by = graphene.Int()
    created_by = graphene.Int()


class ProfileCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        profile_name = graphene.String()
        description = graphene.String()
        allowed_permission = graphene.List(AllowedPermissionInput)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    Profile_instance = graphene.Field(Profile_type)

    @mutation_permission("Profile", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        Profile_instance = None
        preValidation = ProfilePreValidations(kwargs)

        if not preValidation['success']:
            return ProfileCreateMutation(
                Profile_instance=Profile_instance,
                success=preValidation['success'],
                errors=preValidation['error'])
        elif preValidation['instance']:
            Profile_instance = preValidation['instance']
        # save profile
        profile_result = saveProfilePerssion(kwargs.get("allowed_permission", []))
        if not profile_result['success']:
            return ProfileCreateMutation(
                Profile_instance=Profile_instance,
                success=profile_result['success'],
                errors=profile_result['error'])
        kwargs['allowed_permission'] = profile_result['ids']

        if "id" in kwargs and kwargs['id']:

            serializer = ProfileSerializer(Profile_instance, data=kwargs, partial=True)
        else:
            serializer = ProfileSerializer(data=kwargs)
        if serializer and serializer.is_valid():
            try:
                serializer.save()
                Profile_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProfileCreateMutation(
            Profile_instance=Profile_instance,
            success=success,
            errors=errors)


class ProfileDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Profile", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            profile_instance = Profile.objects.get(id=id)
            profile_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except UserManagement.DoesNotExist:
            errors.append('profile  query does not exist.')
        except ProtectedError:
            errors.append('profile is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return ProfileDeleteMutation(success=success, errors=errors)


"""Employee Start"""


class EmployeeCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        employee_name = graphene.String()
        department = graphene.Int()
        user_profile = graphene.Int()
        document = graphene.List(graphene.Int)
        user = graphene.Int()
        education_qualification = graphene.String()
        designation = graphene.String()
        email = graphene.String()
        mobile = graphene.String()
        alt_mobile = graphene.String()
        aadhaar_no = graphene.String()
        pan_no = graphene.String()
        work_start_time = graphene.Time()
        work_end_time = graphene.Time()
        week_off_days = graphene.String()
        uan_no = graphene.String()
        esi_no = graphene.String()
        employee_education = graphene.String()
        experience_year = graphene.Int()
        experience_months = graphene.Int()
        training = graphene.String()
        present_address = graphene.Int()
        permanent_address = graphene.Int()
        remark = graphene.String()
        bank_account_no = graphene.String()
        ifsc_code = graphene.String()
        bank_name = graphene.String()
        branch = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int(required = True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    Employee_instance = graphene.Field(Employee_type)

    @mutation_permission("Employee", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        Employee_instance = None

        if "id" in kwargs and kwargs['id']:
            print(kwargs['id'])
            Employee_instance = Employee.objects.filter(id=kwargs['id']).first()
            if not Employee_instance:
                errors.append("Employee not found")
                return EmployeeCreateMutation(
                    Employee_instance=Employee_instance,
                    success=success,
                    errors=errors)
            else:
                serializer = EmployeeSerializer(Employee_instance, data=kwargs, partial=True)
        else:
            serializer = EmployeeSerializer(data=kwargs)
        print("serializer.is_valid()",serializer.is_valid())
        if serializer and serializer.is_valid():
            try:
                serializer.save()
                print("serializer.instance",serializer.instance)
                Employee_instance = serializer.instance
                success = True
            except CommonError as e:
                print("--", e)
                errors.append(str(e))
            except Exception as e:
                print("e", e)
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return EmployeeCreateMutation(
            Employee_instance=Employee_instance,
            success=success,
            errors=errors)


class EmployeeDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Employee", create_action="Create", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            employee_instance = Employee.objects.get(id=id)
            employee_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except Employee.DoesNotExist:
            errors.append('Employee query does not exist.')
        except ProtectedError:
            errors.append('Employee is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return EmployeeDeleteMutation(success=success, errors=errors)


"""Employee End"""
"""ExpenseRequest Start"""


class ExpenseRequestCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        expense_request_date = graphene.Date()
        employee_name = graphene.Int()
        request_amount = graphene.Decimal()
        expense_for = graphene.String()
        is_cancel = graphene.Boolean()
        approved_by = graphene.Int()
        pay_by = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    ExpenseRequest_instance = graphene.Field(ExpenseRequest_type)

    @mutation_permission("ExpenseRequest", create_action="Request", edit_action=None , edit_extra_actions=["Edit", "Approve","Pay"])
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        ExpenseRequest_instance = None

        if "id" in kwargs and kwargs['id']:
            ExpenseRequest_instance = ExpenseRequest.objects.get(id=kwargs['id'])
            if not ExpenseRequest_instance:
                errors.append("ExpenseRequest not found")
            else:
                serializer = ExpenseRequestSerializer(ExpenseRequest_instance, data=kwargs, partial=True)
        else:
            serializer = ExpenseRequestSerializer(data=kwargs)

        if serializer and serializer.is_valid():
            try:
                serializer.save()
                ExpenseRequest_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return ExpenseRequestCreateMutation(
            ExpenseRequest_instance=ExpenseRequest_instance,
            success=success,
            errors=errors)


class ExpenseRequestDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @mutation_permission("ExpenseRequest", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            ExpenseRequest_instance = ExpenseRequest.objects.get(id=id)
            ExpenseRequest_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except ExpenseRequest.DoesNotExist:
            errors.append('Expense Request query does not exist.')
        except ProtectedError:
            errors.append('Expense Request is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return EmployeeDeleteMutation(success=success, errors=errors)


class ExpenseRequestCancleMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("ExpenseRequest", create_action="Save", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            ExpenseRequest_instance = ExpenseRequest.objects.get(id=id)
            ExpenseRequest_instance.is_cancel = True
            ExpenseRequest_instance.save()
            success = True
        except ExpenseRequest.DoesNotExist:
            errors.append('Expense Request query does not exist.')
        except Exception as e:
            errors.append(str(e))
        return ExpenseRequestCancleMutation(success=success, errors=errors)


"""ExpenseRequest Start"""
"""ExpenseCategories Start"""


class ExpenseCategoriesCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        expense_category_name = graphene.String()
        account_name = graphene.Int()
        active = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    ExpenseCategories_instance = graphene.Field(ExpenseCategories_type)

    @mutation_permission("ExpenseCategories", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        success = False
        errors = []
        ExpenseCategories_instance = None

        if "id" in kwargs and kwargs['id']:
            ExpenseCategories_instance = ExpenseCategories.objects.filter(id=kwargs['id']).first()
            if not ExpenseCategories_instance:
                errors.append("Expense Categories not found")
            else:
                serializer = ExpenseCategoriesSerializer(ExpenseCategories_instance, data=kwargs, partial=True)
        else:
            serializer = ExpenseCategoriesSerializer(data=kwargs)

        if serializer and serializer.is_valid():
            try:
                serializer.save()
                ExpenseCategories_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]

        return ExpenseCategoriesCreateMutation(
            ExpenseCategories_instance=ExpenseCategories_instance,
            success=success,
            errors=errors)


class ExpenseCategoriesDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("ExpenseCategories", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            ExpenseCategories_instance = ExpenseCategories.objects.get(id=id)
            ExpenseCategories_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except ExpenseCategories.DoesNotExist:
            errors.append('Expense Categories query does not exist.')
        except ProtectedError:
            errors.append('Expense Categories is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return ExpenseCategoriesDeleteMutation(success=success, errors=errors)


"""ExpenseCategories End"""

"""ExpenseClaim Start"""


class ExpenseClaimDetailsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        date_of_exp = graphene.Date()
        expense_categories = graphene.Int()
        descriptions = graphene.String()
        claim_amount = graphene.Decimal()
        approved_amount = graphene.Decimal()
        gst_in = graphene.Boolean()
        pdf_url = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    ExpenseClaimDetails_instance = graphene.Field(ExpenseClaimDetails_type)

    def mutate(self, info, **kwargs):
        success = False
        errors = []
        ExpenseClaimDetails_instance = None

        if "id" in kwargs and kwargs['id']:
            ExpenseClaimDetails_instance = ExpenseClaimDetails.objects.filter(id=kwargs['id']).first()
            if not ExpenseClaimDetails_instance:
                errors.append("Expense Claim Details not found")
            else:
                serializer = ExpenseClaimDetailsSerializer(ExpenseClaimDetails_instance, data=kwargs, partial=True)
        else:
            serializer = ExpenseClaimDetailsSerializer(data=kwargs)

        if serializer and serializer.is_valid():
            try:
                serializer.save()
                ExpenseClaimDetails_instance = serializer.instance
                success = True
            except Exception as e:
                errors.append(str(e))
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ExpenseClaimDetailsCreateMutation(
            ExpenseClaimDetails_instance=ExpenseClaimDetails_instance,
            success=success,
            errors=errors)


class ExpenseClaimDetailsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.List(graphene.Int)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            # Use filter to get all matching records, and delete them
            ExpenseClaimDetails_instances = ExpenseClaimDetails.objects.filter(id__in=id)

            # If no records are found, handle it
            if not ExpenseClaimDetails_instances.exists():
                errors.append('No matching Expense Claim Details found.')
            else:
                # Delete all matched records
                ExpenseClaimDetails_instances.delete()
                success = True
        except ProtectedError:
            errors.append('Some Expense Claim Details are linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(f"An unexpected error occurred: {str(e)}")
        return ExpenseClaimDetailsDeleteMutation(success=success, errors=errors)


class ExpenseClaimCreateMutation(graphene.Mutation):
        class Arguments:
            id = graphene.ID()
            expense_claim_date = graphene.Date()
            employee_id = graphene.Int()
            status = graphene.String()
            reimburse_amount = graphene.Decimal()
            balance_amount = graphene.Decimal()
            expense_claim_details = graphene.List(ExpenseClaimDetailInput)
            modified_by = graphene.Int()
            created_by = graphene.Int()
                    
        success = graphene.Boolean()
        errors = graphene.List(graphene.String)
        ExpenseClaim_instance = graphene.Field(ExpenseClaim_type)

        @mutation_permission("ExpenseClaim", create_action="Draft", edit_action=None, edit_extra_actions=["Edit", "Save"])
        def mutate(self, info, **kwargs):
            success = False
            errors = []
            expense_details_instances = []
            total_approved_amount = Decimal("0.000")
            ExpenseClaim_instance = None
            try:
                if "status" in kwargs and kwargs["status"]:
                    statusObjects = CommanStatus.objects.filter(name=kwargs["status"], table="ExpenseClaim").first()
                    if statusObjects:
                        kwargs["status"] = statusObjects.id
                    else:
                        status = kwargs.get("status", "default_status")  # Provide a default value if 'status' is not in kwargs
                        errors.append(f"Ask devopole to add ${status}")
                        return ExpenseClaimCreateMutation(ExpenseClaim_instance=ExpenseClaim_instance, success=success,
                                                        errors=errors)

                if "expense_claim_details" in kwargs and kwargs['expense_claim_details']:
                    try:
                        details_data = kwargs.pop("expense_claim_details", [])
                        for detail in details_data:
                            detail_id = detail.get("id")
                            if detail_id:
                                # Update existing ExpenseClaimDetails
                                detail_obj = ExpenseClaimDetails.objects.get(id=detail_id)
                            else:
                                # Create new ExpenseClaimDetails
                                detail_obj = ExpenseClaimDetails()
                            # Assign fields
                            detail_obj.date_of_exp = detail.get("date_of_exp")
                            detail_obj.expense_categories_id = detail.get("expense_categories")
                            detail_obj.descriptions = detail.get("descriptions")
                            detail_obj.claim_amount = Decimal(detail.get("claim_amount"or 0))
                            detail_obj.approved_amount = Decimal(detail.get("approved_amount") or 0)
                            detail_obj.gst_in = detail.get("gst_in", False)
                            if kwargs['modified_by']:
                                detail_obj.modified_by_id = kwargs['modified_by']
                            if not detail_id and kwargs['created_by']:
                                detail_obj.created_by_id = kwargs['created_by']

                            detail_obj.save()

                            if "pdf_url" in detail:
                                detail_obj.pdf_url.set(detail["pdf_url"])
                            expense_details_instances.append(detail_obj)

                            total_approved_amount += detail_obj.approved_amount or Decimal("0.000")
                    
                    except Exception as e:
                        errors.append(str(e))
                        return ExpenseClaimCreateMutation(success=False,errors=errors,ExpenseClaim_instance=None)

                # Create or update ExpenseClaim
                if "id" in kwargs and kwargs["id"]:
                    expense_claim = ExpenseClaim.objects.get(id=kwargs["id"])
                else:
                    expense_claim = ExpenseClaim()

                expense_claim.expense_claim_date = kwargs.get("expense_claim_date")
                expense_claim.employee_id_id = kwargs.get("employee_id")
                expense_claim.status_id = kwargs.get("status")
                expense_claim.reimburse_amount = kwargs.get("reimburse_amount", Decimal("0.000"))
                expense_claim.balance_amount = kwargs.get("balance_amount", Decimal("0.000"))
                expense_claim.total_approved_amount = total_approved_amount

                if kwargs['modified_by']:
                    expense_claim.modified_by_id = kwargs['modified_by']
                if not getattr(expense_claim, 'id', None) and kwargs['created_by']:
                    expense_claim.created_by_id = kwargs['created_by']

                expense_claim.save()

                expense_claim.expense_claim_details.set(expense_details_instances)

                success = True
                return ExpenseClaimCreateMutation(
                    success=success,
                    errors=[],
                    ExpenseClaim_instance=expense_claim
                )
            except Exception as e:
                errors.append(str(e))
                return ExpenseClaimCreateMutation(success=False, errors=errors,ExpenseClaim_instance=None)


class ExpenseClaimDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("ExpenseClaim", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            ExpenseClaim_instance = ExpenseClaim.objects.get(id=id)
            ExpenseClaim_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except ExpenseClaim.DoesNotExist:
            errors.append('Expense Claim query does not exist.')
        except ProtectedError:
            errors.append('Expense Claim is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return ExpenseClaimDeleteMutation(success=success, errors=errors)


class ExpenseClaimCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("ExpenseClaim", create_action="Create", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            # Get the voucher instance
            expense_claim = ExpenseClaim.objects.get(id=id)

            # Fetch the "Cancelled" status from CommanStatus
            cancel_status = CommanStatus.objects.filter(name="Canceled", table="ExpenseClaim").first()

            if cancel_status:
                # Update the status to "Cancelled"
                expense_claim.status = cancel_status
                expense_claim.save()
                success = True
            else:
                errors.append("Cancel status not found in CommanStatus for PaymentVoucher.")

        except ExpenseClaim.DoesNotExist:
            errors.append("Expense Claim does not exist.")
        except ProtectedError:
            errors.append("Expense Claim is linked with other modules and cannot be deleted.")
        except Exception as e:
            errors.append(str(e))

        return ExpenseClaimCancelMutation(success=success, errors=errors)


"""ExpenseClaim End"""

"""PaymentVoucher Start"""


class PaymentVoucherAdvanceDetailsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        adv_remark = graphene.String()
        amount = graphene.Decimal()
        modified_by = graphene.Int()
        created_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    PaymentVoucherAdvanceDetails_instance = graphene.Field(PaymentVoucherAdvanceDetails_type)

    def mutate(self, info, **kwargs):
        PaymentVoucherAdvanceDetails_instance = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id']:
            # Update operation
            PaymentVoucherAdvanceDetails_instance = PaymentVoucherAdvanceDetails.objects.filter(id=kwargs['id']).first()
            if not PaymentVoucherAdvanceDetails_instance:
                errors.append("Payment Voucher Advance Details Not Found.")
            else:
                serializer = PaymentVoucherAdvanceDetailsSerializer(PaymentVoucherAdvanceDetails_instance, data=kwargs,
                                                                    partial=True)
        else:
            serializer = PaymentVoucherAdvanceDetailsSerializer(data=kwargs)
        if serializer.is_valid() and len(errors) == 0:
            serializer.save()
            PaymentVoucherAdvanceDetails_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return PaymentVoucherAdvanceDetailsCreateMutation(
            PaymentVoucherAdvanceDetails_instance=PaymentVoucherAdvanceDetails_instance,
            success=success, errors=errors)


class PaymentVoucherAdvanceDetailsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            PaymentVoucherAdvanceDetails_instance = PaymentVoucherAdvanceDetails.objects.get(id=id)
            PaymentVoucherAdvanceDetails_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except PaymentVoucherAdvanceDetails.DoesNotExist:
            errors.append('Payment Voucher Advance Details query does not exist.')
        except ProtectedError:
            errors.append('Payment Voucher Advance Details is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return PaymentVoucherAdvanceDetailsDeleteMutation(success=success, errors=errors)



def pre_validate_payment(kwargs, required_fields):
    errors = []    
    # Check for general required fields
    missing = [field for field in required_fields if not kwargs.get(field)]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    
    # Handle advance_details validation
    advance_details = kwargs.get('advance_details')
    cus_sup_amount = kwargs.get('cus_sup_amount')

    if advance_details:
        total_advance = 0
        for i, adv in enumerate(advance_details):
            if not adv.get('adv_amount'):
                errors.append(f"Advance detail at index {i + 1} is missing 'adv_amount'")
            if not adv.get('adv_remarks'):
                errors.append(f"Advance detail at index {i + 1} is missing 'advRemarks'")
            try:
                total_advance += float(adv.get('adv_amount', 0))
            except (ValueError, TypeError):
                errors.append(f"Invalid 'adv_amount' at index {i + 1}")

        if cus_sup_amount is not None and round(total_advance, 2) != round(float(cus_sup_amount), 2):
            errors.append(f"Sum of advance amounts ({total_advance}) does not match Cus/Sup Amount ({cus_sup_amount})")

   # Employee validation logic (if employee_id exists and is not None)
    if 'employee_id' in kwargs and kwargs['employee_id'] is not None:
        if kwargs.get('emp_amount') is None:
            errors.append("Employee amount ('emp_amount') is required when 'employee_id' is provided.")
        if kwargs.get('pay_for') is None:
            errors.append("Field 'pay_for' is required when 'employee_id' is provided.")

    elif 'cus_sup_id' in kwargs and kwargs['cus_sup_id'] is not None:
            if kwargs.get('cus_sup_amount') is None:
                errors.append("Cus/Sup Amount ('cus_sup_amount') is required when 'cus_sup_id' is provided.")

            # Check if pay_mode is "Bank" before validating bank-related fields
            pay_mode_id = kwargs.get('pay_mode')
            if pay_mode_id:
                try:
                    pay_mode = PaymentVoucherPaymode.objects.get(id=pay_mode_id)
                    if pay_mode.name.lower() == "bank":
                        if kwargs.get('bank') is None and kwargs.get('transfer_via') is None:
                            errors.append("Either 'bank' or 'transfer_via' must be provided when pay_mode is 'Bank'.")
                        if kwargs.get('chq_ref_no') is None:
                            errors.append("Cheque reference number ('chq_ref_no') is required when pay_mode is 'Bank'.")
                        if kwargs.get('chq_date') is None:
                            errors.append("Cheque date ('chq_date') is required when pay_mode is 'Bank'.")
                except PaymentVoucherPaymode.DoesNotExist:
                    errors.append("Invalid 'pay_mode' provided.")
    return errors

def SaveAdvanceValues(data):
    saved_advance_ids = []
    for adv in data:
        adv_id = adv.get('id')
        if adv_id:
            # Update existing advance detail
            try:
                advance_obj = PaymentVoucherAdvanceDetails.objects.get(id=adv_id)
                advance_obj.adv_remark = adv.get('adv_remarks', advance_obj.adv_remark)
                advance_obj.amount = adv.get('adv_amount', advance_obj.amount)
                advance_obj.remaining = adv.get('adv_amount', advance_obj.remaining)
                advance_obj.modified_by_id = adv.get('modified_by', advance_obj.modified_by_id)
                advance_obj.save()
            except PaymentVoucherAdvanceDetails.DoesNotExist:
                continue  # or collect error
        else:
            # Create new advance detail
            advance_obj = PaymentVoucherAdvanceDetails.objects.create(
                adv_remark=adv.get('adv_remarks', ''),
                amount=adv.get('adv_amount'),
                remaining=adv.get('adv_amount'),
                created_by_id=adv.get('created_by'),
                modified_by_id=adv.get('modified_by')
            )
        saved_advance_ids.append(advance_obj.id)
    return saved_advance_ids

class PaymentVoucherAgainstInvoiceInput(graphene.InputObjectType):
    id = graphene.ID()
    purchase_invoice_no = graphene.String(required=True)
    purchase_invoice = graphene.Int(required=True)
    adjusted = graphene.String(required=True)
    remarks = graphene.String()

class AdvanceInput(graphene.InputObjectType):
    id = graphene.ID()
    amount = graphene.Decimal(required=True)
    adv_remark = graphene.String(required=True)

class PaymentVoucherLineInput(graphene.InputObjectType):
    id = graphene.ID()
    account_name = graphene.String()
    account = graphene.Int()
    employee_name = graphene.String()
    employee = graphene.Int()
    pay_for = graphene.Int()
    cus_sup_name = graphene.String()
    cus_sup = graphene.Int()
    amount = graphene.Decimal()
    advance_details = graphene.List(AdvanceInput)
    against_invoice_details = graphene.List(PaymentVoucherAgainstInvoiceInput)



class PaymentVoucherCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.String()
        date = graphene.Date()
        pay_by = graphene.String()
        pay_mode = graphene.String()
        currency = graphene.Int()
        exchange_rate = graphene.Decimal()
        expense_request_id = graphene.Decimal()
        against_invoice = graphene.Boolean()
        advance = graphene.Boolean()
        bank = graphene.Int()
        transfer_via = graphene.String()
        chq_ref_no = graphene.String()
        chq_date = graphene.Date()
        payment_voucher_line = graphene.List(PaymentVoucherLineInput)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    PaymentVoucher_instance = graphene.Field(PaymentVoucher_type)

    @mutation_permission("PaymentVoucher", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
       
        status_str = kwargs['status']
        service = PaymentVoucherService(kwargs, status_str, info)
        pv_result = service.process()

        return PaymentVoucherCreateMutation(PaymentVoucher_instance=pv_result['payment_voucher'],
                                            success=pv_result['success'], errors=pv_result['errors'])


# class PaymentVoucherCreateMutation(graphene.Mutation):
#     class Arguments:
#         id = graphene.ID()
#         status = graphene.String()
#         date = graphene.Date()
#         pay_to = graphene.Int()
#         pay_mode = graphene.Int()
#         expense_request_id = graphene.Decimal()
#         employee_id = graphene.Int()
#         pay_for = graphene.Int()
#         pay_via = graphene.Int()
#         emp_amount = graphene.Decimal()
#         blance_emp_amount = graphene.Decimal()
#         cus_sup_id = graphene.Int()
#         cus_sup_amount = graphene.Decimal()
#         against_invoice = graphene.Boolean()
#         advance = graphene.Boolean()
#         against_invoice_details = graphene.List(PaymentVoucherAgainstInvoiceInput)
#         advance_details = graphene.List(AdvanceInput)
#         bank = graphene.Int()
#         transfer_via = graphene.Int()
#         chq_ref_no = graphene.String()
#         chq_date = graphene.Date()
#         modified_by = graphene.Int()
#         created_by = graphene.Int()

#     success = graphene.Boolean()
#     errors = graphene.List(graphene.String)
#     PaymentVoucher_instance = graphene.Field(PaymentVoucher_type)

#     @mutation_permission("PaymentVoucher", create_action="Save", edit_action="Edit")
#     def mutate(self, info, **kwargs):
#         PaymentVoucher_instance = None
#         success = False
#         errors = []
#         status_str = kwargs['status']
#         accounts_general_ledger_data = None

#         """Check the Status"""
#         if kwargs['status']:
#             status = CommanStatus.objects.filter(name=kwargs['status'], table="PaymentVoucher").first()
#             if status:
#                 kwargs['status'] = status.id
#             else:
#                 errors.append(f"Ask Admin To Add The {kwargs['status']}")
#                 return PaymentVoucherCreateMutation(PaymentVoucher_instance=PaymentVoucher_instance,
#                                                     success=success, errors=errors)
        
#         """ Validations for payment """
#         validation_errors = pre_validate_payment(kwargs,['date', 'pay_to', 'pay_mode','pay_via'])
#         if validation_errors:
#             errors.extend(validation_errors)
#             return PaymentVoucherCreateMutation(
#                 PaymentVoucher_instance=PaymentVoucher_instance,
#                 success=success,
#                 errors=errors
#             )
#         if kwargs['advance_details'] and len(kwargs['advance_details'])> 0:
#             saved_advance_ids = SaveAdvanceValues(kwargs['advance_details'])
#             kwargs['advance_details'] = saved_advance_ids
#         if 'id' in kwargs and kwargs['id']:
#             # Update operation
#             PaymentVoucher_instance = PaymentVoucher.objects.filter(id=kwargs['id']).first()
#             if not PaymentVoucher_instance:
#                 errors.append("Payment Voucher Not Found.")
#             else:
#                 serializer = PaymentVoucherSerializer(PaymentVoucher_instance, data=kwargs, partial=True)
#                 if status_str == "Submit":
#                     accounts_general_ledger_data = {
#                             "date":kwargs['date'],
#                             "DebitAccount":kwargs['pay_for'],
#                             'amount':kwargs['emp_amount'],
#                             "customer_supplier":'',
#                             "employee":kwargs['employee_id'],
#                             'remark':"",
#                             'created_by':kwargs['created_by'],
#                             'payment_voucher_no':kwargs['id'],
#                             "creditAccount":kwargs['pay_via']}
#                     result_of_gl = CreateAccountGeneralLedger(accounts_general_ledger_data, True)
#                     if not result_of_gl.get('success'):
#                         errors.append(result_of_gl.get('errors'))
#                         errors.append('ask Dev to fix Bug.')
#                         return PaymentVoucherCreateMutation(PaymentVoucher_instance=PaymentVoucher_instance,
#                                                 success=success, errors=errors)
#         else:
#             serializer = PaymentVoucherSerializer(data=kwargs)
        
#         if serializer.is_valid():
#             serializer.save()
#             PaymentVoucher_instance = serializer.instance
#             success = True
#             if status_str == "Submit":
#                 CreateAccountGeneralLedger(accounts_general_ledger_data, False)
            
#         else:
#             errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
#         return PaymentVoucherCreateMutation(PaymentVoucher_instance=PaymentVoucher_instance,
#                                             success=success, errors=errors)


class PaymentVoucherDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("PaymentVoucher", create_action="Create", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            PaymentVoucher_instance = PaymentVoucher.objects.get(id=id)
            if not PaymentVoucher_instance:
                errors.append("Payment voucher did'n fount.")
                return PaymentVoucherDeleteMutation(success=success, errors=errors)
            
            if not PaymentVoucher_instance.status.name == "Canceled":
                errors.append("“Before deleting, you need to cancel the payment voucher.”")
                return PaymentVoucherDeleteMutation(success=success, errors=errors)

            PaymentVoucher_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
        except PaymentVoucher_instance.DoesNotExist:
            errors.append('Payment Voucher query does not exist.')
        except ProtectedError:
            errors.append('Payment Voucher is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return PaymentVoucherDeleteMutation(success=success, errors=errors)
    
class PaymentVoucherCancelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("PaymentVoucher", create_action="Create", edit_action="Cancel")
    def mutate(self, info, id):
        success = False
        errors = []

        try:
            # Get the voucher instance
            payment_voucher = PaymentVoucher.objects.get(id=id)

            # Fetch the "Cancelled" status from CommanStatus
            cancel_status = CommanStatus.objects.filter(name="Canceled", table="Payment Voucher").first()
            """
            On Cancle dlete the AccountsGeneralLedger
            """
            try:
                AGL = AccountsGeneralLedger.objects.filter(payment_voucher_no=id)
                AGL.delete()
            except AccountsGeneralLedger.DoesNotExist:
                errors.append("Accounts General Ledger Did Not Found")
            except:
                errors.append("Unexception occurred on delete Accounts General Ledger")
            if cancel_status and len(errors) <= 0:
                # Update the status to "Cancelled"
                payment_voucher.status = cancel_status
                payment_voucher.save()
                success = True
            else:
                errors.append("Cancel status not found in CommanStatus for PaymentVoucher.")

        except PaymentVoucher.DoesNotExist:
            errors.append("Payment Voucher does not exist.")
        except ProtectedError:
            errors.append("Payment Voucher is linked with other modules and cannot be deleted.")
        except Exception as e:
            errors.append(str(e))

        return PaymentVoucherCancelMutation(success=success, errors=errors)
"""PaymentVoucher End"""


class ExpenseReconciliationCallFormExpenseClaim(graphene.Mutation):
    class Arguments:
        employee_id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    PaymentVoucher_instence = graphene.List(PaymentVoucher_type)

    @mutation_permission("ExpenseClaim", create_action="Verify", edit_action="Edit")
    def mutate(self, info, employee_id):
        PaymentVoucher_instence = None
        success = False
        errors = []
        try:
            status = CommanStatus.objects.filter(name="Submit", table="Payment Voucher").first()
            if not status:
                errors.append("Submitted status not found.")
            else:
                # Fetch vouchers with 'Submit' status, employee_id and not claimed
                PaymentVoucher_instence = PaymentVoucher.objects.filter(
                    employee_id=employee_id,
                    is_claim=False,
                    status=status
                )
                success = True
        except Exception as e:
            errors.append(e)
        return ExpenseReconciliationCallFormExpenseClaim(success=success, errors=errors,
                                                         PaymentVoucher_instence=PaymentVoucher_instence)


"""ExpenseReconciliation start"""


# class ExpenseReconciliationDetailsInput(graphene.InputObjectType):
#     id = graphene.ID()
#     paymentVoucher_id = graphene.Int()
#     adjusted_amount = graphene.Decimal()
#     claim_id = graphene.Int()
#     modified_by = graphene.Int()
#     created_by = graphene.Int()


# class ExpenseReconciliationDetailsCreateMutation(graphene.Mutation):
#     class Arguments:
#         items = graphene.List(ExpenseReconciliationDetailsInput)

#     success = graphene.Boolean()
#     errors = graphene.List(graphene.String)
#     expense_reconciliation_details_instance = graphene.List(expense_reconciliation_details_type)
#     current_expense_claim = graphene.Field(ExpenseClaim_type)

#     def mutate(self, info, items):
#         expense_reconciliation_details_instance = []
#         success = False
#         errors = []

#         for item in items:
#             if item.get('claim_id'):
#                 try:
#                     current_expense_claim = ExpenseClaim.objects.get(id=item['claim_id'])
#                 except ExpenseClaim.DoesNotExist:
#                     errors.append("Expense Claim Not Found.")
#                     continue  # Proceed with the next item instead of returning immediately

#                 if current_expense_claim:
#                     try:
#                         if item.get('id'):
#                             expense_reconciliation_details_ = ExpenseReconciliationDetails.objects.get(id=item['id'])
#                             serializer = ExpenseReconciliationDetailsSerializer(expense_reconciliation_details_,
#                                                                                 data=item, partial=True)
#                         else:
#                             serializer = ExpenseReconciliationDetailsSerializer(data=item)
#                     except ExpenseReconciliationDetails.DoesNotExist:
#                         errors.append("Expense reconciliation Details instance Not Found.")
#                         continue  # Proceed with the next item

#                     if serializer.is_valid():
#                         reconciliation_details_instance = serializer.save()

#                         # Process the payment voucher logic
#                         payment_id = reconciliation_details_instance.paymentVoucher_id
#                         if payment_id:
#                             payment_amount = payment_id.emp_amount
#                             balance_emp_amount = payment_id.blance_emp_amount
#                             adjusted_amount = reconciliation_details_instance.adjusted_amount

#                             # Balance calculation logic
#                             if balance_emp_amount is not None and balance_emp_amount > 0:
#                                 balance = adjusted_amount - balance_emp_amount
#                                 if balance == 0:
#                                     payment_id.is_claim = True
#                                     payment_id.blance_emp_amount = 0
#                                 else:
#                                     payment_id.blance_emp_amount = balance
#                             else:
#                                 balance = payment_amount - adjusted_amount
#                                 if balance == 0:
#                                     payment_id.is_claim = True
#                                     payment_id.blance_emp_amount = 0
#                                 else:
#                                     payment_id.blance_emp_amount = balance
#                                     payment_id.is_claim = False
#                             payment_id.save()

#                         expense_reconciliation_details_instance.append(reconciliation_details_instance)
#                         current_expense_claim.expense_reconciliation_details.add(reconciliation_details_instance)
#                         current_expense_claim.save()

#                     else:
#                         errors.extend([f"{field}: {'; '.join([str(e) for e in error])}" for field, error in
#                                        serializer.errors.items()])
#                 else:
#                     errors.append("Expense Claim Not Found.")

#         success = len(expense_reconciliation_details_instance) > 0
#         return ExpenseReconciliationDetailsCreateMutation(
#             expense_reconciliation_details_instance=expense_reconciliation_details_instance,
#             success=success,
#             errors=errors,
#             current_expense_claim=current_expense_claim if success else None
#         )

class ExpenseReconciliationDetailsInput(graphene.InputObjectType):
    id = graphene.ID()
    paymentVoucher_id = graphene.Int()
    adjusted_amount = graphene.Decimal()
    modified_by = graphene.Int()
    created_by = graphene.Int()


class ExpenseReconciliationDetailsCreateMutation(graphene.Mutation):
    class Arguments:
        items = graphene.List(ExpenseReconciliationDetailsInput)
        reimburse_amount = graphene.Decimal()
        balance_amount = graphene.Decimal()
        claim_id = graphene.Decimal()
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    expense_reconciliation_details_instance = graphene.List(expense_reconciliation_details_type)
        
    @mutation_permission("ExpenseClaim", create_action="Save", edit_action="Edit")
    def mutate(self, info, items, reimburse_amount, balance_amount, claim_id):
        expense_reconciliation_details_instance = []
        success = False
        errors = []

        try:
            # Step 1: Create or update reconciliation detail records
            for item in items:
                if item.id:
                    # Update existing entry
                    recon_detail = ExpenseReconciliationDetails.objects.get(id=item.id)
                    recon_detail.adjusted_amount = item.adjusted_amount
                    recon_detail.modified_by_id = item.modified_by
                else:
                    # Create new entry
                    recon_detail = ExpenseReconciliationDetails(
                        paymentVoucher_id_id=item.paymentVoucher_id,
                        adjusted_amount=item.adjusted_amount,
                        modified_by_id=item.modified_by,
                        created_by_id=item.created_by
                    )
                recon_detail.save()
                expense_reconciliation_details_instance.append(recon_detail)

                # ✅ Check and update PaymentVoucher fields
                payment_voucher = recon_detail.paymentVoucher_id
                if payment_voucher and recon_detail.adjusted_amount is not None and payment_voucher.emp_amount is not None:
                    adjusted = float(recon_detail.adjusted_amount)
                    balance = float(payment_voucher.blance_emp_amount or payment_voucher.emp_amount)

                    new_balance = balance - adjusted
                    payment_voucher.blance_emp_amount = new_balance

                    if new_balance == 0:
                        payment_voucher.is_claim = True

                    payment_voucher.save()

            # Step 2: Update the claim and associate reconciliation details
            claim = ExpenseClaim.objects.get(id=claim_id)
            for recon_detail in expense_reconciliation_details_instance:
                claim.expense_reconciliation_details.add(recon_detail)
            claim.reimburse_amount = reimburse_amount
            claim.balance_amount = balance_amount
            status = CommanStatus.objects.filter(name="Verified", table="ExpenseClaim").first()
            if status:
                claim.status = status  
            else:
                errors.append(f"Ask Admin To Add The Verify Status For Expense Claim")
                return ExpenseReconciliationDetailsCreateMutation(
                    success=success,
                    errors=errors,
                    expense_reconciliation_details_instance=expense_reconciliation_details_instance
                )
            claim.save()

            success = True

        except ExpenseClaim.DoesNotExist:
            errors.append(f"ExpenseClaim with id {claim_id} not found.")
        except ExpenseReconciliationDetails.DoesNotExist:
            errors.append("One or more reconciliation detail records could not be found.")
        except Exception as e:
            errors.append(str(e))

        return ExpenseReconciliationDetailsCreateMutation(
            success=success,
            errors=errors,
            expense_reconciliation_details_instance=expense_reconciliation_details_instance
        )

                    
class ExpenseReconciliationDetailsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            ExpenseReconciliationDetails_instance = ExpenseReconciliationDetails.objects.get(id=id)
            paymentMode_id = ExpenseReconciliationDetails_instance.paymentVoucher_id
            ExpenseReconciliationDetails_instance.delete()  # This will invoke the delete method and clear related permissions
            success = True
            paymentMode_id.is_claim = False
            paymentMode_id.save()

        except ExpenseReconciliationDetails.DoesNotExist:
            errors.append('Expense Reconciliation Details query does not exist.')
        except ProtectedError:
            errors.append('Expense Reconciliation Details is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return ExpenseReconciliationDetailsDeleteMutation(success=success, errors=errors)


"""ExpenseReconciliation end"""


class HolidaysCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        no_of_days = graphene.Int()
        from_date = graphene.Date()
        to_date = graphene.Date()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    holiday_data_item = graphene.Field(holiday_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Holidays", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        holiday_data_item = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id'] is not None:
            holiday_data_item = Holidays.objects.filter(id=kwargs['id']).first()
            if not holiday_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = HolidaySerializer(holiday_data_item, data=kwargs, partial=True)
        else:
            serializer = HolidaySerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            holiday_data_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return HolidaysCreateMutation(holiday_data_item=holiday_data_item, success=success, errors=errors)


class HolidaysDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("Holidays", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            holiday_instance = Holidays.objects.get(id=id)
            holiday_instance.delete()
            success = True
        except Holidays.DoesNotExist:
            errors.append('Holiday  query does not exist.')
        except ProtectedError:
            errors.append('Holiday is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return HolidaysDeleteMutation(success=success, errors=errors)


class LeaveTypeCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
        leave_type = graphene.String()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    leave_type_data_item = graphene.Field(leave_type_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("LeaveType", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        leave_type_data_item = None
        success = False
        errors = []
        if 'id' in kwargs and kwargs['id'] is not None:
            leave_type_data_item = LeaveType.objects.filter(id=kwargs['id']).first()
            if not leave_type_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = LeaveTypeSerializer(leave_type_data_item, data=kwargs, partial=True)
        else:
            serializer = LeaveTypeSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            leave_type_data_item = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return LeaveTypeCreateMutation(leave_type_data_item=leave_type_data_item, success=success, errors=errors)


class LeaveTypeDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("LeaveType", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            leave_type_instance = LeaveType.objects.get(id=id)
            leave_type_instance.delete()
            success = True
        except LeaveType.DoesNotExist:
            errors.append('Leave Type  query does not exist.')
        except ProtectedError:
            errors.append('Leave Type is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return LeaveTypeDeleteMutation(success=success, errors=errors)


class LeaveAllotedDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("LeaveAlloted", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []
        try:
            leave_type_instance = LeaveAlloted.objects.get(id=id)
            leave_type_instance.delete()
            success = True
        except LeaveType.DoesNotExist:
            errors.append('Leave Allotted  query does not exist.')
        except ProtectedError:
            errors.append('Leave Allotted is linked with other modules and cannot be deleted.')
        except Exception as e:
            errors.append(str(e))
        return LeaveAllotedDeleteMutation(success=success, errors=errors)


class LeaveCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        employee_id = graphene.Int()
        leave_day_type = graphene.String()
        from_date = graphene.Date()
        to_date = graphene.Date()
        applied_days = graphene.String()
        reason = graphene.String()
        approved_days = graphene.String()
        current_balance = graphene.String()
        leave_alloted = graphene.Int()
        status = graphene.String(required=True)
        created_by = graphene.Int()
        modified_by = graphene.Int()
    
    leave_data_item = graphene.Field(leave_modal_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("Leave", create_action="Save", edit_action="Edit")
    def mutate(self, info, **kwargs):
        serializer = ''
        leave_data_item = None
        success = False
        errors = []
        status = kwargs["status"]
        if kwargs["status"]:
            statusObjects = CommanStatus.objects.filter(name=kwargs["status"], table="Leave").first()
            if statusObjects:
                kwargs["status"] = statusObjects.id
            else:
                status = kwargs.get("status", "default_status")
                errors.append(f"Ask devopole to add ${status}")
                return LeaveCreateMutation(leave_data_item=leave_data_item, success=success,
                                           errors=errors)
        if 'id' in kwargs and kwargs['id'] is not None:
            if status != "Approved" or status == "Rejected":
                kwargs["approved_days"] = None
                kwargs["leave_alloted"] = None
                kwargs["current_balance"] = None
            leave_data_item = Leave.objects.filter(id=kwargs['id']).first()
            if not leave_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = LeaveSerializer(leave_data_item, data=kwargs, partial=True)
        else:
            if status != "Approved" or status == "Rejected":
                kwargs["approved_days"] = None
                kwargs["leave_alloted"] = None
                kwargs["current_balance"] = None
            serializer = LeaveSerializer(data=kwargs)
        try:
            if serializer.is_valid():
                leave_data_item = serializer.instance
                employee = kwargs['employee_id']
                if status == "Approved" or status == "Submit":
                    holiday_records = Holidays.objects.filter(
                        Q(from_date__range=[kwargs['from_date'], kwargs['to_date']]) | Q(
                            to_date__range=[kwargs['from_date'], kwargs['to_date']])
                    )
                    if len(holiday_records) > 0:
                        errors.append(
                            f"Leave cannot be applied. Employee is already have Holiday in Attendance for the selected dates."
                        )

                        return LeaveCreateMutation(leave_data_item=None, success=success, errors=errors)

                if status == "Approved" or status == "Submit":
                    leave_records = Leave.objects.filter(
                        Q(employee_id=employee) &
                        (
                                Q(from_date__range=(kwargs['from_date'], kwargs['to_date'])) |
                                Q(to_date__range=(kwargs['from_date'], kwargs['to_date']))
                        ) &
                        Q(status__name="Approved")  # Ensure only approved leaves are fetched
                    )
                    if len(leave_records) > 0:
                        errors.append(
                            f"Leave cannot be applied. Employee is already have Leave in Attendance for the selected dates."
                        )
                        return LeaveCreateMutation(leave_data_item=None, success=success, errors=errors)

                if status == "Approved" or status == "Submit":
                    leave_status = CommanStatus.objects.filter(name="Leave", table="AttendanceRegister").first()
                    attendance_records = AttendanceRegister.objects.filter(
                        Q(employee_id=employee) & Q(date__range=(kwargs["from_date"], kwargs["to_date"]))
                    )
                    if len(attendance_records) > 0:
                        for record in attendance_records:
                            if record.status.name == "Present":
                                errors.append(
                                    f"Leave cannot be applied. Employee is already marked as 'Present' in Attendance for the selected dates."
                                )
                                return LeaveCreateMutation(leave_data_item=None, success=success, errors=errors)
                            if record.status.name == "Leave":
                                errors.append(
                                    f"Leave cannot be applied. Employee is already marked as 'Leave' in Attendance for the selected dates."
                                )
                                return LeaveCreateMutation(leave_data_item=None, success=success, errors=errors)
                            if record.status.name == "Absent":
                                serializer.save()
                                leave_data_item = serializer.instance
                                record.status = leave_status
                                record.leave = leave_data_item
                                record.save()
                    else:
                        serializer.save()
                        leave_data_item = serializer.instance
                elif status == "Submit":
                    serializer.save()
                if status == "Approved":
                    leave_alloted_instance = LeaveAlloted.objects.filter(id=kwargs['leave_alloted']).first()
                    leave_alloted_instance.taken_leave = (leave_alloted_instance.taken_leave or 0) + int(
                        kwargs['approved_days'])
                    leave_alloted_instance.save()
                success = True
        except Exception as e:
            print("e", e)
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return LeaveCreateMutation(leave_data_item=leave_data_item, success=success, errors=errors)


class LeaveDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    @mutation_permission("Leave", create_action="Save", edit_action="Delete")
    def mutate(self, info, id):
        success = False
        errors = []

        try:
            leave_type_instance = Leave.objects.get(id=id)
            # If status is 'Approved' or 'Submit', delete the leave record
            if leave_type_instance.status.name in ["Submit"]:
                leave_type_instance.delete()
                success = True

        except Leave.DoesNotExist:
            errors.append("Leave query does not exist.")
        except ProtectedError:
            errors.append("Leave is linked with other modules and cannot be deleted.")
        except Exception as e:
            errors.append(str(e))

        return LeaveDeleteMutation(success=success, errors=errors)


def validate_existing_allotment(employee, leave_type, from_date, to_date):
    """Check if an employee already has a leave allotted for the same date range and leave type."""
    existing_allotment = LeaveAlloted.objects.filter(
        employee_id=employee,
        leave_type_id=leave_type,
        from_date=from_date,
        to_date=to_date
    ).exists()
    return existing_allotment


class LeaveAllotedCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        employee_id_list = graphene.List(graphene.Int)
        leave_type = graphene.Int()
        from_date = graphene.Date()
        to_date = graphene.Date()
        allotted_days = graphene.Int()
        created_by = graphene.Int()
        modified_by = graphene.Int()

    leave_alloted_data_item = graphene.List(leave_alloted_type)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @mutation_permission("LeaveAlloted", create_action="Save", edit_action="Edit")
    def mutate(self, info, id, employee_id_list, leave_type, from_date, to_date, allotted_days, created_by,
               modified_by):
        success = False
        errors = []
        try:
            existing_employees = Employee.objects.filter(id__in=employee_id_list)
            if not existing_employees:
                errors.append("No employees found with the given IDs.")
                return LeaveAllotedCreateMutation(success=False, errors=errors)

            leave_type_instance = LeaveType.objects.filter(id=leave_type).first()
            if not leave_type_instance:
                errors.append(f"LeaveType with ID {leave_type} not found.")
                return LeaveAllotedCreateMutation(success=False, errors=errors)

            # Validate created_by
            if not created_by:
                errors.append("Created By is required.")
                return LeaveAllotedCreateMutation(success=False, errors=errors)

            try:
                created_by_instance = User.objects.get(id=created_by)
            except User.DoesNotExist:
                errors.append(f"User with ID {created_by} not found.")
                return LeaveAllotedCreateMutation(success=False, errors=errors)

            # Validate modified_by (set to None if not provided)
            modified_by_instance = None
            if modified_by:
                try:
                    modified_by_instance = User.objects.get(id=modified_by)
                except User.DoesNotExist:
                    errors.append(f"User with ID {modified_by} not found.")

            leave_alloted_instances = []
            for employee in existing_employees:
                if id is None:
                    if validate_existing_allotment(employee, leave_type, from_date, to_date):
                        errors.append(
                            f"Leave is already allotted for {employee.employee_name} on this type and on this financial year.")
                        continue
                    try:
                        instance = LeaveAlloted(employee_id=employee, leave_type=leave_type_instance,
                                                from_date=from_date, to_date=to_date, allotted_days=allotted_days,
                                                created_by=created_by_instance, modified_by=modified_by_instance)
                        instance.save()
                        success = True
                        leave_alloted_instances.append(instance)
                    except Exception as e:
                        print("e", e)
                        errors.append(str(e))
                else:  # Update case
                    try:
                        instance = LeaveAlloted.objects.filter(id=id, employee_id=employee).first()
                        if not instance:
                            errors.append(
                                f"No existing record found for Employee {employee.employee_name} with ID {id}.")
                            continue  # Skip if no record found

                        # Update existing record
                        instance.leave_type = leave_type_instance
                        instance.from_date = from_date
                        instance.to_date = to_date
                        instance.allotted_days = allotted_days
                        instance.modified_by = modified_by_instance
                        instance.save()
                        success = True
                        leave_alloted_instances.append(instance)
                    except Exception as e:
                        errors.append(f"Error updating leave for {employee.employee_name}: {str(e)}")

            return LeaveAllotedCreateMutation(success=success, errors=errors)
        except Exception as e:
            print("e", e)
            errors.append(str(e))
            return LeaveAllotedCreateMutation(leave_alloted_data_item=None, success=success, errors=errors)


class AttendanceCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        employee_id = graphene.Int()
        check_in = graphene.Time()
        check_out = graphene.Time()
        work_hours = graphene.Time()
        over_time_hours = graphene.Time()
        break_hours = graphene.Time()
        break_intervals = graphene.JSONString()
        late_in_hours = graphene.Time()
        late_out_hours = graphene.Time()
        status = graphene.String()
        leave = graphene.Int()
        holidays = graphene.Int()
        modified_by = graphene.Int()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    attendance_data_item = graphene.Field(attendance_type)

    def mutate(self, info, **kwargs):
        serializer = ''
        attendance_data_item = None
        success = False
        errors = []

        status = kwargs["status"]
        if kwargs["status"]:
            statusObjects = CommanStatus.objects.filter(name=kwargs["status"], table="AttendanceRegister").first()
            if statusObjects:
                kwargs["status"] = statusObjects.id
            else:
                status = kwargs.get("status", "default_status")
                errors.append(f"Ask devopole to add ${status}")
                return AttendanceCreateMutation(attendance_data_item=attendance_data_item, success=success,
                                                errors=errors)

        if 'id' in kwargs and kwargs['id'] is not None:
            attendance_data_item = AttendanceRegister.objects.filter(id=kwargs['id']).first()
            if not attendance_data_item:
                errors.append(f"Item with {kwargs['id']} not found.")
            else:
                serializer = AttendanceSerializer(attendance_data_item, data=kwargs, partial=True)
        try:

            if serializer.is_valid():
                serializer.save()
                attendance_data_item = serializer.instance
                success = True

        except Exception as e:
            print("e", e)
            errors.append(str(e))
        return AttendanceCreateMutation(attendance_data_item=attendance_data_item, success=success, errors=errors)


class Mutation(graphene.ObjectType):
    role_create_mutation = RoleCreateMutation.Field()
    role_deleteMutation = RoleDeleteMutation.Field()
    user_management_create_mutation = UserManagementCreateMutation.Field()
    user_management_delete_mutation = UserManagementDeleteMutation.Field()
    allowed_permission_create_mutation = AllowedPermissionCreateMutation.Field()
    profile_create_mutation = ProfileCreateMutation.Field()
    profile_delete_mutation = ProfileDeleteMutation.Field()
    employee_create_mutation = EmployeeCreateMutation.Field()
    employee_delete_mutation = EmployeeDeleteMutation.Field()
    expense_request_create_mutation = ExpenseRequestCreateMutation.Field()
    expense_request_delete_mutation = ExpenseRequestDeleteMutation.Field()
    expense_request_cancle_mutation = ExpenseRequestCancleMutation.Field()
    expense_categories_create_mutation = ExpenseCategoriesCreateMutation.Field()
    expense_categories_delete_mutation = ExpenseCategoriesDeleteMutation.Field()
    expense_claim_details_create_mutation = ExpenseClaimDetailsCreateMutation.Field()
    expense_claim_details_delete_mutation = ExpenseClaimDetailsDeleteMutation.Field()
    expense_claim_create_mutation = ExpenseClaimCreateMutation.Field()
    expense_claim_delete_mutation = ExpenseClaimDeleteMutation.Field()
    expense_claim_cancel_mutation = ExpenseClaimCancelMutation.Field()
    payment_voucher_advance_details_create_mutation = PaymentVoucherAdvanceDetailsCreateMutation.Field()
    payment_voucher_advance_details_delete_mutation = PaymentVoucherAdvanceDetailsDeleteMutation.Field()
    payment_voucher_create_mutation = PaymentVoucherCreateMutation.Field()
    payment_voucher_delete_mutation = PaymentVoucherDeleteMutation.Field()
    payment_voucher_cancel_mutation = PaymentVoucherCancelMutation.Field()
    expense_reconciliation_call_form_expense_claim = ExpenseReconciliationCallFormExpenseClaim.Field()
    expense_reconciliation_details_create_mutation = ExpenseReconciliationDetailsCreateMutation.Field()
    expense_reconciliation_details_delete_mutation = ExpenseReconciliationDetailsDeleteMutation.Field()
    holiday_create_mutation = HolidaysCreateMutation.Field()
    holiday_delete_mutation = HolidaysDeleteMutation.Field()
    leave_type_create_mutation = LeaveTypeCreateMutation.Field()
    leave_type_delete_mutation = LeaveTypeDeleteMutation.Field()
    leave_alloted_create_mutation = LeaveAllotedCreateMutation.Field()
    leave_alloted_delete_mutation = LeaveAllotedDeleteMutation.Field()
    leave_create_mutation = LeaveCreateMutation.Field()
    leave_delete_mutation = LeaveDeleteMutation.Field()
    attendance_create_mutation = AttendanceCreateMutation.Field()
