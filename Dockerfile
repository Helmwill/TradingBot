# ---- builder ----
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN useradd --uid 1000 --create-home tradingbot

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ /app/

RUN chown -R tradingbot:tradingbot /app

USER tradingbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "utils.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
