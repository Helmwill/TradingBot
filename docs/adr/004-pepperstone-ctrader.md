# ADR 004: Switch from Coinbase Pro to Pepperstone cTrader Open API

**Status:** Accepted — 2026-03-13

## Why we changed

Coinbase Pro deprecated its API. The new trading focus is CFDs on equities, ETFs, and indices across US and UK markets — assets that Coinbase does not offer. Pepperstone provides a Standard account with no per-trade commission (cost is in the spread), which suits the trading frequency of this bot.

## What we decided

Use the Pepperstone cTrader Open API via the `ctrader-open-api` Python library. The protocol is Protobuf over TCP — a persistent connection rather than stateless REST calls. Order placement uses `ProtoOANewOrderReq`. Real-time prices come from `ProtoOASubscribeSpotsReq`. Historical OHLCV uses `ProtoOAGetTrendbarsReq`.

Django views use a synchronous wrapper for now. Celery tasks (Day 2) will manage the persistent TCP connection properly.

## Trade-offs

- Access to the full Pepperstone CFD universe: US and UK equities, ETFs, major indices
- No per-trade commission on Standard account
- Protocol is more complex than REST — requires managing a TCP connection and Protobuf messages
- Credentials are OAuth-based (client ID, client secret, account ID) stored only in environment variables, never in code
