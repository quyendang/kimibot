"""Lightweight HTTP health-check server for Railway / uptime monitors."""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from eth_signal_bot.core import config


class _HealthHandler(BaseHTTPRequestHandler):
    """Respond to GET / with a plain OK status."""

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            body = b"OK\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"Not Found\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        # keep Railway logs clean
        pass


def start_health_server():
    """Start the health server in a background daemon thread."""
    server = HTTPServer((config.HEALTH_HOST, config.HEALTH_PORT), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"   Health server listening on http://{config.HEALTH_HOST}:{config.HEALTH_PORT}")
