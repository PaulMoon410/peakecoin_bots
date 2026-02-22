from currency_bots.profit_strategies import is_profitable_or_volume_increase, get_profit_percent
import time
import datetime
import json
import os
from currency_bots.fetch_market import get_orderbook_top
from currency_bots.place_order import place_order, get_open_orders, cancel_order, get_balance

HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
TOKEN = "SWAP.BTC"
TICK = 0.0000001
DELAY = 1500  # 25 minutes in seconds

def get_resource_credits(account_name):
    """Return current resource credits percentage for the Hive account."""
    try:
        import requests
        url = f"https://api.hive.blog"
        payload = {
            "jsonrpc": "2.0",
            "method": "rc_api.find_rc_accounts",
            "params": {"accounts": [account_name]},
            "id": 1
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            rc = data.get('result', {}).get('rc_accounts', [{}])[0]
            if rc and 'rc_manabar' in rc and 'max_rc' in rc:
                current = int(rc['rc_manabar']['current_mana'])
                max_rc = int(rc['max_rc'])
                percent = round(current / max_rc * 100, 2) if max_rc > 0 else 0.0
                return percent
    except Exception:
        pass
    return None

def run_bot(username, active_key, profit_target=1.0):
    print("\n==============================")
    print(f"[BTC BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[BTC BOT] Resource Credits: {rc_percent}%")
        if rc_percent < 10.0:
            print(f"[BTC BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[BTC BOT] Resource Credits: Unable to fetch.")

    market = get_orderbook_top(TOKEN)
    if not market:
        print(f"[BTC BOT] Market fetch failed for {TOKEN}. Skipping this cycle.")
        print("==============================\n")
        time.sleep(2)
        pek_market = get_orderbook_top("PEK")
        pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
        if pek_ask <= 0:
            pek_ask = 0.00000001
            print(f"[BTC BOT] PEK market ask unavailable, using fallback price {pek_ask}")
        try:
            place_order(username, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[BTC BOT] Bought 0.00000001 PEK at {pek_ask}")
        except Exception as e:
            print(f"[BTC BOT] PEK buy exception: {e}")
        time.sleep(2)
        return
    print(f"[BTC BOT] Market fetch success for {TOKEN}.")
    bid = float(market.get("highestBid", 0))
    ask = float(market.get("lowestAsk", 0))
    buy_price = round(bid, 8) if bid > 0 else 0
    sell_price = round(ask, 8) if ask > 0 else 0
    if buy_price >= sell_price and buy_price > 0:
        sell_price = round(buy_price * (1 + profit_target / 100), 8)
    hive_balance = get_balance(username, "SWAP.HIVE")
    btc_balance = get_balance(username, TOKEN)
    buy_qty = round(hive_balance * 0.20 / buy_price, 8) if buy_price > 0 else 0
    sell_qty = round(btc_balance * 0.20, 8)
    print(f"[BTC BOT] Preparing BUY: {buy_qty} {TOKEN} at {buy_price}")
    print(f"[BTC BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    time.sleep(2)
    pek_market = get_orderbook_top("PEK")
    pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
    if pek_ask <= 0:
        pek_ask = 0.00000001
        print(f"[BTC BOT] PEK market ask unavailable, using fallback price {pek_ask}")
    try:
        place_order(username, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[BTC BOT] Bought 0.00000001 PEK at {pek_ask}")
    except Exception as e:
        print(f"[BTC BOT] PEK buy exception: {e}")
    time.sleep(2)
    print(f"[BTC BOT] Preparing SELL: {sell_qty} {TOKEN} at {sell_price}")
    open_orders = get_open_orders(username, TOKEN)
    duplicate_buy = any(o.get('type') == 'buy' and float(o.get('price', 0)) == buy_price for o in open_orders)
    if buy_qty <= 0:
        print(f"[BTC BOT] Skipping BUY: buy_qty is zero or negative. Check HIVE balance and buy price.")
    elif duplicate_buy:
        print(f"[BTC BOT] Skipping BUY: Duplicate buy order at {buy_price} detected.")
    else:
        try:
            place_order(username, TOKEN, buy_price, buy_qty, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[BTC BOT] BUY order submitted: {buy_qty} {TOKEN} at {buy_price}")
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[BTC BOT] Open orders after BUY: {len(open_orders)} found.")
            else:
                print(f"[BTC BOT] No open orders found after BUY (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[BTC BOT] BUY order exception: {e}")
    min_profit_percent = profit_target / 100
    min_sell_price = round(buy_price * (1 + min_profit_percent), 8)
    force_sell_price = min_sell_price
    if force_sell_price > buy_price and sell_qty > 0:
        open_orders = get_open_orders(username, TOKEN)
        duplicate_sell = any(o.get('type') == 'sell' and float(o.get('price', 0)) == force_sell_price for o in open_orders)
        if duplicate_sell:
            print(f"[BTC BOT] Skipping SELL: Duplicate sell order at {force_sell_price} detected.")
        else:
            try:
                place_order(username, TOKEN, force_sell_price, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                print(f"[BTC BOT] SELL order submitted: {sell_qty} {TOKEN} at {force_sell_price}")
                print(f"[BTC BOT] Profit percent: {get_profit_percent(buy_price, force_sell_price)}%")
                time.sleep(5)
                open_orders = get_open_orders(username, TOKEN)
                if open_orders:
                    print(f"[BTC BOT] Open orders after SELL: {len(open_orders)} found.")
                else:
                    print(f"[BTC BOT] No open orders found after SELL (may be node delay).")
                time.sleep(1)
            except Exception as e:
                print(f"[BTC BOT] SELL order exception: {e}")
    else:
        print(f"[BTC BOT] SELL order skipped: Not profitable or sell_qty is zero.")
    print(f"[BTC BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    time.sleep(DELAY)
