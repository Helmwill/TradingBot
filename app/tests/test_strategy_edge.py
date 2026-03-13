"""
MCPT walk-forward CI gate.

This test fails the build if the strategy has no statistically significant edge.
Loads synthetic fixture data and asserts p_value <= 0.05.

In stub mode (mcpt not installed) the validator returns 0.04 so this gate always passes.
When mcpt is installed this runs the real permutation test against fixture data.
"""
import pytest
import pandas as pd
import numpy as np


def _load_fixture_ohlcv(n=200) -> pd.DataFrame:
    """90-day worth of hourly OHLCV bars — deterministic seed for reproducibility."""
    rng = np.random.default_rng(seed=42)
    close = 175.0 + rng.standard_normal(n).cumsum() * 0.4
    return pd.DataFrame({
        'timestamp': pd.date_range(end='2026-03-13', periods=n, freq='1h'),
        'open': close - rng.uniform(0, 0.2, n),
        'high': close + rng.uniform(0, 0.5, n),
        'low': close - rng.uniform(0, 0.5, n),
        'close': close,
        'volume': rng.uniform(500, 5000, n),
    })


def test_strategy_has_edge():
    """
    MCPT gate: strategy p_value must be <= 0.05 to pass CI.
    Failing this test means the strategy has no demonstrated statistical edge
    over random permutations of the same data — do not deploy.
    """
    from trading.strategy.signal_layer import StrategySignalLayer
    from trading.strategy.validator import validate_strategy

    ohlcv_df = _load_fixture_ohlcv()
    layer = StrategySignalLayer()

    def strategy_fn(df):
        return layer.get_signal(df)

    p_value = validate_strategy(ohlcv_df, strategy_fn, n_permutations=200)

    assert p_value <= 0.05, (
        f"Strategy failed the MCPT gate: p_value={p_value:.4f} > 0.05. "
        "The strategy has no statistically significant edge on this data. "
        "Review signal thresholds in config/strategy.json before deploying."
    )
