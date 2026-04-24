"""
IBKR connector wrapping ib_insync.

ib_insync is an async wrapper over the official ibapi. This module provides
synchronous methods for use in Django views and Celery tasks.

Required settings (set via environment variables, never hardcoded):
  - settings.IBKR_HOST     IB Gateway container hostname (e.g. ib-gateway)
  - settings.IBKR_PORT     4002 for paper, 4001 for live
  - settings.IBKR_CLIENT_ID integer, unique per concurrent connection
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from ib_insync import IB, Stock, MarketOrder, util
    IB_INSYNC_AVAILABLE = True
except ImportError:
    logger.warning("ib_insync not installed. IBKRConnector will use stub mode.")
    IB_INSYNC_AVAILABLE = False


class IBKRError(Exception):
    """Raised when an IBKR API call fails."""
    pass


class IBKRConnector:
    """
    Synchronous IBKR connector for Django views and Celery tasks.

    Each method connects to IB Gateway, performs the operation, then disconnects.
    Connections are short-lived by design — persistent connections are managed
    by the ib-gateway container, not this client.

    Usage:
        connector = IBKRConnector()
        bars = connector.get_bars('AAPL')
        order = connector.place_market_order('AAPL', 'BUY', quantity=5)
    """

    def _connect(self) -> 'IB':
        ib = IB()
        ib.connect(
            host=getattr(settings, 'IBKR_HOST', 'ib-gateway'),
            port=getattr(settings, 'IBKR_PORT', 4002),
            clientId=getattr(settings, 'IBKR_CLIENT_ID', 1),
        )
        return ib

    def get_bars(self, ticker: str, duration: str = '1 D', bar_size: str = '5 mins') -> 'pd.DataFrame':
        """
        Fetch historical OHLCV bars from IBKR for a US equity.

        Args:
            ticker:   NYSE/NASDAQ symbol (e.g. 'AAPL')
            duration: IBKR duration string (e.g. '1 D', '5 D')
            bar_size: IBKR bar size (e.g. '5 mins', '1 hour')

        Returns:
            DataFrame with columns [timestamp, open, high, low, close, volume]

        Raises:
            IBKRError: if bars cannot be fetched
        """
        if not IB_INSYNC_AVAILABLE:
            return self._stub_get_bars(ticker)
        ib = None
        try:
            ib = self._connect()
            contract = Stock(ticker, 'SMART', 'USD')
            ib.qualifyContracts(contract)
            bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
            )
            df = util.df(bars)
            df = df.rename(columns={'date': 'timestamp'})
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            raise IBKRError(f"Failed to fetch bars for {ticker}: {e}") from e
        finally:
            if ib and ib.isConnected():
                ib.disconnect()

    def place_market_order(self, ticker: str, action: str, quantity: int) -> dict:
        """
        Place a market order via IBKR for a US equity.

        Args:
            ticker:   NYSE/NASDAQ symbol
            action:   'BUY' or 'SELL'
            quantity: number of shares (integer)

        Returns:
            dict with keys: order_id, status, ticker, action, quantity, fill_price

        Raises:
            IBKRError: if order placement fails
            ValueError: if action is not 'BUY' or 'SELL'
        """
        if action not in ('BUY', 'SELL'):
            raise ValueError(f"action must be 'BUY' or 'SELL', got {action!r}")

        if not IB_INSYNC_AVAILABLE:
            return self._stub_place_order(ticker, action, quantity)
        ib = None
        try:
            ib = self._connect()
            contract = Stock(ticker, 'SMART', 'USD')
            ib.qualifyContracts(contract)
            order = MarketOrder(action, quantity)
            trade = ib.placeOrder(contract, order)
            ib.sleep(2)
            return {
                'order_id': str(trade.order.orderId),
                'status': trade.orderStatus.status,
                'ticker': ticker,
                'action': action,
                'quantity': quantity,
                'fill_price': trade.orderStatus.avgFillPrice or 0,
            }
        except Exception as e:
            raise IBKRError(f"Failed to place {action} order for {ticker}: {e}") from e
        finally:
            if ib and ib.isConnected():
                ib.disconnect()

    def get_position(self, ticker: str) -> float:
        """Return current share position for a ticker (0.0 if not held)."""
        if not IB_INSYNC_AVAILABLE:
            return 0.0
        ib = None
        try:
            ib = self._connect()
            for pos in ib.positions():
                if pos.contract.symbol == ticker:
                    return float(pos.position)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get position for {ticker}: {e}")
            return 0.0
        finally:
            if ib and ib.isConnected():
                ib.disconnect()

    # ---- stub implementations (used when ib_insync is not installed) ----

    def _stub_get_bars(self, ticker: str) -> 'pd.DataFrame':
        """Generate synthetic OHLCV bars for testing without IB Gateway."""
        import pandas as pd
        import numpy as np
        rng = np.random.default_rng(seed=abs(hash(ticker)) % (2 ** 32))
        n = 100
        base = {'AAPL': 175.0, 'TSLA': 250.0, 'MSFT': 380.0, 'NVDA': 800.0}.get(ticker, 100.0)
        close = base + rng.standard_normal(n).cumsum() * 0.5
        return pd.DataFrame({
            'timestamp': pd.date_range(end=pd.Timestamp.utcnow(), periods=n, freq='5min'),
            'open': close - rng.uniform(0, 0.3, n),
            'high': close + rng.uniform(0, 0.5, n),
            'low': close - rng.uniform(0, 0.5, n),
            'close': close,
            'volume': rng.uniform(1000, 10000, n),
        })

    def _stub_get_spot_price(self, ticker: str) -> float:
        prices = {'AAPL': 175.50, 'TSLA': 250.30, 'MSFT': 382.10, 'NVDA': 805.20}
        return prices.get(ticker, 100.0)

    def _stub_place_order(self, ticker: str, action: str, quantity: int) -> dict:
        return {
            'order_id': f'stub-{action.lower()}-{ticker}-{quantity}',
            'status': 'Filled',
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'fill_price': self._stub_get_spot_price(ticker),
        }
