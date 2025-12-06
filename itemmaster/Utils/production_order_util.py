from itemmaster.models import *
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import datetime
from decimal import Decimal


def get_all_bom_ids(bom):
    """
    Recursively get all BOM IDs from the given BOM.
    """
    bom_ids = set()
    
    def recurse(bom):
        # print(bom.id)
        if bom.id not in bom_ids:
            bom_ids.add(bom.id)
            raw_materials = bom.raw_material.all()
            for raw_material in raw_materials:        
                raw_material_boms = RawMaterialBomLink.objects.filter(raw_material=raw_material)
                for related_bom in raw_material_boms:
                    recurse(related_bom.bom)

    recurse(bom)
    return bom_ids


def get_all_rm_ids_with_serials(bom):
    """
    Recursively get all BOM IDs and assign serial numbers by level.
    """
    rm_ids = set()
    serials = {}
    current_serial = {}

    def recurse(bom, parent_level=None):
        for index, raw_material in enumerate(bom.raw_material.all(), start=1):
            if raw_material.id not in rm_ids:
                rm_ids.add(raw_material.id)
                
                if parent_level is None: 
                    level = f'{index}'
                else: 
                    level = f"{parent_level}.{current_serial[parent_level] + 1}"
                
                serials[raw_material.id] = level
                current_serial.setdefault(level, 0)
                current_serial[parent_level] = current_serial.get(parent_level, 0) + 1

                raw_material_boms = RawMaterialBomLink.objects.filter(raw_material=raw_material.id)
                for related_bom in raw_material_boms:
                    recurse(related_bom.bom, level)

    recurse(bom)
    return rm_ids, serials


def get_all_rm_ids(initial_rm_ids):
    """
    Recursively get all BOM IDs and assign serial numbers by level.
    """
    rm_ids = set(initial_rm_ids)

    def recurse(raw_material_id):
        raw_material_boms = RawMaterialBomLink.objects.filter(raw_material=raw_material_id)
        for related_bom in raw_material_boms:
            for raw_material in related_bom.bom.raw_material.all():
                if raw_material.id not in rm_ids:
                    rm_ids.add(raw_material.id)
                    recurse(raw_material.id)

    for rm_id in initial_rm_ids:
        recurse(rm_id)
    return rm_ids



