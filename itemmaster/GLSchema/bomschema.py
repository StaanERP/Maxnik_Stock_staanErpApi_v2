import graphene
from graphene import ObjectType
from graphene_django.types import DjangoObjectType
from django.core.paginator import Paginator
from ..serializer import *
from ..models import *
from itemmaster.Utils.stock_statement import *
from itemmaster.Utils.production_order_util import *
from itemmaster.Utils.bom import *
from itemmaster.schema import *


class PageInfoType(graphene.ObjectType):
    total_items = graphene.Int()
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    total_pages = graphene.Int()
   
   
class BomCostVariationType(DjangoObjectType):
    class Meta:
        model = BomCostVariation
        fields = "__all__"


class BomCostVariationConnection(graphene.ObjectType):
    items = graphene.List(BomCostVariationType)
    page_info = graphene.Field(PageInfoType)
    
    
class FetchRecursiveBomType(graphene.ObjectType):
    item_combo = graphene.List(RawMaterialType)
    bom = graphene.List(BomType)
    parent = graphene.ID()


class FetchRecursiveBomConnection(graphene.ObjectType):
    items = graphene.List(FetchRecursiveBomType)
    
   
class PartCodeHasBomType(graphene.ObjectType):
    item_combo = graphene.List(ItemComboType)
    bom = graphene.List(BomType)


class PartCodeHasBomConnection(graphene.ObjectType):
    items = graphene.List(FetchRecursiveBomType)
    

class Query(ObjectType):
    bom_cost_variation = graphene.Field(BomCostVariationConnection)
    recursive_raw_materials = graphene.Field(RawMaterialConnection,  id_list=graphene.List(graphene.Int))
    part_code_has_bom = graphene.Field(PartCodeHasBomConnection, id_list= graphene.List(graphene.String), is_multi = graphene.Boolean())
    fetch_recursive_bom = graphene.Field(FetchRecursiveBomConnection, id = graphene.ID())

    def resolve_bom_cost_variation(self, info, page=1, page_size=20):
        queryset = BomCostVariation.objects.all()
        filter_kwargs = {}
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        return BomCostVariationConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )


    def resolve_recursive_raw_materials(self, info, id_list=None):
        queryset = []
        if id_list:
            all_rm_ids = get_all_rm_ids(id_list)
            queryset = RawMaterial.objects.all()
            filter_kwargs = {}
            if id:
                filter_kwargs['id__in'] = all_rm_ids
            queryset = queryset.filter(**filter_kwargs)
        
        return RawMaterialConnection(items=queryset)
        
        
    def resolve_part_code_has_bom(self, info, id_list=None, is_multi = None):
        result_set = []
        if id_list:
            for id in id_list:
                [bom_no, bom_name, bom_type] = id.split(' -- ')
                main_bom = Bom.objects.get(bom_name = bom_name, bom_no = bom_no, bom_type = bom_type)
                fetch_recursive_bom_with_child_bom(main_bom, result_set, is_multi)
        return PartCodeHasBomConnection(items=result_set)


    def resolve_fetch_recursive_bom(self, info, id=None):
        result_set = []
        if id:
            main_bom = Bom.objects.get(id=id)
            fetch_recursive_bom(main_bom, result_set)
        return FetchRecursiveBomConnection(items=result_set)

