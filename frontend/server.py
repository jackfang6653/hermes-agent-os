"""
Frontend API Bridge — Mini
简化版，排除路径编码问题
"""
import os, sys, json
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, "frontend")

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = "/index.html" if self.path == "/" else self.path
        filepath = os.path.normpath(os.path.join(FRONTEND, path.lstrip("/")))
        
        # API
        if path == "/api/status":
            self._json({"status": "ok", "message": "Hermes OS Dashboard"})
            return
            
        # Static file
        if os.path.isfile(filepath):
            self._file(filepath)
            return
            
        self._json({"error": "not found"}, 404)
    
    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def _file(self, path):
        ext_map = {".html": "text/html", ".js": "application/javascript", ".css": "text/css", ".png": "image/png"}
        ext = os.path.splitext(path)[1]
        ct = ext_map.get(ext, "application/octet-stream")
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"  🌐 {args[0]} {args[1]} {args[2]}")

port = 8000
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
