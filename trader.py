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
        result["PEARLS"] = self.trade_pearls(state)
        result["BERRIES"] = self.trade_berries(state)
        result["COCONUTS"] = self.trade_coconut_pinacoladas(state, "COCONUTS")
        result["PINA_COLADAS"] = self.trade_coconut_pinacoladas(state, "PINA_COLADAS")

        self.logger.flush(state, result)
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
    
    def trade_coconut_pinacoladas(self, state: TradingState, product: str) -> List[Order]:
        orders = []

        # Get the related product
        related_product = "COCONUTS" if product == "PINA_COLADAS" else "PINA_COLADAS"

        # get the order depth and position of the products
        c_order_depth: OrderDepth = state.order_depths["COCONUTS"]
        pc_order_depth: OrderDepth = state.order_depths["PINA_COLADAS"]
        
        # Get the best ask and bid prices and volumes for coconut
        c_best_ask = min(c_order_depth.sell_orders.keys())
        c_best_ask_volume = c_order_depth.sell_orders[c_best_ask]
        c_best_bid = max(c_order_depth.buy_orders.keys())
        c_best_bid_volume = c_order_depth.buy_orders[c_best_bid]
        # Get the best ask and bid prices and volumes for pina colada
        pc_best_ask = min(pc_order_depth.sell_orders.keys())
        pc_best_ask_volume = pc_order_depth.sell_orders[pc_best_ask]
        pc_best_bid = max(pc_order_depth.buy_orders.keys())
        pc_best_bid_volume = pc_order_depth.buy_orders[pc_best_bid]

        if pc_best_bid / c_best_ask > 1.876:
            orders.append(Order(product, c_best_ask, -c_best_ask_volume)) if product == "COCONUTS" \
                else orders.append(Order(product, pc_best_bid, -pc_best_bid_volume))
        elif pc_best_ask / c_best_bid < 1.874:
            orders.append(Order(product, c_best_bid, -c_best_bid_volume)) if product == "COCONUTS" \
                else orders.append(Order(product, pc_best_ask, -pc_best_ask_volume))

        return orders