def CreateSubProductionOrders(sub_po_id_list, po_master):
    for sub_po_id in sub_po_id_list:
        production_order_scrap_ids = []
        production_order_route_ids = []
        production_order_rm_ids = []
        production_order_other_charges_ids = []
        sub_po_item = get_object_or_404(SubProductionOrders, id=sub_po_id)
        po_master_item = get_object_or_404(ProductionOrderMaster, id=po_master)
        if sub_po_item and po_master_item:
            bom_objects  = get_list_or_404(Bom, finished_goods__part_no=sub_po_item.part_code)
            if bom_objects:
                first_bom_object = bom_objects[0]
                if first_bom_object:
                    source_type_object = get_object_or_404(MrpSourceType, name=first_bom_object.bom_type)
                    first_supplier = first_bom_object.supplier.all().first()
                    po_item = ProductionOrderItem.objects.create(
                        part_code = sub_po_item.part_code,
                        bom = first_bom_object,
                        qty = sub_po_item.production_qty,
                        source_type = source_type_object,
                        cost = sub_po_item.part_code.item_mrp,
                        created_by  = sub_po_item.created_by
                    )
                    if first_supplier:
                        po_item.supplier.set([first_supplier])
                    if po_item:
                        main_bom = po_item.bom
            
                    # create production order fg item
                    production_order_fg = ProductionOrderFinishedGoods.objects.create(
                        part_code = main_bom.finished_goods.part_no,
                        production_qty = main_bom.finished_goods.qty * po_item.qty,
                        completed_qty = 0,
                        accepted_qty = 0,
                        rework_qty = 0,
                        rejected_qty = 0,
                        unit=main_bom.finished_goods.unit,
                        remarks = main_bom.finished_goods.remarks,
                        created_by = po_item.created_by,
                        modified_by = po_item.created_by
                    )
            
                    # create production order raw material
                    rm_ids, serial_numbers = get_all_rm_ids_with_serials(main_bom)
                    
                    if rm_ids:
                        for rm_id in list(rm_ids):
                            raw_material_obj = RawMaterial.objects.get(id=rm_id)
                            try:
                                child_bom_link = RawMaterialBomLink.objects.get(raw_material=raw_material_obj.id)
                                child_bom_link = Bom.objects.get(id = child_bom_link.bom.id)
                            except RawMaterialBomLink.DoesNotExist:
                                child_bom_link = None
                            production_order_rm = ProductionOrderRawMaterials.objects.create(
                                serial_number= serial_numbers[rm_id],
                                part_code= raw_material_obj.part_no,
                                category= raw_material_obj.part_no.category,
                                bom = child_bom_link,
                                unit=raw_material_obj.unit,
                                fixed=raw_material_obj.fixed,
                                actual_qty=Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                issued_qty=0,
                                used_qty=0,
                                store=raw_material_obj.store,
                                created_by=po_item.created_by,
                                modified_by=po_item.created_by,
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
                                created_by=po_item.created_by,
                                modified_by=po_item.created_by,
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
                                created_by=po_item.created_by,
                                modified_by=po_item.created_by,
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
                            created_by=po_item.created_by,
                            modified_by=po_item.created_by,
                        )
                        production_order_other_charges_ids.append(mc_production_order_other_charges)
                
                    electricity_charges = main_bom.machinery_charges
                    if electricity_charges:
                        amount = electricity_charges.get('amount')
                        remarks = electricity_charges.get('remarks')
                        ec_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'electricity_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=po_item.created_by,
                            modified_by=po_item.created_by,
                        )
                        production_order_other_charges_ids.append(ec_production_order_other_charges)
                
                    other_charges = main_bom.machinery_charges
                    if other_charges:
                        amount = other_charges.get('amount')
                        remarks = other_charges.get('remarks')
                        oc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'other_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=po_item.created_by,
                            modified_by=po_item.created_by,
                        )
                        production_order_other_charges_ids.append(oc_production_order_other_charges)
                
                    labour_charges = main_bom.machinery_charges
                    if labour_charges:
                        amount = labour_charges.get('amount')
                        remarks = labour_charges.get('remarks')
                        lc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                            description= 'labour_charges',
                            bom_amount= amount,
                            actual_amount=0,
                            remarks=remarks,
                            created_by=po_item.created_by,
                            modified_by=po_item.created_by,
                        )
                        production_order_other_charges_ids.append(lc_production_order_other_charges)                           
    
                    production_order_item_detail = ProductionOrderItemDetail.objects.create(
                        status= ProductionOrderStatus.objects.get(id=1),
                        finished_goods=production_order_fg,
                        created_by=po_item.created_by,
                        modified_by=po_item.created_by,
                    )
                    production_order_item_detail.raw_material.add(*production_order_rm_ids)
                    production_order_item_detail.scrap.add(*production_order_scrap_ids)
                    production_order_item_detail.other_charges.add(*production_order_other_charges_ids)
                    production_order_item_detail.routes.add(*production_order_route_ids)
                    
                    master_item = ProductionOrderMaster.objects.create(
                        order_date = datetime.now().strftime('%Y-%m-%d'),
                        department = po_master_item.department,
                        status = ProductionOrderStatus.objects.get(id=1),
                        created_by = po_item.created_by,
                        modified_by = po_item.created_by,
                        is_sub_production_order = True,
                    )
                    
                    ProductionOrderLinkingTable.objects.create(
                        po_item = po_item,
                        po_item_detail = production_order_item_detail,
                        po_master = master_item,
                        is_sub_production_order = True,
                    )
    

