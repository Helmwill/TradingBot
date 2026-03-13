# ADR 002: Replace moving-average strategy with market-structure and mcpt

**Status:** Accepted — 2026-03-13

## Why we changed

The original `RecursiveAverageStrategy` was a simple momentum filter with no statistical validation. It had no way to confirm whether its signals had a real edge or were just fitting to noise.

## What we decided

Use two libraries from neurotrader888:

- **market-structure** — detects swing highs/lows and ATR-based directional changes in price data
- **mcpt** — runs a Monte Carlo permutation test (walk-forward) to check whether the strategy's returns are statistically better than random permutations of the same data

The CI pipeline includes a gate: if `p_value > 0.05` the strategy has no demonstrated edge and the build fails.

## Trade-offs

- Signals are grounded in structural price analysis, not a moving average threshold
- The mcpt gate prevents deploying a strategy that is just overfitting
- Both libraries are installed from GitHub (not PyPI) so CI must have git access to install them
- The async cTrader connection managed by Celery feeds data into the signal layer
