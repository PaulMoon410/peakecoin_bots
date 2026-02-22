import os
from utils.currency_utils import get_available_currencies
import importlib.util

def main():
    print("\n=== PeakeCoin Command-Line Bot ===\n")
    username = input("Enter your PeakeCoin username: ").strip()
    currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
    currencies = get_available_currencies(currency_bots_path)
    print("\nAvailable currencies:")
    for i, c in enumerate(currencies, 1):
        print(f"  {i}. {c}")
    selected = input("\nEnter the numbers of currencies to trade (comma separated, e.g. 1,3,5): ")
    selected_indices = [int(x.strip())-1 for x in selected.split(',') if x.strip().isdigit() and 0 < int(x.strip()) <= len(currencies)]
    chosen_currencies = [currencies[i] for i in selected_indices]
    keys = {}
    for c in chosen_currencies:
        keys[c] = input(f"Enter active key for {c}: ").strip()
    while True:
        try:
            profit_target = float(input("Enter profit percentage target (0.5 - 20.0): ").strip())
            if 0.5 <= profit_target <= 20.0:
                break
            else:
                print("Profit target must be between 0.5 and 20.0.")
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
