import tkinter as tk
from tkinter import messagebox
import importlib.util
import os
from utils.currency_utils import get_available_currencies

class PlugAndPlayBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        import tkinter as tk
        from tkinter import messagebox
        import importlib.util
        import os
        import threading
        import time
        from utils.currency_utils import get_available_currencies

        class PlugAndPlayBotGUI(tk.Tk):
            def __init__(self):
                super().__init__()
                self.title("Plug and Play Bot - Advanced")
                self.geometry("600x700")
                self.running_bots = {}
                self.bot_threads = {}

                tk.Label(self, text="Username:").pack(pady=5)
                self.username_entry = tk.Entry(self, width=30)
                self.username_entry.pack(pady=5)

                currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
                self.currencies = get_available_currencies(currency_bots_path)
                self.selected_currencies = {}
                self.key_entries = {}

                tk.Label(self, text="Select currencies to trade:").pack(pady=10)
                self.currency_vars = {}
                for currency in self.currencies:
                    var = tk.BooleanVar()
                    chk = tk.Checkbutton(self, text=currency, variable=var, command=self.update_key_fields)
                    chk.pack(anchor='w', padx=20)
                    self.currency_vars[currency] = var

                self.keys_frame = tk.Frame(self)
                self.keys_frame.pack(pady=10)

                # Profit percentage slider
                tk.Label(self, text="Select profit percentage target:").pack(pady=10)
                self.profit_var = tk.DoubleVar(value=2.0)
                self.profit_slider = tk.Scale(self, from_=0.5, to=20.0, orient='horizontal', resolution=0.1, variable=self.profit_var, length=300)
                self.profit_slider.pack(pady=5)
                self.profit_label = tk.Label(self, text=f"Profit Target: {self.profit_var.get():.1f}%")
                self.profit_label.pack()
                self.profit_slider.bind("<Motion>", self.update_profit_label)
                self.profit_slider.bind("<ButtonRelease-1>", self.update_profit_label)

                # Operation mode selection
                tk.Label(self, text="Operation Mode:").pack(pady=(20,5))
                self.mode_var = tk.StringVar(value="once")
                mode_frame = tk.Frame(self)
                mode_frame.pack(pady=5)
                tk.Radiobutton(mode_frame, text="Run Once", variable=self.mode_var, value="once").pack(side=tk.LEFT, padx=10)
                tk.Radiobutton(mode_frame, text="Continuous (Server Mode)", variable=self.mode_var, value="continuous").pack(side=tk.LEFT, padx=10)

                # Buttons frame
                button_frame = tk.Frame(self)
                button_frame.pack(pady=20)
                self.start_button = tk.Button(button_frame, text="Start Bots", command=self.start_bots)
                self.start_button.pack(side=tk.LEFT, padx=10)
                self.stop_button = tk.Button(button_frame, text="Stop Bots", command=self.stop_bots, state=tk.DISABLED)
                self.stop_button.pack(side=tk.LEFT, padx=10)

                # Status display
                tk.Label(self, text="Bot Status:").pack(pady=(20,5))
                self.status_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1)
                self.status_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
                self.status_text = tk.Text(self.status_frame, height=8, width=70, wrap=tk.WORD)
                scrollbar = tk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
                self.status_text.configure(yscrollcommand=scrollbar.set)
                self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                self.log_message("Bot interface initialized. Ready to start trading.")

            def update_key_fields(self):
                for widget in self.keys_frame.winfo_children():
                    widget.destroy()
                self.key_entries.clear()
                for currency, var in self.currency_vars.items():
                    if var.get():
                        tk.Label(self.keys_frame, text=f"Active Key for {currency}:").pack(pady=2)
                        entry = tk.Entry(self.keys_frame, width=50, show="*")
                        entry.pack(pady=2)
                        self.key_entries[currency] = entry

            def update_profit_label(self, event=None):
                self.profit_label.config(text=f"Profit Target: {self.profit_var.get():.1f}%")

            def log_message(self, message):
                timestamp = time.strftime("%H:%M:%S")
                self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.status_text.see(tk.END)
                self.update()

            def validate_input(self):
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
                            try:
                                bot_module.run_bot(username, active_key, profit_target)
                            except TypeError:
                                bot_module.run_bot(username, active_key)
                            if self.running_bots.get(currency, False):
                                time.sleep(5)
                        except Exception as e:
                            self.log_message(f"⚠️ {currency} bot error in cycle #{cycle_count}: {str(e)}")
                            if self.running_bots.get(currency, False):
                                time.sleep(10)
                    self.log_message(f"🛑 {currency} bot stopped after {cycle_count} cycles")
                except Exception as e:
                    self.log_message(f"❌ Failed to start {currency} bot: {str(e)}")

            def run_bot_once(self, currency, username, active_key, profit_target):
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
                data = self.validate_input()
                if not data:
                    return
                mode = self.mode_var.get()
                if mode == "continuous":
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
                if not self.running_bots:
                    return
                self.log_message("🛑 Stopping all bots...")
                for currency in self.running_bots:
                    self.running_bots[currency] = False
                time.sleep(2)
                self.running_bots.clear()
                self.bot_threads.clear()
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.log_message("✅ All bots stopped.")

            def on_closing(self):
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
            if var.get():
                tk.Label(self.keys_frame, text=f"Active Key for {currency}:").pack(pady=2)
                entry = tk.Entry(self.keys_frame)
                entry.pack(pady=2)
                self.key_entries[currency] = entry

    def submit(self):
        username = self.username_entry.get()
        selected = [c for c, v in self.currency_vars.items() if v.get()]
        keys = {c: self.key_entries[c].get() for c in selected if c in self.key_entries}
        profit_target = self.profit_var.get()
        if not username or not selected or not all(keys.values()):
            messagebox.showerror("Error", "Please fill in all fields and select at least one currency.")
            return
        if profit_target < 0.5 or profit_target > 20.0:
            messagebox.showerror("Error", "Please select a valid profit percentage target.")
            return
        # Dynamically import and run each selected bot from currency_bots
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'currency_bots'))
        for currency in selected:
            bot_file = f"uni_{currency.lower()}.py"
            bot_path = os.path.join(currency_bots_path, bot_file)
            if os.path.exists(bot_path):
                spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
                bot_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(bot_module)
                # Call run_bot if available
                if hasattr(bot_module, 'run_bot'):
                    # Pass profit_target as an argument if run_bot supports it, else just pass username and key
                    try:
                        bot_module.run_bot(username, keys[currency], profit_target)
                    except TypeError:
                        bot_module.run_bot(username, keys[currency])
                    messagebox.showinfo("Bot Activated", f"Activated {currency} bot for user {username} with profit target {profit_target:.1f}%.")
                else:
                    messagebox.showerror("Error", f"run_bot function not found in {bot_file}.")
            else:
                messagebox.showerror("Error", f"Bot file for {currency} not found.")

if __name__ == "__main__":
    app = PlugAndPlayBotGUI()
    app.mainloop()
