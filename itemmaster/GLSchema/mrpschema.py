import graphene
from graphene import ObjectType
from graphene_django.types import DjangoObjectType
from django.core.paginator import Paginator
from ..serializer import *
from ..models import *
from itemmaster.Utils.stock_statement import *


class PageInfoType(graphene.ObjectType):
    total_items = graphene.Int()
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    total_pages = graphene.Int()
    
    
class MrpMasterType(DjangoObjectType):
    class Meta:
        model = MrpMaster
        fields = "__all__"


class MrpMasterConnection(graphene.ObjectType):
    items = graphene.List(MrpMasterType)
    page_info = graphene.Field(PageInfoType)
    
    
class MrpSourceTypeType(DjangoObjectType):
    class Meta:
        model = MrpSourceType
        fields = "__all__"


class MrpSourceTypeConnection(graphene.ObjectType):
    items = graphene.List(MrpSourceTypeType)
    page_info = graphene.Field(PageInfoType)
    
    
class MrpItemType(DjangoObjectType):
    class Meta:
        model = MrpItem
        fields = "__all__"


class MrpItemTypeConnection(graphene.ObjectType):
    items = graphene.List(MrpItemType)
    page_info = graphene.Field(PageInfoType)
    
    
class Query(ObjectType):
    mrp_master = graphene.Field(MrpMasterConnection)
    mrp_source = graphene.Field(MrpSourceTypeConnection)
    mrp_item = graphene.Field(MrpItemTypeConnection, id_list= graphene.List(graphene.Int))
    
    
    def resolve_mrp_master(self, info, page=1, page_size=20):
        queryset = MrpMaster.objects.all()
        filter_kwargs = {}
        # if batch_number_name:
        #     filter_kwargs['batch_number_name__icontains'] = batch_number_name
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return MrpMasterConnection(
            items=paginated_data.object_list,
            page_info=page_info)


    def resolve_mrp_source(self, info):
        queryset = MrpSourceType.objects.all()
        return MrpSourceTypeConnection(items=queryset)
    
    
    def resolve_mrp_item(self, item, id_list = None):
        queryset = MrpItem.objects.all()
        filter_kwargs = {}
        if id_list:
            filter_kwargs['id__in'] = id_list
        queryset = queryset.filter(**filter_kwargs)
        return MrpItemTypeConnection(items=queryset)