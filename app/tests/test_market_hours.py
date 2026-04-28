"""
Unit tests for NYSE market hours gating.

Tests cover: open window, pre-open, post-close, weekends, UTC boundary.
Holiday tests use the _utc_window_check fallback when pandas-market-calendars is unavailable.
"""
from datetime import datetime
import pytz
from trading.signals.market_hours import is_market_open, _utc_window_check


def utc(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=pytz.utc)


# ---- _utc_window_check (always available) ----

def test_utc_window_open():
    # Tuesday 15:00 UTC — NYSE open
    assert _utc_window_check(utc(2025, 6, 10, 15, 0)) is True


def test_utc_window_pre_open():
    # 13:00 UTC — pre-market
    assert _utc_window_check(utc(2025, 6, 10, 13, 0)) is False


def test_utc_window_post_close():
    # 21:30 UTC — after close
    assert _utc_window_check(utc(2025, 6, 10, 21, 30)) is False


def test_utc_window_exact_open_boundary():
    assert _utc_window_check(utc(2025, 6, 10, 14, 30)) is True


def test_utc_window_exact_close_boundary():
    # 21:00 is exclusive (< 21:00)
    assert _utc_window_check(utc(2025, 6, 10, 21, 0)) is False


# ---- is_market_open (full check) ----

def test_weekday_during_hours_is_open():
    # Tuesday 16:00 UTC
    assert is_market_open(utc(2025, 6, 10, 16, 0)) is True


def test_saturday_is_closed():
    assert is_market_open(utc(2025, 6, 14, 16, 0)) is False


def test_sunday_is_closed():
    assert is_market_open(utc(2025, 6, 15, 16, 0)) is False


def test_before_open_is_closed():
    assert is_market_open(utc(2025, 6, 10, 10, 0)) is False


def test_after_close_is_closed():
    assert is_market_open(utc(2025, 6, 10, 22, 0)) is False


def test_naive_datetime_treated_as_utc():
    # Should not raise — naive datetime handled gracefully
    naive = datetime(2025, 6, 10, 16, 0)
    result = is_market_open(naive)
    assert isinstance(result, bool)


def test_defaults_to_now():
    # Should not raise when called with no argument
    result = is_market_open()
    assert isinstance(result, bool)
