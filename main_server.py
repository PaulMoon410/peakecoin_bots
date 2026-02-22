import tkinter as tk
from tkinter import messagebox, ttk
import importlib.util
import os
import threading
import time
from utils.currency_utils import get_available_currencies

class PlugAndPlayBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PeakeCoin Plug and Play Bot - Maryland Edition")
        self.geometry("600x700")
        self.running_bots = {}
        self.bot_threads = {}

        # Maryland flag colors
        self.bg_gold = "#fcd116"
        self.bg_red = "#e03a3e"
        self.bg_black = "#000000"
        self.bg_white = "#ffffff"

        self.configure(bg=self.bg_gold)

        # Title
        tk.Label(self, text="PeakeCoin Plug and Play Bot", font=("Segoe UI", 22, "bold"), fg=self.bg_black, bg=self.bg_gold).pack(pady=10)
        tk.Label(self, text="Maryland Edition", font=("Segoe UI", 14, "bold"), fg=self.bg_red, bg=self.bg_gold).pack(pady=2)

        # Username field
        tk.Label(self, text="Username:", bg=self.bg_gold, fg=self.bg_black, font=("Segoe UI", 12)).pack(pady=5)
        self.username_entry = tk.Entry(self, width=30, bg=self.bg_white, fg=self.bg_black, font=("Segoe UI", 11))
        self.username_entry.pack(pady=5)

        # Dynamically load available currencies from currency_bots
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        self.currencies = get_available_currencies(currency_bots_path)
        self.selected_currencies = {}
        self.key_entries = {}

        # Currency selection
        tk.Label(self, text="Select currencies to trade:", bg=self.bg_gold, fg=self.bg_black, font=("Segoe UI", 12, "bold")).pack(pady=10)
        self.currency_vars = {}
        for currency in self.currencies:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self, text=currency, variable=var, command=self.update_key_fields,
                                bg=self.bg_gold, fg=self.bg_red, selectcolor=self.bg_white, font=("Segoe UI", 11, "bold"))
            chk.pack(anchor='w', padx=20)
            self.currency_vars[currency] = var

        # Keys frame
        self.keys_frame = tk.Frame(self, bg=self.bg_gold)
        self.keys_frame.pack(pady=10)

        # Profit percentage slider
        tk.Label(self, text="Select profit percentage target:", bg=self.bg_gold, fg=self.bg_black, font=("Segoe UI", 12)).pack(pady=10)
        self.profit_var = tk.DoubleVar(value=2.0)
        self.profit_slider = tk.Scale(self, from_=0.5, to=20.0, orient='horizontal', 
                                     resolution=0.1, variable=self.profit_var, length=300, bg=self.bg_gold, fg=self.bg_black, highlightbackground=self.bg_black)
        self.profit_slider.pack(pady=5)
        self.profit_label = tk.Label(self, text=f"Profit Target: {self.profit_var.get():.1f}%", bg=self.bg_gold, fg=self.bg_black)
        self.profit_label.pack()
        self.profit_slider.bind("<Motion>", self.update_profit_label)
        self.profit_slider.bind("<ButtonRelease-1>", self.update_profit_label)

        # Operation mode selection
        tk.Label(self, text="Operation Mode:", bg=self.bg_gold, fg=self.bg_black, font=("Segoe UI", 12)).pack(pady=(20,5))
        self.mode_var = tk.StringVar(value="once")

        mode_frame = tk.Frame(self, bg=self.bg_gold)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Run Once", variable=self.mode_var, 
                      value="once", bg=self.bg_gold, fg=self.bg_black, selectcolor=self.bg_white, font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Continuous (Server Mode)", variable=self.mode_var, 
                      value="continuous", bg=self.bg_gold, fg=self.bg_red, selectcolor=self.bg_white, font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)

        # Buttons frame
        button_frame = tk.Frame(self, bg=self.bg_gold)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="Start Bots", command=self.start_bots, 
                                     bg=self.bg_black, fg=self.bg_gold, font=("Segoe UI", 12, "bold"), activebackground=self.bg_red, activeforeground=self.bg_white)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text="Stop Bots", command=self.stop_bots, 
                                    bg=self.bg_red, fg=self.bg_white, font=("Segoe UI", 12, "bold"), activebackground=self.bg_black, activeforeground=self.bg_gold, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Maryland flag bar above status log
        flag_bar = tk.Frame(self, height=24, bg=self.bg_black)
        flag_bar.pack(fill=tk.X, padx=20, pady=(10,0))
        # Add colored blocks to simulate flag pattern
        for i, color in enumerate([self.bg_black, self.bg_gold, self.bg_red, self.bg_white]*3):
            block = tk.Frame(flag_bar, width=40, height=24, bg=color)
            block.pack(side=tk.LEFT, padx=0, pady=0)

        # Status display
        tk.Label(self, text="Bot Status:", bg=self.bg_gold, fg=self.bg_black, font=("Segoe UI", 12, "bold")).pack(pady=(20,5))
        self.status_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1, bg=self.bg_gold)
        self.status_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

        self.status_text = tk.Text(self.status_frame, height=8, width=70, wrap=tk.WORD, bg=self.bg_white, fg=self.bg_black, font=("Consolas", 11))
        scrollbar = tk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_message("Bot interface initialized. Ready to start trading.")

    def update_profit_label(self, event=None):
        self.profit_label.config(text=f"Profit Target: {self.profit_var.get():.1f}%")

    def update_key_fields(self):
        # Clear previous key fields
        for widget in self.keys_frame.winfo_children():
            widget.destroy()
        self.key_entries.clear()
        
        # Add key entry for each selected currency
        for currency, var in self.currency_vars.items():
            if var.get():
                tk.Label(self.keys_frame, text=f"Active Key for {currency}:").pack(pady=2)
                entry = tk.Entry(self.keys_frame, width=50, show="*")
                entry.pack(pady=2)
                self.key_entries[currency] = entry

    def log_message(self, message):
        """Add a message to the status display"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.update()

    def validate_input(self):
        """Validate user input"""
        username = self.username_entry.get().strip()
        selected = [c for c, v in self.currency_vars.items() if v.get()]
        keys = {c: self.key_entries[c].get().strip() for c in selected if c in self.key_entries}
        profit_target = self.profit_var.get()
        
        if not username:
            messagebox.showerror("Error", "Please enter your username.")
            return None
            
        if not selected:
            messagebox.showerror("Error", "Please select at least one currency.")
            return None
            
        if not all(keys.values()):
            messagebox.showerror("Error", "Please enter active keys for all selected currencies.")
            return None
            
        if profit_target < 0.5 or profit_target > 20.0:
            messagebox.showerror("Error", "Please select a valid profit percentage target (0.5% - 20%).")
            return None
            
        return {
            'username': username,
            'selected': selected,
            'keys': keys,
            'profit_target': profit_target
        }

    def run_bot_continuous(self, currency, username, active_key, profit_target):
        """Run a single bot continuously in a loop"""
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        bot_file = f"uni_{currency.lower()}.py"
        bot_path = os.path.join(currency_bots_path, bot_file)
        
        if not os.path.exists(bot_path):
            self.log_message(f"❌ Bot file for {currency} not found: {bot_file}")
            return
            
        try:
            spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            if not hasattr(bot_module, 'run_bot'):
                self.log_message(f"❌ run_bot function not found in {bot_file}")
                return
                
            self.log_message(f"🚀 Starting {currency} bot in continuous mode...")
            
            cycle_count = 0
            while self.running_bots.get(currency, False):
                try:
                    cycle_count += 1
                    self.log_message(f"🔄 {currency} bot - Cycle #{cycle_count}")
                    
                    # Run the bot
                    try:
                        bot_module.run_bot(username, active_key, profit_target)
                    except TypeError:
                        bot_module.run_bot(username, active_key)
                    
                    # Wait before next cycle (bots have their own delays, but add extra safety)
                    if self.running_bots.get(currency, False):
                        time.sleep(5)  # 5 second buffer between cycles
                        
                except Exception as e:
                    self.log_message(f"⚠️ {currency} bot error in cycle #{cycle_count}: {str(e)}")
                    if self.running_bots.get(currency, False):
                        time.sleep(10)  # Wait longer on error
                        
            self.log_message(f"🛑 {currency} bot stopped after {cycle_count} cycles")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start {currency} bot: {str(e)}")

    def run_bot_once(self, currency, username, active_key, profit_target):
        """Run a single bot once"""
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        bot_file = f"uni_{currency.lower()}.py"
        bot_path = os.path.join(currency_bots_path, bot_file)
        
        if not os.path.exists(bot_path):
            self.log_message(f"❌ Bot file for {currency} not found: {bot_file}")
            return
            
        try:
            spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            if not hasattr(bot_module, 'run_bot'):
                self.log_message(f"❌ run_bot function not found in {bot_file}")
                return
                
            self.log_message(f"▶️ Running {currency} bot once...")
            
            try:
                bot_module.run_bot(username, active_key, profit_target)
                self.log_message(f"✅ {currency} bot completed successfully")
            except TypeError:
                bot_module.run_bot(username, active_key)
                self.log_message(f"✅ {currency} bot completed successfully")
                
        except Exception as e:
            self.log_message(f"❌ {currency} bot failed: {str(e)}")

    def start_bots(self):
        """Start the selected bots"""
        data = self.validate_input()
        if not data:
            return
            
        mode = self.mode_var.get()
        
        if mode == "continuous":
            # Start bots in continuous mode
            self.log_message(f"🚀 Starting {len(data['selected'])} bots in continuous mode...")
            
            for currency in data['selected']:
                self.running_bots[currency] = True
                thread = threading.Thread(
                    target=self.run_bot_continuous,
                    args=(currency, data['username'], data['keys'][currency], data['profit_target']),
                    daemon=True
                )
                thread.start()
                self.bot_threads[currency] = thread
                
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_message("✅ All bots started. Click 'Stop Bots' to halt continuous operation.")
            
        else:
            # Run bots once
            self.log_message(f"▶️ Running {len(data['selected'])} bots once...")
            
            for currency in data['selected']:
                thread = threading.Thread(
                    target=self.run_bot_once,
                    args=(currency, data['username'], data['keys'][currency], data['profit_target']),
                    daemon=True
                )
                thread.start()
                
            self.log_message("✅ All bots started in single-run mode.")

    def stop_bots(self):
        """Stop all running bots"""
        if not self.running_bots:
            return
            
        self.log_message("🛑 Stopping all bots...")
        
        # Signal all bots to stop
        for currency in self.running_bots:
            self.running_bots[currency] = False
            
        # Wait a moment for threads to finish
        time.sleep(2)
        
        # Clear tracking
        self.running_bots.clear()
        self.bot_threads.clear()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log_message("✅ All bots stopped.")

    def on_closing(self):
        """Handle window closing"""
        if self.running_bots:
            if messagebox.askokcancel("Quit", "Bots are still running. Stop them and quit?"):
                self.stop_bots()
                time.sleep(1)
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = PlugAndPlayBotGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
