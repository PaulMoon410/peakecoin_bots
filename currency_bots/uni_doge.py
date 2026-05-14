from currency_bots.profit_strategies import choose_sell_price, get_profit_percent, scalping_strategy
import time
import datetime
import json
import os
from currency_bots.fetch_market import get_orderbook_top, get_resource_credits, MIN_RESOURCE_CREDITS
from currency_bots.place_order import place_order, get_open_orders, cancel_order, get_balance

HIVE_NODES = ["https://api.hive.blog", "https://anyx.io", "https://api.openhive.network"]
TOKEN = "SWAP.DOGE"
TICK = 0.0000001
DELAY = 1500  # 25 minutes in seconds

def run_bot(username, active_key, profit_target=1.0, scalping_enabled=False):
    print("\n==============================")
    print(f"[DOGE BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[DOGE BOT] Resource Credits: {rc_percent}%")
        if rc_percent < MIN_RESOURCE_CREDITS:
            print(f"[DOGE BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[DOGE BOT] Resource Credits: Unable to fetch.")

    market = get_orderbook_top(TOKEN)
    if not market:
        print(f"[DOGE BOT] Market fetch failed for {TOKEN}. Skipping this cycle.")
        print("==============================\n")
        time.sleep(2)
        pek_market = get_orderbook_top("PEK")
        pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
        if pek_ask <= 0:
            pek_ask = 0.00000001
            print(f"[DOGE BOT] PEK market ask unavailable, using fallback price {pek_ask}")
        try:
            place_order(username, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[DOGE BOT] Bought 0.00000001 PEK at {pek_ask}")
        except Exception as e:
            print(f"[DOGE BOT] PEK buy exception: {e}")
        time.sleep(2)
        return
    print(f"[DOGE BOT] Market fetch success for {TOKEN}.")
    bid = float(market.get("highestBid", 0))
    ask = float(market.get("lowestAsk", 0))
    # Dynamic profit target: increase if last trade was successful, decrease if not
    last_profit = 0
    try:
        with open(f"{username}_doge_last_profit.json", "r") as f:
            last_profit = json.load(f).get("profit", 0)
    except Exception:
        pass
    dynamic_profit_target = max(0.5, min(5.0, profit_target + (last_profit/10)))
    if scalping_enabled:
        sell_price = scalping_strategy(buy_price, ask, tick=TICK, spread_ticks=2, precision=8)
    else:
        sell_price = choose_sell_price(buy_price, ask, dynamic_profit_target, precision=8)
    stop_loss = round(buy_price * 0.97, 8)  # 3% stop-loss
    hive_balance = get_balance(username, "SWAP.HIVE")
    doge_balance = get_balance(username, TOKEN)
    buy_qty = round(hive_balance * 0.20 / buy_price, 8) if buy_price > 0 else 0
    sell_qty = round(doge_balance * 0.20, 8)
    print(f"[DOGE BOT] Preparing BUY: {buy_qty} {TOKEN} at {buy_price}")
    # PEK fallback
    pek_market = get_orderbook_top("PEK")
    pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
    if pek_ask <= 0:
        pek_ask = 0.00000001
        print(f"[DOGE BOT] PEK market ask unavailable, using fallback price {pek_ask}")
    try:
        place_order(username, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[DOGE BOT] Bought 0.00000001 PEK at {pek_ask}")
    except Exception as e:
        print(f"[DOGE BOT] PEK buy exception: {e}")
    time.sleep(2)
    # Improved duplicate order checks
    open_orders = get_open_orders(username, TOKEN)
    duplicate_buy = any(o.get('type') == 'buy' and abs(float(o.get('price', 0)) - buy_price) < 1e-8 for o in open_orders)
    if buy_qty <= 0:
        print(f"[DOGE BOT] Skipping BUY: buy_qty is zero or negative. Check HIVE balance and buy price.")
    elif duplicate_buy:
        print(f"[DOGE BOT] Skipping BUY: Duplicate buy order at {buy_price} detected.")
    else:
        try:
            place_order(username, TOKEN, buy_price, buy_qty, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[DOGE BOT] BUY order submitted: {buy_qty} {TOKEN} at {buy_price}")
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[DOGE BOT] Open orders after BUY: {len(open_orders)} found.")
            else:
                print(f"[DOGE BOT] No open orders found after BUY (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[DOGE BOT] BUY order exception: {e}")
    # SELL logic with stop-loss
    force_sell_price = sell_price
    open_orders = get_open_orders(username, TOKEN)
    duplicate_sell = any(o.get('type') == 'sell' and abs(float(o.get('price', 0)) - force_sell_price) < 1e-8 for o in open_orders)
    if sell_qty > 0 and not duplicate_sell:
        try:
            # If price drops below stop-loss, sell at market
            if ask < stop_loss:
                print(f"[DOGE BOT] Stop-loss triggered! Selling at market price {ask}")
                place_order(username, TOKEN, ask, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                profit = get_profit_percent(buy_price, ask)
            elif force_sell_price > buy_price:
                place_order(username, TOKEN, force_sell_price, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                print(f"[DOGE BOT] SELL order submitted: {sell_qty} {TOKEN} at {force_sell_price}")
                profit = get_profit_percent(buy_price, force_sell_price)
            else:
                print(f"[DOGE BOT] SELL order skipped: Not profitable.")
                profit = 0
            print(f"[DOGE BOT] Profit percent: {profit}%")
            # Save last profit for dynamic target
            with open(f"{username}_doge_last_profit.json", "w") as f:
                json.dump({"profit": profit}, f)
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[DOGE BOT] Open orders after SELL: {len(open_orders)} found.")
            else:
                print(f"[DOGE BOT] No open orders found after SELL (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[DOGE BOT] SELL order exception: {e}")
    else:
        print(f"[DOGE BOT] SELL order skipped: Not profitable, duplicate, or sell_qty is zero.")
    print(f"[DOGE BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    print(f"[DOGE BOT] Cooldown wait: {DELAY}s before next cycle.")
    time.sleep(DELAY)
