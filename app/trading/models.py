from django.db import models

try:
    from timescale.db.models.models import TimescaleModel
    TIMESCALE_AVAILABLE = True
except ImportError:
    TIMESCALE_AVAILABLE = False
    TimescaleModel = models.Model


class HistoricalData(models.Model):
    product_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    low = models.FloatField()
    high = models.FloatField()
    open = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    def __str__(self):
        return f"{self.product_id} at {self.timestamp}"


_TradeBase = TimescaleModel if TIMESCALE_AVAILABLE else models.Model


class Trade(_TradeBase):
    """Records each executed trade order."""
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    instrument = models.CharField(max_length=50)
    action = models.CharField(max_length=4)  # BUY, SELL
    price = models.DecimalField(max_digits=20, decimal_places=8)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    signal_meta = models.JSONField(default=dict)
    order_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} {self.instrument} @ {self.price} ({self.timestamp})"


class OHLCVBar(_TradeBase):
    """OHLCV price bars for backtesting and MCPT validation."""
    timestamp = models.DateTimeField(db_index=True)
    instrument = models.CharField(max_length=50)
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        ordering = ['-timestamp']
        unique_together = [('instrument', 'timestamp')]
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.instrument} OHLCV @ {self.timestamp}"
