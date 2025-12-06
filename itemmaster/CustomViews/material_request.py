from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from itemmaster.models import *
import datetime

@csrf_exempt
def create_material_request_batch(request):
    if request.method == 'POST':
        try:
            received_data = json.loads(request.body)['data']
            store_data = received_data['rawmaterials']
            created_by = User.objects.get(id = received_data['created_by'])
            dept_instance = Department.objects.get(id = received_data['department'])
            pomaster_instance = ProductionOrderMaster.objects.get(id = received_data['pomaster'])
            for store_item in store_data:
                created_item_detail_id = []
                store_instance = Store.objects.get(id = store_item['storeID'])
                raw_materials_list = store_item['items']
                for raw_materials_item in raw_materials_list:
                    item_master = ItemMaster.objects.get(id = raw_materials_item['partCode']['id'])
                    item_detail_instance = MaterialRequestItemDetails.objects.create(
                        part_number = item_master,
                        hsn_code = item_master.item_hsn,
                        qty = raw_materials_item['actualQty'],
                        uom = UOM.objects.get(id = raw_materials_item['unit']['id']),
                        issued_qty = 0,
                        po_raw_material = ProductionOrderRawMaterials.objects.get(id = raw_materials_item['id']),
                        created_by = created_by,
                        modified_by = created_by,
                    )
                    created_item_detail_id.append(item_detail_instance.id)
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                material_request_instance = MaterialRequestMaster.objects.create(
                    request_for = MaterialRequestFor.objects.get(id = 1),
                    request_date = current_date,
                    production_order = pomaster_instance,
                    department = dept_instance,
                    issuing_store = store_instance,
                    created_by = created_by,
                    modified_by = created_by,
                )
                material_request_instance.item_details.add(*created_item_detail_id)
            response_data = {
                'message': 'Data Created successfully'
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)
