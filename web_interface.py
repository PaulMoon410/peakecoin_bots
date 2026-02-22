from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import subprocess
import json
import threading
import time

class BotWebInterface(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>PeakeCoin Bot Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .running { background-color: #d4edda; color: #155724; }
        .stopped { background-color: #f8d7da; color: #721c24; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background-color: #0056b3; }
        .log-area { background-color: #f8f9fa; padding: 15px; border-radius: 5px; height: 200px; overflow-y: scroll; font-family: monospace; font-size: 12px; }
        .currency-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 10px 0; }
        .currency-item { padding: 10px; background-color: #e9ecef; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 PeakeCoin Bot Server</h1>
        
        <div class="section">
            <h3>Server Status</h3>
            <div class="status running">✅ Server is running</div>
            <div>Server Time: <span id="serverTime"></span></div>
            <div>Bot Version: v1.0</div>
        </div>
        
        <div class="section">
            <h3>Available Currency Bots</h3>
            <div class="currency-list">
                <div class="currency-item">BTC</div>
                <div class="currency-item">ETH</div>
                <div class="currency-item">DOGE</div>
                <div class="currency-item">LTC</div>
                <div class="currency-item">TETHER</div>
                <div class="currency-item">HBD</div>
                <div class="currency-item">BLURT</div>
            </div>
        </div>
        
        <div class="section">
            <h3>How to Use</h3>
            <ol>
                <li><strong>Command Line:</strong> Run <code>python peake_droid.py</code> in the server terminal</li>
                <li><strong>Desktop GUI:</strong> Run <code>python main.py</code> (requires desktop environment)</li>
                <li><strong>Background Service:</strong> Use screen, tmux, or systemd for production</li>
            </ol>
        </div>
        
        <div class="section">
            <h3>Quick Start Commands</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace;">
                # Install dependencies<br>
                pip install -r requirements.txt<br><br>
                
                # Run command-line version<br>
                python peake_droid.py<br><br>
                
                # Run in background (Linux/Mac)<br>
                screen -S peakebot python peake_droid.py<br><br>
                
                # Check running screens<br>
                screen -ls
            </div>
        </div>
        
        <div class="section">
            <h3>Important Notes</h3>
            <ul>
                <li>🔐 <strong>Security:</strong> Never share your private keys</li>
                <li>⚡ <strong>Resources:</strong> Monitor your Hive Resource Credits</li>
                <li>📊 <strong>Profit:</strong> Set realistic profit targets (0.5% - 20%)</li>
                <li>🔄 <strong>Monitoring:</strong> Check bot status regularly</li>
                <li>💾 <strong>Backup:</strong> Keep backups of your configuration</li>
            </ul>
        </div>
        
        <div class="section">
            <h3>Support</h3>
            <p>For help and support, join the PeakeCoin community or refer to the documentation files:</p>
            <ul>
                <li>README.md - Basic usage guide</li>
                <li>SERVER_DEPLOYMENT.md - Server setup guide</li>
            </ul>
        </div>
    </div>
    
    <script>
        function updateTime() {
            document.getElementById('serverTime').textContent = new Date().toLocaleString();
        }
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
            """
            self.wfile.write(html_content.encode())
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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_web_server(port)
