from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.conf import settings
from datetime import datetime, timezone, timedelta
from .models import HistoricalData

def health_check(request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)

def coinbase_historical_data_view(request):
    # Define default start dates if not provided by user
    default_start_dates = {
        'BTC-USD': '2022-07-17T00:00:00Z',  # Default start date for Bitcoin
        'ETH-USD': '2022-08-07T00:00:00Z'   # Default start date for Ethereum
    }

    # Get query parameters from the request
    start_param = request.GET.get('start')
    end_param = request.GET.get('end')
    product_id = request.GET.get('product_id', 'BTC-USD')  # Default to BTC-USD if not specified

    # Validate product_id
    if product_id not in default_start_dates:
        return JsonResponse({"error": "Invalid product_id. Valid options are 'BTC-USD' and 'ETH-USD'."}, status=400)

    # Set start and end dates based on user input or defaults
    start = start_param if start_param else default_start_dates[product_id]
    end = end_param if end_param else datetime.now(timezone.utc).isoformat()

    # Parse start and end dates
    try:
        start_date = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        end_date = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use ISO 8601 format."}, status=400)

    # Ensure start date is not after end date
    if start_date >= end_date:
        return JsonResponse({"error": "Start date must be before end date."}, status=400)

    historical_data = {}
    fetch_limit = 300

    while start_date < end_date:
        period_end = min(start_date + timedelta(days=fetch_limit), end_date)

        url = f'https://api.pro.coinbase.com/products/{product_id}/candles?start={start_date.isoformat()}&end={period_end.isoformat()}&granularity=86400'
        print(f'Fetching data from {start_date.isoformat()} to {period_end.isoformat()} for {product_id}')

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if product_id not in historical_data:
                historical_data[product_id] = []
            historical_data[product_id].extend(data)
            print(f'Successfully fetched {len(data)} records for {product_id}')

            for candle in data:
                HistoricalData.objects.create(
                    product_id=product_id,
                    timestamp=datetime.fromtimestamp(candle[0], tz=timezone.utc),
                    low=candle[1],
                    high=candle[2],
                    open=candle[3],
                    close=candle[4],
                    volume=candle[5]
                )
            start_date = period_end
        else:
            historical_data[product_id] = {
                'error': 'Failed to fetch data from Coinbase',
                'status_code': response.status_code,
                'response': response.text
            }
            print(f'Error fetching data for {product_id}: {response.status_code} - {response.text}')
            break

    return JsonResponse(historical_data, safe=False)

def current_prices_view(request):
    # Define the product IDs to fetch prices for
    products = ['BTC-USD', 'ETH-USD']
    current_prices = {}

    for product_id in products:
        url = f'https://api.pro.coinbase.com/products/{product_id}/ticker'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            usd_price = float(data['price'])
            volume = float(data['volume'])
            formatted_volumes = f"{volume:,.0f}"
            formatted_prices = f'${usd_price:,.2f}'
            current_prices[product_id] = {
                'Price': formatted_prices, 
                'Volume': formatted_volumes
            }
        else:
            current_prices[product_id] = {
                'error': 'Failed to fetch data from Coinbase',
                'status_code': response.status_code,
                'response': response.text
            }

    return JsonResponse(current_prices, safe=False)
