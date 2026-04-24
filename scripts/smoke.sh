#!/usr/bin/env bash
# Smoke test — runs after every deployment. Exits 1 on any failure to trigger auto-rollback.
set -euo pipefail

BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
TIMEOUT=10

check_status() {
    local url="$1" expected="$2" label="$3" actual
    actual=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url")
    if [ "$actual" != "$expected" ]; then
        echo "FAIL: $label — expected HTTP $expected, got $actual ($url)"
        exit 1
    fi
    echo "PASS: $label (HTTP $actual)"
}

echo "--- Smoke test against ${BASE_URL} ---"

# Health endpoint — unauthenticated, must return 200
check_status "$BASE_URL/health/" "200" "GET /health/"

# Auth-protected endpoints must exist and reject unauthenticated access
check_status "$BASE_URL/bot/status/" "401" "GET /bot/status/ (auth required)"
check_status "$BASE_URL/bot/trades/" "401" "GET /bot/trades/ (auth required)"

# Token endpoint exists (GET returns 405 — POST-only)
check_status "$BASE_URL/api/token/" "405" "POST /api/token/ endpoint exists"

echo "--- Smoke test passed ---"
