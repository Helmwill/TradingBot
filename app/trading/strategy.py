class RecursiveAverageStrategy:
    def __init__(self, momentum_window=5, buy_threshold=1.02, sell_threshold=0.98):
        self.prices = []
        self.recursive_avg = None
        self.momentum_window = momentum_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def add_price(self, price):
        self.prices.append(price)
        self.update_recursive_avg(price)

    def update_recursive_avg(self, price):
        if self.recursive_avg is None:
            self.recursive_avg = price
        else:
            n = len(self.prices)
            self.recursive_avg = (price + (n - 1) * self.recursive_avg) / n

    def calculate_momentum(self):
        if len(self.prices) < self.momentum_window:
            return None
        return self.prices[-1] / self.prices[-self.momentum_window] - 1

    def get_signal(self):
        if len(self.prices) < self.momentum_window:
            return "hold"
        
        current_price = self.prices[-1]
        momentum = self.calculate_momentum()

        if momentum is None:
            return "hold"
        
        if current_price > self.recursive_avg * self.buy_threshold and momentum > 0:
            return "buy"
        elif current_price < self.recursive_avg * self.sell_threshold and momentum < 0:
            return "sell"
        else:
            return "hold"

