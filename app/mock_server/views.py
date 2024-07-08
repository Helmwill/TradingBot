from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def mock_create_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        response_data = {
            "id": "mock-order-id",
            "status": "done",
            "product_id": data['product_id'],
            "amount": data['funds'] if data['side'] == 'buy' else data['size'],
            "side": data['side']
        }
        return JsonResponse(response_data, status=200)
    return JsonResponse({"error": "Invalid request method"}, status=405)
