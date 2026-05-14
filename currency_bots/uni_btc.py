
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
TOKEN = "SWAP.BTC"
TICK = 0.0000001
DELAY = 1500  # 25 minutes in seconds

def run_bot(username, active_key, profit_target=1.0, scalping_enabled=False,
            self_buy_enabled=True, profit_currency_enabled=False, profit_currency="PEK", profit_amount=0.00000001):
    print("\n==============================")
    print(f"[BTC BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[BTC BOT] Resource Credits: {rc_percent}%")
        if rc_percent < MIN_RESOURCE_CREDITS:
            print(f"[BTC BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[BTC BOT] Resource Credits: Unable to fetch.")

    # Centralized order management
    enforce_open_order_limit(username, TOKEN, active_key=active_key)
    cancel_oldest_order(username, active_key=active_key)

    # Example: get balances and market
    # ...existing code for fetching balances and market...
    # Use place_profitable_order, handle_self_buy, handle_profit_currency_buy, ensure_min_orders_per_cycle as needed
    # ...
