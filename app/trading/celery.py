import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utils.settings')

app = Celery('trading')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Register one periodic trading cycle per configured instrument."""
    from trading.strategy.config_loader import get_instruments, get_strategy_config
    for instrument in get_instruments():
        config = get_strategy_config(instrument)
        interval = config.get('poll_interval_seconds', 60)
        sender.add_periodic_task(
            interval,
            run_trading_cycle.s(instrument),
            name=f'trading-cycle-{instrument}',
        )


from trading.tasks import run_trading_cycle  # noqa: E402 — imported after app is created
