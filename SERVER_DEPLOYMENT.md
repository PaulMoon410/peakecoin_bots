# Server Deployment Guide

This guide will help you deploy the PeakeCoin Bot on various server platforms using **Python directly** (recommended approach).

## ⭐ Recommended: Direct Python Deployment

### Linux/Ubuntu Server (Most Popular)

1. **Upload the bot files to your server:**
   ```bash
   scp -r plug_and_play_bot/ user@your-server:/home/user/
   ```

2. **Connect to your server and set up:**
   ```bash
   ssh user@your-server
   cd plug_and_play_bot
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Run the bot in continuous mode:**
   ```bash
   # Interactive setup (recommended)
   python server_bot.py
   
   # Or run in background immediately
   screen -S peakebot python server_bot.py
   # Press Ctrl+A then D to detach from screen
   ```

4. **Manage your running bot:**
   ```bash
   # View bot status
   screen -r peakebot
   
   # Stop bot (inside screen session)
   # Press Ctrl+C
   
   # List screen sessions
   screen -ls
   ```

### Windows Server

1. **Copy the bot folder to your Windows server**

2. **Run the setup script:**
   ```cmd
   setup.bat
   ```

3. **Run the bot:**
   ```cmd
   # Activate virtual environment
   venv\Scripts\activate
   
   # Run continuous server mode
   python server_bot.py
   ```

4. **For background operation on Windows:**
   ```cmd
   # Option 1: Use Task Scheduler (recommended)
   # Create a new task that runs: python server_bot.py
   
   # Option 2: Use PowerShell in background
   Start-Process python -ArgumentList "server_bot.py" -WindowStyle Hidden
   ```

### VPS/Cloud Hosting (DigitalOcean, Linode, AWS, etc.)

1. **Create a new droplet/instance with Ubuntu 20.04+ or similar**

2. **Update the system:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git screen -y
   ```

3. **Upload your bot files:**
   ```bash
   # Option 1: Upload via SCP
   scp -r plug_and_play_bot/ root@your-server-ip:/root/
   
   # Option 2: Clone from repository (if you have one)
   git clone https://your-repo/peakecoin-bot.git
   cd peakecoin-bot
   ```

4. **Setup and run:**
   ```bash
   cd plug_and_play_bot
   chmod +x setup.sh
   ./setup.sh
   
   # Start the bot
   python server_bot.py
   ```

### Quick One-Liner Setup for VPS
```bash
# Download, setup, and run (if you have a download link)
wget your-bot-download-link.zip && unzip peakebot.zip && cd plug_and_play_bot && chmod +x setup.sh && ./setup.sh && python server_bot.py
```

## Process Management (Keeping Bot Running 24/7)

## Environment File

Create a `.env` file from the example before starting the bot:

```bash
cp .env.example .env
```

Recommended server variables:

```bash
PORT=8080
REQUIRE_HTTPS=true
API_KEY_REQUIRED=true
WEB_API_KEY=replace-this
PEAKECOIN_USERNAME=your-account
PEAKECOIN_CURRENCIES=BTC,ETH
PEAKECOIN_ACTIVE_KEY_BTC=...
PEAKECOIN_ACTIVE_KEY_ETH=...
```

`server_bot.py` and `peake_droid.py` will use these values as defaults, so secrets can stay in environment variables instead of being typed interactively each run.

### Using systemd (Linux - Recommended for Production)

Create a service file `/etc/systemd/system/peakebot.service`:

```ini
[Unit]
Description=PeakeCoin Trading Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/plug_and_play_bot
Environment=PATH=/home/your-username/plug_and_play_bot/venv/bin
EnvironmentFile=/home/your-username/plug_and_play_bot/.env
ExecStart=/home/your-username/plug_and_play_bot/venv/bin/python server_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/peakebot.log
StandardError=append:/var/log/peakebot-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable peakebot
sudo systemctl start peakebot
sudo systemctl status peakebot

# View logs
sudo journalctl -u peakebot -f
```

### Using screen (Simple but Effective)
```bash
# Start bot in background
screen -S peakebot python server_bot.py

# Detach with Ctrl+A then D
# Reattach anytime with:
screen -r peakebot

# Kill session
screen -X -S peakebot quit
```

### Using PM2 (If you have Node.js)
```bash
npm install -g pm2
pm2 start "python server_bot.py" --name peakebot --interpreter python3
pm2 startup
pm2 save

# Manage
pm2 status
pm2 logs peakebot
pm2 restart peakebot
```

## Security Considerations

1. **Never share your private keys**
2. **Use environment variables for sensitive data**
3. **Set up firewall rules if needed**
4. **Keep your server updated**
5. **Use strong passwords and SSH keys**
6. **Do not commit `.env` files to source control**

## Monitoring Your Bot

### Real-time Status
```bash
# If using screen
screen -r peakebot

# If using systemd
sudo journalctl -u peakebot -f

# If using PM2
pm2 logs peakebot --lines 50
```

### Check if Bot is Running
```bash
# Check processes
ps aux | grep python
ps aux | grep server_bot

# Check specific screen session
screen -ls | grep peakebot

# Check systemd service
sudo systemctl status peakebot
```

### Bot Health Indicators
- Look for periodic log messages from each currency bot
- Check for "Resource Credits" messages
- Watch for trade cycle completions
- Monitor for error messages

## Troubleshooting

### Common Issues

1. **Bot not starting:**
   - Check Python version: `python3 --version` (need 3.11+)
   - Verify dependencies: `pip list | grep requests`
   - Check file permissions: `ls -la server_bot.py`

2. **Network/Connection issues:**
   - Test Hive node connectivity: `curl https://api.hive.blog`
   - Check internet connection
   - Verify firewall settings

3. **Permission/Key errors:**
   - Double-check active keys are correct
   - Ensure account has sufficient Resource Credits
   - Verify account exists and is active

4. **Resource issues:**
   - Monitor server CPU/memory: `htop`
   - Check disk space: `df -h`
   - Monitor bot resource usage

### Log Analysis
```bash
# Search for errors in systemd logs
sudo journalctl -u peakebot | grep -i error

# Search for specific currency activity
sudo journalctl -u peakebot | grep "BTC BOT"

# Check last 100 lines
sudo journalctl -u peakebot --lines 100
```

## Support

For additional support, refer to the main README.md or contact the PeakeCoin community.
