from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
import logging
import time

from .models import Trade
from .ctrader_client import CTraderClient, CTraderClientError
from .strategy.config_loader import get_instruments

_START_TIME = time.monotonic()

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bot_status(request):
    """Current bot status: strategy, instruments, last signal, last trade, uptime, celery health."""
    last_trade = Trade.objects.first()
    last_trade_data = None
    if last_trade:
        last_trade_data = {
            "instrument": last_trade.instrument,
            "action": last_trade.action,
            "price": str(last_trade.price),
            "timestamp": last_trade.timestamp.isoformat(),
        }

    celery_status = _check_celery_health()

    return JsonResponse({
        "status": "running",
        "strategy": "MarketStructureStrategy",
        "instruments": get_instruments(),
        "last_trade": last_trade_data,
        "uptime_seconds": int(time.monotonic() - _START_TIME),
        "celery_worker": celery_status,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bot_trades(request):
    """Paginated trade history with cumulative P&L."""
    page_size = int(request.GET.get('page_size', 50))
    page = int(request.GET.get('page', 1))
    offset = (page - 1) * page_size

    trades = Trade.objects.all()[offset:offset + page_size]
    total = Trade.objects.count()

    trade_list = [
        {
            "id": t.pk,
            "timestamp": t.timestamp.isoformat(),
            "instrument": t.instrument,
            "action": t.action,
            "price": str(t.price),
            "amount": str(t.amount),
            "order_id": t.order_id,
            "signal_meta": t.signal_meta,
        }
        for t in trades
    ]

    return JsonResponse({
        "total": total,
        "page": page,
        "page_size": page_size,
        "trades": trade_list,
    })


def _check_celery_health() -> str:
    try:
        from .celery import app as celery_app
        result = celery_app.control.inspect(timeout=1.0).ping()
        return "healthy" if result else "unavailable"
    except Exception:
        return "unavailable"
