import os
import time
import threading
import signal
import sys
from utils.currency_utils import get_available_currencies
import importlib.util

class PeakeBotServer:
    def __init__(self):
        self.running_bots = {}
        self.bot_threads = {}
        self.shutdown_requested = False
        
        # Handle shutdown signals
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received shutdown signal ({signum}). Stopping all bots...")
        self.shutdown_requested = True
        self.stop_all_bots()
        sys.exit(0)
        
    def log_message(self, message):
        """Log messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_bot_continuous(self, currency, username, active_key, profit_target):
        """Run a single bot continuously in a loop"""
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        bot_file = f"uni_{currency.lower()}.py"
        bot_path = os.path.join(currency_bots_path, bot_file)
        
        if not os.path.exists(bot_path):
            self.log_message(f"❌ {currency}: Bot file not found: {bot_file}")
            return
            
        try:
            spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            if not hasattr(bot_module, 'run_bot'):
                self.log_message(f"❌ {currency}: run_bot function not found in {bot_file}")
                return
                
            self.log_message(f"🚀 {currency}: Starting continuous trading bot...")
            
            cycle_count = 0
            while self.running_bots.get(currency, False) and not self.shutdown_requested:
                try:
                    cycle_count += 1
                    self.log_message(f"🔄 {currency}: Starting cycle #{cycle_count}")
                    
                    # Run the bot
                    try:
                        bot_module.run_bot(username, active_key, profit_target)
                    except TypeError:
                        bot_module.run_bot(username, active_key)
                    
                    self.log_message(f"✅ {currency}: Cycle #{cycle_count} completed")
                    
                    # Wait before next cycle (bots have their own delays)
                    if self.running_bots.get(currency, False) and not self.shutdown_requested:
                        time.sleep(5)  # 5 second buffer between cycles
                        
                except Exception as e:
                    self.log_message(f"⚠️ {currency}: Error in cycle #{cycle_count}: {str(e)}")
                    if self.running_bots.get(currency, False) and not self.shutdown_requested:
                        time.sleep(60)  # Wait 1 minute on error before retrying
                        
            self.log_message(f"🛑 {currency}: Bot stopped after {cycle_count} cycles")
            
        except Exception as e:
            self.log_message(f"❌ {currency}: Failed to start bot: {str(e)}")
            
    def start_bot(self, currency, username, active_key, profit_target):
        """Start a bot for a specific currency"""
        if currency in self.running_bots:
            self.log_message(f"⚠️ {currency}: Bot already running")
            return False
            
        self.running_bots[currency] = True
        thread = threading.Thread(
            target=self.run_bot_continuous,
            args=(currency, username, active_key, profit_target),
            daemon=True
        )
        thread.start()
        self.bot_threads[currency] = thread
        return True
        
    def stop_bot(self, currency):
        """Stop a specific bot"""
        if currency in self.running_bots:
            self.running_bots[currency] = False
            self.log_message(f"🛑 {currency}: Stop signal sent")
            return True
        return False
        
    def stop_all_bots(self):
        """Stop all running bots"""
        if not self.running_bots:
            return
            
        self.log_message("🛑 Stopping all bots...")
        
        # Signal all bots to stop
        for currency in list(self.running_bots.keys()):
            self.running_bots[currency] = False
            
        # Wait for threads to finish
        for currency, thread in self.bot_threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
                
        # Clear tracking
        self.running_bots.clear()
        self.bot_threads.clear()
        
        self.log_message("✅ All bots stopped")
        
    def get_status(self):
        """Get current status of all bots"""
        return {
            'running_bots': list(self.running_bots.keys()),
            'total_running': len(self.running_bots),
            'shutdown_requested': self.shutdown_requested
        }
        
    def run_interactive(self):
        """Run in interactive mode"""
        self.log_message("🚀 PeakeCoin Bot Server - Interactive Mode")
        self.log_message("=" * 50)
        
        # Get user input
        username = input("Enter your PeakeCoin username: ").strip()
        if not username:
            print("❌ Username is required")
            return
            
        # Get available currencies
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        currencies = get_available_currencies(currency_bots_path)
        
        print(f"\nAvailable currencies: {', '.join(currencies)}")
        selected_input = input("Enter currencies to trade (comma separated, e.g., BTC,ETH,DOGE): ").strip()
        
        if not selected_input:
            print("❌ No currencies selected")
            return
            
        selected_currencies = [c.strip().upper() for c in selected_input.split(',')]
        valid_currencies = [c for c in selected_currencies if c in currencies]
        
        if not valid_currencies:
            print("❌ No valid currencies selected")
            return
            
        # Get keys for each currency
        keys = {}
        for currency in valid_currencies:
            key = input(f"Enter active key for {currency}: ").strip()
            if not key:
                print(f"❌ Key required for {currency}")
                return
            keys[currency] = key
            
        # Get profit target
        while True:
            try:
                profit_target = float(input("Enter profit percentage target (0.5 - 20.0): ").strip())
                if 0.5 <= profit_target <= 20.0:
                    break
                else:
                    print("❌ Profit target must be between 0.5 and 20.0")
            except ValueError:
                print("❌ Please enter a valid number")
                
        # Start bots
        self.log_message(f"🚀 Starting {len(valid_currencies)} bots for user: {username}")
        self.log_message(f"📊 Profit target: {profit_target}%")
        self.log_message(f"💰 Trading currencies: {', '.join(valid_currencies)}")
        
        for currency in valid_currencies:
            if self.start_bot(currency, username, keys[currency], profit_target):
                self.log_message(f"✅ {currency}: Bot started successfully")
            else:
                self.log_message(f"❌ {currency}: Failed to start bot")
                
        # Keep running until shutdown
        try:
            self.log_message("🔄 Server running... Press Ctrl+C to stop all bots")
            while not self.shutdown_requested and self.running_bots:
                time.sleep(10)
                # Print status every 10 minutes
                if int(time.time()) % 600 == 0:
                    status = self.get_status()
                    self.log_message(f"📊 Status: {status['total_running']} bots running")
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

def main():
    """Main entry point"""
    server = PeakeBotServer()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("PeakeCoin Bot Server")
        print("Usage:")
        print("  python server_bot.py          - Interactive mode")
        print("  python server_bot.py --help   - Show this help")
        return
        
    try:
        server.run_interactive()
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
