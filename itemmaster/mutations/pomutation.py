import graphene
from django.db.models import ProtectedError
from itemmaster.GLSchema.poschema import *
from itemmaster.serializer import *
from itemmaster.Utils.production_order_util import *


class ProductionOrderStatusCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        name = graphene.String()
    production_order_status = graphene.Field(ProductionOrderStatusType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_status_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_status_instance = ProductionOrderStatus.objects.filter(id=kwargs['id']).first()
            if not production_order_status_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderStatusSerializer(production_order_status_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderStatusSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_status_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderStatusCreateMutation(production_order_item=production_order_status_instance, success=success, errors=errors)


class ProductionOrderStatusDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderStatus.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderStatusDeleteMutation(success=success, errors=errors)


class ProductionOrderItemCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_code = graphene.Int()
        bom = graphene.Int()
        qty = graphene.Decimal()
        source_type = graphene.Int()
        cost = graphene.String()
        supplier = graphene.List(graphene.Int)
        is_combo = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_item = graphene.Field(ProductionOrderItemType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_item_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_item_instance = ProductionOrderItem.objects.filter(id=kwargs['id']).first()
            if not production_order_item_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = POItemSerializer(production_order_item_instance, data=kwargs, partial=True)
        else:
            serializer = POItemSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_item_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderItemCreateMutation(production_order_item=production_order_item_instance, success=success, errors=errors)


class ProductionOrderItemDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderItem.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderItemDeleteMutation(success=success, errors=errors)
    

class SubProductionOrderCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        status = graphene.Int()
        part_code = graphene.Int()
        production_qty = graphene.Int()
        completed_qty = graphene.Int()
        pending_qty = graphene.Decimal()
        unit = graphene.Int()
        created_by = graphene.Int()
        modified_by =  graphene.Int()
    sub_production_order = graphene.Field(SubProductionOrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        sub_production_order_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            sub_production_order_instance = SubProductionOrders.objects.filter(id=kwargs['id']).first()
            if not sub_production_order_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = SubProductionOrdersSerializer(sub_production_order_instance, data=kwargs, partial=True)
        else:
            serializer = SubProductionOrdersSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            sub_production_order_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return SubProductionOrderCreateMutation(sub_production_order=sub_production_order_instance, success=success, errors=errors)


class SubProductionOrderDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = SubProductionOrders.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return SubProductionOrderDeleteMutation(success=success, errors=errors)
    
    
class ProductionOrderFinishedGoodsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_code = graphene.Int()
        category = graphene.Int()
        production_qty = graphene.Decimal()
        completed_qty = graphene.Decimal()
        accepted_qty = graphene.Decimal()
        rework_qty = graphene.Decimal()
        rejected_qty = graphene.Decimal()
        unit = graphene.Int()
        remarks = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_fg = graphene.Field(ProductionOrderFinishedGoodsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_fg_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_fg_instance = ProductionOrderFinishedGoods.objects.filter(id=kwargs['id']).first()
            if not production_order_fg_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderFinishedGoodsSerializer(production_order_fg_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderFinishedGoodsSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_fg_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderFinishedGoodsCreateMutation(production_order_fg=production_order_fg_instance, success=success, errors=errors)


class ProductionOrderFinishedGoodsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderFinishedGoods.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderFinishedGoodsDeleteMutation(success=success, errors=errors)
    

class ProductionOrderRawMaterialsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.String()
        part_code = graphene.Int()
        category = graphene.Int()
        bom = graphene.Int()
        unit = graphene.Int()
        fixed = graphene.Boolean()
        actual_qty = graphene.Decimal()
        issued_qty = graphene.Decimal()
        used_qty = graphene.Decimal()
        store = graphene.Int()
        created_by = graphene.Int()
        modified_by = graphene.Int()
    production_order_rm = graphene.Field(ProductionOrderRawMaterialsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_rm_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_rm_instance = ProductionOrderRawMaterials.objects.filter(id=kwargs['id']).first()
            if not production_order_rm_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = POItemSerializer(production_order_rm_instance, data=kwargs, partial=True)
        else:
            serializer = POItemSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_rm_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderRawMaterialsCreateMutation(production_order_rm=production_order_rm_instance, success=success, errors=errors)


class ProductionOrderRawMaterialsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderRawMaterials.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderRawMaterialsDeleteMutation(success=success, errors=errors)
    

class ProductionOrderScrapCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_code = graphene.Int()
        bom = graphene.Int()
        unit = graphene.Int()
        actual_qty = graphene.Decimal()
        store = graphene.Int()
        cost_allocation = graphene.Decimal()
        supplier = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_scrap = graphene.Field(ProductionOrderScrapType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_scrap_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_scrap_instance = ProductionOrderScrap.objects.filter(id=kwargs['id']).first()
            if not production_order_scrap_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderScrapSerializer(production_order_scrap_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderScrapSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_scrap_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderScrapCreateMutation(production_order_scrap=production_order_scrap_instance, success=success, errors=errors)


class ProductionOrderScrapDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderItem.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderScrapDeleteMutation(success=success, errors=errors)
    

class ProductionOrderOtherChargesCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        description = graphene.String()
        bom_amount = graphene.Decimal()
        actual_amount = graphene.Decimal()
        remarks = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_other_charges = graphene.Field(ProductionOrderOtherChargesType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_other_charges_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_other_charges_instance = ProductionOrderOtherCharges.objects.filter(id=kwargs['id']).first()
            if not production_order_other_charges_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderOtherChargesSerializer(production_order_other_charges_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderOtherChargesSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_other_charges_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderOtherChargesCreateMutation(production_order_other_charges=production_order_other_charges_instance, success=success, errors=errors)


class ProductionOrderOtherChargesDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderOtherCharges.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderOtherChargesDeleteMutation(success=success, errors=errors)


class ProductionOrderProcessRouteCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        serial_number = graphene.Int()
        route = graphene.Int()
        work_center = graphene.Int()
        duration = graphene.Int()
        start_time = graphene.String()
        end_time = graphene.String()
        actual_duration = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_process_route = graphene.Field(ProductionOrderProcessRouteType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_process_route_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_process_route_instance = ProductionOrderProcessRoute.objects.filter(id=kwargs['id']).first()
            print(production_order_process_route_instance)
            if not production_order_process_route_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderProcessRouteSerializer(production_order_process_route_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderProcessRouteSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_process_route_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderProcessRouteCreateMutation(production_order_process_route=production_order_process_route_instance, success=success, errors=errors)


class ProductionOrderProcessRouteDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderProcessRoute.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderProcessRouteDeleteMutation(success=success, errors=errors)
    

class ProductionOrderMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        order_no = graphene.String()
        order_date = graphene.Date()
        department = graphene.Int()
        status = graphene.Int()
        is_combo = graphene.Boolean()
        is_multi_level_manufacture = graphene.Boolean()
        is_sub_production_order = graphene.Boolean()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_master = graphene.Field(ProductionOrderMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_master_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_master_instance = ProductionOrderMaster.objects.filter(id=kwargs['id']).first()
            if not production_order_master_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderMasterSerializer(production_order_master_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderMasterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_master_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderMasterCreateMutation(production_order_master=production_order_master_instance, success=success, errors=errors)


class ProductionOrderMasterDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderMaster.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderMasterDeleteMutation(success=success, errors=errors)
    
    
class ProductionOrderItemDetailCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        due_date = graphene.Date()
        status = graphene.Int()
        remarks = graphene.String()
        sub_production_orders = graphene.List(graphene.Int)
        finished_goods = graphene.Int()
        raw_material = graphene.List(graphene.Int)
        scrap = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()
    production_order_item_detail = graphene.Field(ProductionOrderItemDetailType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_item_detail_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_item_detail_instance = ProductionOrderItemDetail.objects.filter(id=kwargs['id']).first()
            if not production_order_item_detail_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderItemDetailSerializer(production_order_item_detail_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderItemDetailSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_item_detail_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderItemDetailCreateMutation(production_order_item_detail=production_order_item_detail_instance, success=success, errors=errors)


class ProductionOrderItemDetailDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderItemDetail.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderItemDetailDeleteMutation(success=success, errors=errors)


class ProductionOrderLinkingTableCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        po_master = graphene.Int()
        po_item = graphene.Int()
        sub_productions = graphene.List(graphene.Int)
        raw_materials = graphene.List(graphene.Int)
        po_item_detail = graphene.Int()
    production_order_link = graphene.Field(ProductionOrderLinkingTableType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        production_order_link_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            production_order_link_instance = ProductionOrderLinkingTable.objects.filter(id=kwargs['id']).first()
            if not production_order_link_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = ProductionOrderLinkingTableSerializer(production_order_link_instance, data=kwargs, partial=True)
        else:
            serializer = ProductionOrderLinkingTableSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            production_order_link_instance = serializer.instance
            
            # populate sub tables
            if 'id' not in kwargs:
                created_sub_production_order_ids = kwargs['sub_productions']
                production_order_scrap_ids = []
                production_order_route_ids = []
                production_order_rm_ids = kwargs['raw_materials']
                production_order_other_charges_ids = []
                master_item = get_object_or_404(ProductionOrderItem, id=kwargs['po_item'])
                
                if master_item:
                    main_bom = master_item.bom
                   
                    #create production order fg item
                    production_order_fg = ProductionOrderFinishedGoods.objects.create(
                        part_code= main_bom.finished_goods.part_no,
                        production_qty = master_item.qty,
                        completed_qty = 0,
                        accepted_qty = 0,
                        rework_qty = 0,
                        rejected_qty = 0,
                        unit = main_bom.finished_goods.unit,
                        remarks = main_bom.finished_goods.remarks,
                        created_by = master_item.created_by,
                        modified_by = master_item.created_by
                    )
                    
                    #create production order raw material
                    rm_ids, serial_numbers = get_all_rm_ids_with_serials(main_bom)
                    try:
                        rm_list = main_bom.raw_material.all()
                    except:
                        rm_list = []
                        
                    if rm_list:
                        for rm_instance in rm_list:
                            rm_id = rm_instance.id
                            raw_material_obj = RawMaterial.objects.get(id=rm_id)
                            try:
                                parent_bom = Bom.objects.get(raw_material__id = rm_id)
                            except:
                                parent_bom = None
                            try:
                                child_bom_link = RawMaterialBomLink.objects.get(raw_material=raw_material_obj.id)
                                child_bom_link = Bom.objects.get(id = child_bom_link.bom.id)
                            except RawMaterialBomLink.DoesNotExist:
                                child_bom_link = None
                            if not child_bom_link:
                                production_order_rm = ProductionOrderRawMaterials.objects.create(
                                    serial_number= serial_numbers[rm_id],
                                    part_code= raw_material_obj.part_no,
                                    category= raw_material_obj.part_no.category,
                                    parent_bom = parent_bom,
                                    bom = child_bom_link,
                                    unit=raw_material_obj.unit,
                                    fixed=raw_material_obj.fixed,
                                    actual_qty=raw_material_obj.raw_qty * master_item.qty,
                                    issued_qty=0,
                                    used_qty=0,
                                    store=raw_material_obj.store,
                                    created_by=master_item.created_by,
                                    modified_by=master_item.created_by,
                                )
                                production_order_rm_ids.append(production_order_rm)
                    
                    # create production order scrap
                    if main_bom.scrap.all():
                        scrap_materials = main_bom.scrap.all()
                        for scrap_material in scrap_materials:
                            production_order_scrap = ProductionOrderScrap.objects.create(
                                part_code= scrap_material.part_no,
                                category= scrap_material.part_no.category,
                                unit=scrap_material.unit,
                                actual_qty=0,
                                store=main_bom.scrap_store,
                                cost_allocation=scrap_material.cost_allocation,
                                created_by=master_item.created_by,
                                modified_by=master_item.created_by,
                            )
                            production_order_scrap_ids.append(production_order_scrap)
                    
                    # routing 
                    if main_bom.routes.all():
                        route_process = main_bom.routes.all()
                        for route_item in route_process:
                            production_order_route = ProductionOrderProcessRoute.objects.create(
                                serial_number= route_item.serial_number,
                                route= Routing.objects.get(id=route_item.route.id),
                                work_center= WorkCenter.objects.get(id=route_item.work_center.id),
                                duration= route_item.duration,
                                start_time=None,
                                end_time=None,
                                actual_duration='0',
                                created_by=master_item.created_by,
                                modified_by=master_item.created_by,
                            )
                            production_order_route_ids.append(production_order_route)
                    
                    
                    # create production order other charges
                    machinery_charges = main_bom.machinery_charges
                    if machinery_charges:
                        amount = machinery_charges.get('amount')
                        remarks = machinery_charges.get('remarks')
                        mc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'machinery_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=master_item.created_by,
                            modified_by=master_item.created_by,
                        )
                        production_order_other_charges_ids.append(mc_production_order_other_charges)
                        
                    electricity_charges = main_bom.electricity_charges
                    if electricity_charges:
                        amount = electricity_charges.get('amount')
                        remarks = electricity_charges.get('remarks')
                        ec_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'electricity_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=master_item.created_by,
                            modified_by=master_item.created_by,
                        )
                        production_order_other_charges_ids.append(ec_production_order_other_charges)
                        
                    other_charges = main_bom.other_charges
                    if other_charges:
                        amount = other_charges.get('amount')
                        remarks = other_charges.get('remarks')
                        oc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'other_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=master_item.created_by,
                            modified_by=master_item.created_by,
                        )
                        production_order_other_charges_ids.append(oc_production_order_other_charges)
                        
                    labour_charges = main_bom.labour_charges
                    if labour_charges:
                        amount = labour_charges.get('amount')
                        remarks = labour_charges.get('remarks')
                        lc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'labour_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=master_item.created_by,
                            modified_by=master_item.created_by,
                        )
                        production_order_other_charges_ids.append(lc_production_order_other_charges)            

                    
                    production_order_item_detail = ProductionOrderItemDetail.objects.create(
                        status= ProductionOrderStatus.objects.get(id=1),
                        finished_goods=production_order_fg,
                        created_by=master_item.created_by,
                        modified_by=master_item.created_by,
                    )
                    production_order_item_detail.sub_production_orders.add(*created_sub_production_order_ids)
                    production_order_item_detail.raw_material.add(*production_order_rm_ids)
                    production_order_item_detail.scrap.add(*production_order_scrap_ids)
                    production_order_item_detail.other_charges.add(*production_order_other_charges_ids)
                    production_order_item_detail.routes.add(*production_order_route_ids)
                    production_order_link_instance.po_item_detail = production_order_item_detail
                    try:
                        sub_orders = RecursiveSubOrders(production_order_item_detail.id, None)
                        if sub_orders:
                            parent_order_no = ProductionOrderMaster.objects.get(id = kwargs['po_master'])
                            for index, sub_order in enumerate(sub_orders, start=1):
                                sub_po_master = sub_order.po_master
                                sub_po_master.order_no = f'{parent_order_no.order_no}-{index}'
                                sub_po_master.save()
                    except Exception as e:
                        print(e, "sub production Error ----------------->")
                    production_order_link_instance.save()
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return ProductionOrderLinkingTableCreateMutation(production_order_link=production_order_link_instance, success=success, errors=errors)


class ProductionOrderLinkingTableDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = ProductionOrderLinkingTable.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return ProductionOrderLinkingTableDeleteMutation(success=success, errors=errors)


class Mutation(graphene.ObjectType):
    production_order_status_create_mutation = ProductionOrderStatusCreateMutation.Field()
    production_order_status_delete_mutation = ProductionOrderStatusDeleteMutation.Field()
    
    production_order_item_create_mutation = ProductionOrderItemCreateMutation.Field()
    production_order_item_delete_mutation = ProductionOrderItemDeleteMutation.Field()
    
    sub_production_order_create_mutation = SubProductionOrderCreateMutation.Field()
    sub_production_order_delete_mutation = SubProductionOrderDeleteMutation.Field()
    
    production_order_fg_create_mutation = ProductionOrderFinishedGoodsCreateMutation.Field()
    production_order_fg_delete_mutation = ProductionOrderFinishedGoodsDeleteMutation.Field()
    
    production_order_rm_create_mutation = ProductionOrderRawMaterialsCreateMutation.Field()
    production_order_rm_delete_mutation = ProductionOrderRawMaterialsDeleteMutation.Field()
    
    production_order_scrap_create_mutation = ProductionOrderScrapCreateMutation.Field()
    production_order_scrap_delete_mutation = ProductionOrderScrapDeleteMutation.Field()
    
    production_order_other_charges_create_mutation = ProductionOrderOtherChargesCreateMutation.Field()
    production_order_other_charges_delete_mutation = ProductionOrderOtherChargesDeleteMutation.Field()
    
    production_order_master_create_mutation = ProductionOrderMasterCreateMutation.Field()
    production_order_master_delete_mutation = ProductionOrderMasterDeleteMutation.Field()
    
    production_order_item_detail_create_mutation = ProductionOrderItemDetailCreateMutation.Field()
    production_order_item_detail_delete_mutation = ProductionOrderItemDetailDeleteMutation.Field()
    
    production_order_link_create_mutation = ProductionOrderLinkingTableCreateMutation.Field()
    production_order_link_delete_mutation = ProductionOrderLinkingTableDeleteMutation.Field()
    
    production_order_process_route_create_mutation = ProductionOrderProcessRouteCreateMutation.Field()
    production_order_process_route_delete_mutation = ProductionOrderProcessRouteDeleteMutation.Field()