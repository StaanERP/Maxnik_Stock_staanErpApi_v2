import graphene
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import Lower, Cast
from graphene import ObjectType, List, Int
from graphene_django.types import DjangoObjectType

from itemmaster.Utils.CommanUtils import permission_required
from .models import *
from django.utils import timezone
from datetime import datetime, timedelta
import datetime
from django.db.models import DateField

current_date = timezone.now().date()
extra_one_date = timezone.now().date() + timedelta(days=1, seconds=-1)


class PageInfoType(graphene.ObjectType):
    total_items = graphene.Int()
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    total_pages = graphene.Int()


class ConferencedataType(DjangoObjectType):
    class Meta:
        model = Conferencedata
        fields = "__all__"


class ConferencedataConnection(graphene.ObjectType):
    items = graphene.List(ConferencedataType)
    page_info = graphene.Field(PageInfoType)


class ProductType(DjangoObjectType):
    class Meta:
        model = product
        fields = "__all__"


class ProductConnection(graphene.ObjectType):
    items = graphene.List(ProductType)
    page_info = graphene.Field(PageInfoType)


class EnquiryDataType(DjangoObjectType):
    interests = graphene.List(ProductType)
    interests_joined = graphene.String()

    class Meta:
        model = enquiryDatas
        fields = "__all__" 

    status = graphene.String()

    def resolve_status_display(self, info):
        return self.get_status_display()


    def resolve_interests(self, info):
        return self.interests.all()

    def resolve_interests_joined(self, info):
        products = [str(product.Name) for product in self.interests.all()]
        return ','.join(products)


class EnquiryDataConnection(graphene.ObjectType):
    items = graphene.List(EnquiryDataType)
    page_info = graphene.Field(PageInfoType)


class EnquiryStatusType(graphene.ObjectType):
    id = graphene.String()
    status = graphene.String()


class EnquiryStatusConnection(graphene.ObjectType):
    items = graphene.List(EnquiryStatusType)
    


class ProductType(DjangoObjectType):
    class Meta:
        model = product
        field = '__all__'


class ProductConnection(graphene.ObjectType):
    items = graphene.List(ProductType)


class UserPermissionType(DjangoObjectType):
    class Meta:
        model = UserPermission
        field = '__all__'


class UserPermissionConnection(graphene.ObjectType):
    items = graphene.List(UserPermissionType)


