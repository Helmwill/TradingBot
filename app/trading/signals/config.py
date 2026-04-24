"""Load per-ticker strategy configuration from config/strategy.json."""
import json
import os

_CONFIG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', 'config', 'strategy.json',
))

_config_cache = None


def _load() -> dict:
    global _config_cache
    if _config_cache is None:
        path = os.environ.get('STRATEGY_CONFIG_PATH', _CONFIG_PATH)
        with open(os.path.normpath(path)) as f:
            _config_cache = json.load(f)
    return _config_cache


def get_tickers() -> list:
    """
    Return the active ticker list.
    Priority: TRADING_TICKERS env var → config/strategy.json tickers key.
    """
    env_tickers = os.environ.get('TRADING_TICKERS', '')
    if env_tickers:
        return [t.strip() for t in env_tickers.split(',') if t.strip()]
    return _load().get('tickers', ['AAPL'])


def get_ticker_config(ticker: str) -> dict:
    """Return merged config for a ticker (default values + ticker-specific overrides)."""
    cfg = _load()
    return {**cfg.get('default', {}), **cfg.get(ticker, {})}
