import pytest
import pandas as pd
import numpy as np


def make_df(n=100, trend='flat'):
    np.random.seed(42)
    if trend == 'up':
        close = 100.0 + np.arange(n) * 0.5
    elif trend == 'down':
        close = 100.0 - np.arange(n) * 0.5
    else:
        close = 100.0 + np.random.randn(n).cumsum() * 0.3
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1h'),
        'open': close - 0.1,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.abs(np.random.randn(n) * 1000) + 500,
    })


@pytest.fixture
def layer():
    from trading.strategy.signal_layer import StrategySignalLayer
    return StrategySignalLayer()


def test_signal_returns_dict(layer):
    result = layer.get_signal(make_df())
    assert isinstance(result, dict)
    assert set(result.keys()) >= {'action', 'confidence', 'metadata'}


def test_signal_action_is_valid(layer):
    result = layer.get_signal(make_df())
    assert result['action'] in ('BUY', 'SELL', 'HOLD')


def test_confidence_between_0_and_1(layer):
    result = layer.get_signal(make_df())
    assert 0.0 <= result['confidence'] <= 1.0


def test_returns_hold_on_insufficient_data(layer):
    result = layer.get_signal(make_df(5))
    assert result['action'] == 'HOLD'
    assert result['confidence'] == 0.0


def test_returns_hold_on_none(layer):
    result = layer.get_signal(None)
    assert result['action'] == 'HOLD'


def test_factory_creates_layer():
    from trading.strategy.signal_layer import create_signal_layer
    layer = create_signal_layer('AAPL')
    assert callable(getattr(layer, 'get_signal', None))
