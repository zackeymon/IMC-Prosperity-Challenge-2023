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

        logger.flush(state, result)
        return result

    def trade_pearls(self, order_depth: OrderDepth) -> List[Order]:
        product = "PEARLS"
        fair_value = 10000
        orders = []

        if order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders.keys())
            best_ask_volume = order_depth.sell_orders[best_ask]
            if best_ask < fair_value:
                print("BUY", product,
                      str(-best_ask_volume) + "x", best_ask)
                orders.append(
                    Order(product, best_ask, -best_ask_volume))
        if order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_volume = order_depth.buy_orders[best_bid]
            if best_bid > fair_value:
                print("SELL", product, str(
                    best_bid_volume) + "x", best_bid)
                orders.append(
                    Order(product, best_bid, -best_bid_volume))

        return orders
