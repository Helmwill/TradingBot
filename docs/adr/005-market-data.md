# ADR 005 — Market Data: IBKR Feed

**Status:** Accepted  
**Date:** 2026-04-24

## Decision

Use IBKR's own market data feed (via `ib_insync.reqHistoricalData`) as the sole source of OHLCV price bars in production. No third-party data provider.

## Rationale

- IBKR market data is free with an active account — zero additional cost
- Data comes from the same system that executes orders — no slippage between signal data and actual fills
- `reqHistoricalData` supports flexible duration and bar-size parameters suitable for the 5-min polling strategy
- Eliminates a network hop to an external API — lower latency between data fetch and order placement

## Rejected alternatives

- **yfinance**: unofficial, scrapes Yahoo Finance — unreliable in production, rate-limited, no SLA
- **Alpha Vantage / Polygon.io**: paid subscriptions add ongoing cost; introduce a second external dependency
- **Coinbase / crypto feeds**: project scope is US equities only

## Usage

`IBKRConnector.get_bars(ticker, duration='1 D', bar_size='5 mins')` fetches bars and returns a DataFrame with columns `[timestamp, open, high, low, close, volume]`. Bars are persisted to the `OHLCVBar` TimescaleDB hypertable after each fetch.
