import logging
from celery import shared_task
from django.utils import timezone

from .ctrader_client import CTraderClient, CTraderClientError
from .strategy.signal_layer import create_signal_layer
from .strategy.config_loader import get_strategy_config
from .models import Trade, OHLCVBar

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_trading_cycle(self, instrument: str):
    """
    Single trading cycle for one instrument.

    Flow: fetch OHLCV bars → get signal → place order if BUY/SELL → write Trade record.
    Retries up to 3 times with a 60-second delay on cTrader errors.
    """
    logger.debug(f"Starting trading cycle for {instrument}")
    try:
        client = CTraderClient()
        signal_layer = create_signal_layer(instrument)
        config = get_strategy_config(instrument)

        ohlcv_df = client.get_ohlcv_bars(instrument, n_bars=100)

        # Persist bars for backtesting and MCPT validation
        _save_ohlcv_bars(instrument, ohlcv_df)

        signal = signal_layer.get_signal(ohlcv_df)
        logger.info(f"{instrument}: signal={signal['action']} confidence={signal['confidence']:.2f}")

        if signal['action'] not in ('BUY', 'SELL'):
            return {'instrument': instrument, 'action': 'HOLD'}

        volume = float(config.get('position_size', 1.0))
        order = client.place_order(instrument, signal['action'], volume)

        if order.get('status') == 'FILLED':
            Trade.objects.create(
                instrument=instrument,
                action=signal['action'],
                price=order.get('price', 0),
                amount=volume,
                signal_meta=signal,
                order_id=order.get('order_id', ''),
            )
            logger.info(
                f"Trade recorded: {signal['action']} {instrument} "
                f"@ {order.get('price')} order_id={order.get('order_id')}"
            )

        return {
            'instrument': instrument,
            'action': signal['action'],
            'order': order,
        }

    except CTraderClientError as e:
        logger.error(f"cTrader error for {instrument}: {e}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error in trading cycle for {instrument}: {e}", exc_info=True)
        _log_trading_error(instrument, str(e))
        raise


def _save_ohlcv_bars(instrument: str, df) -> None:
    """Persist new OHLCV bars, skipping duplicates."""
    bars = [
        OHLCVBar(
            timestamp=row['timestamp'],
            instrument=instrument,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
        )
        for _, row in df.iterrows()
    ]
    OHLCVBar.objects.bulk_create(bars, ignore_conflicts=True)


def _log_trading_error(instrument: str, message: str) -> None:
    """Write failed task details to the database error log."""
    try:
        from .models import TradingError
        TradingError.objects.create(instrument=instrument, message=message)
    except Exception:
        logger.error(f"Could not persist trading error for {instrument}: {message}")
