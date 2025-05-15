import signal
import sys
from http.server import HTTPServer, CGIHTTPRequestHandler

class MyCGIHandler(CGIHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

PORT = 4000
httpd = HTTPServer(("localhost", PORT), MyCGIHandler)

def graceful_shutdown(signum, frame):
    print("\nShutting down server...")
    httpd.shutdown()       # Завершает serve_forever()
    httpd.server_close()   # Закрывает сокет
    print("Server stopped.")
    sys.exit(0)

# Перехватываем Ctrl+C (SIGINT) и kill (SIGTERM)
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

print(f"Serving on http://localhost:{PORT}")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    graceful_shutdown(None, None)