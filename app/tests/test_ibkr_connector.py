"""
Unit tests for IBKRConnector.

All tests run in stub mode — no live IB Gateway connection is ever made.
"""
import pytest
import pandas as pd
from trading.broker.ibkr import IBKRConnector


@pytest.fixture
def connector():
    return IBKRConnector()


def test_get_bars_returns_dataframe(connector):
    df = connector.get_bars('AAPL')
    assert isinstance(df, pd.DataFrame)


def test_get_bars_has_required_columns(connector):
    df = connector.get_bars('AAPL')
    assert set(df.columns) >= {'timestamp', 'open', 'high', 'low', 'close', 'volume'}


def test_get_bars_non_empty(connector):
    df = connector.get_bars('TSLA')
    assert len(df) > 0


def test_get_bars_close_positive(connector):
    df = connector.get_bars('MSFT')
    assert (df['close'] > 0).all()


def test_place_buy_returns_dict(connector):
    order = connector.place_market_order('AAPL', 'BUY', 5)
    assert isinstance(order, dict)


def test_place_buy_has_required_keys(connector):
    order = connector.place_market_order('AAPL', 'BUY', 5)
    assert set(order.keys()) >= {'order_id', 'status', 'ticker', 'action', 'quantity', 'fill_price'}


def test_place_sell_action_recorded(connector):
    order = connector.place_market_order('TSLA', 'SELL', 2)
    assert order['action'] == 'SELL'
    assert order['ticker'] == 'TSLA'
    assert order['quantity'] == 2


def test_place_order_fill_price_positive(connector):
    order = connector.place_market_order('AAPL', 'BUY', 1)
    assert float(order['fill_price']) > 0


def test_invalid_action_raises_value_error(connector):
    with pytest.raises(ValueError):
        connector.place_market_order('AAPL', 'HOLD', 1)


def test_get_position_returns_float(connector):
    pos = connector.get_position('AAPL')
    assert isinstance(pos, float)


def test_stub_prices_differ_by_ticker(connector):
    aapl = connector._stub_get_spot_price('AAPL')
    tsla = connector._stub_get_spot_price('TSLA')
    assert aapl != tsla


def test_stub_bars_seeded_deterministic(connector):
    df1 = connector._stub_get_bars('NVDA')
    df2 = connector._stub_get_bars('NVDA')
    assert df1['close'].iloc[0] == df2['close'].iloc[0]
