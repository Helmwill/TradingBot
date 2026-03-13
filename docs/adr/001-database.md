# ADR 001: Switch to TimescaleDB

**Status:** Accepted — 2026-03-13

## Why we changed

The original codebase used MySQL on AWS RDS. Trading data is inherently time-series — every price tick, OHLCV bar, and trade record is indexed by time. MySQL handles this adequately but TimescaleDB is purpose-built for it, offering automatic time-based partitioning and faster range queries at no extra code cost.

## What we decided

Replace MySQL with TimescaleDB (a PostgreSQL extension). Use `django-timescaledb` to declare hypertables from Django models. Run TimescaleDB in Docker alongside the application rather than on a managed cloud service.

## Trade-offs

- Faster time-range queries on trade history and OHLCV bars out of the box
- Full PostgreSQL compatibility — Django ORM needs no changes
- Removes the AWS RDS dependency and its monthly cost
- One-time data migration from MySQL is required (manual, handled by Helmwill)
- `pymysql` and `mysql-connector-python` dependencies removed
