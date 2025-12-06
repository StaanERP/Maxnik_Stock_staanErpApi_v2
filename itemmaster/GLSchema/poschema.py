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
    
    
class ProductionOrderItemType(DjangoObjectType):
    class Meta:
        model = ProductionOrderItem
        fields = "__all__"


class ProductionOrderItemConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderItemType)
    page_info = graphene.Field(PageInfoType)
    
    
class ProductionOrderStatusType(DjangoObjectType):
    class Meta:
        model = ProductionOrderStatus
        fields = "__all__"


class ProductionOrderStatusConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderStatusType)
    page_info = graphene.Field(PageInfoType)
    
    
class SubProductionOrderType(DjangoObjectType):
    class Meta:
        model = SubProductionOrders
        fields = "__all__"


class SubProductionOrderConnection(graphene.ObjectType):
    items = graphene.List(SubProductionOrderType)
    page_info = graphene.Field(PageInfoType)
    
    
class ProductionOrderFinishedGoodsType(DjangoObjectType):
    class Meta:
        model = ProductionOrderFinishedGoods
        fields = "__all__"


class ProductionOrderFinishedGoodsConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderFinishedGoodsType)
    page_info = graphene.Field(PageInfoType)
     
    
class ProductionOrderRawMaterialsType(DjangoObjectType):
    class Meta:
        model = ProductionOrderRawMaterials
        fields = "__all__"


class ProductionOrderRawMaterialsConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderRawMaterialsType)
    page_info = graphene.Field(PageInfoType)
     
    
class ProductionOrderScrapType(DjangoObjectType):
    class Meta:
        model = ProductionOrderScrap
        fields = "__all__"


class ProductionOrderScrapConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderScrapType)
    page_info = graphene.Field(PageInfoType)
    

class ProductionOrderOtherChargesType(DjangoObjectType):
    class Meta:
        model = ProductionOrderOtherCharges
        fields = "__all__"


class ProductionOrderOtherChargesConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderOtherChargesType)
    page_info = graphene.Field(PageInfoType)
    
    
class ProductionOrderProcessRouteType(DjangoObjectType):
    class Meta:
        model = ProductionOrderProcessRoute
        fields = "__all__"


class ProductionOrderProcessRouteConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderProcessRouteType)
    page_info = graphene.Field(PageInfoType)
  
  
class ProductionOrderMasterType(DjangoObjectType):
    class Meta:
        model = ProductionOrderMaster
        fields = "__all__"


class ProductionOrderMasterConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderMasterType)
    page_info = graphene.Field(PageInfoType)


class ProductionOrderItemDetailType(DjangoObjectType):
    class Meta:
        model = ProductionOrderItemDetail
        fields = "__all__"


class ProductionOrderItemDetailConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderItemDetailType)
    page_info = graphene.Field(PageInfoType)


class ProductionOrderLinkingTableType(DjangoObjectType):
    class Meta:
        model = ProductionOrderLinkingTable
        fields = "__all__"


class ProductionOrderLinkingTableConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderLinkingTableType)
    page_info = graphene.Field(PageInfoType)


class ProductionOrderSubItemsType(graphene.ObjectType):
    id = graphene.ID()


class ProductionOrderSubItemsConnection(graphene.ObjectType):
    items = graphene.List(ProductionOrderSubItemsType)



       