class Query(ObjectType):
    currentConference_data = graphene.Field(ConferencedataConnection, user_id=graphene.Int(),
                                            isCurrenConference=graphene.Boolean())
    conference_data = graphene.Field(ConferencedataConnection, page=graphene.Int(), page_size=graphene.Int(),
                                     order_by=graphene.String(), in_charge=graphene.String(),
                                     date=graphene.String(), descending=graphene.Boolean(), id=graphene.Int(),
                                     name=graphene.String(), in_charge_id=graphene.Int(), status=graphene.Boolean(),
                                     created_by=graphene.String(), start_date=graphene.String(),
                                     end_date=graphene.String(), )

    enquiry_data = graphene.Field(EnquiryDataConnection, page=graphene.Int(), page_size=graphene.Int(),
                                  id=graphene.Int(), name=graphene.String(), status=graphene.String(),
                                  organization_name=graphene.String(), email=graphene.String(),
                                  mobile_number=graphene.String(),
                                  location=graphene.String(), message=graphene.String(),
                                  conference_data=graphene.String(),
                                  interests_joined=graphene.String(), sales_person=graphene.String(),
                                  remarks=graphene.String(),
                                  name_contains=graphene.String(), status_contains=graphene.String(),
                                  organization_name_contains=graphene.String(), email_contains=graphene.String(),
                                  mobile_number_contains=graphene.String(),
                                  location_contains=graphene.String(), message_contains=graphene.String(),
                                  conference_data_contains=graphene.String(),
                                  interests_joined_contains=graphene.String(), sales_person_contains=graphene.String(),
                                  remarks_contains=graphene.String(),
                                  order_by=graphene.String(), descending=graphene.Boolean(),
                                  current_user=graphene.Int(),
                                  other_number=graphene.String(), other_number_contains=graphene.String(),
                                  alternate_mobile_number=graphene.String(),
                                  alternate_mobile_number_contains=graphene.String(),
                                  district=graphene.String(), counter = graphene.String()
                                  )

    enquiry_status = graphene.Field(EnquiryStatusConnection)

    product = graphene.Field(ProductConnection)

    user_permission = graphene.Field(UserPermissionConnection, user_id=graphene.Int(), user_name=graphene.String(),
                                     isSales=graphene.Boolean(),
                                     isAdmin=graphene.Boolean(), isenquiry=graphene.Boolean())

    
    @permission_required(models=["Conference", "POS", "Enquiry"])
    def resolve_conference_data(self, info, page=1, page_size=20, id=None, in_charge=None, date=None,
                                name=None, in_charge_id=None, created_by=None, start_date=None,
                                end_date=None, status=None, order_by=None, descending=None):
        queryset = Conferencedata.objects.all().order_by('-id')
        # Apply filters
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if in_charge_id:
            filter_kwargs['in_charge'] = in_charge_id
        if in_charge:
            filter_kwargs['in_charge__username'] = in_charge
        if name:
            filter_kwargs['name__icontains'] = name
        if created_by:
            filter_kwargs['created_by__username'] = created_by
        if status is not None:
            filter_kwargs['status'] = status
        if start_date:
            s_date, e_date = start_date.split(' - ')
            updated_start_date = datetime.datetime.strptime(s_date, '%d-%m-%Y')
            updated_end_date = datetime.datetime.strptime(e_date, '%d-%m-%Y')
            if s_date == e_date:
                filter_kwargs['start_date'] = updated_start_date.date()
            else:
                filter_kwargs['start_date__range'] = (updated_start_date, updated_end_date)
        if end_date:
            s_date, e_date = end_date.split(' - ')
            updated_start_date = datetime.datetime.strptime(s_date, '%d-%m-%Y')
            updated_end_date = datetime.datetime.strptime(e_date, '%d-%m-%Y')
            if s_date == e_date:
                filter_kwargs['end_date'] = updated_start_date.date()
            else:
                filter_kwargs['end_date__range'] = (updated_start_date, updated_end_date)
        if date:
            today_date = datetime.date.today()
            filter_kwargs['start_date__lte'] = today_date
            filter_kwargs['end_date__gte'] = today_date

        queryset = queryset.filter(**filter_kwargs)

        #
        db_s = {
            "name": {"field": "name", "is_text": True},
            'status': {"field": 'status', "is_text": True},
            'inCharge': {"field": 'in_charge__username', "is_text": True},
            "createdBy": {"field": "created_by__username", "is_text": True},
            "mobileNumber": {"field": "mobile_number", "is_text": True},
            "startDate": {"field": "start_date", "is_text": False},
            "endDate": {"field": "end_date", "is_text": False},
        }

        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]
                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)

        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)

        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        # Return the paginated data along with pagination info
        return ConferencedataConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_currentConference_data(self, info, user_id=None, isCurrenConference=None):

        query = Conferencedata.objects.annotate(
            start_date_only=Cast('start_date', DateField()),
            end_date_only=Cast('end_date', DateField())
        ).filter(
            Q(additional_in_charges=user_id) | Q(in_charge=user_id),
            Q(start_date_only__lte=current_date),
            Q(end_date_only__gte=current_date),
            Q(status=True)
        )
        if isCurrenConference:
            return ConferencedataConnection(items=query)
        else:
            user_data = UserPermission.objects.filter(user_id=user_id).first()
            if user_data:
                is_admin_person = user_data.is_admin_person
                if is_admin_person:

                    query = Conferencedata.objects.filter(status=True)

                    return ConferencedataConnection(items=query)
                else:
                    return ConferencedataConnection(items=query)
    @permission_required(models=["Enquiry"])
    def resolve_enquiry_data(self, info, page=1, page_size=100, id=None, name=None, status=None,
                             organization_name=None, email=None, mobile_number=None, location=None,
                             message=None, conference_data=None, interests_joined=None, sales_person=None,
                             remarks=None, other_number=None, name_contains=None, status_contains=None,
                             organization_name_contains=None, email_contains=None, mobile_number_contains=None,
                             location_contains=None, message_contains=None, conference_data_contains=None,
                             interests_joined_contains=None, sales_person_contains=None, remarks_contains=None,
                             order_by=None, descending=None, other_number_contains=None, current_user=None,
                             alternate_mobile_number=None, alternate_mobile_number_contains=None, district=None, counter=None):
        queryset = enquiryDatas.objects.prefetch_related('interests').all().order_by('-id')
         
        has_contains = False
        contains_key = None
        # Apply filters
        filter_kwargs = {}

        if district:
            filter_kwargs['district__district__icontains'] = district
        if counter:
            filter_kwargs['counter__icontains'] = counter
        if name:
            filter_kwargs['name'] = name
        if status: 
            filter_kwargs['status'] = status
        if organization_name:
            filter_kwargs['organization_name'] = organization_name
        if email:
            filter_kwargs['email'] = email
        if mobile_number:
            filter_kwargs['mobile_number'] = mobile_number
        if location:
            filter_kwargs['location'] = location
        if message:
            filter_kwargs['message'] = message
        if conference_data:
            filter_kwargs['conference_data__name'] = conference_data
        if interests_joined:
            filter_kwargs['interests__Name'] = interests_joined
        if sales_person:
            filter_kwargs['sales_person__username'] = sales_person
        if remarks:
            filter_kwargs['remarks'] = remarks
        if other_number:
            filter_kwargs['other_number'] = other_number
        if alternate_mobile_number:
            filter_kwargs['alternate_mobile_number'] = alternate_mobile_number
        if name_contains:
            filter_kwargs['name__icontains'] = name_contains
            has_contains = True
            contains_key = 'name'
        if status_contains:
            filter_kwargs['status__icontains'] = status_contains
            has_contains = True
            contains_key = 'status'
        if id:
            filter_kwargs['id'] = id
        if organization_name_contains:
            filter_kwargs['organization_name__icontains'] = organization_name_contains
            has_contains = True
            contains_key = 'organization_name'
        if email_contains:
            filter_kwargs['email__icontains'] = email_contains
            has_contains = True
            contains_key = 'email'
        if mobile_number_contains:
            filter_kwargs['mobile_number__icontains'] = mobile_number_contains
            has_contains = True
            contains_key = 'mobile_number'
        if location_contains:
            filter_kwargs['location__icontains'] = location_contains
            has_contains = True
            contains_key = 'location'
        if message_contains:
            filter_kwargs['message__icontains'] = message_contains
            has_contains = True
            contains_key = 'message'
        if conference_data_contains:
            filter_kwargs['conference_data__name__icontains'] = conference_data_contains
            has_contains = True
            contains_key = 'conference_data__name'
        if interests_joined_contains:
            filter_kwargs['interests__Name__icontains'] = interests_joined_contains
            has_contains = True
            contains_key = 'interests__Name'
        if sales_person_contains:
            filter_kwargs['sales_person__username__icontains'] = sales_person_contains
            has_contains = True
            contains_key = 'sales_person__username'
        if remarks_contains:
            filter_kwargs['remarks__icontains'] = remarks_contains
            has_contains = True
            contains_key = 'remarks'
        if other_number_contains:
            filter_kwargs['other_number__icontains'] = other_number_contains
            has_contains = True
            contains_key = 'other_number'
        if alternate_mobile_number_contains:
            filter_kwargs['alternate_mobile_number__icontains'] = alternate_mobile_number_contains
            has_contains = True
            contains_key = 'alternate_mobile_number'
        queryset = queryset.exclude(status='Converted To Lead')
        queryset = queryset.filter(**filter_kwargs)
        db_s = {
            "name": {"field": "name", "is_text": True},
            'status': {"field": 'status', "is_text": True},
            'organizationName': {"field": 'organization_name', "is_text": True},
            "email": {"field": "email", "is_text": True},
            "mobileNumber": {"field": "mobile_number", "is_text": True},
            "otherNumber": {"field": "other_number", "is_text": True},
            "alternateMobileNumber": {"field": "alternate_mobile_number", "is_text": True},
            "location": {"field": "location", "is_text": True},
            "message": {"field": "message", "is_text": True},
            "remarks": {"field": "remarks", "is_text": True},
            "conferenceData": {"field": "conference_data__name", "is_text": True},
            "salesPerson": {"field": "sales_person__username", "is_text": True},
            "interestsJoined": {"field": "interests__Name", "is_text": True}
        }
        if order_by:
            order_by_config = db_s.get(order_by)

            if order_by_config:
                order_by_field = order_by_config["field"]
                is_text_field = order_by_config["is_text"]

                if is_text_field:
                    # For text fields, annotate with a lowercased version for case-insensitive sorting
                    annotated_field_name = f'lower_{order_by_field}'
                    queryset = queryset.annotate(**{annotated_field_name: Lower(order_by_field)})
                    order_by_field = annotated_field_name

                # Determine sorting direction
                if descending:
                    order_by_field = f'-{order_by_field}'

                # Apply sorting
                queryset = queryset.order_by(order_by_field)
        if has_contains:
            queryset = queryset.order_by(contains_key).distinct(contains_key)
        # Pagination
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page) 
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )

        return EnquiryDataConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )

    def resolve_enquiry_status(self, info):
        data = [
            {'id': 'Not Contacted', 'status': 'Not Contacted'},
            {'id': 'Converted To Lead', 'status': 'Converted To Lead'},
            {'id': 'Junk', 'status': 'Junk'},
            {'id': 'Inprogress', 'status': 'Inprogress'},
        ]
        return EnquiryStatusConnection(items=data)

    @permission_required(models=["Enquiry"])
    def resolve_product(self, info):
        queryset = product.objects.all()
        return ProductConnection(items=queryset)

    @permission_required(models=["SalesOrder_2"])
    def resolve_user_permission(self, info, user_id=None, user_name=None, isSales=None, isAdmin=None, isenquiry=None):
        queryset = UserPermission.objects.all()
        if user_id:
            queryset = queryset.filter(id=user_id)
        if user_name:
            queryset = queryset.filter(user_id__username__icontains=user_name)
        if isSales is not None:
            queryset = queryset.filter(is_sales_person=isSales)
        if isAdmin is not None:
            queryset = queryset.filter(is_admin_person=isAdmin)
        if isAdmin is not None:
            queryset = queryset.filter(is_admin_person=isAdmin)
        if isenquiry:
            queryset = queryset.filter(is_enquiry_admin=isenquiry)
        return UserPermissionConnection(items=queryset)


schema = graphene.Schema(query=Query)
