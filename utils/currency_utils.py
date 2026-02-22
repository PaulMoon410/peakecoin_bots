import os

def get_available_currencies(uni_bots_path):
    currencies = []
    for filename in os.listdir(uni_bots_path):
        if filename.startswith('uni_') and filename.endswith('.py') and filename != 'uni_bot_base.py':
            currency = filename[4:-3].upper()
            currencies.append(currency)
    return currencies