class Query(ObjectType):
    production_order_item = graphene.Field(ProductionOrderItemConnection, id_list = graphene.List(graphene.Int))
    
    production_order_status = graphene.Field(ProductionOrderStatusConnection, id = graphene.Int())
    
    sub_production_order = graphene.Field(SubProductionOrderConnection, id = graphene.Int(), id_list = graphene.List(graphene.Int), source_type=graphene.String(), is_combo = graphene.Boolean())
    
    production_order_finished_goods = graphene.Field(ProductionOrderFinishedGoodsConnection, id = graphene.Int())
    
    production_order_raw_materials = graphene.Field(ProductionOrderRawMaterialsConnection, id = graphene.Int(), source_type=graphene.String(), id_list = graphene.List(graphene.Int), is_bom = graphene.Boolean())
    
    production_order_scrap = graphene.Field(ProductionOrderScrapConnection, id = graphene.Int(), id_list = graphene.List(graphene.Int))
    
    production_order_other_charges = graphene.Field(ProductionOrderOtherChargesConnection, id = graphene.Int())
    
    production_order_master = graphene.Field(ProductionOrderMasterConnection, id = graphene.Int(), order_no_contains = graphene.String())
    
    production_order_item_detail = graphene.Field(ProductionOrderItemDetailConnection, id = graphene.Int())
    
    production_order_linking = graphene.Field(ProductionOrderLinkingTableConnection, id = graphene.Int(), po_master= graphene.Int(), 
                                              page = graphene.Int(), page_size= graphene.Int(), is_sub_production_order = graphene.Boolean())
    
    production_order_process_route = graphene.Field(ProductionOrderProcessRouteConnection, id = graphene.Int(), id_list = graphene.List(graphene.Int))
    
    production_order_fetch_sub_items = graphene.Field(ProductionOrderSubItemsConnection, id_list = graphene.List(graphene.Int))
    
    recursive_sub_production_order = graphene.Field(SubProductionOrderConnection, detail_id = graphene.Int(), source_type = graphene.String(), is_multi = graphene.Boolean())
    
    recursive_raw_materials = graphene.Field(ProductionOrderRawMaterialsConnection, detail_id = graphene.Int(), source_type = graphene.String())
        
    
    def resolve_production_order_item(self, info, page=1, page_size=20, id_list = None):
        queryset = ProductionOrderItem.objects.all().order_by('-id')
        filter_kwargs = {}
        if id_list:
            filter_kwargs['id__in'] = id_list
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderItemConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )


    def resolve_production_order_status(self, info, page=1, page_size=20, id = None):
        queryset = ProductionOrderStatus.objects.all()
        filter_kwargs = {}
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
        
        return ProductionOrderStatusConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_sub_production_order(self, info, page=1, page_size=20, id = None, id_list = None, source_type = None, is_combo=None):
        queryset = SubProductionOrders.objects.all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if id_list:
            filter_kwargs['id__in'] = id_list
        if source_type:
            filter_kwargs['bom_type__name'] = source_type
            # filter_kwargs['is_combo'] = False
        if is_combo is not None:
            filter_kwargs['is_combo'] = is_combo
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return SubProductionOrderConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_production_order_finished_goods(self, info, page=1, page_size=20, id = None):
        queryset = ProductionOrderFinishedGoods.objects.all()
        filter_kwargs = {}
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
        
        return ProductionOrderFinishedGoodsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
        
        
    def resolve_production_order_raw_materials(self, info, page=1, page_size=20, id = None,  id_list = None, is_bom = None,  source_type = None):
        queryset = ProductionOrderRawMaterials.objects.all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if id_list:
            filter_kwargs['id__in'] = id_list
        if source_type:
            if source_type == 'MANUFACTURE':
                queryset = queryset.exclude(parent_bom__bom_type='SUBCONTRACT')
            else:
                filter_kwargs['parent_bom__bom_type'] = source_type
        if is_bom is not None:
            if is_bom == False:
                filter_kwargs['bom__isnull'] = True
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderRawMaterialsConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_production_order_scrap(self, info, page=1, page_size=20, id = None, id_list = None):
        queryset = ProductionOrderScrap.objects.all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if id_list:
            filter_kwargs['id__in'] = id_list
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderScrapConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_production_order_other_charges(self, info, page=1, page_size=20, id = None):
        queryset = ProductionOrderOtherCharges.objects.all()
        filter_kwargs = {}
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
        
        return ProductionOrderOtherChargesConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
        
        
    def resolve_production_order_master(self, info, page=1, page_size=20, id = None, order_no_contains = None):
        queryset = ProductionOrderMaster.objects.all()
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if order_no_contains:
            filter_kwargs['order_no__contains'] = order_no_contains
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderMasterConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_production_order_item_detail(self, info, page=1, page_size=20):
        queryset = ProductionOrderItemDetail.objects.all()
        filter_kwargs = {}
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
        
        return ProductionOrderItemDetailConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
    
    
    def resolve_production_order_linking(self, info, page=1, page_size=20, id=None, po_master=None, is_sub_production_order = None):
        queryset = ProductionOrderLinkingTable.objects.all().order_by('-id')
        filter_kwargs = {
            'is_sub_production_order': False
        }
        if is_sub_production_order:
            del filter_kwargs['is_sub_production_order']
        if id:
            filter_kwargs['id'] = id
        if po_master:
            filter_kwargs['po_master'] = po_master
        # if not id and not po_master:
        #     queryset = queryset.order_by('po_master', '-id').distinct('po_master')
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderLinkingTableConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
        
        
    def resolve_production_order_process_route(self, info, page=1, page_size=20, id=None, id_list = None):
        queryset = ProductionOrderProcessRoute.objects.all().order_by('-id')
        filter_kwargs = {}
        if id:
            filter_kwargs['id'] = id
        if id_list:
            filter_kwargs['id__in'] = id_list
        queryset = queryset.filter(**filter_kwargs)
        paginator = Paginator(queryset, page_size)
        paginated_data = paginator.get_page(page)
        page_info = PageInfoType(
            total_items=paginator.count,
            has_next_page=paginated_data.has_next(),
            has_previous_page=paginated_data.has_previous(),
            total_pages=paginator.num_pages,
        )
        
        return ProductionOrderProcessRouteConnection(
            items=paginated_data.object_list,
            page_info=page_info
        )
   
       
    def resolve_recursive_sub_production_order(self, info, detail_id = None, source_type = None):
        queryset = []
        if detail_id:
           queryset = RecursiveSubOrders(detail_id, source_type)
        return SubProductionOrderConnection(items = queryset)
    

    def resolve_recursive_raw_materials(self, info, detail_id = None, source_type = None):
        queryset = []
        if detail_id:
           queryset = RecursiveRawMaterials(detail_id, source_type)
        return ProductionOrderRawMaterialsConnection(items = queryset)