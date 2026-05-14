import contextlib
import importlib.util
import os
import re
import threading
import time
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox

from currency_bots.fetch_market import get_orderbook_top
from currency_bots.place_order import place_order
from utils.currency_utils import get_available_currencies


class PlugAndPlayBotGUI(tk.Tk):
    TOKEN_ALIAS_TO_MARKET = {
        "PEK": "PEK",
        "PIMP": "PIMP",
        "TETHER": "SWAP.USDT",
    }

    def __init__(self):
        super().__init__()
        self.title("PeakeCoin Plug and Play Bot")
        self.geometry("760x860")
        self.configure(bg="#f7f8fb")

        self.running_bots = {}
        self.bot_threads = {}

        self.profit_lock = threading.Lock()
        self.profit_events = 0
        self.total_profit_percent = 0.0
        self.last_profit_percent = 0.0
        self.per_currency_stats = {}

        self._build_ui()
        self.log_message("Interface ready. Guaranteed-profit sell pricing is enabled in currency bots.")

    def _build_ui(self):
        header = tk.Frame(self, bg="#ffffff", bd=1, relief=tk.SOLID)
        header.pack(fill=tk.X, padx=14, pady=(14, 8))

        tk.Label(
            header,
            text="PeakeCoin Plug and Play Bot",
            bg="#ffffff",
            fg="#0f172a",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(10, 2))
        tk.Label(
            header,
            text="Cleaner UI • Profit-Target Enforcement • Profit Tracking Over Time",
            bg="#ffffff",
            fg="#475569",
            font=("Segoe UI", 10),
        ).pack(pady=(0, 10))

        form = tk.Frame(self, bg="#f7f8fb")
        form.pack(fill=tk.X, padx=14)

        tk.Label(form, text="Username", bg="#f7f8fb", fg="#111827", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.username_entry = tk.Entry(form, width=42, font=("Segoe UI", 11))
        self.username_entry.pack(anchor="w", pady=(2, 10))

        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "currency_bots"))
        self.currencies = get_available_currencies(currency_bots_path)
        self.currency_vars = {}
        self.key_entries = {}

        currency_box = tk.LabelFrame(form, text="Currencies", bg="#f7f8fb", fg="#111827", padx=10, pady=8)
        currency_box.pack(fill=tk.X, pady=(0, 10))

        for index, currency in enumerate(self.currencies):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                currency_box,
                text=currency,
                variable=var,
                command=self.update_key_fields,
                bg="#f7f8fb",
                fg="#1f2937",
                anchor="w",
                width=16,
                font=("Segoe UI", 10),
            )
            chk.grid(row=index // 4, column=index % 4, sticky="w", padx=6, pady=4)
            self.currency_vars[currency] = var

        self.keys_frame = tk.LabelFrame(form, text="Active Keys", bg="#f7f8fb", fg="#111827", padx=10, pady=8)
        self.keys_frame.pack(fill=tk.X, pady=(0, 10))


        profit_box = tk.LabelFrame(form, text="Profit Strategy", bg="#f7f8fb", fg="#111827", padx=10, pady=8)
        profit_box.pack(fill=tk.X)

        self.profit_var = tk.DoubleVar(value=2.0)
        self.profit_label = tk.Label(
            profit_box,
            text=f"Profit Target: {self.profit_var.get():.1f}%",
            bg="#f7f8fb",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
        )
        self.profit_label.pack(anchor="w")

        self.profit_slider = tk.Scale(
            profit_box,
            from_=0.5,
            to=20.0,
            orient="horizontal",
            resolution=0.1,
            variable=self.profit_var,
            length=360,
            bg="#f7f8fb",
            highlightthickness=0,
            command=lambda _=None: self.update_profit_label(),
        )
        self.profit_slider.pack(anchor="w")

        self.guarantee_label = tk.Label(
            profit_box,
            text="Guaranteed-profit mode: sell pricing is set to at least your selected profit target.",
            bg="#f7f8fb",
            fg="#0b7a3b",
            font=("Segoe UI", 9),
        )
        self.guarantee_label.pack(anchor="w", pady=(4, 0))

        # Scalping logic option
        self.scalping_var = tk.BooleanVar(value=False)
        self.scalping_check = tk.Checkbutton(
            profit_box,
            text="Enable Scalping Logic (buy/sell small quantities at close range)",
            variable=self.scalping_var,
            bg="#f7f8fb",
            fg="#0ea5e9",
            font=("Segoe UI", 10),
        )
        self.scalping_check.pack(anchor="w", pady=(8, 0))

        mode_frame = tk.Frame(form, bg="#f7f8fb")
        mode_frame.pack(fill=tk.X, pady=(10, 6))
        self.mode_var = tk.StringVar(value="once")
        tk.Label(mode_frame, text="Operation Mode", bg="#f7f8fb", fg="#111827", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="Run Once", variable=self.mode_var, value="once", bg="#f7f8fb", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="Continuous", variable=self.mode_var, value="continuous", bg="#f7f8fb", font=("Segoe UI", 10)).pack(anchor="w")

        micro_buy_frame = tk.LabelFrame(form, text="Micro Profit Buys", bg="#f7f8fb", fg="#111827", padx=10, pady=8)
        micro_buy_frame.pack(fill=tk.X, pady=(6, 0))

        self.enable_extra_micro_buy = tk.BooleanVar(value=False)
        tk.Checkbutton(
            micro_buy_frame,
            text="Enable extra micro buy each cycle",
            variable=self.enable_extra_micro_buy,
            bg="#f7f8fb",
            fg="#111827",
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        selector_row = tk.Frame(micro_buy_frame, bg="#f7f8fb")
        selector_row.pack(fill=tk.X, pady=(6, 2))
        tk.Label(selector_row, text="Extra token:", bg="#f7f8fb", fg="#111827", width=12, anchor="w").pack(side=tk.LEFT)
        self.extra_micro_token_var = tk.StringVar(value="PEK")
        self.extra_micro_options = ["PEK"]
        self.extra_micro_menu = tk.OptionMenu(selector_row, self.extra_micro_token_var, *self.extra_micro_options)
        self.extra_micro_menu.config(width=16)
        self.extra_micro_menu.pack(side=tk.LEFT)

        tk.Label(
            micro_buy_frame,
            text="Always buys 0.00000001 PEK every cycle. Optional extra token buy also uses 0.00000001.",
            bg="#f7f8fb",
            fg="#0f766e",
            font=("Segoe UI", 9),
            wraplength=620,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(2, 0))

        button_bar = tk.Frame(self, bg="#f7f8fb")
        button_bar.pack(fill=tk.X, padx=14, pady=(8, 6))

        self.start_button = tk.Button(button_bar, text="Start Bots", command=self.start_bots, bg="#111827", fg="#ffffff", width=14)
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_button = tk.Button(button_bar, text="Stop Bots", command=self.stop_bots, state=tk.DISABLED, bg="#b91c1c", fg="#ffffff", width=14)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(button_bar, text="Clear Log", command=self.clear_log, bg="#e5e7eb", fg="#111827", width=14).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(button_bar, text="Copy Log", command=self.copy_log, bg="#0369a1", fg="#ffffff", width=14).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(button_bar, text="Save Log...", command=self.save_log, bg="#065f46", fg="#ffffff", width=14).pack(side=tk.LEFT)

        stats = tk.LabelFrame(self, text="Profit Over Time", bg="#ffffff", fg="#111827", padx=10, pady=8)
        stats.pack(fill=tk.X, padx=14, pady=(4, 8))

        self.total_signals_var = tk.StringVar(value="Sell Signals: 0")
        self.avg_profit_var = tk.StringVar(value="Average Profit Signal: 0.00%")
        self.cumulative_profit_var = tk.StringVar(value="Cumulative Profit Signal: 0.00%")
        self.last_profit_var = tk.StringVar(value="Last Profit Signal: 0.00%")

        tk.Label(stats, textvariable=self.total_signals_var, bg="#ffffff", fg="#111827", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=2, pady=2)
        tk.Label(stats, textvariable=self.avg_profit_var, bg="#ffffff", fg="#111827", font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=14, pady=2)
        tk.Label(stats, textvariable=self.cumulative_profit_var, bg="#ffffff", fg="#111827", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=2, pady=2)
        tk.Label(stats, textvariable=self.last_profit_var, bg="#ffffff", fg="#111827", font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=14, pady=2)

        self.currency_profit_var = tk.StringVar(value="Per-currency: n/a")
        tk.Label(stats, textvariable=self.currency_profit_var, bg="#ffffff", fg="#334155", font=("Segoe UI", 9), justify=tk.LEFT).grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=(8, 0))

        status_wrap = tk.LabelFrame(self, text="Bot Status", bg="#ffffff", fg="#111827", padx=8, pady=8)
        status_wrap.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))

        self.status_text = tk.Text(
            status_wrap, height=14, bg="#0b1220", fg="#dbeafe",
            wrap=tk.WORD, font=("Consolas", 10),
            state=tk.NORMAL, exportselection=True,
        )
        scrollbar = tk.Scrollbar(status_wrap, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        # Allow Ctrl+A to select all text in log for easy copy
        self.status_text.bind("<Control-a>", lambda e: (self.status_text.tag_add("sel", "1.0", tk.END), "break")[1])
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def update_profit_label(self):
        self.profit_label.config(text=f"Profit Target: {self.profit_var.get():.1f}%")

    def clear_log(self):
        self.status_text.delete("1.0", tk.END)

    def copy_log(self):
        text = self.status_text.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log_message("[Log] Copied to clipboard.")
        else:
            messagebox.showinfo("Copy Log", "Log is empty.")

    def save_log(self):
        text = self.status_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Save Log", "Log is empty.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"peakecoin_bot_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            title="Save Log File",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.log_message(f"[Log] Saved to {path}")

    def update_key_fields(self):
        for widget in self.keys_frame.winfo_children():
            widget.destroy()
        self.key_entries.clear()

        selected = [currency for currency, var in self.currency_vars.items() if var.get()]
        if not selected:
            tk.Label(self.keys_frame, text="Select at least one currency to enter keys.", bg="#f7f8fb", fg="#64748b").pack(anchor="w")
            return

        for currency in selected:
            row = tk.Frame(self.keys_frame, bg="#f7f8fb")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"Active Key for {currency}", bg="#f7f8fb", fg="#111827", width=18, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, width=58, show="*")
            entry.pack(side=tk.LEFT, padx=(8, 0))
            self.key_entries[currency] = entry

        token_options = ["PEK"] + selected
        if self.extra_micro_token_var.get() not in token_options:
            self.extra_micro_token_var.set("PEK")
        self._refresh_extra_token_menu(token_options)

    def _refresh_extra_token_menu(self, options):
        self.extra_micro_options = options
        menu = self.extra_micro_menu["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.extra_micro_token_var, option))

    def _to_market_symbol(self, token_alias):
        token_alias = (token_alias or "").strip().upper()
        if not token_alias:
            return "PEK"
        if token_alias.startswith("SWAP."):
            return token_alias
        if token_alias in self.TOKEN_ALIAS_TO_MARKET:
            return self.TOKEN_ALIAS_TO_MARKET[token_alias]
        return f"SWAP.{token_alias}"

    def _buy_micro_token(self, username, active_key, token_alias, reason):
        symbol = self._to_market_symbol(token_alias)
        market = get_orderbook_top(symbol)
        ask = float(market.get("lowestAsk", 0)) if market else 0.0
        if ask <= 0:
            ask = 0.00000001
        try:
            ok = place_order(
                username,
                symbol,
                ask,
                0.00000001,
                order_type="buy",
                active_key=active_key,
            )
            if ok:
                self.log_message(f"[{reason}] Micro buy submitted: 0.00000001 {symbol} @ {ask}")
            else:
                self.log_message(f"[{reason}] Micro buy skipped/failed: {symbol}")
        except Exception as exc:
            self.log_message(f"[{reason}] Micro buy exception for {symbol}: {exc}")

    def _append_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def log_message(self, message):
        self.after(0, self._append_status, message)

    def validate_input(self):
        username = self.username_entry.get().strip()
        selected = [c for c, v in self.currency_vars.items() if v.get()]
        keys = {c: self.key_entries[c].get().strip() for c in selected if c in self.key_entries}
        profit_target = self.profit_var.get()
        scalping_enabled = self.scalping_var.get()

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
            "username": username,
            "selected": selected,
            "keys": keys,
            "profit_target": profit_target,
            "scalping_enabled": scalping_enabled,
        }

    def _load_bot_module(self, currency):
        currency_bots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "currency_bots"))
        bot_file = f"uni_{currency.lower()}.py"
        bot_path = os.path.join(currency_bots_path, bot_file)

        if not os.path.exists(bot_path):
            raise FileNotFoundError(f"Bot file not found: {bot_file}")

        spec = importlib.util.spec_from_file_location(f"uni_{currency.lower()}", bot_path)
        bot_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bot_module)

        if not hasattr(bot_module, "run_bot"):
            raise AttributeError(f"run_bot function not found in {bot_file}")

        return bot_module

    def _record_profit_signals(self, currency, output):
        matches = re.findall(r"Profit percent:\s*([-+]?\d*\.?\d+)", output)
        if not matches:
            return

        with self.profit_lock:
            for m in matches:
                value = float(m)
                self.profit_events += 1
                self.total_profit_percent += value
                self.last_profit_percent = value
                stat = self.per_currency_stats.setdefault(currency, {"count": 0, "sum": 0.0})
                stat["count"] += 1
                stat["sum"] += value

        self.after(0, self._refresh_profit_ui)

    def _refresh_profit_ui(self):
        with self.profit_lock:
            events = self.profit_events
            total = self.total_profit_percent
            last = self.last_profit_percent
            per_currency = dict(self.per_currency_stats)

        avg = (total / events) if events else 0.0
        self.total_signals_var.set(f"Sell Signals: {events}")
        self.avg_profit_var.set(f"Average Profit Signal: {avg:.2f}%")
        self.cumulative_profit_var.set(f"Cumulative Profit Signal: {total:.2f}%")
        self.last_profit_var.set(f"Last Profit Signal: {last:.2f}%")

        if per_currency:
            parts = []
            for currency in sorted(per_currency.keys()):
                count = per_currency[currency]["count"]
                total_cur = per_currency[currency]["sum"]
                avg_cur = total_cur / count if count else 0.0
                parts.append(f"{currency}: avg {avg_cur:.2f}% ({count} signals)")
            self.currency_profit_var.set("Per-currency: " + " | ".join(parts))
        else:
            self.currency_profit_var.set("Per-currency: n/a")

    def _run_bot_cycle(self, bot_module, currency, username, active_key, profit_target, scalping_enabled=False):
        class _UILogWriter:
            def __init__(self, outer, bot_currency):
                self.outer = outer
                self.bot_currency = bot_currency
                self.buffer = ""
                self.full_text = []

            def write(self, text):
                if not text:
                    return
                self.buffer += text
                self.full_text.append(text)
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self.outer.log_message(f"[{self.bot_currency}] {line}")

            def flush(self):
                if self.buffer.strip():
                    self.outer.log_message(f"[{self.bot_currency}] {self.buffer.strip()}")
                self.buffer = ""

        writer = _UILogWriter(self, currency)
        cycle_started = time.time()
        self.log_message(f"[{currency}] Cycle started with target {profit_target:.1f}%")

        with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
            try:
                bot_module.run_bot(username, active_key, profit_target, scalping_enabled=scalping_enabled)
            except TypeError:
                # Fallback for bots that don't accept scalping_enabled yet
                try:
                    bot_module.run_bot(username, active_key, profit_target)
                except TypeError:
                    bot_module.run_bot(username, active_key)
            except Exception as exc:
                self.log_message(f"[{currency}] Bot runtime exception: {exc}")
                tb = traceback.format_exc().strip()
                if tb:
                    for line in tb.splitlines():
                        self.log_message(f"[{currency}] {line}")
                raise

        writer.flush()
        output = "".join(writer.full_text).strip()

        # Always buy micro PEK every cycle
        self._buy_micro_token(username, active_key, "PEK", f"{currency} cycle")

        # Optional extra token micro buy
        if self.enable_extra_micro_buy.get():
            extra_token = self.extra_micro_token_var.get().strip().upper()
            if extra_token and extra_token != "PEK":
                self._buy_micro_token(username, active_key, extra_token, f"{currency} extra")

        self._record_profit_signals(currency, output)
        cycle_seconds = time.time() - cycle_started
        self.log_message(f"[{currency}] Cycle finished in {cycle_seconds:.1f}s")

    def run_bot_continuous(self, currency, username, active_key, profit_target, scalping_enabled=False):
        try:
            bot_module = self._load_bot_module(currency)
            self.log_message(f"🚀 Starting {currency} bot (continuous)")
        except Exception as exc:
            self.log_message(f"❌ {currency} startup error: {exc}")
            return

        cycle_count = 0
        while self.running_bots.get(currency, False):
            cycle_count += 1
            self.log_message(f"🔄 {currency} cycle #{cycle_count}")
            try:
                self._run_bot_cycle(bot_module, currency, username, active_key, profit_target, scalping_enabled)
            except Exception as exc:
                self.log_message(f"⚠️ {currency} cycle error: {exc}")

            if self.running_bots.get(currency, False):
                time.sleep(3)

        self.log_message(f"🛑 {currency} stopped after {cycle_count} cycles")

    def run_bot_once(self, currency, username, active_key, profit_target, scalping_enabled=False):
        try:
            bot_module = self._load_bot_module(currency)
            self.log_message(f"▶️ Running {currency} once")
            self._run_bot_cycle(bot_module, currency, username, active_key, profit_target, scalping_enabled)
            self.log_message(f"✅ {currency} completed")
        except Exception as exc:
            self.log_message(f"❌ {currency} failed: {exc}")

    def start_bots(self):
        data = self.validate_input()
        if not data:
            return

        self.log_message(f"🛡️ Guaranteed-profit mode active at {data['profit_target']:.1f}% target.")
        scalping_enabled = data.get('scalping_enabled', False)

        if self.mode_var.get() == "continuous":
            self.log_message(f"Starting {len(data['selected'])} bot(s) in continuous mode")
            for currency in data["selected"]:
                self.running_bots[currency] = True
                thread = threading.Thread(
                    target=self.run_bot_continuous,
                    args=(currency, data["username"], data["keys"][currency], data["profit_target"], scalping_enabled),
                    daemon=True,
                )
                thread.start()
                self.bot_threads[currency] = thread

            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.log_message(f"Running {len(data['selected'])} bot(s) once")
            for currency in data["selected"]:
                thread = threading.Thread(
                    target=self.run_bot_once,
                    args=(currency, data["username"], data["keys"][currency], data["profit_target"], scalping_enabled),
                    daemon=True,
                )
                thread.start()

    def stop_bots(self):
        if not self.running_bots:
            return

        self.log_message("Stopping all continuous bots...")
        for currency in list(self.running_bots.keys()):
            self.running_bots[currency] = False

        time.sleep(1)
        self.running_bots.clear()
        self.bot_threads.clear()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("All bots stopped.")

    def on_closing(self):
        if self.running_bots:
            if messagebox.askokcancel("Quit", "Bots are still running. Stop and quit?"):
                self.stop_bots()
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = PlugAndPlayBotGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
