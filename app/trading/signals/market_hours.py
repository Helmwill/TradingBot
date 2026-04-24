"""
NYSE market hours gating.

Returns True only when NYSE is open for trading.
Handles weekends, US market holidays, and DST shifts via pandas-market-calendars.
"""
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

try:
    import pandas_market_calendars as mcal
    _nyse = mcal.get_calendar('NYSE')
    MCAL_AVAILABLE = True
except ImportError:
    logger.warning("pandas-market-calendars not installed. Market hours check will use UTC time window only.")
    _nyse = None
    MCAL_AVAILABLE = False


def is_market_open(now: datetime = None) -> bool:
    """
    Returns True if NYSE is currently open for regular trading.

    Uses pandas-market-calendars for accurate holiday and DST handling.
    Falls back to a UTC time window (14:30–21:00) when the library is unavailable.

    Args:
        now: datetime to check (defaults to current UTC time). Must be tz-aware or naive UTC.
    """
    if now is None:
        now = datetime.now(pytz.utc)
    elif now.tzinfo is None:
        now = pytz.utc.localize(now)

    if now.weekday() >= 5:
        return False

    if not MCAL_AVAILABLE:
        return _utc_window_check(now)

    date_str = now.strftime('%Y-%m-%d')
    try:
        schedule = _nyse.schedule(start_date=date_str, end_date=date_str)
        if schedule.empty:
            return False
        market_open = schedule.iloc[0]['market_open'].to_pydatetime()
        market_close = schedule.iloc[0]['market_close'].to_pydatetime()
        if market_open.tzinfo is None:
            market_open = pytz.utc.localize(market_open)
        if market_close.tzinfo is None:
            market_close = pytz.utc.localize(market_close)
        return market_open <= now <= market_close
    except Exception as e:
        logger.error(f"NYSE calendar check failed: {e}. Falling back to UTC window.")
        return _utc_window_check(now)


def _utc_window_check(now: datetime) -> bool:
    """Fallback: 14:30–21:00 UTC Mon–Fri, no holiday awareness."""
    h, m = now.hour, now.minute
    return (h, m) >= (14, 30) and (h, m) < (21, 0)
