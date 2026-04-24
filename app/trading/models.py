from django.db import models

try:
    from timescale.db.models.models import TimescaleModel
    TIMESCALE_AVAILABLE = True
except ImportError:
    TIMESCALE_AVAILABLE = False
    TimescaleModel = models.Model


_TradeBase = TimescaleModel if TIMESCALE_AVAILABLE else models.Model


class Trade(_TradeBase):
    """Records each executed trade order."""
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ticker = models.CharField(max_length=20)
    action = models.CharField(max_length=4)  # BUY, SELL
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    fill_price = models.DecimalField(max_digits=20, decimal_places=8)
    order_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='Filled')
    signal_meta = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ticker', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} {self.ticker} @ {self.fill_price} ({self.timestamp})"


class OHLCVBar(_TradeBase):
    """OHLCV price bars persisted from IBKR market data feed."""
    timestamp = models.DateTimeField(db_index=True)
    ticker = models.CharField(max_length=20)
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        ordering = ['-timestamp']
        unique_together = [('ticker', 'timestamp')]
        indexes = [
            models.Index(fields=['ticker', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.ticker} OHLCV @ {self.timestamp}"


class TradingError(models.Model):
    """Dead-letter log for failed Celery task errors."""
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ticker = models.CharField(max_length=20)
    message = models.TextField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Error {self.ticker} @ {self.timestamp}: {self.message[:60]}"