def CreateSubProductionOrdersWithoutMaster(sub_po_item_id, bom_obj, department, master_qty, created_by_user, child_ids, is_multi):
    department = Department.objects.get(id = department)
    created_child_ids = []
    def CreateProductionOrder(sub_po_item, bom_obj_selected):
            created_sub_production_po_ids = []
            sub_po_id_list = []
            production_order_scrap_ids = []
            production_order_route_ids = []
            production_order_rm_ids = []
            production_order_other_charges_ids = []
            item_qty = Decimal(sub_po_item.production_qty)
            source_type_object = MrpSourceType.objects.get(name=bom_obj_selected.bom_type)
            part_code_object = ItemMaster.objects.get(id=sub_po_item.part_code.id)
            production_qty = item_qty
            po_item = ProductionOrderItem.objects.create(
                part_code = part_code_object,
                bom = bom_obj_selected,
                qty = production_qty,
                source_type = source_type_object,
                cost = part_code_object.item_mrp,
                created_by  = created_by_user
            )
            if po_item:
                main_bom = po_item.bom
                
                # create production order fg item
                production_order_fg = ProductionOrderFinishedGoods.objects.create(
                    part_code = main_bom.finished_goods.part_no,
                    production_qty = Decimal( main_bom.finished_goods.qty) * Decimal(po_item.qty),
                    completed_qty = 0,
                    accepted_qty = 0,
                    rework_qty = 0,
                    rejected_qty = 0,
                    unit=main_bom.finished_goods.unit,
                    remarks = main_bom.finished_goods.remarks,
                    created_by = po_item.created_by,
                    modified_by = po_item.created_by
                )
                
                # create production order raw material
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
                                actual_qty= Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                issued_qty=0,
                                used_qty=0,
                                store=raw_material_obj.store,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_rm_ids.append(production_order_rm)
                        else:
                            if is_multi == False:
                                try:
                                    production_order_rm = ProductionOrderRawMaterials.objects.create(
                                        serial_number= serial_numbers[rm_id],
                                        part_code= raw_material_obj.part_no,
                                        category= raw_material_obj.part_no.category,
                                        parent_bom = parent_bom,
                                        bom = child_bom_link,
                                        unit= raw_material_obj.unit,
                                        fixed= raw_material_obj.fixed,
                                        actual_qty= Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                        issued_qty=0,
                                        used_qty=0,
                                        store=child_bom_link.fg_store,
                                        created_by=created_by_user,
                                        modified_by=created_by_user,
                                    )
                                    production_order_rm_ids.append(production_order_rm)
                                except Exception as e:
                                    print(e, "raw material")
                            else:
                                if child_ids:
                                    if rm_id in child_ids:
                                        new_sub_production_order_instance = SubProductionOrders.objects.create(
                                            status = ProductionOrderStatus.objects.get(id=1), 
                                            part_code = child_bom_link.finished_goods.part_no,
                                            production_qty = Decimal(rm_instance.qty) * Decimal(po_item.qty),
                                            completed_qty = 0,
                                            bom_type = MrpSourceType.objects.get(name=child_bom_link.bom_type),
                                            pending_qty = Decimal(rm_instance.qty) * Decimal(po_item.qty),
                                            unit = child_bom_link.finished_goods.unit,
                                            created_by = created_by_user,
                                            modified_by = created_by_user,
                                        )
                                        created_child_ids.append(rm_id)
                                        sub_po_id_list.append(new_sub_production_order_instance.id)
                                        created_sub_production_po_ids.append({
                                            'id':new_sub_production_order_instance,
                                            'bom': child_bom_link
                                        })
                                    else:
                                        try:
                                            production_order_rm = ProductionOrderRawMaterials.objects.create(
                                                serial_number= serial_numbers[rm_id],
                                                part_code= raw_material_obj.part_no,
                                                category= raw_material_obj.part_no.category,
                                                parent_bom = parent_bom,
                                                bom = child_bom_link,
                                                unit= raw_material_obj.unit,
                                                fixed= raw_material_obj.fixed,
                                                actual_qty= Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                                issued_qty=0,
                                                used_qty=0,
                                                store=child_bom_link.fg_store,
                                                created_by=created_by_user,
                                                modified_by=created_by_user,
                                            )
                                            production_order_rm_ids.append(production_order_rm)
                                        except Exception as e:
                                            print(e, "raw material")
                                else:
                                    try:
                                        production_order_rm = ProductionOrderRawMaterials.objects.create(
                                            serial_number= serial_numbers[rm_id],
                                            part_code= raw_material_obj.part_no,
                                            category= raw_material_obj.part_no.category,
                                            parent_bom = parent_bom,
                                            bom = child_bom_link,
                                            unit= raw_material_obj.unit,
                                            fixed= raw_material_obj.fixed,
                                            actual_qty= Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                            issued_qty=0,
                                            used_qty=0,
                                            store=child_bom_link.fg_store,
                                            created_by=created_by_user,
                                            modified_by=created_by_user,
                                        )
                                        production_order_rm_ids.append(production_order_rm)
                                    except Exception as e:
                                        print(e, "raw material")
                        
        
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
                            created_by=created_by_user,
                            modified_by=created_by_user,
                        )
                        production_order_scrap_ids.append(production_order_scrap)
                
                if po_item.bom.bom_type != 'SUBCONTRACT':
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
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_route_ids.append(production_order_route)

                    # create production order other charges
                    machinery_charges = main_bom.machinery_charges
                    if machinery_charges:
                        amount = machinery_charges.get('amount')
                        remarks = machinery_charges.get('remarks')
                        try:
                            mc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'machinery_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(mc_production_order_other_charges)
                        except:
                            pass
                    electricity_charges = main_bom.electricity_charges
                    if electricity_charges:
                        amount = electricity_charges.get('amount')
                        remarks = electricity_charges.get('remarks')
                        try:
                            ec_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'electricity_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(ec_production_order_other_charges)
                        except:
                            pass
                    other_charges = main_bom.other_charges
                    if other_charges:
                        amount = other_charges.get('amount')
                        remarks = other_charges.get('remarks')
                        try:
                            oc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'other_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(oc_production_order_other_charges)
                        except Exception as e:
                            pass
                    labour_charges = main_bom.labour_charges
                    if labour_charges:
                        amount = labour_charges.get('amount')
                        remarks = labour_charges.get('remarks')
                        try:
                            lc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'labour_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(lc_production_order_other_charges)                           
                        except:
                            pass
                production_order_item_detail = ProductionOrderItemDetail.objects.create(
                    status= ProductionOrderStatus.objects.get(id=1),
                    finished_goods=production_order_fg,
                    created_by=created_by_user,
                    modified_by=created_by_user,
                )
                production_order_item_detail.raw_material.add(*production_order_rm_ids)
                production_order_item_detail.scrap.add(*production_order_scrap_ids)
                production_order_item_detail.sub_production_orders.add(*sub_po_id_list)
                if po_item.bom.bom_type != 'SUBCONTRACT':
                    production_order_item_detail.other_charges.add(*production_order_other_charges_ids)
                    production_order_item_detail.routes.add(*production_order_route_ids)                        
                master_item = ProductionOrderMaster.objects.create(
                    order_date = datetime.now().strftime('%Y-%m-%d'),
                    department = department,
                    status = ProductionOrderStatus.objects.get(id=1),
                    created_by = created_by_user,
                    modified_by = created_by_user,
                    is_sub_production_order = True,
                )
                sub_po_item.po_master = master_item
                try:
                    sub_po_item.save()
                except Exception as e:
                    pass
                ProductionOrderLinkingTable.objects.create(
                    po_item = po_item,
                    po_item_detail = production_order_item_detail,
                    po_master = master_item,
                    is_sub_production_order = True,
                )
                if is_multi:
                    if created_sub_production_po_ids:
                        for created_sub_production_po_id in created_sub_production_po_ids:
                            CreateProductionOrder(created_sub_production_po_id['id'], created_sub_production_po_id['bom'])
    if department:
        CreateProductionOrder(sub_po_item_id, bom_obj)
                        


