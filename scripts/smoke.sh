#!/usr/bin/env bash
set -euo pipefail

# Smoke tests run after each deployment.
# Exits 1 on any failure, which triggers automatic rollback in the deploy-prod workflow.

BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
TIMEOUT=10

echo "Running smoke tests against $BASE_URL"

check_status() {
    local url="$1"
    local expected="$2"
    local label="$3"
    local actual
    actual=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url")
    if [ "$actual" != "$expected" ]; then
        echo "FAIL: $label — expected HTTP $expected, got $actual ($url)"
        exit 1
    fi
    echo "PASS: $label (HTTP $actual)"
}

# Health endpoint — no auth required
check_status "$BASE_URL/health/" "200" "health check"

# Auth-protected endpoints must exist and reject unauthenticated requests
check_status "$BASE_URL/bot/status/" "401" "bot status endpoint exists"
check_status "$BASE_URL/bot/trades/" "401" "bot trades endpoint exists"

# Token endpoint is POST-only, so GET returns 405 (not 404)
check_status "$BASE_URL/api/token/" "405" "token endpoint exists"

echo ""
echo "All smoke tests passed."
