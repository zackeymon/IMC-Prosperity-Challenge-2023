import json
from typing import Dict, List, Any
from datamodel import *
from collections import defaultdict

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()

class Trader:
    def __init__(self) -> None:
        self.trade_prices = defaultdict(list)   


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}
        result["PEARLS"] = self.trade_pearls(state.order_depths["PEARLS"])
        result["BERRIES"] = self.trade_berries(state)

        for product in state.listings.keys():
            if product == "DOLPHIN_SIGHTINGS":
                continue
            else: 
                if product == "COCONUTS":
                    result["COCONUTS"] = self.trade_coco_pina(state, product)
                if product == "PINA_COLADAS":
                    result["PINA_COLADAS"] = self.trade_coco_pina(state, product)
        logger.flush(state, result)
        return result
    

    def trade_pearls(self, state: TradingState) -> List[Order]:
        product = "PEARLS"
        limit = 20
        fair_value = 10000
        order_depth, position = state.order_depths.get(
            product, None), state.position.get(product, 0)
        if not order_depth:
            return []
        orders = []

        if order_depth.sell_orders and position < limit:
            asks = sorted(order_depth.sell_orders.keys())
            for ask in asks:
                if ask < fair_value:
                    volume = order_depth.sell_orders[ask]
                    orders.append(Order(product, ask, -volume))
        if order_depth.buy_orders and position > -limit:
            bids = sorted(order_depth.buy_orders.keys(), reverse=True)
            for bid in bids:
                if bid > fair_value:
                    volume = order_depth.buy_orders[bid]
                    orders.append(Order(product, bid, -volume))
        return orders

    def trade_berries(self, state: TradingState) -> List[Order]:
        product = "BERRIES"
        limit = 250
        order_depth, position, timestamp = state.order_depths.get(
            product, None), state.position.get(product, 0), state.timestamp
        if not order_depth:
            return []

        # # backtesting
        # buy_ends_at = 30 * 1000
        # sell_starts_at = 50 * 1000

        # production
        buy_ends_at = 300 * 1000
        sell_starts_at = 500 * 1000

        if timestamp < buy_ends_at and order_depth.sell_orders and position < limit:
            best_ask = min(order_depth.sell_orders.keys())
            volume = order_depth.sell_orders[best_ask]
            return [Order(product, best_ask, -volume)]
        if timestamp > sell_starts_at and order_depth.buy_orders and position > -limit:
            best_bid = max(order_depth.buy_orders.keys())
            volume = order_depth.buy_orders[best_bid]
            return [Order(product, best_bid, -volume)]
        return []
    

    def trade_coco_pina(self, state: TradingState, product: str) -> List[Order]:
        orders = []
        # Get the related product
        related_product = "COCONUTS" if product == "PINA_COLADAS" else "PINA_COLADAS"

        # Compare the normalized fair values and implement statistical arbitrage
        order_depth: OrderDepth = state.order_depths[product]
        related_order_depth: OrderDepth = state.order_depths[related_product]
        best_ask = min(order_depth.sell_orders.keys())
        best_ask_volume = order_depth.sell_orders[best_ask]
        best_bid = max(order_depth.buy_orders.keys())
        best_bid_volume = order_depth.buy_orders[best_bid]
        related_best_ask = min(related_order_depth.sell_orders.keys())
        related_best_bid = max(related_order_depth.buy_orders.keys())
        mid_price = (best_ask + best_bid) / 2
        related_mid_price = (related_best_ask + related_best_bid) / 2

        # Normalize the fair values based on the base prices
        base_prices = {"COCONUTS": 8000, "PINA_COLADAS": 15000}
        normalized_fair_value = (base_prices[product]-mid_price) / base_prices[product]
        normalized_related_fair_value = (base_prices[related_product] - related_mid_price) / base_prices[related_product]
        
        # make sure the algo doesn't trade too much
        if abs(normalized_fair_value - normalized_related_fair_value) < 0.16 and (best_ask_volume > 20 or best_bid_volume > 20):
            best_ask_volume = 20
            best_bid_volume = 20
        # Buy the product if its normalized fair value is lower than the related product's normalized fair value
        if normalized_fair_value < normalized_related_fair_value and len(order_depth.sell_orders) > 0:
            orders.append(Order(product, best_ask, -best_ask_volume))

        # Sell the product if its normalized fair value is higher than the related product's normalized fair value
        elif normalized_fair_value > normalized_related_fair_value and len(order_depth.buy_orders) > 0:
            orders.append(Order(product, best_bid, -best_bid_volume))
        elif normalized_fair_value == normalized_related_fair_value and len(order_depth.buy_orders):
            orders.append(Order(product, best_bid, -best_bid_volume))

        return orders


# def process_diving_gear_orders(self, state: TradingState, product: str, fair_value: float, dolphin_sightings: int) -> Order:

    #     order_depth: OrderDepth = state.order_depths[product]

    #     # You can adjust the threshold according to the importance of dolphin sightings
    #     sighting_threshold = 10

    #     adjusted_fair_value = fair_value * (1 + dolphin_sightings / sighting_threshold)

    #     # Buy the product if the adjusted fair value is higher than the best ask
    #     if len(order_depth.sell_orders) > 0:
    #         best_ask = min(order_depth.sell_orders.keys())
    #         best_ask_volume = order_depth.sell_orders[best_ask]

    #         if best_ask < adjusted_fair_value:
    #             print("BUY", str(-best_ask_volume) + "x", best_ask)
    #             return Order(product, best_ask, -best_ask_volume)

    #     # Sell the product if the adjusted fair value is lower than the best bid
    #     if len(order_depth.buy_orders) > 0:
    #         best_bid = max(order_depth.buy_orders.keys())
    #         best_bid_volume = order_depth.buy_orders[best_bid]

    #         if best_bid > adjusted_fair_value:
    #             print("SELL", str(best_bid_volume) + "x", best_bid)
    #             return Order(product, best_bid, -best_bid_volume)
            