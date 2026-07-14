"""
趋势追踪器 — 自动从GitHub/社区/网络学习优化

核心能力：
1. 监控 GitHub 上的设计系统/品牌项目
2. 搜索社区最佳实践
3. 自动学习新的设计模式
4. 持续优化参数化颗粒度
5. 生成进化报告
"""
import os, json, requests, time, urllib.parse
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LearningResult:
    """一次学习的结果"""
    source: str                          # github/web/community
    topic: str                           # 学习主题
    findings: List[str] = field(default_factory=list)
    actionable_improvements: List[str] = field(default_factory=list)  # 可执行的改进
    new_parameters: Dict[str, Any] = field(default_factory=dict)      # 新发现的参数
    confidence: float = 0.0
    learned_at: str = ""


class TrendTracker:
    """趋势追踪器 — 持续学习进化"""

    def __init__(self):
        self.learning_history: List[LearningResult] = []
        self.github_token = os.environ.get("GITHUB_TOKEN", "")

    def learn_from_github(self, query: str, max_results: int = 5) -> LearningResult:
        """从GitHub搜索学习"""
        findings = []
        improvements = []
        new_params = {}

        # 搜索仓库
        repos = self._search_github(query, max_results)
        for repo in repos:
            findings.append(f"Found repo: {repo.get('full_name', '')} - {repo.get('description', '')}")

        # 搜索README内容
        for repo in repos[:3]:
            readme = self._get_readme(repo.get("full_name", ""))
            if readme:
                # 提取参数化相关信息
                if "parameter" in readme.lower() or "config" in readme.lower():
                    improvements.append(f"Parameter system found in {repo['full_name']}")
                if "pbr" in readme.lower() or "material" in readme.lower():
                    improvements.append(f"Material system reference in {repo['full_name']}")

        # 搜索design system相关
        ds = self._search_github(query + " design system", 3)
        for d in ds:
            findings.append(f"Design system: {d.get('full_name', '')}")

        return LearningResult(
            source="github",
            topic=query,
            findings=findings,
            actionable_improvements=improvements,
            new_parameters=new_params,
            confidence=0.6,
            learned_at=datetime.utcnow().isoformat(),
        )

    def learn_from_web(self, topic: str) -> LearningResult:
        """从网络搜索学习最佳实践"""
        findings = []
        improvements = []

        try:
            # DuckDuckGo search
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": topic, "format": "json"},
                timeout=10
            )
            if r.ok:
                data = r.json()
                for result in data.get("Results", [])[:5]:
                    text = result.get("Text", "")
                    findings.append(text[:200])
                    if "parameter" in text.lower() or "workflow" in text.lower():
                        improvements.append(f"Found workflow info: {text[:100]}")
        except:
            pass

        return LearningResult(
            source="web",
            topic=topic,
            findings=findings,
            actionable_improvements=improvements,
            confidence=0.4,
            learned_at=datetime.utcnow().isoformat(),
        )

    def learn_from_trends(self) -> List[LearningResult]:
        """自动追踪多个方向的趋势"""
        topics = [
            "product photography AI reverse engineering 2026",
            "brand design system parametric",
            "e-commerce product page design best practices",
            "PBR material estimation single image",
            "AI product photography workflow",
        ]
        results = []
        for topic in topics:
            try:
                result = self.learn_from_web(topic)
                results.append(result)
                time.sleep(0.5)
            except:
                pass
        self.learning_history.extend(results)
        return results

    def get_improvement_suggestions(self) -> List[str]:
        """获取所有可执行的改进建议"""
        all_improvements = []
        for lr in self.learning_history:
            all_improvements.extend(lr.actionable_improvements)
        return list(set(all_improvements))

    def _search_github(self, query: str, max_results: int = 5) -> List[Dict]:
        """搜索GitHub仓库"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        try:
            r = requests.get(
                f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&per_page={max_results}",
                headers=headers,
                timeout=15
            )
            if r.ok:
                return r.json().get("items", [])
        except:
            pass
        return []

    def _get_readme(self, repo_full_name: str) -> Optional[str]:
        """获取仓库README"""
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        try:
            r = requests.get(
                f"https://api.github.com/repos/{repo_full_name}/readme",
                headers=headers,
                timeout=10
            )
            if r.ok:
                return r.text[:5000]
        except:
            pass
        return None
