"""
Unit tests for SignalEngine.

All tests use the stub evaluate path (pandas-ta may not be installed in CI).
Core contracts — correct return shape, valid action, confidence in range —
hold regardless of whether the real or stub implementation runs.
"""
import pytest
import numpy as np
import pandas as pd
from trading.signals.engine import SignalEngine, create_signal_engine


def make_df(n=100, trend='flat', seed=42):
    rng = np.random.default_rng(seed=seed)
    if trend == 'up':
        close = 100.0 + np.arange(n) * 0.5 + rng.standard_normal(n) * 0.1
    elif trend == 'down':
        close = 100.0 - np.arange(n) * 0.5 + rng.standard_normal(n) * 0.1
    else:
        close = 100.0 + rng.standard_normal(n).cumsum() * 0.3
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='5min'),
        'open': close - 0.1,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.abs(rng.standard_normal(n) * 1000) + 500,
    })


@pytest.fixture
def engine():
    return SignalEngine()


def test_evaluate_returns_dict(engine, sample_ohlcv_df):
    result = engine.evaluate(sample_ohlcv_df)
    assert isinstance(result, dict)
    assert set(result.keys()) >= {'action', 'confidence', 'indicators'}


def test_action_is_valid(engine, sample_ohlcv_df):
    result = engine.evaluate(sample_ohlcv_df)
    assert result['action'] in ('BUY', 'SELL', 'HOLD')


def test_confidence_in_range(engine, sample_ohlcv_df):
    result = engine.evaluate(sample_ohlcv_df)
    assert 0.0 <= result['confidence'] <= 1.0


def test_hold_on_insufficient_data(engine):
    result = engine.evaluate(make_df(n=5))
    assert result['action'] == 'HOLD'
    assert result['confidence'] == 0.0


def test_hold_on_none(engine):
    result = engine.evaluate(None)
    assert result['action'] == 'HOLD'


def test_indicators_is_dict(engine, sample_ohlcv_df):
    result = engine.evaluate(sample_ohlcv_df)
    assert isinstance(result['indicators'], dict)


def test_uptrend_does_not_produce_sell(engine):
    # Strong uptrend — stub should produce BUY or HOLD, not SELL
    result = engine.evaluate(make_df(n=100, trend='up'))
    assert result['action'] != 'SELL'


def test_downtrend_does_not_produce_buy(engine):
    # Strong downtrend — stub should produce SELL or HOLD, not BUY
    result = engine.evaluate(make_df(n=100, trend='down'))
    assert result['action'] != 'BUY'


def test_factory_creates_engine_with_config():
    engine = create_signal_engine('AAPL')
    assert isinstance(engine, SignalEngine)
    assert engine.rsi_period == 14


def test_factory_applies_ticker_overrides():
    engine = create_signal_engine('TSLA')
    assert engine.rsi_oversold == 35.0
    assert engine.rsi_overbought == 65.0


def test_custom_thresholds():
    engine = SignalEngine(rsi_oversold=25.0, rsi_overbought=75.0)
    assert engine.rsi_oversold == 25.0
    assert engine.rsi_overbought == 75.0
