# ADR 002 — Signal Library: pandas-ta

**Status:** Accepted  
**Date:** 2026-04-24

## Decision

Use `pandas-ta` for all technical indicator calculations (RSI, MACD, EMA, ATR, VWAP).

## Rationale

- MIT licensed, pure Python, no C extensions — installs cleanly in Docker with no system deps
- Single library covers all indicators needed for the default RSI+MACD crossover strategy
- Operates directly on pandas DataFrames — zero glue code between data fetch and signal evaluation
- Active maintenance, 4k+ GitHub stars

## Rejected alternatives

- **neurotrader888/market-structure**: unverified API, no PyPI release, git-only install — fragile in CI
- **TradingView Pine Script**: requires ongoing subscription and webhook infrastructure — adds cost and external dependency between signal and execution
- **TA-Lib**: requires system-level C library install — complicates Docker builds

## Default strategy

RSI(14) + MACD(12,26,9) crossover. BUY when RSI < oversold threshold AND MACD histogram crosses from negative to positive. SELL when RSI > overbought threshold AND histogram crosses from positive to negative. Thresholds configurable per ticker in `config/strategy.json`.
