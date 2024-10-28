from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Authorization')
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()
httpd = HTTPServer(('localhost', 8000), CORSRequestHandler)
print("Server running on http://localhost:8000")
httpd.serve_forever()