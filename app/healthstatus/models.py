from django.db import models

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