def get_all_rm_ids_with_serials_for_combo(bom, start_number, selected_child_ids):
    """
    Recursively get all BOM IDs and assign serial numbers by level.
    """
    rm_ids = set()
    serials = {}
    current_serial = {start_number: 0}

    def recurse(bom, parent_level=None):
        prefix = ''
        if bom.bom_type == 'MANUFACTURE':
            prefix = 'CM'
        else:
            prefix = 'CS'
        for index, raw_material in enumerate(bom.raw_material.all(), start=1):
            if raw_material.id not in rm_ids:
                rm_ids.add(raw_material.id)
                
                if parent_level is None: 
                    level = f'{index}'
                else: 
                    level = f"{parent_level}.{current_serial[parent_level] + 1}"
                
                serials[raw_material.id] = {'level': level, 'prefix': prefix}
                current_serial.setdefault(level, 0)
                current_serial[parent_level] = current_serial.get(parent_level, 0) + 1
                if raw_material.id in selected_child_ids:
                    raw_material_boms = RawMaterialBomLink.objects.filter(raw_material=raw_material.id)
                    for related_bom in raw_material_boms:
                        recurse(related_bom.bom, level)

    recurse(bom, start_number)
    return rm_ids, serials



def CreateSubProductionOrderForPoItem(po_item_, bom_obj, master_qty, department, created_by_user, child_items, is_multi):
    created_child_ids = []
    department = Department.objects.get(id = department)
    def CreateProductionOrder(sub_po_item, bom_obj_selected):
            created_sub_production_po_ids = []
            sub_po_id_list = []
            production_order_scrap_ids = []
            production_order_route_ids = []
            production_order_rm_ids = []
            production_order_other_charges_ids = []
            item_qty = Decimal(sub_po_item.production_qty)
            source_type_object = MrpSourceType.objects.get(name=bom_obj_selected.bom_type)
            part_code_object = ItemMaster.objects.get(id=sub_po_item.part_code.id)
            production_qty = item_qty
            po_item = ProductionOrderItem.objects.create(
                part_code = part_code_object,
                bom = bom_obj_selected,
                qty = production_qty,
                source_type = source_type_object,
                cost = part_code_object.item_mrp,
                created_by  = created_by_user
            )
            if po_item:
                main_bom = po_item.bom
                # create production order fg item
                production_order_fg = ProductionOrderFinishedGoods.objects.create(
                    part_code = main_bom.finished_goods.part_no,
                    production_qty = Decimal( main_bom.finished_goods.qty) * Decimal(po_item.qty),
                    completed_qty = 0,
                    accepted_qty = 0,
                    rework_qty = 0,
                    rejected_qty = 0,
                    unit=main_bom.finished_goods.unit,
                    remarks = main_bom.finished_goods.remarks,
                    created_by = po_item.created_by,
                    modified_by = po_item.created_by
                )
                
                # create production order raw material
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
                            if  rm_id not in created_child_ids:
                                production_order_rm = ProductionOrderRawMaterials.objects.create(
                                    serial_number= serial_numbers[rm_id],
                                    part_code= raw_material_obj.part_no,
                                    category= raw_material_obj.part_no.category,
                                    parent_bom = parent_bom,
                                    bom = child_bom_link,
                                    unit=raw_material_obj.unit,
                                    fixed=raw_material_obj.fixed,
                                    actual_qty= Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                    issued_qty=0,
                                    used_qty=0,
                                    store=raw_material_obj.store,
                                    created_by=created_by_user,
                                    modified_by=created_by_user,
                                )
                                created_child_ids.append(rm_id)
                                production_order_rm_ids.append(production_order_rm)
                        else:
                            try:
                                current_child = child_items[str(part_code_object.id)]
                                selected_child_ids = [int(item['id']) for item in current_child]
                            except Exception as e:
                                current_child = None
                                selected_child_ids = None
                            if selected_child_ids:
                                if rm_id in selected_child_ids and child_bom_link:
                                    new_sub_production_order_instance = SubProductionOrders.objects.create(
                                        status = ProductionOrderStatus.objects.get(id=1), 
                                        part_code = child_bom_link.finished_goods.part_no,
                                        production_qty = Decimal(rm_instance.qty) * Decimal(po_item.qty),
                                        completed_qty = 0,
                                        bom_type = MrpSourceType.objects.get(name=child_bom_link.bom_type),
                                        pending_qty = Decimal(rm_instance.qty) * Decimal(po_item.qty),
                                        unit = child_bom_link.finished_goods.unit,
                                        created_by = created_by_user,
                                        modified_by = created_by_user,
                                    )
                                    created_sub_production_po_ids.append({
                                        'id':new_sub_production_order_instance,
                                        'bom': child_bom_link
                                    })
                                    sub_po_id_list.append(new_sub_production_order_instance.id)
                            else:
                                production_order_rm = ProductionOrderRawMaterials.objects.create(
                                    serial_number = serial_numbers[rm_id],
                                    part_code = raw_material_obj.part_no,
                                    category = raw_material_obj.part_no.category,
                                    parent_bom = parent_bom,
                                    bom = child_bom_link,
                                    unit = raw_material_obj.unit,
                                    fixed = raw_material_obj.fixed,
                                    actual_qty = Decimal(raw_material_obj.raw_qty) * Decimal(po_item.qty),
                                    issued_qty = 0,
                                    used_qty = 0,
                                    store = child_bom_link.fg_store,
                                    created_by = created_by_user,
                                    modified_by = created_by_user,
                                )
                                created_child_ids.append(rm_id)
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
                            created_by=created_by_user,
                            modified_by=created_by_user,
                        )
                        production_order_scrap_ids.append(production_order_scrap)
                
                if po_item.bom.bom_type != 'SUBCONTRACT':
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
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_route_ids.append(production_order_route)

                    # create production order other charges
                    machinery_charges = main_bom.machinery_charges
                    if machinery_charges:
                        amount = machinery_charges.get('amount')
                        remarks = machinery_charges.get('remarks')
                        try:
                            mc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'machinery_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(mc_production_order_other_charges)
                        except:
                            pass
                    electricity_charges = main_bom.electricity_charges
                    if electricity_charges:
                        amount = electricity_charges.get('amount')
                        remarks = electricity_charges.get('remarks')
                        try:
                            ec_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'electricity_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(ec_production_order_other_charges)
                        except:
                            pass
                    other_charges = main_bom.other_charges
                    if other_charges:
                        amount = other_charges.get('amount')
                        remarks = other_charges.get('remarks')
                        try:
                            oc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'other_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(oc_production_order_other_charges)
                        except Exception as e:
                            pass
                    labour_charges = main_bom.labour_charges
                    if labour_charges:
                        amount = labour_charges.get('amount')
                        remarks = labour_charges.get('remarks')
                        try:
                            lc_production_order_other_charges = ProductionOrderOtherCharges.objects.create(
                                description= 'labour_charges',
                                bom_amount= amount,
                                actual_amount=0,
                                remarks=remarks,
                                created_by=created_by_user,
                                modified_by=created_by_user,
                            )
                            production_order_other_charges_ids.append(lc_production_order_other_charges)                           
                        except:
                            pass
                production_order_item_detail = ProductionOrderItemDetail.objects.create(
                    status= ProductionOrderStatus.objects.get(id=1),
                    finished_goods=production_order_fg,
                    created_by=created_by_user,
                    modified_by=created_by_user,
                )
                production_order_item_detail.raw_material.add(*production_order_rm_ids)
                production_order_item_detail.scrap.add(*production_order_scrap_ids)
                production_order_item_detail.sub_production_orders.add(*sub_po_id_list)
                if po_item.bom.bom_type != 'SUBCONTRACT':
                    production_order_item_detail.other_charges.add(*production_order_other_charges_ids)
                    production_order_item_detail.routes.add(*production_order_route_ids)                        
                master_item = ProductionOrderMaster.objects.create(
                    order_date = datetime.now().strftime('%Y-%m-%d'),
                    department = department,
                    status = ProductionOrderStatus.objects.get(id=1),
                    created_by = created_by_user,
                    modified_by = created_by_user,
                    is_sub_production_order = True,
                )
                sub_po_item.po_master = master_item
                try:
                    sub_po_item.save()
                except Exception as e:
                    pass
                ProductionOrderLinkingTable.objects.create(
                    po_item = po_item,
                    po_item_detail = production_order_item_detail,
                    po_master = master_item,
                    is_sub_production_order = True,
                )
                if created_sub_production_po_ids:
                    for created_sub_production_po_id in created_sub_production_po_ids:
                        CreateProductionOrder(created_sub_production_po_id['id'], created_sub_production_po_id['bom'])
    
    sub_po_ids = []
    created_rm_ids = []
    if department:
        try:
            current_child = child_items[po_item_['partCode']['value']]
            selected_child_ids = [int(item['id']) for item in current_child]
        except:
            current_child = []
            selected_child_ids = []
        for raw_material in bom_obj.raw_material.all():
            try:
                child_bom_link = RawMaterialBomLink.objects.get(raw_material=raw_material.id)
                child_bom_link = Bom.objects.get(id = child_bom_link.bom.id)
            except RawMaterialBomLink.DoesNotExist:
                child_bom_link = None
            if child_bom_link:
                if raw_material.id in selected_child_ids:
                    new_sub_production_order_instance = SubProductionOrders.objects.create(
                        status = ProductionOrderStatus.objects.get(id=1), 
                        part_code = child_bom_link.finished_goods.part_no,
                        production_qty = Decimal(raw_material.raw_qty) * Decimal(master_qty),
                        completed_qty = 0,
                        bom_type = MrpSourceType.objects.get(name=child_bom_link.bom_type),
                        pending_qty = Decimal(raw_material.raw_qty) * Decimal(master_qty),
                        unit = child_bom_link.finished_goods.unit,
                        created_by = created_by_user,
                        modified_by = created_by_user,
                    )
                    sub_po_ids.append(new_sub_production_order_instance.id)
                    CreateProductionOrder(new_sub_production_order_instance, child_bom_link)
                else:
                    try:
                        production_order_rm = ProductionOrderRawMaterials.objects.create(
                            serial_number= '',
                            part_code= raw_material.part_no,
                            category= raw_material.part_no.category,
                            parent_bom = bom_obj,
                            bom = child_bom_link,
                            unit= raw_material.unit,
                            fixed= raw_material.fixed,
                            actual_qty= Decimal(raw_material.raw_qty) * Decimal(master_qty),
                            issued_qty=0,
                            used_qty=0,
                            store=child_bom_link.fg_store,
                            created_by=created_by_user,
                            modified_by=created_by_user,
                        )
                        created_rm_ids.append(production_order_rm.id)
                    except Exception as e:
                        print(e, "raw material")
    return sub_po_ids, created_rm_ids         
        
        

