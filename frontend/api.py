"""
Frontend API Bridge — 连接HTML前端到 Hermes Pipeline

启动: python frontend/api.py
访问: http://localhost:8000
"""
import os, sys, json, subprocess, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 缓存pipeline实例
_pipeline = None
def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from pipeline import HermesPipeline
        _pipeline = HermesPipeline()
    return _pipeline

def api_response(data, status=200):
    data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return status, {"Content-Type": "application/json; charset=utf-8"}, data_bytes

class FrontendHandler(SimpleHTTPRequestHandler):
    """HTTP处理器 — 静态文件 + API"""
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".css": "text/css",
        ".json": "application/json",
    }

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API路由
        if path == "/api/status":
            pipe = get_pipeline()
            s = pipe.stats()
            code, headers, body = api_response({
                "status": "ok",
                "database": s["database"],
                "output_dir": s["output_dir"],
                "pipeline": "HermesPipeline"
            })

        elif path == "/api/brands":
            pipe = get_pipeline()
            brands = pipe.db.list_brands()
            code, headers, body = api_response({"brands": brands})

        elif path.startswith("/api/brand/"):
            name = path.split("/api/brand/")[1]
            pipe = get_pipeline()
            brand = pipe.db.get_brand(name)
            knowledge = pipe.db.get_knowledge(name)
            code, headers, body = api_response({
                "brand": brand,
                "knowledge": knowledge
            })

        elif path == "/api/knowledge":
            pipe = get_pipeline()
            s = pipe.db.stats()
            patterns = pipe.db.search_patterns()
            cases = pipe.db.list_agency_cases(5)
            code, headers, body = api_response({
                "stats": s,
                "patterns": patterns[:10],
                "agency_cases": cases
            })

        # 静态文件
        else:
            if path == "/":
                path = "/index.html"
            file_path = os.path.join(ROOT, "frontend", path.lstrip("/"))
            if os.path.isfile(file_path):
                # 读取文件内容直接返回（避免编码问题）
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    ext = os.path.splitext(file_path)[1]
                    ct = self.extensions_map.get(ext, 'application/octet-stream')
                    code, headers, body = 200, {"Content-Type": ct}, content
                except Exception as e:
                    code, headers, body = api_response({"error": str(e)}, 500)
            else:
                code, headers, body = api_response({"error": "not found"}, 404)

        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len else "{}"
        data = json.loads(body) if body else {}
        parsed = urlparse(self.path)
        path = parsed.path

        pipe = get_pipeline()

        if path == "/api/research":
            brand = data.get("brand", "")
            category = data.get("category", "furniture")
            try:
                r = pipe.run(brand=brand, category=category)
                code, headers, body = api_response(r)
            except Exception as e:
                code, headers, body = api_response({"error": str(e)}, 500)

        elif path == "/api/generate":
            brand = data.get("brand", "product")
            category = data.get("category", "furniture")
            try:
                r = pipe.run(brand=brand, category=category)
                code, headers, body = api_response(r)
            except Exception as e:
                code, headers, body = api_response({"error": str(e)}, 500)

        elif path == "/api/evolution":
            try:
                from research.agency_researcher import FourAResearcher, EvolutionScheduler
                r = FourAResearcher(pipe.api_key)
                r.connect_knowledge_base(pipe.db)
                s = EvolutionScheduler(r, pipe.db)
                cycle = s.run_evolution_cycle()
                code, headers, body = api_response(cycle)
            except Exception as e:
                code, headers, body = api_response({"error": str(e)}, 500)

        else:
            code, headers, body = api_response({"error": "not found"}, 404)

        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"  🌐 {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    port = 8000
    server = HTTPServer(("0.0.0.0", port), FrontendHandler)
    print(f"\n  🚀 Hermes OS Dashboard")
    print(f"  ─────────────────────")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")
    webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
