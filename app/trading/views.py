from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import json
import logging

from .models import Trade
from .ctrader_client import CTraderClient, CTraderClientError

logger = logging.getLogger(__name__)

_ctrader_client = CTraderClient()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historical_data_view(request):
    """
    Historical OHLCV data endpoint.
    Full implementation pending cTrader ProtoOAGetTrendbarsReq integration (Day 2).
    """
    return JsonResponse(
        {"error": "Historical data endpoint not yet implemented. Planned for Day 2 via ProtoOAGetTrendbarsReq."},
        status=501
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_prices_view(request):
    """Fetch the current spot price for a given instrument from cTrader."""
    symbol = request.GET.get('symbol') or request.GET.get('product_id')
    if not symbol:
        logger.warning("Missing symbol in current prices request")
        return JsonResponse({"error": "Missing symbol parameter"}, status=400)

    try:
        price = _ctrader_client.get_spot_price(symbol)
        return JsonResponse({
            "symbol": symbol,
            "price": price,
        })
    except CTraderClientError as e:
        logger.error(f"Failed to fetch current price for {symbol}: {e}")
        return JsonResponse({"error": "Failed to fetch current price"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_request(request):
    """Place a BUY market order via cTrader and record the trade."""
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol') or data.get('product_id')
        amount = data.get('amount')

        if not symbol or not amount:
            logger.warning("Missing symbol or amount in buy request")
            return JsonResponse({"error": "Missing symbol or amount"}, status=400)

        volume = float(amount)
        order = _ctrader_client.place_order(symbol, 'BUY', volume)

        if order.get('status') not in ('FILLED', 'done'):
            return JsonResponse({"message": "Order not filled", "order": order}, status=200)

        Trade.objects.create(
            instrument=symbol,
            action='BUY',
            price=order.get('price', 0),
            amount=volume,
            signal_meta={},
            order_id=order.get('order_id', ''),
        )

        logger.info(f"Executed BUY order for {symbol} volume={volume} order_id={order.get('order_id')}")
        return JsonResponse(order)

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid buy request data: {e}")
        return JsonResponse({"error": f"Invalid request data: {e}"}, status=400)
    except CTraderClientError as e:
        logger.error(f"cTrader error in buy_request: {e}")
        return JsonResponse({"error": "Order placement failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in buy_request: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_request(request):
    """Place a SELL market order via cTrader and record the trade."""
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol') or data.get('product_id')
        amount = data.get('amount')

        if not symbol or not amount:
            logger.warning("Missing symbol or amount in sell request")
            return JsonResponse({"error": "Missing symbol or amount"}, status=400)

        volume = float(amount)
        order = _ctrader_client.place_order(symbol, 'SELL', volume)

        if order.get('status') not in ('FILLED', 'done'):
            return JsonResponse({"message": "Order not filled", "order": order}, status=200)

        Trade.objects.create(
            instrument=symbol,
            action='SELL',
            price=order.get('price', 0),
            amount=volume,
            signal_meta={},
            order_id=order.get('order_id', ''),
        )

        logger.info(f"Executed SELL order for {symbol} volume={volume} order_id={order.get('order_id')}")
        return JsonResponse(order)

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid sell request data: {e}")
        return JsonResponse({"error": f"Invalid request data: {e}"}, status=400)
    except CTraderClientError as e:
        logger.error(f"cTrader error in sell_request: {e}")
        return JsonResponse({"error": "Order placement failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in sell_request: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
