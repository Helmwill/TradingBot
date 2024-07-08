from django.core.management.base import BaseCommand
from trading.views import buy_request, sell_request, get_current_price
from trading.strategy import RecursiveAverageStrategy
import time

class Command(BaseCommand):
    help = 'Runs the trading bot'

    def handle(self, *args, **kwargs):
        strategy = RecursiveAverageStrategy(momentum_window=5, buy_threshold=1.02, sell_threshold=0.98)

        while True:
            # Replace with your actual logic to fetch the current price and product ID
            product_id = 'BTC-USD'
            current_price = get_current_price(product_id)

            strategy.add_price(current_price)
            signal = strategy.get_signal()

            if signal == "buy":
                buy_request(product_id, amount='your_amount')
            elif signal == "sell":
                sell_request(product_id, amount='your_amount')

            # Log the action
            self.stdout.write(self.style.SUCCESS(f'Processed {signal} signal for {product_id} at price {current_price}'))

            # Sleep for a while before the next iteration (e.g., 1 minute)
            time.sleep(60)
