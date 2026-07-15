"""
模型健康检查与自动修复引擎

功能:
1. 定期检查所有配置模型的可用性
2. 模型失效时自动切换到可用备用模型
3. 记录模型健康历史
4. 发出告警
"""
import os, json, requests, time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ModelHealth:
    """单个模型的健康状态"""
    name: str
    provider: str
    status: str = "unknown"      # healthy / degraded / dead
    latency_ms: float = 0
    last_checked: str = ""
    error_count: int = 0
    success_count: int = 0
    last_error: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    @property
    def health_score(self) -> float:
        total = self.success_count + self.error_count
        if total == 0:
            return 0.5
        return self.success_count / total


class ModelHealthMonitor:
    """模型健康监控器"""

    PROVIDERS = {
        "deepseek": {
            "url": "https://api.deepseek.com/chat/completions",
            "key_env": "DEEPSEEK_API_KEY",
            "header_key": "Authorization",
            "header_prefix": "Bearer ",
        },
        "openrouter": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key_env": "OPENROUTER_API_KEY",
            "header_key": "Authorization",
            "header_prefix": "Bearer ",
        },
        "openai": {
            "url": "https://api.openai.com/v1/chat/completions",
            "key_env": "OPENAI_API_KEY",
            "header_key": "Authorization",
            "header_prefix": "Bearer ",
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        self.health_map: Dict[str, ModelHealth] = {}
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "model_health.json"
        )
        self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.health_map[k] = ModelHealth(**v)
            except:
                pass

    def _save(self):
        with open(self.config_path, "w") as f:
            json.dump({k: v.__dict__ for k, v in self.health_map.items()},
                      f, indent=2, default=str)

    def check_model(self, model_name: str, provider: str,
                    test_prompt: str = "respond with only: ok") -> ModelHealth:
        """检查单个模型的健康状态"""
        key = f"{provider}/{model_name}"
        
        prov = self.PROVIDERS.get(provider)
        if not prov:
            return ModelHealth(model_name, provider, "unknown",
                               last_error=f"Unknown provider: {provider}")

        api_key = os.environ.get(prov["key_env"])
        if not api_key:
            return ModelHealth(model_name, provider, "dead",
                               last_error=f"Missing {prov['key_env']}")

        t0 = time.time()
        try:
            resp = requests.post(
                prov["url"],
                headers={
                    prov["header_key"]: f'{prov["header_prefix"]}{api_key}',
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 10,
                    "temperature": 0.1,
                },
                timeout=15,
            )
            latency = (time.time() - t0) * 1000
            ok = resp.status_code == 200
            health = self.health_map.get(key) or ModelHealth(model_name, provider)
            health.last_checked = datetime.utcnow().isoformat()
            health.latency_ms = latency

            if ok:
                health.status = "healthy"
                health.success_count += 1
            elif resp.status_code == 429:
                health.status = "degraded"
                health.error_count += 1
                health.last_error = f"Rate limited (429)"
            else:
                health.status = "dead"
                health.error_count += 1
                health.last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"

            self.health_map[key] = health
            self._save()
            return health

        except requests.Timeout:
            last_error = "Timeout (>15s)"
            health = self._update_health(key, model_name, provider, "dead", last_error)
            return health
        except requests.ConnectionError:
            last_error = "Connection refused"
            health = self._update_health(key, model_name, provider, "dead", last_error)
            return health
        except Exception as e:
            # Sanitize: remove any API key from error message
            safe = str(e).replace(api_key, "[REDACTED]") if api_key in str(e) else str(e)
            health = self._update_health(key, model_name, provider, "dead", safe[:100])
            return health

    def _update_health(self, key: str, model_name: str, provider: str,
                        status: str, error: str = "") -> ModelHealth:
        health = self.health_map.get(key) or ModelHealth(model_name, provider)
        health.status = status
        health.last_checked = datetime.utcnow().isoformat()
        if error:
            health.last_error = error
            health.error_count += 1
        else:
            health.success_count += 1
        self.health_map[key] = health
        self._save()
        return health

    def check_all(self, models: List[Tuple[str, str]]) -> Dict[str, ModelHealth]:
        """检查所有配置的模型"""
        results = {}
        for model_name, provider in models:
            results[f"{provider}/{model_name}"] = self.check_model(model_name, provider)
        return results

    def get_healthy(self) -> List[str]:
        """获取所有健康模型的列表"""
        return [k for k, v in self.health_map.items() if v.is_healthy]

    def get_best_fallback(self, primary: str, provider: str) -> Optional[str]:
        """获取可用的最佳备用模型"""
        key = f"{provider}/{primary}"
        primary_health = self.health_map.get(key)
        
        if primary_health and primary_health.is_healthy:
            return f"{provider}/{primary}"
        
        # 从其他健康模型中选最佳
        healthy = [(k, v.health_score) for k, v in self.health_map.items() if v.is_healthy]
        if healthy:
            healthy.sort(key=lambda x: -x[1])
            return healthy[0][0]
        return None


# ── 一键诊断 ──────────────────────────────────────────

MODELS_TO_CHECK = [
    ("deepseek-v4-flash", "deepseek"),
    ("deepseek-v4-pro", "deepseek"),
    ("openai/gpt-5.6", "openrouter"),
    ("nvidia/nemotron-3-super-120b-a12b:free", "openrouter"),
    ("google/gemma-4-31b-it:free", "openrouter"),
    ("gpt-4o", "openai"),
]


def run_diagnostic(monitor: Optional[ModelHealthMonitor] = None) -> Dict[str, Any]:
    """运行完整诊断"""
    if monitor is None:
        monitor = ModelHealthMonitor()
    
    print("\n  🏥 模型健康诊断")
    print("  " + "="*40)
    
    results = {}
    for model_name, provider in MODELS_TO_CHECK:
        health = monitor.check_model(model_name, provider)
        icon = "✅" if health.is_healthy else "⚠️" if health.status == "degraded" else "❌"
        results[f"{provider}/{model_name}"] = health
        print(f"  {icon} {provider}/{model_name}")
        print(f"     状态: {health.status} | 延迟: {health.latency_ms:.0f}ms  | "
              f"健康分: {health.health_score:.1f}  | "
              f"{'最近错误: '+health.last_error[:60] if health.last_error else ''}")
    
    print(f"\n  健康: {sum(1 for h in results.values() if h.is_healthy)}/{len(results)}")
    print(f"  降级: {sum(1 for h in results.values() if h.status == 'degraded')}/{len(results)}")
    print(f"  死亡: {sum(1 for h in results.values() if h.status == 'dead')}/{len(results)}")
    
    return results


if __name__ == "__main__":
    run_diagnostic()
