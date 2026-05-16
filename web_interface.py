from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import subprocess
import json
import threading
import time

from utils.settings import API_KEY_REQUIRED, REQUIRE_HTTPS, SERVER_PORT, WEB_API_KEY

class BotWebInterface(SimpleHTTPRequestHandler):
    def _send_common_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'same-origin')

    def _is_https_request(self):
        forwarded_proto = self.headers.get('X-Forwarded-Proto', '')
        return forwarded_proto.lower() == 'https'

    def _redirect_to_https(self):
        host = self.headers.get('Host', 'localhost')
        location = f"https://{host}{self.path}"
        self.send_response(301)
        self.send_header('Location', location)
        self._send_common_headers()
        self.end_headers()

    def _authorize_request(self):
        if not API_KEY_REQUIRED:
            return True
        if not WEB_API_KEY:
            return False
        supplied_key = self.headers.get('X-API-Key', '')
        return supplied_key == WEB_API_KEY

    VERSION = "0.00000003"  # Auto-incremented on each push
    def do_GET(self):
        if REQUIRE_HTTPS and not self._is_https_request():
            self._redirect_to_https()
            return

        # Handle bot start with scalping option
        if self.path.startswith('/start_bot'):
            from urllib.parse import urlparse, parse_qs
            query = urlparse(self.path).query
            params = parse_qs(query)
            bot = params.get('bot', [''])[0]
            scalping = params.get('scalping', ['false'])[0].lower() == 'true'
            # Here you would start the bot with the scalping option
            print(f"[WEB] Start bot: {bot}, Scalping: {scalping}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._send_common_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'started', 'bot': bot, 'scalping': scalping}).encode())
            return

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self._send_common_headers()
            self.end_headers()
            html_content = """
            <!DOCTYPE html>
            <html lang='en'>
            <head>
                <meta charset='UTF-8'>
                <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                <title>__VERSION__</title>
                <link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap' rel='stylesheet'>
                <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>
                <style>
                    body { font-family: 'Inter', Arial, sans-serif; background: linear-gradient(120deg, #0f172a 0%, #0ea5e9 100%); min-height: 100vh; margin: 0; }
                    .container { max-width: 700px; margin: 40px auto; background: rgba(30,41,59,0.8); border-radius: 18px; box-shadow: 0 12px 48px rgba(14,165,233,0.18), 0 2px 8px rgba(0,0,0,0.12); padding: 40px 32px 32px 32px; text-align: center; color: #fff; }
                    h1 { font-size: 2.2em; margin-bottom: 0.15em; font-weight: 900; background: linear-gradient(90deg, #38bdf8 0%, #fbbf24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
                    .section { margin: 22px 0; padding: 18px; background: rgba(255,255,255,0.05); border-radius: 10px; }
                    .status { padding: 10px; border-radius: 5px; margin: 10px 0; font-weight: 600; }
                    .running { background-color: #22c55e33; color: #22c55e; }
                    .stopped { background-color: #ef444433; color: #ef4444; }
                    button { background-color: #0ea5e9; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; font-weight: 600; }
                    button:hover { background-color: #0369a1; }
                    .currency-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 10px 0; }
                    .currency-item { padding: 10px; background-color: #334155; border-radius: 5px; text-align: center; font-weight: 600; }
                    .log-area { background-color: #0f172a; padding: 15px; border-radius: 5px; height: 180px; overflow-y: scroll; font-family: monospace; font-size: 13px; color: #fbbf24; text-align: left; }
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='section'>
                        <h3>Login Options</h3>
                        <div style="margin-bottom: 12px;">
                            <button id="keychainLoginBtn" onclick="hiveKeychainLogin()">Login with Hive Keychain</button>
                            <button id="recheckKeychainBtn" onclick="recheckKeychain()" style="margin-left:10px;">Re-check for Hive Keychain</button>
                            <div id="keychainStatus" style="margin-top:10px;"></div>
                            <div id="keychainDebug" style="margin-top:10px; color:#fbbf24; font-size:13px;"></div>
                        </div>
                        <div style="margin-bottom: 8px;">
                            <input type="text" id="manualUsername" placeholder="Hive username" style="padding:6px; border-radius:4px; border:1px solid #ccc; width:140px;">
                            <input type="password" id="manualActiveKey" placeholder="Active key" style="padding:6px; border-radius:4px; border:1px solid #ccc; width:220px;">
                            <button onclick="manualLogin()">Manual Login</button>
                        </div>
                        <div id="manualLoginStatus" style="margin-top:8px;"></div>
                    </div>
                    <h1>🚀 PeakeCoin Bot Dashboard</h1>
                    <div class='section'>
                        <h3>Server Status</h3>
                        <div class='status running'>✅ Server is running</div>
                        <div>Server Time: <span id='serverTime'></span></div>
                        <div>Bot Version: v1.0</div>
                        <div id="statusDetails" style="margin-top:10px;text-align:left;font-size:15px;">
                            <div>Storage: <span id="storageStatus">PeakeCoin Servers</span></div>
                            <div>Python Engine: <span id="pythonStatus">Checking...</span></div>
                            <div>Node Server: <span id="nodeStatus">Checking...</span></div>
                        </div>
                    </div>
                    <div class='section'>
                        <h3>Available Currency Bots</h3>
                        <div style="margin-bottom:10px;text-align:left;">
                            <input type="checkbox" id="scalpingToggle" style="transform:scale(1.2);margin-right:8px;">
                            <label for="scalpingToggle" style="font-weight:600;color:#0ea5e9;">Enable Scalping Logic (buy/sell small quantities at close range)</label>
                        </div>
                        <div class='currency-list' id='botList'>
                            <div class='currency-item'>BTC <button onclick="startBot('BTC')">Start</button> <button onclick="stopBot('BTC')">Stop</button></div>
                            <div class='currency-item'>ETH <button onclick="startBot('ETH')">Start</button> <button onclick="stopBot('ETH')">Stop</button></div>
                            <div class='currency-item'>DOGE <button onclick="startBot('DOGE')">Start</button> <button onclick="stopBot('DOGE')">Stop</button></div>
                            <div class='currency-item'>LTC <button onclick="startBot('LTC')">Start</button> <button onclick="stopBot('LTC')">Stop</button></div>
                            <div class='currency-item'>TETHER <button onclick="startBot('TETHER')">Start</button> <button onclick="stopBot('TETHER')">Stop</button></div>
                            <div class='currency-item'>HBD <button onclick="startBot('HBD')">Start</button> <button onclick="stopBot('HBD')">Stop</button></div>
                            <div class='currency-item'>BLURT <button onclick="startBot('BLURT')">Start</button> <button onclick="stopBot('BLURT')">Stop</button></div>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class='section'>
                            <h3>Bot Logs</h3>
                            <div class='log-area' id='logArea'>Waiting for logs...</div>
                        </div>
                        <div class='section'>
                            <h3>How to Use</h3>
                            <ol style='text-align:left;'>
                                <li><strong>Command Line:</strong> Run <code>python peake_droid.py</code> in the server terminal</li>
                                <li><strong>Desktop GUI:</strong> Run <code>python main.py</code> (requires desktop environment)</li>
                                <li><strong>Background Service:</strong> Use screen, tmux, or systemd for production</li>
                            </ol>
                        </div>
                        <div class='section'>
                            <h3>Support</h3>
                            <p>For help and support, join the PeakeCoin community or refer to the documentation files:</p>
                            <ul style='text-align:left;'>
                                <li>README.md - Basic usage guide</li>
                                <li>SERVER_DEPLOYMENT.md - Server setup guide</li>
                            </ul>
                        </div>
                    </div>
                    <script>
                    // Simulate status checks (replace with real API calls as needed)
                    function checkKeychainExtension(showStatus) {
                        var debug = [];
                        debug.push('Protocol: ' + window.location.protocol);
                        var hasKeychain = (typeof window.hive_keychain !== 'undefined');
                        debug.push('window.hive_keychain: ' + hasKeychain);
                        debug.push('window keys: ' + Object.keys(window).filter(k => k.toLowerCase().includes('keychain')).join(','));
                        // Try to read CSP header via meta tag (not always possible)
                        var csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                        if (csp) {
                            debug.push('CSP meta: ' + csp.getAttribute('content'));
                        } else {
                            debug.push('CSP meta: not present');
                        }
                        document.getElementById('keychainDebug').textContent = debug.join(' | ');
                        // Disable button if extension not detected
                        var btn = document.getElementById('keychainLoginBtn');
                        if (!hasKeychain) {
                            btn.disabled = true;
                            btn.textContent = 'Hive Keychain Not Detected';
                            if (showStatus) document.getElementById('keychainStatus').textContent = '❌ Hive Keychain browser extension is not installed or enabled.';
                        } else {
                            btn.disabled = false;
                            btn.textContent = 'Login with Hive Keychain';
                            if (showStatus) document.getElementById('keychainStatus').textContent = '';
                        }
                    }
                    function recheckKeychain() {
                        checkKeychainExtension(true);
                    }
                    window.addEventListener('DOMContentLoaded', function() {
                        // Simulate Python Engine status
                        setTimeout(function() {
                            document.getElementById('pythonStatus').textContent = 'Online';
                        }, 1000);
                        // Simulate Node Server status
                        setTimeout(function() {
                            document.getElementById('nodeStatus').textContent = 'Connected';
                        }, 1200);
                        checkKeychainExtension(true);
                        // Delayed re-check in case extension injects late
                        setTimeout(function() { checkKeychainExtension(false); }, 1500);
                        setTimeout(function() { checkKeychainExtension(false); }, 3000);
                    });

                    function hiveKeychainLogin() {
                        document.getElementById('keychainStatus').textContent = '';
                        var username = document.getElementById('manualUsername').value.trim();
                        if (!username) {
                            document.getElementById('keychainStatus').textContent = `❌ Please enter your Hive username above first.`;
                            return;
                        }
                        if (window.hive_keychain) {
                            window.hive_keychain.requestSignBuffer(username, `Login to PeakeCoin Bot Dashboard`, 'Posting', function(response) {
                                if (response.success) {
                                    document.getElementById('keychainStatus').textContent = `✅ Logged in as ${username}`;
                                } else {
                                    document.getElementById('keychainStatus').textContent = `❌ Login failed or cancelled.`;
                                }
                            });
                        } else {
                            document.getElementById('keychainStatus').textContent = `❌ Hive Keychain extension not detected.`;
                        }
                    }

                    function manualLogin() {
                        document.getElementById('manualLoginStatus').textContent = '';
                        var username = document.getElementById('manualUsername').value.trim();
                        var key = document.getElementById('manualActiveKey').value.trim();
                        if (!username || !key) {
                            document.getElementById('manualLoginStatus').textContent = `❌ Please enter both username and active key.`;
                            return;
                        }
                        // Basic validation: active key should start with '5' and be 51 chars
                        if (!/^5[HJK][1-9A-Za-z]{49}$/.test(key)) {
                            document.getElementById('manualLoginStatus').textContent = `❌ Invalid active key format.`;
                            return;
                        }
                        document.getElementById('manualLoginStatus').textContent = `✅ Logged in as ${username} (manual key)`;
                        // In a real app, store securely in session/localStorage or send to backend as needed
                    }
                    function updateTime() {
                        document.getElementById('serverTime').textContent = new Date().toLocaleString();
                    }
                    updateTime();
                    setInterval(updateTime, 1000);
                    function startBot(bot) {
                        var scalping = document.getElementById('scalpingToggle').checked;
                        logMsg(`Starting ${bot} bot... Scalping: ${scalping ? 'ENABLED' : 'DISABLED'}`);
                        // Send scalping option to backend
                        fetch(`/start_bot?bot=${encodeURIComponent(bot)}&scalping=${scalping}`)
                            .then(response => response.json())
                            .then(data => {
                                logMsg(`Backend: ${JSON.stringify(data)}`);
                            })
                            .catch(err => {
                                logMsg(`Backend error: ${err}`);
                            });
                    }
                    function stopBot(bot) {
                        logMsg(`Stopping ${bot} bot... (API integration needed)`);
                    }
                    function logMsg(msg) {
                        var logArea = document.getElementById('logArea');
                        logArea.textContent += `\n${new Date().toLocaleTimeString()} - ${msg}`;
                        logArea.scrollTop = logArea.scrollHeight;
                    }
                    </script>
                </body>
                </html>
                """
            html_content = html_content.replace("__VERSION__", self.VERSION)
            self.wfile.write(html_content.encode())
        else:
            # Redirect to the latest versioned HTML if root is accessed
            if self.path == '/':
                self.send_response(302)
                self.send_header('Location', versioned_path)
                self.end_headers()
            else:
                super().do_GET()

def start_web_server(port=8080):
    """Start the web interface server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, BotWebInterface)
    print(f"🌐 PeakeCoin Bot Web Interface started at http://localhost:{port}")
    print("📝 This interface provides information about your bot setup")
    print("⚡ To run the actual trading bot, use: python peake_droid.py")
    print("🛑 Press Ctrl+C to stop the web server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped")
        httpd.server_close()

if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 0))
    if not port:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER_PORT
    start_web_server(port)
