# tests/test_strategy.py

import unittest
from trading.strategy import RecursiveAverageStrategy

class TestRecursiveAverageStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = RecursiveAverageStrategy()

    def test_initial_state(self):
        self.assertIsNone(self.strategy.recursive_avg)
        self.assertEqual(self.strategy.get_signal(), "hold")

    def test_add_price(self):
        self.strategy.add_price(100)
        self.assertEqual(self.strategy.recursive_avg, 100)
        self.assertEqual(self.strategy.get_signal(), "hold")

    def test_recursive_average_calculation(self):
        prices = [100, 105, 110, 95, 90]
        for price in prices:
            self.strategy.add_price(price)

        # Manually calculate the recursive average
        n = len(prices)
        expected_avg = sum(prices) / n
        self.assertAlmostEqual(self.strategy.recursive_avg, expected_avg, places=2)

    def test_buy_signal(self):
        self.strategy.add_price(100)
        self.strategy.add_price(110)
        self.assertEqual(self.strategy.get_signal(), "buy")

    def test_sell_signal(self):
        self.strategy.add_price(100)
        self.strategy.add_price(90)
        self.assertEqual(self.strategy.get_signal(), "sell")

if __name__ == '__main__':
    unittest.main()

