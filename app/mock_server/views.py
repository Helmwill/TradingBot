from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def mock_create_order(request):
    """Simulates a cTrader market order response for integration testing."""
    if request.method == 'POST':
        data = json.loads(request.body)
        symbol = data.get('symbol', 'AAPL')
        side = data.get('side', 'BUY')
        volume = float(data.get('volume', 1.0))
        prices = {'AAPL': 175.50, 'TSLA': 195.30, 'UK100': 7500.0}
        return JsonResponse({
            'order_id': f'mock-{side.lower()}-{symbol}',
            'status': 'FILLED',
            'symbol': symbol,
            'side': side,
            'volume': volume,
            'price': prices.get(symbol, 100.0),
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def mock_get_spot_price(request):
    """Simulates a cTrader spot price response for integration testing."""
    if request.method == 'GET':
        symbol = request.GET.get('symbol', 'AAPL')
        prices = {'AAPL': 175.50, 'TSLA': 195.30, 'UK100': 7500.0}
        return JsonResponse({'symbol': symbol, 'price': prices.get(symbol, 100.0)})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
