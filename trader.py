from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
from collections import defaultdict


'''
# Tutorial round

In the tutorial round there are two tradable goods: PEARLS and BANANAS. While the value of the PEARLS has been stable throughout the history of the archipelago, the value of BANANAS has been going up and down over time. All algorithms uploaded in the tutorial round will be processed and generate results instantly, so you can experiment with different programs and strategies.

Position limits for the newly introduced products:

- PEARLS: 20
- BANANAS: 20
'''


class Trader:

    def __init__(self) -> None:
        self.trade_prices = defaultdict(list)

    def calculate_fair_value(self, product) -> float:
        MIN_SAMPLE_SIZE = 10
        MAX_SAMPLE_SIZE = 300
        prev_trades = self.trade_prices[product]
        if len(prev_trades) < MIN_SAMPLE_SIZE:
            return None

        # finding the weighted average
        total_volume, total_quantity = 0, 0
        for trade in prev_trades[-MAX_SAMPLE_SIZE:]:
            total_volume += trade.price * trade.quantity
            total_quantity += trade.quantity

        return total_volume / total_quantity

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        BUY_DISCOUNT = 0.95
        SELL_PREMIUM = 1.05

        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
            order_depth: OrderDepth = state.order_depths[product]

            # Initialize the list of Orders to be sent as an empty list
            orders: list[Order] = []

            # Define a fair value.
            self.trade_prices[product].extend(state.market_trades[product])
            fair_value = self.calculate_fair_value(product)
            if fair_value is None:
                continue
            print(product, fair_value)

            # If statement checks if there are any SELL orders in the PEARLS market
            if len(order_depth.sell_orders) > 0:

                # Sort all the available sell orders by their price,
                # and select only the sell order with the lowest price
                best_ask = min(order_depth.sell_orders.keys())
                best_ask_volume = order_depth.sell_orders[best_ask]

                # Check if the lowest ask (sell order) is lower than the above defined fair value
                if best_ask < fair_value * BUY_DISCOUNT:

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
                if best_bid > fair_value * SELL_PREMIUM:
                    print("SELL", str(best_bid_volume) + "x", best_bid)
                    orders.append(
                        Order(product, best_bid, -best_bid_volume))

            # Add all the above the orders to the result dict
            result[product] = orders

        # Return the dict of orders
        return result
