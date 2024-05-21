from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.conf import settings
from datetime import datetime, timezone, timedelta
from .models import HistoricalData

def health_check (request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)

def coinbase_historical_data_view(request):
    # Define the product IDs and granularity
    products = {
        'BTC-USD': '2020-07-17T00:00:00Z',  # Start date for Bitcoin
        'ETH-USD': '2020-08-07T00:00:00Z'   # Start date for Ethereum
    }
    # Get the current date in ISO 8601 format
    end = datetime.now(timezone.utc).isoformat()
    historical_data = {}
    fetch_limit = 300

    for product_id, start in products.items():
        start_date = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        end_date = datetime.now(timezone.utc)

        while start_date < end_date:
            period_end = min(start_date + timedelta(days=fetch_limit), end_date)


        url = f'https://api.pro.coinbase.com/products/{product_id}/candles?start={start}&end={end}&granularity=86400'
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
                     timestamp=datetime.fromtimestamp(candle[0]), tz=timezone.utc,
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