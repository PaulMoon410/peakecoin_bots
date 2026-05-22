import os
import signal
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Path to your main bot server process (adjust as needed)
BOT_PROCESS_NAME = "server_bot.py"

# Store the process handle globally
bot_process = None

def start_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        print("Bot already running. Restarting...")
        stop_bot()
    print("Starting bot process...")
    bot_process = subprocess.Popen([sys.executable, BOT_PROCESS_NAME])

def stop_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        print("Stopping bot process...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            bot_process.kill()
    bot_process = None

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/dashboard/restart":
            stop_bot()
            start_bot()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot restarted.")
        elif self.path == "/dashboard/shutdown":
            stop_bot()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot shut down.")
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>PeakeCoin Dashboard</h1><p>Use /dashboard/restart or /dashboard/shutdown</p>")

def run_dashboard_server(port=8090):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"Dashboard server running at http://localhost:{port}/dashboard/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard server stopped.")
        stop_bot()
        httpd.server_close()

if __name__ == "__main__":
    # Start the bot on dashboard server start
    start_bot()
    run_dashboard_server()
