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
    
    def process_statistical_arbitrage_orders(self, state: TradingState, product: str, fair_value: float) -> Order:
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
            print("BUY", str(-best_ask_volume) + "x", best_ask)            
            return Order(product, best_ask, -best_ask_volume)

        # Sell the product if its fair value is higher than the related product's fair value
        elif fair_value > related_fair_value and len(order_depth.buy_orders) > 0:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_volume = order_depth.buy_orders[best_bid]
            print("SELL", str(best_bid_volume) + "x", best_bid)
            return Order(product, best_bid, -best_bid_volume)
            


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}
        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.listings.keys():
            order_depth: OrderDepth = state.order_depths[product]

            orders: list[Order] = []

            if product in state.market_trades:
                self.trade_prices[product].extend(state.market_trades[product])

            fair_value = self.calculate_fair_value(product)

            if fair_value is None:
                continue

            # Process orders for PEARLS and BANANAS
            if product in {"PEARLS", "BANANAS"}:
                if len(order_depth.sell_orders) > 0:

                # Sort all the available sell orders by their price,
                # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = order_depth.sell_orders[best_ask]

                # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < fair_value:

                    # In case the lowest ask is lower than our fair value,
                    # This presents an opportunity for us to buy cheaply
                    # The code below therefore sends a BUY order at the price level of the ask,
                    # with the same quantity
                    # We expect this order to trade with the sell order
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(
                            Order(product, best_ask, -best_ask_volume))

            # The below code block is similar to the one above,
            # the difference is that it find the highest bid (buy order)
            # If the price of the order is higher than the fair value
            # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = order_depth.buy_orders[best_bid]
                    if best_bid > fair_value:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(
                            Order(product, best_bid, -best_bid_volume))

            # Process orders for COCONUTS and PINA_COLADAS using statistical arbitrage
            if product in {"COCONUTS", "PINA_COLADAS"}:
                orders.append(
                    self.process_statistical_arbitrage_orders(state, product, fair_value))
            
            # Add all the above the orders to the result dict
            result[product] = orders

        return result
