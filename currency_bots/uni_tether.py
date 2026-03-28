from currency_bots.profit_strategies import choose_sell_price, get_profit_percent
import time
from currency_bots.fetch_market import get_orderbook_top, get_resource_credits, MIN_RESOURCE_CREDITS
from currency_bots.place_order import place_order, get_open_orders, get_balance

HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
TOKEN = "SWAP.USDT"
DELAY = 1500

def run_bot(username, active_key, profit_target=1.0):
    print("\n==============================")
    print(f"[USDT BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[USDT BOT] Resource Credits: {rc_percent}%")
        if rc_percent < MIN_RESOURCE_CREDITS:
            print(f"[USDT BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[USDT BOT] Resource Credits: Unable to fetch.")

    pek_market = get_orderbook_top("PEK")
    pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0
    if pek_ask <= 0:
        pek_ask = 0.00000001
        print(f"[USDT BOT] PEK market ask unavailable, using fallback price {pek_ask}")
    try:
        pek_ok = place_order(username, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        if pek_ok:
            print(f"[USDT BOT] Bought 0.00000001 PEK at {pek_ask}")
        else:
            print(f"[USDT BOT] PEK buy failed at {pek_ask}")
    except Exception as e:
        print(f"[USDT BOT] PEK buy exception: {e}")
    time.sleep(2)

    market = get_orderbook_top(TOKEN)
    if not market:
        print(f"[USDT BOT] Market fetch failed for {TOKEN}. Skipping this cycle.")
        print("==============================\n")
        return
    print(f"[USDT BOT] Market fetch success for {TOKEN}.")
    bid = float(market.get("highestBid", 0))
    ask = float(market.get("lowestAsk", 0))
    buy_price = round(bid, 6) if bid > 0 else 0
    sell_price = choose_sell_price(buy_price, ask, profit_target, precision=6)
    hive_balance = get_balance(username, "SWAP.HIVE")
    usdt_balance = get_balance(username, TOKEN)
    buy_qty = round(hive_balance * 0.20 / buy_price, 2) if buy_price > 0 else 0
    sell_qty = round(usdt_balance * 0.20, 2)
    print(f"[USDT BOT] Preparing BUY: {buy_qty} {TOKEN} at {buy_price}")
    print(f"[USDT BOT] Preparing SELL: {sell_qty} {TOKEN} at {sell_price}")
    open_orders = get_open_orders(username, TOKEN)
    duplicate_buy = any(o.get('type') == 'buy' and float(o.get('price', 0)) == buy_price for o in open_orders)
    if buy_qty <= 0:
        print(f"[USDT BOT] Skipping BUY: buy_qty is zero or negative. Check HIVE balance and buy price.")
    elif duplicate_buy:
        print(f"[USDT BOT] Skipping BUY: Duplicate buy order at {buy_price} detected.")
    else:
        try:
            buy_ok = place_order(username, TOKEN, buy_price, buy_qty, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            if buy_ok:
                print(f"[USDT BOT] BUY order submitted: {buy_qty} {TOKEN} at {buy_price}")
            else:
                print(f"[USDT BOT] BUY order failed: {buy_qty} {TOKEN} at {buy_price}")
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[USDT BOT] Open orders after BUY: {len(open_orders)} found.")
            else:
                print(f"[USDT BOT] No open orders found after BUY (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[USDT BOT] BUY order exception: {e}")
    force_sell_price = sell_price
    if force_sell_price > buy_price and sell_qty > 0:
        open_orders = get_open_orders(username, TOKEN)
        duplicate_sell = any(o.get('type') == 'sell' and float(o.get('price', 0)) == force_sell_price for o in open_orders)
        if duplicate_sell:
            print(f"[USDT BOT] Skipping SELL: Duplicate sell order at {force_sell_price} detected.")
        else:
            try:
                sell_ok = place_order(username, TOKEN, force_sell_price, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                if sell_ok:
                    print(f"[USDT BOT] SELL order submitted: {sell_qty} {TOKEN} at {force_sell_price}")
                    print(f"[USDT BOT] Profit percent: {get_profit_percent(buy_price, force_sell_price)}%")
                else:
                    print(f"[USDT BOT] SELL order failed: {sell_qty} {TOKEN} at {force_sell_price}")
                time.sleep(5)
                open_orders = get_open_orders(username, TOKEN)
                if open_orders:
                    print(f"[USDT BOT] Open orders after SELL: {len(open_orders)} found.")
                else:
                    print(f"[USDT BOT] No open orders found after SELL (may be node delay).")
                time.sleep(1)
            except Exception as e:
                print(f"[USDT BOT] SELL order exception: {e}")
    else:
        print(f"[USDT BOT] SELL order skipped: Not profitable or sell_qty is zero.")
    print(f"[USDT BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    print(f"[USDT BOT] Cooldown wait: {DELAY}s before next cycle.")
    time.sleep(DELAY)
