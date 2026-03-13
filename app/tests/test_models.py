import pytest
from decimal import Decimal
from django.utils import timezone
from trading.models import Trade, OHLCVBar


@pytest.mark.django_db
def test_create_trade():
    trade = Trade.objects.create(
        instrument='AAPL',
        action='BUY',
        price=Decimal('175.50'),
        amount=Decimal('1.0'),
        signal_meta={'confidence': 0.8},
        order_id='order-001',
    )
    assert trade.pk is not None
    assert trade.instrument == 'AAPL'
    assert trade.action == 'BUY'


@pytest.mark.django_db
def test_create_ohlcvbar():
    bar = OHLCVBar.objects.create(
        timestamp=timezone.now(),
        instrument='AAPL',
        open=Decimal('174.00'),
        high=Decimal('176.00'),
        low=Decimal('173.50'),
        close=Decimal('175.50'),
        volume=Decimal('1000000'),
    )
    assert bar.pk is not None
    assert bar.high == Decimal('176.00')


@pytest.mark.django_db
def test_trade_signal_meta_stores_dict():
    meta = {'action': 'BUY', 'confidence': 0.82, 'atr_window': 14}
    trade = Trade.objects.create(
        instrument='UK100',
        action='BUY',
        price=Decimal('7500'),
        amount=Decimal('0.5'),
        signal_meta=meta,
    )
    reloaded = Trade.objects.get(pk=trade.pk)
    assert reloaded.signal_meta == meta


@pytest.mark.django_db
def test_trades_ordered_newest_first():
    Trade.objects.create(instrument='AAPL', action='BUY', price=Decimal('100'), amount=Decimal('1'), signal_meta={})
    Trade.objects.create(instrument='TSLA', action='SELL', price=Decimal('200'), amount=Decimal('1'), signal_meta={})
    trades = list(Trade.objects.all())
    assert trades[0].timestamp >= trades[1].timestamp
