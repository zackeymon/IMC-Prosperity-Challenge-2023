from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
from collections import defaultdict

class Trader:
    def __init__(self) -> None:
        self.trade_prices = defaultdict(list)

    def calculate_fair_value(self, product) -> float:
        MIN_SAMPLE_SIZE = 5
        MAX_SAMPLE_SIZE = 100

        # Remove earlier data points
        self.trade_prices[product] = self.trade_prices[product][-MAX_SAMPLE_SIZE:]
        prev_trades = self.trade_prices[product]
        if len(prev_trades) < MIN_SAMPLE_SIZE:
            return None

        # finding the weighted average
        total_volume, total_quantity = 0, 0
        for trade in prev_trades:
            total_volume += trade.price * trade.quantity
            total_quantity += trade.quantity

        return total_volume / total_quantity

    # ... (rest of the Trader class remains unchanged) ...

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}

        for product in state.listings.keys():
            order_depth: OrderDepth = state.order_depths[product]
            if product in state.market_trades:
                self.trade_prices[product].extend(state.market_trades[product])

            fair_value = self.calculate_fair_value(product)

            if fair_value is None:
                continue

            # Process orders for PEARLS and BANANAS
            if product in {"PEARLS", "BANANAS"}:
                orders = self.process_orders(fair_value, order_depth)
                result[product] = orders
            # Process orders for COCONUTS and PINA_COLADAS using statistical arbitrage
            elif product in {"COCONUTS", "PINA_COLADAS"}:
                orders = self.process_statistical_arbitrage_orders(state, product, fair_value)
                result[product] = orders

        return result

    def process_statistical_arbitrage_orders(self, state: TradingState, product: str, fair_value: float) -> List[Order]:
        orders = []

        # Get the related product
        related_product = "COCONUTS" if product == "PINA_COLADAS" else "PINA_COLADAS"

        # Calculate the fair value of the related product
        related_fair_value = self.calculate_fair_value(related_product)

        if related_fair_value is None:
            return orders

        # Compare the fair values of the two products and implement statistical arbitrage
        order_depth: OrderDepth = state.order_depths[product]
        related_order_depth: OrderDepth = state.order_depths[related_product]

        # Buy the product if its fair value is lower than the related product's fair value
        if fair_value < related_fair_value and len(order_depth.sell_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
            best_ask_volume = order_depth.sell_orders[best_ask]
            orders.append(Order(product, best_ask, -best_ask_volume))

        # Sell the product if its fair value is higher than the related product's fair value
        elif fair_value > related_fair_value and len(order_depth.buy_orders) > 0:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_volume = order_depth.buy_orders[best_bid]
            orders.append(Order(product, best_bid, -best_bid_volume))

        return orders
