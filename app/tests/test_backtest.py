"""
Backtest CI gate (replaces MCPT).

Runs SignalEngine over a 200-bar fixture and asserts:
  - Sharpe ratio > 0.5
  - Max drawdown < 20%

A failure here means the default RSI+MACD strategy produces statistically
poor results on the fixture data — review thresholds before deploying.
"""
import pytest
import numpy as np
import pandas as pd
from trading.signals.engine import SignalEngine


def _simulate_trades(df: pd.DataFrame, engine: SignalEngine) -> list:
    """Walk forward through bars, collect simulated P&L per trade."""
    returns = []
    position = None  # (entry_price, action)

    for i in range(engine._min_bars, len(df)):
        window = df.iloc[:i]
        signal = engine.evaluate(window)

        if signal['action'] == 'BUY' and position is None:
            position = ('long', float(df['close'].iloc[i - 1]))

        elif signal['action'] == 'SELL' and position and position[0] == 'long':
            exit_price = float(df['close'].iloc[i - 1])
            pct_return = (exit_price - position[1]) / position[1]
            returns.append(pct_return)
            position = None

    return returns


def _sharpe(returns: list) -> float:
    if len(returns) < 2:
        return 0.0
    arr = np.array(returns)
    return float(arr.mean() / arr.std()) * np.sqrt(252) if arr.std() > 0 else 0.0


def _max_drawdown(returns: list) -> float:
    if not returns:
        return 0.0
    cumulative = np.cumprod(1 + np.array(returns))
    peak = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - peak) / peak
    return float(abs(drawdowns.min()))


def test_backtest_sharpe_and_drawdown(backtest_fixture_df):
    engine = SignalEngine()
    returns = _simulate_trades(backtest_fixture_df, engine)

    if len(returns) < 2:
        pytest.skip("Fixture produced fewer than 2 trades — increase fixture size or adjust thresholds")

    sharpe = _sharpe(returns)
    drawdown = _max_drawdown(returns)

    assert sharpe > 0.5, (
        f"Backtest Sharpe {sharpe:.3f} < 0.5. "
        "Strategy has insufficient risk-adjusted return on fixture data."
    )
    assert drawdown < 0.20, (
        f"Backtest max drawdown {drawdown:.1%} >= 20%. "
        "Strategy has excessive drawdown on fixture data."
    )
