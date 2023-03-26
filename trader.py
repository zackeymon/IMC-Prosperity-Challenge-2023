import json
from typing import Dict, List, Any
from datamodel import *
from collections import defaultdict


class Logger:
    # Set this to true, if u want to create
    # local logs
    local: bool
    # this is used as a buffer for logs
    # instead of stdout
    local_logs: dict[int, str] = {}

    def __init__(self, local=False) -> None:
        self.logs = ""
        self.local = local

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        output = json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True)
        if self.local:
            self.local_logs[state.timestamp] = output
        print(output)

        self.logs = ""


class Trader:

    logger = Logger(local=True)

    def __init__(self) -> None:
        self.trade_prices = defaultdict(list)

    def run(self, state: TradingState) -> Dict[str, List[Order]]:

        result = {}
        result["PEARLS"] = self.trade_pearls(state.order_depths["PEARLS"])
        result["BERRIES"] = self.trade_berries(
            state.order_depths["BERRIES"], state.timestamp)

        self.logger.flush(state, result)
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

    def trade_berries(self, order_depth: OrderDepth, timestamp: Time) -> List[Order]:
        product = "BERRIES"

        # # backtesting
        # buy_ends_at = 30 * 1000
        # sell_starts_at = 50 * 1000

        # production
        buy_ends_at = 300 * 1000
        sell_starts_at = 500 * 1000

        if timestamp < buy_ends_at and order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders.keys())
            volume = order_depth.sell_orders[best_ask]
            return [Order(product, best_ask, -volume)]
        if timestamp > sell_starts_at and order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders.keys())
            volume = order_depth.buy_orders[best_bid]
            return [Order(product, best_bid, -volume)]
        return []
