import pytest
from decimal import Decimal
from django.utils import timezone
from trading.models import Trade, OHLCVBar


@pytest.mark.django_db
def test_create_trade():
    trade = Trade.objects.create(
        ticker='AAPL',
        action='BUY',
        quantity=Decimal('5'),
        fill_price=Decimal('175.50'),
        signal_meta={'confidence': 0.8},
        order_id='order-001',
        status='Filled',
    )
    assert trade.pk is not None
    assert trade.ticker == 'AAPL'
    assert trade.action == 'BUY'
    assert trade.status == 'Filled'


@pytest.mark.django_db
def test_create_ohlcvbar():
    bar = OHLCVBar.objects.create(
        timestamp=timezone.now(),
        ticker='AAPL',
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
    meta = {'action': 'BUY', 'confidence': 0.82, 'indicators': {'rsi': 28.5}}
    trade = Trade.objects.create(
        ticker='TSLA',
        action='BUY',
        quantity=Decimal('2'),
        fill_price=Decimal('250.00'),
        signal_meta=meta,
    )
    reloaded = Trade.objects.get(pk=trade.pk)
    assert reloaded.signal_meta == meta


@pytest.mark.django_db
def test_trades_ordered_newest_first():
    Trade.objects.create(ticker='AAPL', action='BUY', quantity=Decimal('1'),
                         fill_price=Decimal('100'), signal_meta={})
    Trade.objects.create(ticker='TSLA', action='SELL', quantity=Decimal('1'),
                         fill_price=Decimal('200'), signal_meta={})
    trades = list(Trade.objects.all())
    assert trades[0].timestamp >= trades[1].timestamp


@pytest.mark.django_db
def test_ohlcvbar_unique_together_prevents_duplicate():
    from django.db import IntegrityError
    ts = timezone.now()
    OHLCVBar.objects.create(
        timestamp=ts, ticker='MSFT',
        open=380, high=385, low=378, close=382, volume=500000,
    )
    with pytest.raises(IntegrityError):
        OHLCVBar.objects.create(
            timestamp=ts, ticker='MSFT',
            open=381, high=386, low=379, close=383, volume=600000,
        )
