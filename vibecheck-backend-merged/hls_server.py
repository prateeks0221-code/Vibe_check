#!/usr/bin/env python3
"""Simple HLS server with CORS and no-cache headers."""
import http.server
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
DIRECTORY = sys.argv[2] if len(sys.argv) > 2 else "hls"

class HLSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress verbose logs
        pass

with socketserver.TCPServer(("", PORT), HLSHandler) as httpd:
    print(f"HLS server on port {PORT} serving {DIRECTORY}")
    httpd.serve_forever()
