"""
Frontend Server — 完整版 API + 静态文件
"""
import os, sys, json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, "frontend")
sys.path.insert(0, ROOT)

# Lazy-loaded pipeline
_pipeline = None
def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from pipeline import HermesPipeline
        _pipeline = HermesPipeline()
    return _pipeline

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8"}

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path):
        ext = os.path.splitext(path)[1]
        ct = self.extensions_map.get(ext, "application/octet-stream")
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        print(f"  GET {path}")

        # API routes
        if path == "/api/status":
            pipe = get_pipeline()
            s = pipe.stats()
            return self._json({"status":"ok","database":s["database"],"output_dir":s["output_dir"]})
        if path == "/api/brands":
            pipe = get_pipeline()
            return self._json({"brands": pipe.db.list_brands()})
        if path.startswith("/api/brand/"):
            name = path.split("/api/brand/")[1]
            pipe = get_pipeline()
            return self._json({"brand": pipe.db.get_brand(name), "knowledge": pipe.db.get_knowledge(name)})
        if path == "/api/knowledge":
            pipe = get_pipeline()
            return self._json({"stats": pipe.db.stats(), "patterns": pipe.db.search_patterns()[:10],
                               "agency_cases": pipe.db.list_agency_cases(5)})

        # Static files
        if path == "/": path = "/index.html"
        filepath = os.path.normpath(os.path.join(FRONTEND, path.lstrip("/")))
        if os.path.isfile(filepath) and filepath.startswith(FRONTEND):
            return self._file(filepath)
        self._json({"error":"not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        print(f"  POST {path}")
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len else "{}"
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        pipe = get_pipeline()

        if path == "/api/deep-research":
            try:
                from hermes_os.research.deep_researcher import DeepBrandResearcher
                r = DeepBrandResearcher(pipe.api_key)
                result = r.full_research(data.get("brand",""), data.get("category",""))
                r.save_result(result)
                return self._json(result)
            except Exception as e:
                return self._json({"error":str(e)}, 500)
        if path == "/api/research":
            try:
                r = pipe.run(brand=data.get("brand",""), category=data.get("category","furniture"))
                return self._json(r)
            except Exception as e:
                return self._json({"error":str(e)}, 500)
        if path == "/api/generate":
            try:
                r = pipe.run(brand=data.get("brand","product"), category=data.get("category","furniture"))
                return self._json(r)
            except Exception as e:
                return self._json({"error":str(e)}, 500)
        if path == "/api/evolution":
            try:
                from research.agency_researcher import FourAResearcher, EvolutionScheduler
                r = FourAResearcher(pipe.api_key)
                r.connect_knowledge_base(pipe.db)
                s = EvolutionScheduler(r, pipe.db)
                cycle = s.run_evolution_cycle()
                return self._json(cycle)
            except Exception as e:
                return self._json({"error":str(e)}, 500)
        if path.startswith("/api/mcp/"):
            tool = path.split("/api/mcp/")[1]
            try:
                from dna_engine.mcp_bridge import DesignMCPBridge
                bridge = DesignMCPBridge()
                tool_map = {
                    "trends": bridge.learn_current_trends,
                    "palettes": lambda: bridge._call("get_modern_palettes", {"category":"warm"}),
                    "typography": lambda: bridge._call("get_typography_guidance", {}),
                    "layout": lambda: bridge._call("get_layout_patterns", {}),
                    "color": lambda: bridge._call("get_color_guidance", {}),
                    "accessibility": lambda: bridge._call("get_accessibility_guidance", {}),
                    "components": lambda: bridge._call("get_component_guidance", {}),
                    "animation": lambda: bridge._call("get_animation_guidance", {}),
                    "responsive": lambda: bridge._call("get_responsive_guidance", {}),
                    "section": lambda: bridge._call("get_section_guidance", {}),
                    "principles": lambda: bridge._call("get_design_principles", {}),
                    "inspiration": lambda: bridge._call("get_inspiration_by_mood", {}),
                    "holistic": lambda: bridge._call("get_holistic_design_review", {}),
                }
                fn = tool_map.get(tool)
                if fn:
                    result = fn()
                    return self._json(result)
                return self._json({"error":"unknown tool"}, 404)
            except Exception as e:
                return self._json({"error":str(e)}, 500)
        self._json({"error":"not found"}, 404)

    def log_message(self, fmt, *args):
        print(f"  🌐 {args[0]} {args[1]} {args[2]}")

if __name__ == "__main__":
    port = 8000
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
