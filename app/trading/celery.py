import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utils.settings')

app = Celery('trading')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Register one periodic trading cycle per configured ticker."""
    from trading.signals.config import get_tickers, get_ticker_config
    for ticker in get_tickers():
        config = get_ticker_config(ticker)
        interval = config.get('poll_interval_seconds', 300)
        sender.add_periodic_task(
            interval,
            run_trading_cycle.s(ticker),
            name=f'trading-cycle-{ticker}',
        )


from trading.tasks import run_trading_cycle  # noqa: E402
