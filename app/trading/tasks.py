import logging
from celery import shared_task

from .broker.ibkr import IBKRConnector, IBKRError
from .signals.engine import create_signal_engine
from .signals.market_hours import is_market_open
from .signals.config import get_ticker_config
from .models import Trade, OHLCVBar, TradingError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_trading_cycle(self, ticker: str):
    """
    Single trading cycle for one ticker.

    Flow: check market hours → fetch OHLCV bars from IBKR → evaluate signal
          → place market order if BUY/SELL → write Trade record.
    Retries up to 3 times on IBKR errors. Non-IBKR errors go to TradingError dead-letter log.
    """
    if not is_market_open():
        logger.debug(f"{ticker}: market closed, skipping cycle")
        return {'ticker': ticker, 'action': 'MARKET_CLOSED'}

    logger.debug(f"Starting trading cycle for {ticker}")
    try:
        connector = IBKRConnector()
        engine = create_signal_engine(ticker)

        df = connector.get_bars(ticker)
        _save_ohlcv_bars(ticker, df)

        signal = engine.evaluate(df)
        logger.info(f"{ticker}: signal={signal['action']} confidence={signal['confidence']:.2f}")

        if signal['action'] not in ('BUY', 'SELL'):
            return {'ticker': ticker, 'action': 'HOLD'}

        config = get_ticker_config(ticker)
        quantity = int(config.get('position_size', 1))
        order = connector.place_market_order(ticker, signal['action'], quantity)

        if order.get('status') in ('Filled', 'FILLED'):
            Trade.objects.create(
                ticker=ticker,
                action=signal['action'],
                quantity=quantity,
                fill_price=order.get('fill_price', 0),
                order_id=order.get('order_id', ''),
                status=order.get('status', 'Filled'),
                signal_meta=signal,
            )
            logger.info(
                f"Trade recorded: {signal['action']} {ticker} "
                f"qty={quantity} @ {order.get('fill_price')} order_id={order.get('order_id')}"
            )

        return {'ticker': ticker, 'action': signal['action'], 'order': order}

    except IBKRError as e:
        logger.error(f"IBKR error for {ticker}: {e}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error in trading cycle for {ticker}: {e}", exc_info=True)
        _log_trading_error(ticker, str(e))
        raise


def _save_ohlcv_bars(ticker: str, df) -> None:
    bars = [
        OHLCVBar(
            timestamp=row['timestamp'],
            ticker=ticker,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
        )
        for _, row in df.iterrows()
    ]
    OHLCVBar.objects.bulk_create(bars, ignore_conflicts=True)


def _log_trading_error(ticker: str, message: str) -> None:
    try:
        TradingError.objects.create(ticker=ticker, message=message)
    except Exception:
        logger.error(f"Could not persist trading error for {ticker}: {message}")
