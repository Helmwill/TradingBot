import json
import logging
import time

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .broker.ibkr import IBKRConnector, IBKRError
from .models import Trade
from .signals.config import get_tickers
from .signals.market_hours import is_market_open

_START_TIME = time.monotonic()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historical_data_view(request):
    """OHLCV bars from TimescaleDB for a given ticker and date range."""
    ticker = request.GET.get('ticker') or request.GET.get('symbol')
    if not ticker:
        return JsonResponse({"error": "Missing ticker parameter"}, status=400)

    from .models import OHLCVBar
    bars = OHLCVBar.objects.filter(ticker=ticker).order_by('timestamp')[:500]
    data = [
        {
            'timestamp': b.timestamp.isoformat(),
            'open': str(b.open),
            'high': str(b.high),
            'low': str(b.low),
            'close': str(b.close),
            'volume': str(b.volume),
        }
        for b in bars
    ]
    return JsonResponse({'ticker': ticker, 'bars': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_prices_view(request):
    """Fetch the current spot price for a ticker from IBKR."""
    ticker = request.GET.get('ticker') or request.GET.get('symbol') or request.GET.get('product_id')
    if not ticker:
        logger.warning("Missing ticker in current prices request")
        return JsonResponse({"error": "Missing ticker parameter"}, status=400)

    try:
        connector = IBKRConnector()
        bars = connector.get_bars(ticker, duration='1 D', bar_size='1 min')
        price = float(bars['close'].iloc[-1]) if not bars.empty else 0.0
        return JsonResponse({'ticker': ticker, 'price': price})
    except IBKRError as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        return JsonResponse({"error": "Failed to fetch current price"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_request(request):
    """Place a manual BUY market order via IBKR and record the trade."""
    try:
        data = json.loads(request.body)
        ticker = data.get('ticker') or data.get('symbol') or data.get('product_id')
        quantity = data.get('quantity') or data.get('amount')

        if not ticker or not quantity:
            logger.warning("Missing ticker or quantity in buy request")
            return JsonResponse({"error": "Missing ticker or quantity"}, status=400)

        qty = int(float(quantity))
        connector = IBKRConnector()
        order = connector.place_market_order(ticker, 'BUY', qty)

        if order.get('status') not in ('Filled', 'FILLED'):
            return JsonResponse({"message": "Order not filled", "order": order}, status=200)

        Trade.objects.create(
            ticker=ticker,
            action='BUY',
            quantity=qty,
            fill_price=order.get('fill_price', 0),
            order_id=order.get('order_id', ''),
            status=order.get('status', 'Filled'),
            signal_meta={},
        )
        logger.info(f"Manual BUY: {ticker} qty={qty} order_id={order.get('order_id')}")
        return JsonResponse(order)

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid buy request data: {e}")
        return JsonResponse({"error": f"Invalid request data: {e}"}, status=400)
    except IBKRError as e:
        logger.error(f"IBKR error in buy_request: {e}")
        return JsonResponse({"error": "Order placement failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in buy_request: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_request(request):
    """Place a manual SELL market order via IBKR and record the trade."""
    try:
        data = json.loads(request.body)
        ticker = data.get('ticker') or data.get('symbol') or data.get('product_id')
        quantity = data.get('quantity') or data.get('amount')

        if not ticker or not quantity:
            logger.warning("Missing ticker or quantity in sell request")
            return JsonResponse({"error": "Missing ticker or quantity"}, status=400)

        qty = int(float(quantity))
        connector = IBKRConnector()
        order = connector.place_market_order(ticker, 'SELL', qty)

        if order.get('status') not in ('Filled', 'FILLED'):
            return JsonResponse({"message": "Order not filled", "order": order}, status=200)

        Trade.objects.create(
            ticker=ticker,
            action='SELL',
            quantity=qty,
            fill_price=order.get('fill_price', 0),
            order_id=order.get('order_id', ''),
            status=order.get('status', 'Filled'),
            signal_meta={},
        )
        logger.info(f"Manual SELL: {ticker} qty={qty} order_id={order.get('order_id')}")
        return JsonResponse(order)

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid sell request data: {e}")
        return JsonResponse({"error": f"Invalid request data: {e}"}, status=400)
    except IBKRError as e:
        logger.error(f"IBKR error in sell_request: {e}")
        return JsonResponse({"error": "Order placement failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in sell_request: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bot_status(request):
    """Bot running state, tickers, market hours, IBKR connection, last trade, Celery health."""
    last_trade = Trade.objects.first()
    last_trade_data = None
    if last_trade:
        last_trade_data = {
            'ticker': last_trade.ticker,
            'action': last_trade.action,
            'fill_price': str(last_trade.fill_price),
            'quantity': str(last_trade.quantity),
            'timestamp': last_trade.timestamp.isoformat(),
        }

    ibkr_port = getattr(settings, 'IBKR_PORT', 4002)
    return JsonResponse({
        'status': 'running',
        'broker': 'Interactive Brokers',
        'account_mode': 'paper' if ibkr_port == 4002 else 'live',
        'tickers': get_tickers(),
        'market_open': is_market_open(),
        'last_trade': last_trade_data,
        'uptime_seconds': int(time.monotonic() - _START_TIME),
        'celery_worker': _check_celery_health(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bot_trades(request):
    """Paginated trade history."""
    page_size = int(request.GET.get('page_size', 50))
    page = int(request.GET.get('page', 1))
    offset = (page - 1) * page_size

    trades = Trade.objects.all()[offset:offset + page_size]
    total = Trade.objects.count()

    trade_list = [
        {
            'id': t.pk,
            'timestamp': t.timestamp.isoformat(),
            'ticker': t.ticker,
            'action': t.action,
            'quantity': str(t.quantity),
            'fill_price': str(t.fill_price),
            'order_id': t.order_id,
            'status': t.status,
            'signal_meta': t.signal_meta,
        }
        for t in trades
    ]

    return JsonResponse({
        'total': total,
        'page': page,
        'page_size': page_size,
        'trades': trade_list,
    })


def _check_celery_health() -> str:
    try:
        from .celery import app as celery_app
        result = celery_app.control.inspect(timeout=1.0).ping()
        return 'healthy' if result else 'unavailable'
    except Exception:
        return 'unavailable'
