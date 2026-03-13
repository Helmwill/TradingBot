"""
Synchronous wrapper around the ctrader-open-api library.

cTrader Open API uses Protobuf over TCP (async). This wrapper provides
synchronous methods for use in Django REST views. Day 2 Celery tasks
will use persistent async connections for better performance.

Required settings (set via environment variables, never hardcoded):
  - settings.CTRADER_CLIENT_ID
  - settings.CTRADER_CLIENT_SECRET
  - settings.CTRADER_ACCOUNT_ID
  - settings.CTRADER_HOST (demo.ctraderapi.com or live.ctraderapi.com)
  - settings.CTRADER_PORT (default 5035)
"""
import asyncio
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
    from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
    from ctrader_open_api.messages.OpenApiMessages_pb2 import *
    CTRADER_AVAILABLE = True
except ImportError:
    logger.warning("ctrader-open-api not installed. CTraderClient will use stub mode.")
    CTRADER_AVAILABLE = False


class CTraderClientError(Exception):
    """Raised when a cTrader API call fails."""
    pass


class CTraderClient:
    """
    Synchronous cTrader Open API client for use in Django views.

    Usage:
        client = CTraderClient()
        price = client.get_spot_price('AAPL')
        order = client.place_order('AAPL', 'BUY', volume=1.0)
    """

    def get_spot_price(self, symbol: str) -> float:
        """
        Get the current spot price for a CFD instrument.

        Args:
            symbol: cTrader symbol name (e.g. 'AAPL', 'UK100')

        Returns:
            float: current bid price

        Raises:
            CTraderClientError: if price cannot be fetched
        """
        if not CTRADER_AVAILABLE:
            return self._stub_get_spot_price(symbol)
        try:
            return asyncio.run(self._async_get_spot_price(symbol))
        except Exception as e:
            raise CTraderClientError(f"Failed to get spot price for {symbol}: {e}") from e

    def place_order(self, symbol: str, side: str, volume: float) -> dict:
        """
        Place a market order via cTrader.

        Args:
            symbol: cTrader symbol name (e.g. 'AAPL')
            side: 'BUY' or 'SELL'
            volume: order volume in lots

        Returns:
            dict with order details (order_id, status, symbol, side, volume)

        Raises:
            CTraderClientError: if order placement fails
            ValueError: if side is not 'BUY' or 'SELL'
        """
        if side not in ('BUY', 'SELL'):
            raise ValueError(f"side must be 'BUY' or 'SELL', got '{side}'")

        if not CTRADER_AVAILABLE:
            return self._stub_place_order(symbol, side, volume)
        try:
            return asyncio.run(self._async_place_order(symbol, side, volume))
        except Exception as e:
            raise CTraderClientError(f"Failed to place {side} order for {symbol}: {e}") from e

    # ---- async implementations ----

    async def _async_get_spot_price(self, symbol: str) -> float:
        """Connect to cTrader, subscribe to spot, get price, disconnect."""
        host = getattr(settings, 'CTRADER_HOST', 'demo.ctraderapi.com')
        port = getattr(settings, 'CTRADER_PORT', 5035)
        client_id = getattr(settings, 'CTRADER_CLIENT_ID', '')
        client_secret = getattr(settings, 'CTRADER_CLIENT_SECRET', '')
        account_id = getattr(settings, 'CTRADER_ACCOUNT_ID', '')

        # TODO: Implement full async cTrader spot price subscription
        # Reference: ctrader-open-api ProtoOASubscribeSpotsReq
        # This is a placeholder — implement using the ctrader-open-api callback pattern
        raise NotImplementedError(
            "Async cTrader spot price not yet implemented. "
            "Implement using ProtoOASubscribeSpotsReq in Day 2 Celery tasks."
        )

    async def _async_place_order(self, symbol: str, side: str, volume: float) -> dict:
        """Place a ProtoOANewOrderReq via cTrader TCP connection."""
        # TODO: Implement full async order placement
        # Reference: ctrader-open-api ProtoOANewOrderReq
        raise NotImplementedError(
            "Async cTrader order placement not yet implemented. "
            "Implement using ProtoOANewOrderReq in Day 2 Celery tasks."
        )

    # ---- stub implementations (used when ctrader-open-api not installed) ----

    def _stub_get_spot_price(self, symbol: str) -> float:
        """Return a fake price for testing without live API."""
        stub_prices = {'AAPL': 175.50, 'TSLA': 195.30, 'UK100': 7500.0}
        return stub_prices.get(symbol, 100.0)

    def _stub_place_order(self, symbol: str, side: str, volume: float) -> dict:
        """Return a fake order response for testing."""
        return {
            'order_id': f'stub-{side.lower()}-{symbol}-{volume}',
            'status': 'FILLED',
            'symbol': symbol,
            'side': side,
            'volume': volume,
            'price': self._stub_get_spot_price(symbol),
        }
