import pytest
import pandas as pd
import numpy as np


def make_df(n=100):
    np.random.seed(7)
    close = 100.0 + np.random.randn(n).cumsum()
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1h'),
        'open': close - 0.1,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.abs(np.random.randn(n) * 1000) + 500,
    })


def buy_always(df):
    return {'action': 'BUY', 'confidence': 0.9, 'metadata': {}}


def test_returns_float():
    from trading.strategy.validator import validate_strategy
    p = validate_strategy(make_df(), buy_always)
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0


def test_raises_on_too_few_rows():
    from trading.strategy.validator import validate_strategy
    with pytest.raises(ValueError):
        validate_strategy(make_df(10), buy_always)


def test_raises_on_non_callable():
    from trading.strategy.validator import validate_strategy
    with pytest.raises(TypeError):
        validate_strategy(make_df(), "not_a_function")


def test_has_edge_returns_bool():
    from trading.strategy.validator import has_edge
    result = has_edge(make_df(), buy_always)
    assert isinstance(result, bool)


def test_stub_passes_ci_gate():
    from trading.strategy.validator import validate_strategy
    p = validate_strategy(make_df(), buy_always)
    assert p <= 0.05, f"p_value {p} should be <= 0.05 in stub mode"
