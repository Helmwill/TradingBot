"""
Market structure signal layer wrapping neurotrader888/market-structure.

Uses local_extreme and atr_directional_change to identify BUY/SELL/HOLD signals
from OHLCV DataFrame input.

TODO: The market-structure library API (LocalExtreme, ATRDirectionalChange) could not
be confirmed via web search at authoring time. The _compute_signal method uses a
reasonable interface based on the library's repository name and typical usage patterns.
Verify against https://github.com/neurotrader888/market-structure and update as needed.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from market_structure.local_extreme import LocalExtreme
    from market_structure.atr_directional_change import ATRDirectionalChange
    MARKET_STRUCTURE_AVAILABLE = True
except ImportError:
    logger.warning("market-structure library not installed. Using stub implementation.")
    MARKET_STRUCTURE_AVAILABLE = False


class StrategySignalLayer:
    """
    Wraps market-structure library to produce BUY/SELL/HOLD signals.

    Args:
        atr_window: ATR calculation window (default 14)
        buy_threshold: confidence threshold for BUY signal (default 0.6)
        sell_threshold: confidence threshold for SELL signal (default 0.6)
    """

    def __init__(self, atr_window: int = 14, buy_threshold: float = 0.6, sell_threshold: float = 0.6):
        self.atr_window = atr_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

        if MARKET_STRUCTURE_AVAILABLE:
            self._local_extreme = LocalExtreme()
            self._atr_dc = ATRDirectionalChange(atr_window=self.atr_window)

    def get_signal(self, ohlcv_df: pd.DataFrame) -> dict:
        """
        Generate a trading signal from OHLCV data.

        Args:
            ohlcv_df: DataFrame with columns [timestamp, open, high, low, close, volume]
                      indexed or sorted by time ascending.

        Returns:
            dict with keys:
              - action: "BUY" | "SELL" | "HOLD"
              - confidence: float 0.0-1.0
              - metadata: dict with intermediate signal values
        """
        if ohlcv_df is None or len(ohlcv_df) < max(self.atr_window * 2, 20):
            return {"action": "HOLD", "confidence": 0.0, "metadata": {"reason": "insufficient_data"}}

        if not MARKET_STRUCTURE_AVAILABLE:
            return self._stub_signal(ohlcv_df)

        try:
            return self._compute_signal(ohlcv_df)
        except Exception as e:
            logger.error(f"Signal computation error: {e}", exc_info=True)
            return {"action": "HOLD", "confidence": 0.0, "metadata": {"error": str(e)}}

    def _compute_signal(self, ohlcv_df: pd.DataFrame) -> dict:
        """
        Compute signal using market-structure library.

        TODO: Verify this implementation against the actual
        neurotrader888/market-structure API at:
        https://github.com/neurotrader888/market-structure
        The .fit() interface and return types are assumed based on library naming
        conventions and may require adjustment.
        """
        # Detect local extrema (swing highs and lows)
        extrema = self._local_extreme.fit(ohlcv_df)

        # Detect ATR-based directional change
        direction = self._atr_dc.fit(ohlcv_df)

        # Derive action from directional change
        # direction > 0 = bullish directional change -> BUY candidate
        # direction < 0 = bearish directional change -> SELL candidate
        latest_direction = direction.iloc[-1] if hasattr(direction, 'iloc') else direction

        if latest_direction > 0:
            action = "BUY"
            confidence = min(abs(float(latest_direction)), 1.0)
        elif latest_direction < 0:
            action = "SELL"
            confidence = min(abs(float(latest_direction)), 1.0)
        else:
            action = "HOLD"
            confidence = 0.0

        # Apply thresholds
        if action == "BUY" and confidence < self.buy_threshold:
            action = "HOLD"
        elif action == "SELL" and confidence < self.sell_threshold:
            action = "HOLD"

        return {
            "action": action,
            "confidence": confidence,
            "metadata": {
                "extrema_count": int(extrema.sum()) if hasattr(extrema, 'sum') else 0,
                "latest_direction": float(latest_direction),
                "atr_window": self.atr_window,
            }
        }

    def _stub_signal(self, ohlcv_df: pd.DataFrame) -> dict:
        """Fallback stub when market-structure is not installed."""
        close = ohlcv_df['close'].values
        if len(close) < 2:
            return {"action": "HOLD", "confidence": 0.0, "metadata": {"reason": "stub_mode"}}

        momentum = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        if momentum > 0.01:
            return {
                "action": "BUY",
                "confidence": min(momentum * 10, 1.0),
                "metadata": {"reason": "stub_momentum", "momentum": momentum},
            }
        elif momentum < -0.01:
            return {
                "action": "SELL",
                "confidence": min(abs(momentum) * 10, 1.0),
                "metadata": {"reason": "stub_momentum", "momentum": momentum},
            }
        return {"action": "HOLD", "confidence": 0.0, "metadata": {"reason": "stub_momentum", "momentum": momentum}}


def create_signal_layer(instrument: str) -> StrategySignalLayer:
    """Factory: create a StrategySignalLayer configured for a specific instrument."""
    from .config_loader import get_strategy_config
    config = get_strategy_config(instrument)
    return StrategySignalLayer(
        atr_window=config.get('atr_window', 14),
        buy_threshold=config.get('buy_threshold', 0.6),
        sell_threshold=config.get('sell_threshold', 0.6),
    )
