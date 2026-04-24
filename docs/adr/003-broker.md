# ADR 003 — Broker: Interactive Brokers via ib_insync

**Status:** Accepted  
**Date:** 2026-04-24

## Decision

Use Interactive Brokers (IBKR) as the sole execution broker, accessed via `ib_insync` Python library connecting to a containerised IB Gateway (`ghcr.io/gnzsnz/ib-gateway`).

## Rationale

- IBKR provides direct market access to NYSE and NASDAQ — no CFD spread markup
- `ib_insync` is the de-facto Python async wrapper for the official `ibapi` — well maintained, well documented
- IB Gateway container (`gnzsnz/ib-gateway`) enables auto-login via env vars — no manual TWS session required on the VPS
- Paper trading account is free and API-identical to live — safe for development and CI
- No per-trade commission on IBKR Lite for US equities under $1M/month

## Rejected alternatives

- **Pepperstone/cTrader**: CFD-only, no direct NYSE/NASDAQ access, Protobuf API with no maintained Python SDK
- **Alpaca**: US equities but no international market access for future expansion
- **Interactive Brokers TWS (desktop)**: requires GUI session — not suitable for headless VPS

## Connection

Paper: `ib-gateway:4002` | Live: `ib-gateway:4001`. Port never exposed publicly — only on `platform-net` Docker network.
