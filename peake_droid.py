import os
from utils.currency_utils import get_available_currencies
from utils.settings import DEFAULT_PROFIT_TARGET, MAX_PROFIT_TARGET, MIN_PROFIT_TARGET, PEAKECOIN_CURRENCIES, PEAKECOIN_USERNAME, get_active_key
import importlib.util

def main():
    print("\n=== PeakeCoin Command-Line Bot ===\n")
    username_prompt = f"Enter your PeakeCoin username [{PEAKECOIN_USERNAME}]: " if PEAKECOIN_USERNAME else "Enter your PeakeCoin username: "
    username = input(username_prompt).strip() or PEAKECOIN_USERNAME
    currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
    currencies = get_available_currencies(currency_bots_path)
    print("\nAvailable currencies:")
    for i, c in enumerate(currencies, 1):
        print(f"  {i}. {c}")
    default_indices = [str(index) for index, currency in enumerate(currencies, 1) if currency in PEAKECOIN_CURRENCIES]
    selected_prompt = "\nEnter the numbers of currencies to trade (comma separated, e.g. 1,3,5)"
    if default_indices:
        selected_prompt += f" [{','.join(default_indices)}]"
    selected = input(f"{selected_prompt}: ").strip() or ",".join(default_indices)
    selected_indices = [int(x.strip())-1 for x in selected.split(',') if x.strip().isdigit() and 0 < int(x.strip()) <= len(currencies)]
    chosen_currencies = [currencies[i] for i in selected_indices]
    keys = {}
    for c in chosen_currencies:
        env_key = get_active_key(c)
        key_prompt = f"Enter active key for {c} [from .env]: " if env_key else f"Enter active key for {c}: "
        keys[c] = input(key_prompt).strip() or env_key
    while True:
        try:
            prompt = f"Enter profit percentage target ({MIN_PROFIT_TARGET} - {MAX_PROFIT_TARGET}) [{DEFAULT_PROFIT_TARGET}]: "
            profit_input = input(prompt).strip()
            profit_target = float(profit_input) if profit_input else DEFAULT_PROFIT_TARGET
            if MIN_PROFIT_TARGET <= profit_target <= MAX_PROFIT_TARGET:
                break
            else:
                print(f"Profit target must be between {MIN_PROFIT_TARGET} and {MAX_PROFIT_TARGET}.")
        except ValueError:
            print("Please enter a valid number.")
    for currency in chosen_currencies:
        bot_file = f"uni_{currency.lower()}.py"
        bot_path = os.path.join(currency_bots_path, bot_file)
        if os.path.exists(bot_path):
            spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            if hasattr(bot_module, 'run_bot'):
                try:
                    bot_module.run_bot(username, keys[currency], profit_target)
                except TypeError:
                    bot_module.run_bot(username, keys[currency])
                print(f"[OK] {currency} bot finished.\n")
            else:
                print(f"[ERROR] run_bot function not found in {bot_file}.")
        else:
            print(f"[ERROR] Bot file for {currency} not found.")

if __name__ == "__main__":
    main()
