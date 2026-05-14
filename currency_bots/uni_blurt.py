
import time
import datetime
import json
import os
from currency_bots.fetch_market import get_orderbook_top, get_resource_credits, MIN_RESOURCE_CREDITS
from currency_bots.place_order import get_balance
from currency_bots.order_manager import (
    enforce_open_order_limit, cancel_oldest_order, place_profitable_order,
    ensure_min_orders_per_cycle, handle_self_buy, handle_profit_currency_buy, PROFIT_CURRENCIES
)

HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
TOKEN = "SWAP.BLURT"
TICK = 0.0000001
DELAY = 1500  # 25 minutes in seconds

def run_bot(username, active_key, profit_target=1.0, scalping_enabled=False,
            self_buy_enabled=True, profit_currency_enabled=False, profit_currency="PEK", profit_amount=0.00000001):
    print("\n==============================")
    print(f"[BLURT BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[BLURT BOT] Resource Credits: {rc_percent}%")
        if rc_percent < MIN_RESOURCE_CREDITS:
            print(f"[BLURT BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[BLURT BOT] Resource Credits: Unable to fetch.")

    enforce_open_order_limit(username, TOKEN, active_key=active_key)
    cancel_oldest_order(username, active_key=active_key)
    # ...centralized order logic for BLURT bot...
    pek_market = get_orderbook_top("PEK")
    pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
    if pek_ask <= 0:
        pek_ask = 0.00000002
        print(f"[BLURT BOT] PEK market ask unavailable, using fallback price {pek_ask}")
    try:
        place_order(username, "PEK", pek_ask, 0.00000002, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[BLURT BOT] Bought 0.00000002 PEK at {pek_ask}")
    except Exception as e:
        print(f"[BLURT BOT] PEK buy exception: {e}")
    time.sleep(2)
    # Buy 0.00000001 of own token per cycle
    try:
        place_order(username, TOKEN, ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[BLURT BOT] Bought 0.00000001 {TOKEN} at {ask}")
    except Exception as e:
        print(f"[BLURT BOT] {TOKEN} self-buy exception: {e}")
    time.sleep(2)
    print(f"[BLURT BOT] Preparing SELL: {sell_qty} {TOKEN} at {sell_price}")
    open_orders = get_open_orders(username, TOKEN)
    duplicate_buy = any(o.get('type') == 'buy' and float(o.get('price', 0)) == buy_price for o in open_orders)
    if buy_qty <= 0:
        print(f"[BLURT BOT] Skipping BUY: buy_qty is zero or negative. Check HIVE balance and buy price.")
    elif duplicate_buy:
        print(f"[BLURT BOT] Skipping BUY: Duplicate buy order at {buy_price} detected.")
    else:
        try:
            place_order(username, TOKEN, buy_price, buy_qty, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[BLURT BOT] BUY order submitted: {buy_qty} {TOKEN} at {buy_price}")
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[BLURT BOT] Open orders after BUY: {len(open_orders)} found.")
            else:
                print(f"[BLURT BOT] No open orders found after BUY (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[BLURT BOT] BUY order exception: {e}")
    force_sell_price = sell_price
    if force_sell_price > buy_price and sell_qty > 0:
        open_orders = get_open_orders(username, TOKEN)
        duplicate_sell = any(o.get('type') == 'sell' and float(o.get('price', 0)) == force_sell_price for o in open_orders)
        if duplicate_sell:
            print(f"[BLURT BOT] Skipping SELL: Duplicate sell order at {force_sell_price} detected.")
        else:
            try:
                place_order(username, TOKEN, force_sell_price, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                print(f"[BLURT BOT] SELL order submitted: {sell_qty} {TOKEN} at {force_sell_price}")
                print(f"[BLURT BOT] Profit percent: {get_profit_percent(buy_price, force_sell_price)}%")
                time.sleep(5)
                open_orders = get_open_orders(username, TOKEN)
                if open_orders:
                    print(f"[BLURT BOT] Open orders after SELL: {len(open_orders)} found.")
                else:
                    print(f"[BLURT BOT] No open orders found after SELL (may be node delay).")
                time.sleep(1)
            except Exception as e:
                print(f"[BLURT BOT] SELL order exception: {e}")
    else:
        print(f"[BLURT BOT] SELL order skipped: Not profitable or sell_qty is zero.")
    print(f"[BLURT BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    print(f"[BLURT BOT] Cooldown wait: {DELAY}s before next cycle.")
    time.sleep(DELAY)
