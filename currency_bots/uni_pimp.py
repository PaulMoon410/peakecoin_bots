import time
from currency_bots.fetch_market import get_orderbook_top, get_resource_credits, MIN_RESOURCE_CREDITS
from currency_bots.place_order import place_order, get_open_orders, get_balance
from currency_bots.profit_strategies import choose_sell_price, get_profit_percent, scalping_strategy

TOKEN = "PIMP"
HIVE_NODES = ["api.hive.blog", "anyx.io", "hive.roelandp.nl"]
DELAY = 2

def run_bot(username, active_key, profit_target=2.0, scalping_enabled=False):
    print("\n==============================")
    print(f"[PIMP BOT] Starting Smart Trade for {TOKEN}")
    rc_percent = get_resource_credits(username)
    if rc_percent is not None:
        print(f"[PIMP BOT] Resource Credits: {rc_percent}%")
        if rc_percent < MIN_RESOURCE_CREDITS:
            print(f"[PIMP BOT] WARNING: Resource Credits too low ({rc_percent}%). Skipping trade cycle.")
            print("==============================\n")
            return
    else:
        print(f"[PIMP BOT] Resource Credits: Unable to fetch.")

    # Buy a tiny amount of PEK for node health (like other bots)
    # Buy PEK at 0.00000002 per cycle
    pek_market = get_orderbook_top("PEK")
    pek_ask = float(pek_market.get("lowestAsk", 0)) if pek_market else 0.00000002
    try:
        place_order(username, "PEK", pek_ask, 0.00000002, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[PIMP BOT] Bought 0.00000002 PEK at {pek_ask}")
    except Exception as e:
        print(f"[PIMP BOT] PEK buy exception: {e}")
    time.sleep(DELAY)
    # Buy 0.00000001 of own token per cycle
    market = get_orderbook_top(TOKEN)
    ask = float(market.get("lowestAsk", 0)) if market else 0
    try:
        place_order(username, TOKEN, ask, 0.00000001, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
        print(f"[PIMP BOT] Bought 0.00000001 {TOKEN} at {ask}")
    except Exception as e:
        print(f"[PIMP BOT] {TOKEN} self-buy exception: {e}")
    time.sleep(DELAY)

    market = get_orderbook_top(TOKEN)
    if not market:
        print(f"[PIMP BOT] Market fetch failed for {TOKEN}. Skipping this cycle.")
        print("==============================\n")
        return
    print(f"[PIMP BOT] Market fetch success for {TOKEN}.")
    bid = float(market.get("highestBid", 0))
    ask = float(market.get("lowestAsk", 0))
    buy_price = round(bid, 8) if bid > 0 else 0
    if scalping_enabled:
        sell_price = scalping_strategy(buy_price, ask, tick=TICK, spread_ticks=2, precision=8)
    else:
        sell_price = choose_sell_price(buy_price, ask, profit_target, precision=8)

    hive_balance = get_balance(username, "SWAP.HIVE")
    pimp_balance = get_balance(username, TOKEN)
    buy_qty = round(hive_balance * 0.20 / buy_price, 8) if buy_price > 0 else 0
    sell_qty = round(pimp_balance * 0.20, 8)

    print(f"[PIMP BOT] Preparing BUY: {buy_qty} {TOKEN} at {buy_price}")
    open_orders = get_open_orders(username, TOKEN)
    duplicate_buy = any(o.get('type') == 'buy' and float(o.get('price', 0)) == buy_price for o in open_orders)
    if buy_qty <= 0:
        print(f"[PIMP BOT] Skipping BUY: buy_qty is zero or negative. Check HIVE balance and buy price.")
    elif duplicate_buy:
        print(f"[PIMP BOT] Skipping BUY: Duplicate buy order at {buy_price} detected.")
    else:
        try:
            place_order(username, TOKEN, buy_price, buy_qty, order_type="buy", active_key=active_key, nodes=HIVE_NODES)
            print(f"[PIMP BOT] BUY order submitted: {buy_qty} {TOKEN} at {buy_price}")
            time.sleep(5)
            open_orders = get_open_orders(username, TOKEN)
            if open_orders:
                print(f"[PIMP BOT] Open orders after BUY: {len(open_orders)} found.")
            else:
                print(f"[PIMP BOT] No open orders found after BUY (may be node delay).")
            time.sleep(1)
        except Exception as e:
            print(f"[PIMP BOT] BUY order exception: {e}")

    force_sell_price = sell_price
    print(f"[PIMP BOT] Preparing SELL: {sell_qty} {TOKEN} at {force_sell_price}")
    open_orders = get_open_orders(username, TOKEN)
    duplicate_sell = any(o.get('type') == 'sell' and float(o.get('price', 0)) == force_sell_price for o in open_orders)
    if force_sell_price > buy_price and sell_qty > 0:
        if duplicate_sell:
            print(f"[PIMP BOT] Skipping SELL: Duplicate sell order at {force_sell_price} detected.")
        else:
            try:
                place_order(username, TOKEN, force_sell_price, sell_qty, order_type="sell", active_key=active_key, nodes=HIVE_NODES)
                print(f"[PIMP BOT] SELL order submitted: {sell_qty} {TOKEN} at {force_sell_price}")
                print(f"[PIMP BOT] Profit percent: {get_profit_percent(buy_price, force_sell_price)}%")
                time.sleep(5)
                open_orders = get_open_orders(username, TOKEN)
                if open_orders:
                    print(f"[PIMP BOT] Open orders after SELL: {len(open_orders)} found.")
                else:
                    print(f"[PIMP BOT] No open orders found after SELL (may be node delay).")
                time.sleep(1)
            except Exception as e:
                print(f"[PIMP BOT] SELL order exception: {e}")
    else:
        print(f"[PIMP BOT] SELL order skipped: Not profitable or sell_qty is zero.")
    print(f"[PIMP BOT] Trade cycle for {TOKEN} complete.")
    print("==============================\n")
    print(f"[PIMP BOT] Cooldown wait: {DELAY}s before next cycle.")
    time.sleep(DELAY)
