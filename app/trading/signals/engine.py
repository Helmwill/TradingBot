"""
Signal engine using pandas-ta indicators.

Default strategy: RSI(14) + MACD crossover.
- BUY:  RSI < rsi_oversold  AND MACD histogram crosses from negative to positive
- SELL: RSI > rsi_overbought AND MACD histogram crosses from positive to negative
- HOLD: everything else
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    logger.warning("pandas-ta not installed. SignalEngine will use stub momentum fallback.")
    PANDAS_TA_AVAILABLE = False


class SignalEngine:
    """
    Evaluates BUY/SELL/HOLD signals from OHLCV data using pandas-ta.

    Args:
        rsi_period:     RSI calculation period (default 14)
        rsi_oversold:   RSI threshold for BUY consideration (default 30)
        rsi_overbought: RSI threshold for SELL consideration (default 70)
        macd_fast:      MACD fast EMA period (default 12)
        macd_slow:      MACD slow EMA period (default 26)
        macd_signal:    MACD signal EMA period (default 9)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self._min_bars = max(rsi_period * 2, macd_slow + macd_signal + 10)

    def evaluate(self, df: pd.DataFrame) -> dict:
        """
        Evaluate a trading signal from OHLCV data.

        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, volume],
                sorted ascending by time.

        Returns:
            dict with keys:
              - action:     "BUY" | "SELL" | "HOLD"
              - confidence: float 0.0–1.0
              - indicators: dict of intermediate values
        """
        if df is None or len(df) < self._min_bars:
            return {'action': 'HOLD', 'confidence': 0.0, 'indicators': {'reason': 'insufficient_data'}}

        if not PANDAS_TA_AVAILABLE:
            return self._stub_evaluate(df)

        try:
            return self._compute(df)
        except Exception as e:
            logger.error(f"SignalEngine compute error: {e}", exc_info=True)
            return {'action': 'HOLD', 'confidence': 0.0, 'indicators': {'error': str(e)}}

    def _compute(self, df: pd.DataFrame) -> dict:
        close = df['close'].astype(float).reset_index(drop=True)

        rsi = ta.rsi(close, length=self.rsi_period)
        macd_df = ta.macd(close, fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)

        rsi_now = float(rsi.iloc[-1])
        hist_col = f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        hist_now = float(macd_df[hist_col].iloc[-1])
        hist_prev = float(macd_df[hist_col].iloc[-2])

        indicators = {
            'rsi': round(rsi_now, 2),
            'macd_histogram': round(hist_now, 4),
            'macd_histogram_prev': round(hist_prev, 4),
        }

        macd_crossed_up = hist_prev < 0 and hist_now >= 0
        macd_crossed_down = hist_prev > 0 and hist_now <= 0

        if rsi_now < self.rsi_oversold and macd_crossed_up:
            confidence = min((self.rsi_oversold - rsi_now) / self.rsi_oversold, 1.0)
            return {'action': 'BUY', 'confidence': round(confidence, 3), 'indicators': indicators}

        if rsi_now > self.rsi_overbought and macd_crossed_down:
            confidence = min((rsi_now - self.rsi_overbought) / (100.0 - self.rsi_overbought), 1.0)
            return {'action': 'SELL', 'confidence': round(confidence, 3), 'indicators': indicators}

        return {'action': 'HOLD', 'confidence': 0.0, 'indicators': indicators}

    def _stub_evaluate(self, df: pd.DataFrame) -> dict:
        """Momentum fallback when pandas-ta is not installed."""
        close = df['close'].values.astype(float)
        momentum = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0.0
        if momentum > 0.01:
            return {'action': 'BUY', 'confidence': min(momentum * 10, 1.0),
                    'indicators': {'stub': True, 'momentum': round(momentum, 4)}}
        if momentum < -0.01:
            return {'action': 'SELL', 'confidence': min(abs(momentum) * 10, 1.0),
                    'indicators': {'stub': True, 'momentum': round(momentum, 4)}}
        return {'action': 'HOLD', 'confidence': 0.0,
                'indicators': {'stub': True, 'momentum': round(momentum, 4)}}


def create_signal_engine(ticker: str) -> SignalEngine:
    """Factory: create a SignalEngine configured for a specific ticker."""
    from trading.signals.config import get_ticker_config
    cfg = get_ticker_config(ticker)
    return SignalEngine(
        rsi_period=cfg.get('rsi_period', 14),
        rsi_oversold=cfg.get('rsi_oversold', 30.0),
        rsi_overbought=cfg.get('rsi_overbought', 70.0),
        macd_fast=cfg.get('macd_fast', 12),
        macd_slow=cfg.get('macd_slow', 26),
        macd_signal=cfg.get('macd_signal', 9),
    )
