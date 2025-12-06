from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from itemmaster.models import *
from django.db.models import Sum


@csrf_exempt
def fetch_total_qty_for_inventory_approval(request):
    if request.method == 'POST':
        try:
            received_data = json.loads(request.body)['data']
            inventory_approval_id = received_data['id_list']
            queryset = ItemInventoryApproval.objects.filter(id__in=inventory_approval_id)
            total_qty = queryset.aggregate(total_qty=Sum('qty'))['total_qty']
            response_data = {
                'message': 'Data received successfully',
                'data': {
                    'total_qty': total_qty,
                }
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)