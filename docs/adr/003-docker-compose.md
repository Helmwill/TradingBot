# ADR 003: Docker Compose for deployment

**Status:** Accepted — 2026-03-13

## Why we chose it

The VPS that hosts this bot already runs a dashboard stack using Docker Compose with a shared `platform-net` network and Traefik as a reverse proxy. Using the same approach means the bot slots into the existing infrastructure without any new tooling.

## What we decided

Define four services in `docker-compose.yml`: `tradingbot`, `timescaledb`, `redis`, and `celery-worker`. All services attach to the external `platform-net` network. Traefik routing is configured via container labels — the target hostname is set by the `TRAEFIK_HOST` environment variable so the same Compose file works across dev, QA, and prod.

## Trade-offs

- Zero new infrastructure tooling — consistent with the rest of the VPS platform
- `platform-net` lets the future dashboard call the bot's API directly without going through the public internet
- Scaling is manual (no orchestration layer), which is acceptable at this trading volume
