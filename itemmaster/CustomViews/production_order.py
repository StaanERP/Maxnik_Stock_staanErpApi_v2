from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from itemmaster.Utils.production_order_util import *


def create_direct_raw_material(data_list, child_items, master_qty, created_by_user, department, is_multi):
    created_rm_ids = []
    created_sub_po_ids = []
    for index, data_item in enumerate(data_list, start=1):
        item_master_obj = ItemMaster.objects.get(id = data_item['partNumber']['id'])
        try:
            store_obj = Store.objects.get(store_name = data_item['selectedStore'])
        except:
            store_obj = None
        try:
            [bom_no, bom_name, bom_type] = data_item['selectedBom'].split(' -- ') 
            bom_obj = Bom.objects.get(bom_name = bom_name, bom_no = bom_no, bom_type = bom_type)
        except:
            bom_obj = None
        if not bom_obj:
            po_rm_instance = ProductionOrderRawMaterials.objects.create(
                serial_number = f'CM{index}',
                part_code = item_master_obj,
                category = item_master_obj.category,
                bom = bom_obj,
                unit = item_master_obj.item_uom,
                fixed = False,
                actual_qty = Decimal(data_item['itemQty']) * Decimal(master_qty),
                is_combo = True,
                issued_qty = 0,
                used_qty = 0,
                store = store_obj,
                created_by = created_by_user,
                modified_by = created_by_user,
            )
            created_rm_ids.append(po_rm_instance.id)
        else:
            sub_production_order = SubProductionOrders.objects.create(
                status = ProductionOrderStatus.objects.get(id=1), 
                part_code = bom_obj.finished_goods.part_no,
                production_qty = Decimal(data_item['itemQty']) * Decimal(master_qty),
                completed_qty = 0,
                bom_type = MrpSourceType.objects.get(name=bom_obj.bom_type),
                pending_qty = Decimal(data_item['itemQty']) ,
                unit = bom_obj.finished_goods.unit,
                created_by = created_by_user,
                modified_by = created_by_user,
                is_combo = True,
            )
            try:
                current_child = child_items[data_item['partNumber']['id']]
                selected_child_ids = [int(item['id']) for item in current_child]
            except Exception as e:
                current_child = None
                selected_child_ids = None
            created_sub_po_ids.append(sub_production_order.id)
            CreateSubProductionOrdersWithoutMaster(sub_production_order, bom_obj, department, master_qty, created_by_user, selected_child_ids, is_multi)
    return created_rm_ids, created_sub_po_ids


@csrf_exempt
def combo_items_creation(request):
    if request.method == 'POST':
        try:
            received_data = json.loads(request.body)['data']
            combo = received_data['combo']
            child_items = received_data['child']
            department = received_data['department']
            is_multi = received_data['is_multi']
            po_item = received_data['po_item']
            try:
                created_by = User.objects.get(id=received_data['created_by'])
            except:
                created_by = None
            created_rm_ids = []
            if combo:
                po_item_instance = ProductionOrderItem.objects.get(id = po_item)
                po_item_instance.is_combo = True
                po_item_instance.save()
                created_rm_ids, created_sub_po_ids = create_direct_raw_material(combo, child_items,  po_item_instance.qty, created_by, department, is_multi)
            response_data = {
                'message': 'Data received successfully',
                'data': {
                    'raw_material': created_rm_ids,
                    'sub_production': created_sub_po_ids,
                }
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    
        
@csrf_exempt
def sub_production_creation(request):
    if request.method == 'POST':
        try:
            received_data = json.loads(request.body)['data']
            data_list = received_data['combo']
            child_items = received_data['child']
            department = received_data['department']
            is_multi = received_data['is_multi']
            qty = received_data['qty']
            try:
                created_by = User.objects.get(id=received_data['created_by'])
            except:
                created_by = None
            created_sub_po_list = []
            created_rm_list = []
            for index, data_item in enumerate(data_list, start=1):
                try:
                    bom_obj = Bom.objects.get(id = data_item['bom']['id'])
                except:
                    bom_obj = None
                if bom_obj:
                    created_sub_po_list, created_rm_list = CreateSubProductionOrderForPoItem(data_item, bom_obj, qty, department, created_by, child_items, is_multi)
                    
            response_data = {
                'message': 'Data received successfully',
                'data': {
                    'sub_production': created_sub_po_list,
                    'raw_material': created_rm_list,
                }
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def sub_production_to_raw_material_creation(request):
    if request.method == 'POST':
        try:
            received_data = json.loads(request.body)['data']
            data_list = received_data['combo']
            qty = received_data['qty']
            created_rm_ids = []
            for index, data_item in enumerate(data_list, start=1):
                created_by_user = User.objects.get(id = data_item['modifiedBy'])
                try:
                    bom_obj = Bom.objects.get(id = data_item['bom']['id'])
                except:
                    bom_obj = None
                if bom_obj:
                    for raw_material in bom_obj.raw_material.all():
                        try:
                            child_bom_link = RawMaterialBomLink.objects.get(raw_material=raw_material.id)
                            child_bom_link = Bom.objects.get(id = child_bom_link.bom.id)
                        except RawMaterialBomLink.DoesNotExist:
                            child_bom_link = None
                        try:
                            production_order_rm = ProductionOrderRawMaterials.objects.create(
                                serial_number= index,
                                part_code= raw_material.part_no,
                                category= raw_material.part_no.category,
                                parent_bom = bom_obj,
                                bom = child_bom_link,
                                unit = raw_material.unit,
                                fixed = raw_material.fixed,
                                actual_qty= Decimal(raw_material.raw_qty) * Decimal(qty),
                                issued_qty = 0,
                                used_qty = 0,
                                store = child_bom_link.fg_store,
                                created_by = created_by_user,
                                modified_by = created_by_user,
                            )
                            created_rm_ids.append(production_order_rm.id)
                        except Exception as e:
                            print(e, "raw material")
            response_data = {
                'message': 'Data received successfully',
                'data': {
                    'sub_production': [],
                    'raw_material': created_rm_ids,
                }
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)