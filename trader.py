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
        self._buffer_best_asks_bid_orders(state)
        result["PEARLS"] = self.trade_pearls(state)
        result["BERRIES"] = self.trade_berries(state)
        result["COCONUTS"] = self.trade_coconut_pinacoladas(state, "COCONUTS")
        result["PINA_COLADAS"] = self.trade_coconut_pinacoladas(
            state, "PINA_COLADAS")
        result["BAGUETTE"], result["DIP"], result["UKULELE"], result["PICNIC_BASKET"] = self.trade_basket(
            state)

        self.logger.flush(state, result)
        return result

    def _buffer_best_asks_bid_orders(self, state: TradingState):
        limits = {
            'PEARLS': 20,
            'BANANAS': 20,
            'COCONUTS': 600,
            'PINA_COLADAS': 300,
            'DIVING_GEAR': 50,
            'BERRIES': 250,
            'BAGUETTE': 150,
            'DIP': 300,
            'UKULELE': 70,
            'PICNIC_BASKET': 70,
        }
        self.best_ask_orders: Dict[Symbol, Order] = {}
        self.best_bid_orders: Dict[Symbol, Order] = {}
        for product, order_depth in state.order_depths.items():
            if product == "DOLPHIN_SIGHTINGS":
                continue
            pos = state.position.get(product, 0)
            limit = limits[product]
            if order_depth.sell_orders:
                best_ask = min(order_depth.sell_orders.keys())
                volume = max(order_depth.sell_orders[best_ask], pos-limit)
                self.best_ask_orders[product] = Order(
                    product, best_ask, -volume)
            if order_depth.buy_orders:
                best_bid = max(order_depth.buy_orders.keys())
                volume = min(order_depth.buy_orders[best_bid], limit+pos)
                self.best_bid_orders[product] = Order(
                    product, best_bid, -volume)

    def trade_pearls(self, state: TradingState) -> List[Order]:
        product = "PEARLS"
        fair_value = 10000

        if self.best_ask_orders[product].price < fair_value:
            return [self.best_ask_orders[product]]
        if self.best_bid_orders[product].price > fair_value:
            return [self.best_bid_orders[product]]
        return []

    def trade_berries(self, state: TradingState) -> List[Order]:
        product = "BERRIES"
        timestamp = state.timestamp

        buy_ends_at = 300 * 1000
        sell_starts_at = 500 * 1000

        if timestamp < buy_ends_at:
            return [self.best_ask_orders[product]]
        if timestamp > sell_starts_at:
            return [self.best_bid_orders[product]]
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

    def trade_basket(self, state: TradingState) -> List[List[Order]]:
        components = {"BAGUETTE": 2, "DIP": 4, "UKULELE": 1}
        combined_ask = 0
        combined_bid = 0
        for product, quantity in components.items():
            if product not in self.best_ask_orders:
                combined_ask = 99999999
            else:
                combined_ask += self.best_ask_orders[product].price * quantity

            if product not in self.best_bid_orders:
                combined_bid = -99999999
            else:
                combined_bid += self.best_bid_orders[product].price * quantity

        if combined_ask < self.best_bid_orders["PICNIC_BASKET"].price:
            return [self.best_ask_orders["BAGUETTE"]], [self.best_ask_orders["DIP"]], [self.best_ask_orders["UKULELE"]], [self.best_bid_orders["PICNIC_BASKET"]]
        if combined_bid > self.best_ask_orders["PICNIC_BASKET"].price:
            return [self.best_bid_orders["BAGUETTE"]], [self.best_bid_orders["DIP"]], [self.best_bid_orders["UKULELE"]], [self.best_ask_orders["PICNIC_BASKET"]]

        return [], [], [], []