def RecursiveSubOrders(po_detail_id, source_type):
    all_sub_orders = list()
    def get_all_sub_orders(po_item_detail_instance):
        if po_item_detail_instance:
            try:
                sub_orders = po_item_detail_instance.sub_production_orders.all()
            except Exception as e:
                sub_orders = []
            if sub_orders:
                for sub_order in sub_orders:
                    if source_type: 
                        if sub_order.bom_type.name == source_type:
                            all_sub_orders.append(sub_order)
                    else:
                        all_sub_orders.append(sub_order)
                    try:
                        link_instance = ProductionOrderLinkingTable.objects.filter(po_master = sub_order.po_master)
                    except:
                        link_instance = None
                    if link_instance:
                        link_instance = link_instance[0]
                        get_all_sub_orders(link_instance.po_item_detail)
    #                   
    try:
        po_item_detail_instance = ProductionOrderItemDetail.objects.get(id = po_detail_id)
    except Exception as e:
        # print(e, "item detail")
        po_item_detail_instance = None
    get_all_sub_orders(po_item_detail_instance)
    return all_sub_orders



def RecursiveRawMaterials(po_detail_id, source_type):
    all_raw_materials = list()
    def get_all_sub_orders(po_item_detail_instance, is_source):
        if po_item_detail_instance:
            if is_source:
                try:
                    raw_materials = po_item_detail_instance.raw_material.all()
                    if source_type == 'MANUFACTURE':
                        raw_materials = raw_materials.filter(Q(parent_bom__bom_type=source_type) | Q(parent_bom__bom_type=None))
                    else:
                        raw_materials = raw_materials.filter(parent_bom__bom_type = source_type)
                except Exception as e:
                    raw_materials = []
                all_raw_materials.extend(raw_materials)
            try:
                sub_orders = po_item_detail_instance.sub_production_orders.all()
            except Exception as e:
                sub_orders = []
            if sub_orders:
                for sub_order in sub_orders:
                    is_source = False
                    if source_type: 
                        if sub_order.bom_type.name == source_type:
                            is_source = True
                    else:
                        is_source = True
                    try:
                        link_instance = ProductionOrderLinkingTable.objects.filter(po_master = sub_order.po_master)
                    except:
                        link_instance = None
                    if link_instance:
                        link_instance = link_instance[0]
                        get_all_sub_orders(link_instance.po_item_detail, is_source)
    #                   
    try:
        po_item_detail_instance = ProductionOrderItemDetail.objects.get(id = po_detail_id)
    except Exception as e:
        # print(e, "item detail")
        po_item_detail_instance = None
    get_all_sub_orders(po_item_detail_instance, True)
    # all_raw_materials.sort(key=lambda x: x.id)
    return all_raw_materials