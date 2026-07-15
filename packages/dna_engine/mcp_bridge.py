"""
设计审美自进化桥接层 — 通过 MCP 协议连接设计指南服务
"""
import os
import json
import subprocess
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from queue import Queue


class MCPClient:
    """MCP JSON-RPC 2.0 客户端 — 通过 stdin/stdout 通信"""

    def __init__(self, command: List[str]):
        self.command = command
        self.proc: Optional[subprocess.Popen] = None
        self._msg_id = 0
        self._lock = threading.Lock()

    def start(self):
        if self.proc is None:
            self.proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def call_tool(self, name: str, arguments: Optional[Dict] = None) -> Dict:
        self.start()
        with self._lock:
            self._msg_id += 1
            msg_id = self._msg_id
            payload = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "tools/call",
                "params": {"name": name},
            }
            if arguments:
                payload["params"]["arguments"] = arguments

            if self.proc and self.proc.stdin:
                self.proc.stdin.write(json.dumps(payload) + "\n")
                self.proc.stdin.flush()

                response = self.proc.stdout.readline() if self.proc.stdout else ""
                if response:
                    try:
                        return json.loads(response.strip())
                    except:
                        return {"error": f"Parse error: {response[:200]}"}
        return {"error": "No response"}

    def __del__(self):
        self.stop()


class DesignMCPBridge:
    """连接 MCP Page Design Guide 与品牌 DNA 系统的桥接层"""

    def __init__(self, knowledge_base=None, trend_tracker=None):
        self.knowledge = knowledge_base
        self.trend_tracker = trend_tracker
        # try npx.cmd first (Windows), fall back to npx
        import shutil
        npx = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
        self.client = MCPClient([npx, "-y", "page-design-guide-mcp"])
        self._cache: Dict[str, Any] = {}

    def _call(self, tool: str, args: Optional[Dict] = None) -> Dict:
        """带缓存的MCP调用"""
        cache_key = f"{tool}:{json.dumps(args or {})}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        result = self.client.call_tool(tool, args)
        self._cache[cache_key] = result
        return result

    def learn_current_trends(self) -> Dict[str, Any]:
        return {
            "trends": self._call("get_modern_trends"),
            "palettes": self._call("get_modern_palettes"),
            "learned_at": datetime.utcnow().isoformat(),
        }

    def learn_layout_patterns(self) -> Dict[str, Any]:
        return self._call("get_layout_patterns")

    def learn_color_psychology(self) -> Dict[str, Any]:
        return self._call("get_color_guidance")

    def learn_typography(self) -> Dict[str, Any]:
        return self._call("get_typography_guidance")

    def evaluate_design(self, description: str) -> Dict[str, Any]:
        return self._call("get_holistic_design_review", {"design_description": description})

    def get_section_advice(self, section: str) -> Dict[str, Any]:
        return self._call("get_section_guidance", {"section_type": section})

    def evolve_brand_knowledge(self, brand: str) -> Dict:
        results = {}
        for name, method in [
            ("trends", self.learn_current_trends),
            ("layouts", self.learn_layout_patterns),
            ("colors", self.learn_color_psychology),
            ("typography", self.learn_typography),
        ]:
            results[name] = method()
        if self.knowledge:
            for k, v in results.items():
                self.knowledge.save_knowledge(brand, f"mcp_{k}", v)
        return results

    def close(self):
        self.client.stop()


class SelfEvolutionEngine:
    """自进化引擎"""

    def __init__(self, bridge: DesignMCPBridge):
        self.bridge = bridge
        self.log: List[Dict] = []

    def run_evolution_cycle(self, brand: str = "norhor") -> Dict:
        print(f"  🔄 自进化: {brand}")
        cycle = {"brand": brand, "started_at": datetime.utcnow().isoformat(), "steps": {}}
        
        for name, label, method_name in [
            ("trends", "趋势", "learn_current_trends"),
            ("layouts", "版式", "learn_layout_patterns"),
            ("colors", "色彩", "learn_color_psychology"),
            ("typography", "字体", "learn_typography"),
        ]:
            print(f"  📈 学习{label}...", end=" ")
            try:
                r = getattr(self.bridge, method_name)()
                ok = not (isinstance(r, dict) and "error" in r)
                cycle["steps"][name] = "✅" if ok else "❌"
                print("✅" if ok else "❌")
            except Exception as e:
                cycle["steps"][name] = f"❌ {e}"
                print("❌")

        cycle["completed_at"] = datetime.utcnow().isoformat()
        self.log.append(cycle)
        ok = sum(1 for s in cycle["steps"].values() if s == "✅")
        print(f"  ✅ 完成: {ok}/{len(cycle['steps'])}")
        return cycle
