"""
CEO 管理系统 — 派活、汇总、把控方向

CEO不亲自做具体工作，而是:
1. 理解项目需求
2. 拆解为子任务
3. 分配给对应Agent（通过delegate_task）
4. 汇总各Agent产出
5. 把控质量和大方向

每个Agent接到任务后：
- 查询品牌DNA参考库 → 获取品牌规则
- 结合自身专业技能 → 独立完成工作
- 产出结构化报告 → 存入项目档案
- 贡献新知识 → 优化DNA库
"""
import os, json, sys, time
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TaskAssignment:
    """CEO分配给一个Agent的任务"""
    task_id: str = ""
    agent_name: str = ""
    task_type: str = ""       # research/creative/art_direction/production
    brand: str = ""
    products: List[Dict] = field(default_factory=list)
    dna_reference: str = ""   # 品牌DNA参考摘要（供Agent使用）
    status: str = "pending"   # pending/running/completed/failed
    result: Any = None
    started_at: str = ""
    completed_at: str = ""


class CEOSystem:
    """CEO管理系统"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._projects: Dict[str, List[TaskAssignment]] = {}
        self._dna_ref = None

    def _get_dna_ref(self):
        if not self._dna_ref:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
            from agency.dna_ref import BrandDNARef
            self._dna_ref = BrandDNARef()
        return self._dna_ref

    # ── 项目规划 ──────────────────────────────────────

    def plan_project(self, brand: str, products: List[Dict], 
                     project_id: Optional[str] = None) -> List[TaskAssignment]:
        """
        CEO: 理解项目 → 拆解任务 → 分配给Agent
        
        每个Agent的任务包括：
        - 品牌DNA参考摘要（供Agent查询使用）
        - 明确的交付标准
        """
        pid = project_id or f"PROJ-{hash(brand+str(datetime.utcnow()))%10000:04d}"
        
        # 查询品牌DNA参考
        dna_ref = self._get_dna_ref()
        brand_ref = dna_ref.get_designer_reference(brand) if brand else ""
        
        tasks = [
            TaskAssignment(
                task_id=f"{pid}-STRAT",
                agent_name="策略策划",
                task_type="strategy",
                brand=brand, products=products,
                dna_reference=brand_ref,
            ),
            TaskAssignment(
                task_id=f"{pid}-CREATIVE",
                agent_name="创意总监",
                task_type="creative",
                brand=brand, products=products,
                dna_reference=brand_ref,
            ),
            TaskAssignment(
                task_id=f"{pid}-ART",
                agent_name="美术指导",
                task_type="art_direction",
                brand=brand, products=products,
                dna_reference=brand_ref,
            ),
            TaskAssignment(
                task_id=f"{pid}-PROD",
                agent_name="制作",
                task_type="production",
                brand=brand, products=products,
                dna_reference=brand_ref,
            ),
        ]
        
        self._projects[pid] = tasks
        return tasks

    # ── CEO分配任务 ───────────────────────────────────

    def assign_and_execute(self, task: TaskAssignment) -> Dict:
        """
        CEO将任务派发给对应Agent执行
        
        每个Agent通过 delegate_task 独立工作
        使用品牌DNA参考库中的知识
        """
        print(f"\n  👑 [CEO] 分配任务: {task.task_id}")
        print(f"      Agent: {task.agent_name}")
        print(f"      类型: {task.task_type}")
        print(f"      品牌: {task.brand}")
        
        if task.dna_reference:
            print(f"      📚 品牌DNA参考已提供 ({len(task.dna_reference)} chars)")
        
        # Agent通过delegate_task独立工作
        return self._dispatch_to_agent(task)

    def _dispatch_to_agent(self, task: TaskAssignment) -> Dict:
        """
        将任务发给Agent执行
        每个Agent都有自己的专业能力和知识库
        
        Agent独立工作流程:
        1. 读取任务 + 品牌DNA参考
        2. 调用自身专业技能完成工作
        3. 产出结构化结果
        4. 将新知识贡献回DNA库
        """
        from hermes_tools import delegate_task
        
        # 构建Agent任务上下文
        context = f"""
品牌: {task.brand}
任务类型: {task.task_type}
产品数量: {len(task.products)}

品牌DNA参考:
{task.dna_reference[:2000] if task.dna_reference else "尚无品牌DNA数据，需从本次项目提取"}

你的角色: {task.agent_name}
你的专业技能: 见角色定义
你的工作: 独立完成{task.task_type}任务
你的交付: 结构化报告 + 新品牌知识（用于更新DNA库）
"""
        
        # 派发给Agent子任务
        goal = f"作为{task.agent_name}，为品牌{task.brand}完成{task.task_type}工作。参考品牌DNA库已有知识，产出专业报告，并将新学到的品牌知识贡献回DNA库。"
        
        result = delegate_task(
            goal=goal,
            context=context
        )
        
        return result

    # ── CEO汇总 ───────────────────────────────────────

    def collect_results(self, project_id: str) -> Dict:
        """CEO汇总所有Agent的产出"""
        tasks = self._projects.get(project_id, [])
        
        summary = {
            "project_id": project_id,
            "total_tasks": len(tasks),
            "completed": sum(1 for t in tasks if t.status == "completed"),
            "failed": sum(1 for t in tasks if t.status == "failed"),
            "agent_outputs": {},
        }
        
        for task in tasks:
            summary["agent_outputs"][task.agent_name] = {
                "task_type": task.task_type,
                "status": task.status,
                "result": task.result,
            }
        
        return summary

    def project_summary(self, brand: str, project_id: str, outputs: Dict) -> str:
        """CEO撰写项目总结 — 把控大方向"""
        lines = [
            f"\n  {'='*60}",
            f"  📋 CEO项目总结",
            f"  {'='*60}",
            f"  项目: {project_id}",
            f"  品牌: {brand}",
            f"  状态: 完成",
            f"",
            f"  Agent产出汇总:",
        ]
        
        for agent_name, result in outputs.items():
            status = "✅" if result.get("success") else "❌"
            lines.append(f"    {status} {agent_name}: {result.get('summary','')[:80]}")
        
        lines.extend([
            f"",
            f"  📚 品牌DNA库更新: 本次项目的新知识已自动入库",
            f"  下次同类项目可直接参考调用",
            f"  {'='*60}",
        ])
        
        return "\n".join(lines)
