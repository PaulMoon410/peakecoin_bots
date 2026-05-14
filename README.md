# PeakeCoin Plug and Play Bot

## Overview
This is the official PeakeCoin trading bot suite. It supports Windows, Linux, Mac, Android, and server deployment. The bot can be run with a graphical interface (desktop), as a command-line tool, or hosted on a server for 24/7 operation.

---

## Features
- Trade multiple PeakeCoin-supported currencies (BTC, ETH, DOGE, LTC, TETHER, HBD, BLURT)
- Set your profit percentage target (0.5% - 20%)
- **Multiple Operation Modes:**
  - **Desktop GUI** (`main.py`) - Simple interface for one-time runs
  - **Server GUI** (`main_server.py`) - Enhanced interface with continuous mode
  - **Command Line** (`peake_droid.py`) - Interactive single-run mode
  - **Server Mode** (`server_bot.py`) - Continuous trading for 24/7 operation
- Server deployment for 24/7 operation
- Web interface for server monitoring
- Resource credit monitoring
- Real-time status logging

---

## Server Deployment 🚀

### ⚡ Super Quick Server Setup
```bash
# One-command server deployment
chmod +x deploy_server.sh && ./deploy_server.sh
```

### Manual Server Setup
1. **Upload to your server:**
   ```bash
   # Linux/Mac
   ./setup.sh
   
   # Windows
   setup.bat
   ```

2. **Run the bot:**
   ```bash
   # Quick launcher (interactive menu)
   ./launch.sh
   
   # Or run directly:
   python server_bot.py        # ⭐ RECOMMENDED for servers
   python main_server.py       # GUI with continuous option
   python web_interface.py     # Web interface only
   ```

3. **Background operation:**
   ```bash
   # Using screen (recommended for servers)
   screen -S peakebot python server_bot.py
   
   # Using launcher script
   ./launch.sh  # Select option 6 for background
   ```

📖 **See [SERVER_DEPLOYMENT.md](SERVER_DEPLOYMENT.md) for detailed server setup instructions**

---

## Understanding Bot Modes 🤖

### Single Run Mode
- **Who:** Desktop users wanting to run trades occasionally
- **Files:** `main.py`, `peake_droid.py`
- **Behavior:** Runs each selected bot once and stops
- **Best for:** Testing, manual trading sessions

### Continuous Mode  
- **Who:** Server operators, 24/7 traders
- **Files:** `main_server.py`, `server_bot.py`
- **Behavior:** Keeps running bots in loops until manually stopped
- **Best for:** Automated trading, server deployment

### Mode Comparison
| Feature | Single Run | Continuous |
|---------|------------|------------|
| Runs once | ✅ | ❌ |
| Runs continuously | ❌ | ✅ |
| GUI available | ✅ | ✅ |
| Server friendly | ❌ | ✅ |
| Good for testing | ✅ | ❌ |
| Good for production | ❌ | ✅ |

---
- Server deployment for 24/7 operation
- Web interface for server monitoring
- Docker support for easy deployment
- Resource credit monitoring

---

## Quick Start (Desktop)
1. **Install Python 3.11+**
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Optional: create an environment file for secrets and deployment settings:**
   ```
   cp .env.example .env
   ```
   Use `.env` for server port, HTTPS/API protection, username defaults, and active keys.
4. **Choose your interface:**
   ```
   python main.py          # Simple GUI (single runs)
   python main_server.py   # Enhanced GUI (single + continuous)
   python peake_droid.py   # Command line (single run)
   python server_bot.py    # Server mode (continuous)
   ```
4. **Fill in your username, select currencies, enter keys, and set your profit target.**

> **💡 For 24/7 trading:** Use `main_server.py` (GUI) or `server_bot.py` (command line) and select continuous mode.

## Environment Variables

The bot now loads `.env` automatically from the project root.

Common settings:
```bash
cp .env.example .env
```

Useful variables:
- `PORT` or `SERVER_PORT` for Render and other hosted platforms
- `REQUIRE_HTTPS=true` to force HTTPS redirects behind a proxy
- `API_KEY_REQUIRED=true` and `WEB_API_KEY=...` to protect the web interface
- `PEAKECOIN_USERNAME=...` to avoid retyping the account name
- `PEAKECOIN_CURRENCIES=BTC,ETH` to preselect server/CLI currencies
- `PEAKECOIN_ACTIVE_KEY_BTC=...` and similar per-currency active keys

When `PEAKECOIN_ACTIVE_KEY_<CURRENCY>` variables are present, the CLI and server modes will use them as defaults instead of requiring you to type secrets every run.

## Render Notes

For a Render web service:
- Build command: `pip install -r requirements.txt`
- Start command: `python web_interface.py`
- Set environment variables in the Render dashboard instead of committing `.env`
- Render supplies `PORT` automatically; the app now respects it

---

## Quick Start (Android)
1. **Install Pydroid 3** from Google Play Store.
2. **Transfer the bot folder** (including all subfolders and files) to your phone.
3. **Install dependencies:**
   - Open Pydroid 3, go to Pip, and install `requests`.
4. **Run the command-line version:**
   - Open Pydroid 3, open `peake_droid.py`, and tap Run.
   - Follow the prompts in the terminal.

> **Note:** The GUI (main.py) will not work on Android. Use `peake_droid.py` for command-line operation.

---

## Creating a Standalone .exe (Windows)
1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   pyinstaller --onefile --windowed main.py
   ```
3. The .exe will be in the `dist` folder. Distribute it with the `currency_bots/` and `utils/` folders.

---

## Folders and Files
- `main.py` — GUI for desktop
- `peake_droid.py` — Command-line version for Android/terminal
- `currency_bots/` — Individual currency trading bots
- `utils/` — Utility functions

---

## Support
- 📖 **Documentation:** README.md, SERVER_DEPLOYMENT.md
- 🌐 **Web Interface:** Run `python web_interface.py` for server status
- 💬 **Community:** Visit the PeakeCoin community for help
- 🔒 **Security:** Always keep your keys secure!
- 🆕 **Updates:** Check for new currency support and features

**New in this version:** SWAP.BLURT support added!

## Linux GUI Note

The Tk desktop apps use the system Tk package. On Linux, install it with your OS package manager, for example:

```bash
sudo apt-get install python3-tk
```
