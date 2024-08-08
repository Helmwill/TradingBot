# trading/views.py

from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import requests
from django.conf import settings
from datetime import datetime, timezone, timedelta
import json
import logging
from .models import HistoricalData
from .strategy import RecursiveAverageStrategy

logger = logging.getLogger(__name__)

strategy = RecursiveAverageStrategy()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coinbase_historical_data_view(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        logger.warning("Missing product_id in historical data request")
        return JsonResponse({"error": "Missing product_id"}, status=400)

    # Set the granularity for the historical data (e.g., 300 for 5-minute candles)
    granularity = request.GET.get('granularity', '300')

    try:
        url = f'https://api.pro.coinbase.com/products/{product_id}/candles?granularity={granularity}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Format the response to a readable format
        formatted_data = [
            {
                "time": candle[0],
                "low": candle[1],
                "high": candle[2],
                "open": candle[3],
                "close": candle[4],
                "volume": candle[5],
            }
            for candle in data
        ]
        return JsonResponse(formatted_data, safe=False)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch historical data: {e}")
        return JsonResponse({"error": "Failed to fetch historical data"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_prices_view(request):
    """
    Fetch the current price for a given product ID from Coinbase
    """
    product_id = request.GET.get('product_id')
    if not product_id:
        logger.warning("Missing product_id in current prices request")
        return JsonResponse({"error": "Missing product_id"}, status=400)

    try:
        url = f'https://api.pro.coinbase.com/products/{product_id}/ticker'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current_price = {
            "product_id": product_id,
            "price": data['price'],
            "time": data['time'],
            "trade_id": data['trade_id'],
            "volume_24h": data['volume'],
            "last_size": data['last_size'],
            "best_bid": data['best_bid'],
            "best_ask": data['best_ask']
        }
        return JsonResponse(current_price)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch current price: {e}")
        return JsonResponse({"error": "Failed to fetch current price"}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            amount = data.get('amount')

            if not product_id or not amount:
                logger.warning("Missing product_id or amount in buy request")
                return JsonResponse({"error": "Missing product_id or amount"}, status=400)

            # Get current price and add it to the strategy
            current_price = get_current_price(product_id)
            strategy.add_price(current_price)
            signal = strategy.get_signal()

            if signal != "buy":
                return JsonResponse({"message": "No buy signal generated"}, status=200)

            response = execute_buy_order(product_id, amount)
            logger.info(f"Executed buy order for {product_id} with amount {amount}")
            return JsonResponse(response)
        except Exception as e:
            logger.error(f"Error in buy_request: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    logger.error("Invalid request method in buy_request")
    return JsonResponse({"error": "Invalid request method"}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            amount = data.get('amount')

            if not product_id or not amount:
                logger.warning("Missing product_id or amount in sell request")
                return JsonResponse({"error": "Missing product_id or amount"}, status=400)

            # Get current price and add it to the strategy
            current_price = get_current_price(product_id)
            strategy.add_price(current_price)
            signal = strategy.get_signal()

            if signal != "sell":
                return JsonResponse({"message": "No sell signal generated"}, status=200)

            response = execute_sell_order(product_id, amount)
            logger.info(f"Executed sell order for {product_id} with amount {amount}")
            return JsonResponse(response)
        except Exception as e:
            logger.error(f"Error in sell_request: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    logger.error("Invalid request method in sell_request")
    return JsonResponse({"error": "Invalid request method"}, status=405)

def execute_buy_order(product_id, amount):
    try:
        url = 'https://api-public.sandbox.pro.coinbase.com/orders'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.COINBASE_API_KEY}'
        }
        data = {
            'type': 'market',
            'side': 'buy',
            'product_id': product_id,
            'funds': amount  # The amount of quote currency to use (e.g., USD)
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to execute buy order: {e}")
        return {"error": str(e)}

def execute_sell_order(product_id, amount):
    try:
        url = 'https://api-public.sandbox.pro.coinbase.com/orders'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.COINBASE_API_KEY}'
        }
        data = {
            'type': 'market',
            'side': 'sell',
            'product_id': product_id,
            'size': amount  # The amount of base currency to sell (e.g., BTC)
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to execute sell order: {e}")
        return {"error": str(e)}

def get_current_price(product_id):
    url = f'https://api.pro.coinbase.com/products/{product_id}/ticker'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data['price'])
    else:
        raise Exception("Failed to fetch current price from Coinbase")
