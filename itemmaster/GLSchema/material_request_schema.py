import graphene
from graphene_django.types import DjangoObjectType, ObjectType
from django.core.paginator import Paginator
from ..serializer import *
from ..models import *
from itemmaster.Utils.stock_statement import *
from itemmaster.Utils.production_order_util import *


class PageInfoType(graphene.ObjectType):
    total_items = graphene.Int()
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    total_pages = graphene.Int()
    
    
class MaterialRequestMasterType(DjangoObjectType):
    class Meta:
        model = MaterialRequestMaster
        fields = "__all__"


class MaterialRequestMasterConnection(graphene.ObjectType):
    items = graphene.List(MaterialRequestMasterType)
    page_info = graphene.Field(PageInfoType)
    
    
class MaterialRequestItemDetailType(DjangoObjectType):
    class Meta:
        model = MaterialRequestItemDetails
        fields = "__all__"


class MaterialRequestItemDetailConnection(graphene.ObjectType):
    items = graphene.List(MaterialRequestItemDetailType)
    page_info = graphene.Field(PageInfoType)
    

class MaterialRequestForType(DjangoObjectType):
    class Meta:
        model = MaterialRequestFor
        fields = "__all__"


class MaterialRequestForConnection(graphene.ObjectType):
    items = graphene.List(MaterialRequestForType)
    page_info = graphene.Field(PageInfoType)
    
    
    
class Query(ObjectType):
    material_request_master = graphene.Field(MaterialRequestMasterConnection, page = graphene.Int(),
                                             page_size = graphene.Int(),
                                             id = graphene.Int(), id_list = graphene.List(graphene.Int))
    
    material_request_item_details = graphene.Field(MaterialRequestItemDetailConnection, id_list = graphene.List(graphene.Int))
    
    material_request_for = graphene.Field(MaterialRequestForConnection, id_list = graphene.List(graphene.Int))
    

    def resolve_material_request_master(self, info, page=1, page_size=20, id=None, id_list = None):
        queryset = MaterialRequestMaster.objects.all().order_by('-id')
        filter_kwargs = {}
        if id_list:
            filter_kwargs['id__in'] = id_list
        if id:
            filter_kwargs['id'] = id
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return MaterialRequestMasterConnection(items=paginated_data.object_list, page_info=page_info)


    def resolve_material_request_item_details(self, info, page=1, page_size=20, id=None, id_list = None):
        queryset = MaterialRequestItemDetails.objects.all().order_by('-id')
        filter_kwargs = {}
        if id_list:
            filter_kwargs['id__in'] = id_list
        if id:
            filter_kwargs['id'] = id
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return MaterialRequestItemDetailConnection(items=paginated_data.object_list, page_info=page_info)
    
    
    def resolve_material_request_for(self, info, page=1, page_size=20, id=None, id_list = None):
        queryset = MaterialRequestFor.objects.all().order_by('-id')
        filter_kwargs = {}
        if id_list:
            filter_kwargs['id__in'] = id_list
        if id:
            filter_kwargs['id'] = id
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return MaterialRequestForConnection(items=paginated_data.object_list, page_info=page_info)

    