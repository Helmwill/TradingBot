"""Load per-instrument strategy configuration from config/strategy.json."""
import json
import os

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    '..', 'config', 'strategy.json'
)

_config_cache = None


def get_strategy_config(instrument: str) -> dict:
    """
    Get strategy config for an instrument.
    Falls back to 'default' if instrument not found.
    """
    global _config_cache
    if _config_cache is None:
        config_path = os.environ.get('STRATEGY_CONFIG_PATH', _CONFIG_PATH)
        with open(os.path.normpath(config_path), 'r') as f:
            _config_cache = json.load(f)

    return {**_config_cache.get('default', {}), **_config_cache.get(instrument, {})}


def get_instruments() -> list:
    """Return the configured instrument list."""
    global _config_cache
    if _config_cache is None:
        get_strategy_config('default')
    return _config_cache.get('instruments', ['AAPL'])
