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
            asks = sorted(order_depth.sell_orders.keys())
            for ask in asks:
                if ask < fair_value:
                    volume = order_depth.sell_orders[ask]
                    orders.append(Order(product, ask, -volume))
        if order_depth.buy_orders:
            bids = sorted(order_depth.buy_orders.keys(), reverse=True)
            for bid in bids:
                if bid > fair_value:
                    volume = order_depth.buy_orders[bid]
                    orders.append(Order(product, bid, -volume))
        return orders
