import json
from typing import Dict, List, Any
from datamodel import *
from collections import defaultdict
import numpy as np

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

    def __init__(self) :
        self.trade_prices = defaultdict(list)
        self.logs = ""
        self.pos_limit = {"PEARLS": 20, "BANANAS": 20, "COCONUTS": 600,
                          "PINA_COLADAS": 300, "BERRIES": 250, "DIVING_GEAR": 50}
        self.pos = {"PEARLS": 0, "BANANAS": 0, "COCONUTS": 0,
                    "PINA_COLADAS": 0, "BERRIES": 0, "DIVING_GEAR": 0}
        self.sma = {"PEARLS": [], "BANANAS": [],
                    "BERRIES": [], "DIVING_GEAR": []}
        self.last_timestamp = {"PEARLS": 0, "BANANAS": 0, "COCONUTS": 0,
                               "PINA_COLADAS": 0, "BERRIES": 0, "DIVING_GEAR": 0}
        self.diffs = []
        self.entered = 0
        self.pc_midprices = []
        self.c_midprices = []
        self.dolphin_sightings = []

    def run(self, state: TradingState) -> Dict[str, List[Order]]:

        result = {}
        for product, trades in state.own_trades.items():
            if len(trades) == 0 or trades[0].timestamp == self.last_timestamp[product]:
                continue
            pos_delta = 0
            for trade in trades:
                print(trade.buyer, trade.seller, trade.price,
                      trade.quantity, trade.symbol)
                if trade.buyer == "SUBMISSION":
                    # We bought product
                    pos_delta += trade.quantity
                    # self.profit -= trade.price * trade.quantity
                elif trade.seller == "SUBMISSION":
                    pos_delta -= trade.quantity
                    # self.profit += trade.price * trade.quantity
            self.pos[product] += pos_delta
            self.last_timestamp[product] = trades[0].timestamp
        result["PEARLS"] = self.trade_pearls(state)
        result["BERRIES"] = self.trade_berries(state)
        result["COCONUTS"], result["PINA_COLADAS"] = self.pair_trade(state)

        self.logger.flush(state, result)
        return result
    
    def get_order_book_info(self, order_depth):
        best_ask = min(order_depth.sell_orders.keys()) if len(
            order_depth.sell_orders) != 0 else None
        best_ask_volume = order_depth.sell_orders[best_ask] if best_ask is not None else None
        best_bid = max(order_depth.buy_orders.keys()) if len(
            order_depth.buy_orders) != 0 else None
        best_bid_volume = order_depth.buy_orders[best_bid] if best_bid is not None else None
        avg = (best_bid + best_ask) / \
            2 if best_bid is not None and best_ask is not None else None
        return best_ask, best_ask_volume, best_bid, best_bid_volume, avg

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
    def pair_trade(self, state: TradingState):
        # Pair trading between COCONUTS and PINA_COLADAS
        orders_coconut: list[Order] = []
        orders_pina = []
        order_depth_coconut = state.order_depths["COCONUTS"]
        best_ask_coconut, best_ask_volume_coconut, best_bid_coconut, best_bid_volume_coconut, avg_coconut = self.get_order_book_info(
            order_depth_coconut)
        order_depth_pina = state.order_depths["PINA_COLADAS"]
        best_ask_pina, best_ask_volume_pina, best_bid_pina, best_bid_volume_pina, avg_pina = self.get_order_book_info(
            order_depth_pina)

        # compute normed price difference

        print("entered = ", self.entered)
        if avg_coconut is not None and avg_pina is not None:
            self.c_midprices.append(avg_coconut)
            self.pc_midprices.append(avg_pina)
            x = np.array(self.pc_midprices)
            y = np.array(self.c_midprices)
            A = np.vstack([x, np.ones(len(x))]).T
            m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
            print("hedge ratio = ", m)
            difference = avg_coconut - m * avg_pina
            self.diffs.append(difference)
            mean = np.array(self.diffs).mean()
            std = np.array(self.diffs).std()
            z = (difference - mean) / std
            print(difference, len(self.diffs), mean, std, z)
            if abs(z) < 0.2:
                print("AAAAAAAAAAAAAAAAAAAAAA")
                self.entered = 0
                product = "COCONUTS"
                volume = self.pos["COCONUTS"]
                print("COCONUTS volume = ", volume)
                if volume > 0:
                    # sell all existing positions
                    print("SELL", product, str(-volume) + "x", best_bid_coconut)
                    orders_coconut.append(
                        Order(product, best_bid_coconut, -volume))
                elif volume < 0:
                    # buy all existing positions
                    print("BUY", product, str(-volume) + "x", best_ask_coconut)
                    orders_coconut.append(
                        Order(product, best_ask_coconut, -volume))

                product = "PINA_COLADAS"
                volume = self.pos["PINA_COLADAS"]
                if volume > 0:
                    # sell all existing positions
                    print("SELL", product, str(-volume) + "x", best_bid_pina)
                    orders_pina.append(Order(product, best_bid_pina, -volume))
                elif volume < 0:
                    # buy all existing positions
                    print("BUY", product, str(-volume) + "x", best_ask_pina)
                    orders_pina.append(Order(product, best_ask_pina, -volume))
            elif z > 1:
                print("BBBBBBBBBBBBBBBBBBBBBBBBB")
                # COCONUT overpriced, PINA underpriced
                self.entered += 1
                bid_product = "PINA_COLADAS"
                ask_product = "COCONUTS"
                bid_volume = min(-best_ask_volume_pina,
                                 self.pos_limit[bid_product] - self.pos[bid_product])
                ask_volume = -min(best_bid_volume_coconut,
                                  self.pos_limit[ask_product] + self.pos[ask_product])
                volume = min(bid_volume, int(-ask_volume * m))
                bid_volume, ask_volume = volume, int(-volume / m)
                # TODO: TREAT VOLUME SEPARATELY?
                if bid_volume > 0:
                    print("BUY", bid_product, str(
                        bid_volume) + "x", best_ask_pina)
                    orders_pina.append(
                        Order(bid_product, best_ask_pina, bid_volume))
                if ask_volume < 0:
                    print("SELL", ask_product, str(
                        ask_volume) + "x", best_bid_coconut)
                    orders_coconut.append(
                        Order(ask_product, best_bid_coconut, ask_volume))
            elif z < -1:
                # PINA overpriced, COCONUT underpriced
                self.entered -= 1
                bid_product = "COCONUTS"
                ask_product = "PINA_COLADAS"
                bid_volume = min(-best_ask_volume_coconut,
                                 self.pos_limit[bid_product] - self.pos[bid_product])
                ask_volume = -min(best_bid_volume_pina,
                                  self.pos_limit[ask_product] + self.pos[ask_product])
                volume = min(int(bid_volume * m), -ask_volume)
                bid_volume, ask_volume = int(volume / m), -volume
                # TODO: TREAT VOLUME SEPARATELY?
                print("CCCCCCCCCCCCCCCCCCCCCCCC Buy = ", bid_volume, -best_ask_volume_coconut, self.pos_limit[bid_product] - self.pos[bid_product],
                      "Sell = ", ask_volume, best_bid_volume_pina, self.pos_limit[ask_product] + self.pos[ask_product])
                if bid_volume > 0:
                    print("BUY", bid_product, str(
                        bid_volume) + "x", best_ask_coconut)
                    orders_coconut.append(
                        Order(bid_product, best_ask_coconut, bid_volume))
                if ask_volume < 0:
                    print("SELL", ask_product, str(
                        ask_volume) + "x", best_bid_pina)
                    orders_pina.append(
                        Order(ask_product, best_bid_pina, ask_volume))

        return orders_coconut, orders_pina