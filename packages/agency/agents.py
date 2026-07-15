"""
4A Agent 角色系统 — 每个Agent有专业岗位技能

每个Agent:
1. 明确的岗位定义和职责
2. 专业技能体系 (可查询的知识库)
3. 标准工作流程
4. 质量标准
5. 持续学习机制
"""
import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentSkill:
    """一项专业技能"""
    name: str = ""
    description: str = ""
    proficiency: str = ""  # junior/mid/senior/expert
    knowledge_areas: List[str] = field(default_factory=list)


@dataclass
class AgentRole:
    """岗位定义"""
    title: str = ""
    department: str = ""
    seniority: str = "senior"
    
    responsibilities: List[str] = field(default_factory=list)
    skills: List[AgentSkill] = field(default_factory=list)
    
    workflow_steps: List[str] = field(default_factory=list)
    quality_criteria: List[str] = field(default_factory=list)
    
    domain_knowledge: Dict[str, str] = field(default_factory=dict)


# ── 预定义岗位 ─────────────────────────────────────────

PLANNER_ROLE = AgentRole(
    title="策略策划 Strategic Planner",
    department="Strategy",
    seniority="senior",
    responsibilities=[
        "市场调研与竞品分析",
        "消费者洞察与趋势研究",
        "品牌定位与沟通策略",
        "设计策略文档撰写",
    ],
    skills=[
        AgentSkill("市场研究", "系统化收集和分析市场数据", "expert",
                   ["定性研究", "定量研究", "竞品对标", "行业趋势"]),
        AgentSkill("消费者洞察", "理解目标受众心理和行为", "expert",
                   ["用户画像", "消费心理学", "行为分析"]),
        AgentSkill("品牌策略", "品牌定位和沟通策略制定", "senior",
                   ["品牌架构", "定位理论", "沟通策略"]),
        AgentSkill("策略文档", "撰写专业策略报告", "senior",
                   ["简报撰写", "策略提案", "数据分析可视化"]),
    ],
    workflow_steps=[
        "1. 收集品牌信息和市场数据",
        "2. 竞品视觉系统分析（多产品）",
        "3. 消费者洞察提取",
        "4. 品牌定位和沟通策略",
        "5. 策略文档输出",
    ],
    quality_criteria=[
        "数据来源可靠且可追溯",
        "洞察具有 actionable 价值",
        "策略与品牌目标一致",
        "文档结构清晰专业",
    ],
    domain_knowledge={
        "品牌定位": "品牌定位决定设计方向，所有设计决策服务于品牌战略",
        "视觉一致性": "同一品牌的视觉系统应有一定范围的变化，而非完全一致",
        "消费者心理": "色彩/构图/光线都影响消费者的品牌感知",
        "竞品分析": "通过分析竞品视觉系统发现差异化机会",
    }
)

CREATIVE_ROLE = AgentRole(
    title="创意总监 Creative Director",
    department="Creative",
    seniority="senior",
    responsibilities=[
        "创意概念发想与评估",
        "视觉风格方向确定",
        "创意方案评分与推荐",
        "创意简报撰写",
    ],
    skills=[
        AgentSkill("创意发想", "多角度创意概念生成", "expert",
                   ["头脑风暴", "概念开发", "创意方法论"]),
        AgentSkill("视觉语言", "理解和创造视觉语法", "expert",
                   ["视觉语法", "设计原则", "美学理论"]),
        AgentSkill("创意评估", "系统化评估创意方案", "senior",
                   ["评分体系", "可行性评估", "品牌合规"]),
        AgentSkill("提案呈现", "创意方案可视化呈现", "senior",
                   ["视觉呈现", "故事叙述", "方案包装"]),
    ],
    workflow_steps=[
        "1. 理解策略方向",
        "2. 多角度创意发想（至少5套）",
        "3. 创意方案评分与筛选",
        "4. 推荐最优方案",
        "5. 创意简报输出",
    ],
    quality_criteria=[
        "创意方向至少有5个不同角度",
        "每个创意有明确的 rationale",
        "评分标准一致且可复现",
        "推荐的方案有数据支撑",
    ],
    domain_knowledge={
        "创意方法论": "SCAMPER/头脑风暴/逆向思维等多种创意方法",
        "视觉语法": "版式/色彩/构图/光影构成视觉语言",
        "设计趋势": "了解当代设计趋势和历史背景",
        "品牌合规": "创意必须在品牌调性范围内",
    }
)

ART_ROLE = AgentRole(
    title="美术指导 Art Director",
    department="Creative",
    seniority="senior",
    responsibilities=[
        "产品摄影参数规划",
        "灯光方案设计",
        "色彩系统规划",
        "场景构图设计",
        "PBR材质参数把控",
    ],
    skills=[
        AgentSkill("摄影技术", "产品摄影全流程技术", "expert",
                   ["相机参数", "灯光布光", "镜头选择", "景深控制"]),
        AgentSkill("色彩管理", "品牌色彩系统设计和控制", "expert",
                   ["色彩理论", "色板规划", "色彩心理学", "后期调色"]),
        AgentSkill("灯光设计", "影棚和自然光灯光方案", "expert",
                   ["灯光类型", "布光方案", "光质控制", "色温管理"]),
        AgentSkill("构图设计", "画面构图和视觉引导", "senior",
                   ["构图法则", "视觉重心", "留白控制", "比例关系"]),
        AgentSkill("材质把控", "PBR材质参数理解和控制", "senior",
                   ["PBR材质", "表面质感", "光线交互", "材质真实感"]),
    ],
    workflow_steps=[
        "1. 理解创意方向",
        "2. 规划摄影参数（相机/灯光/构图）",
        "3. 设计色彩系统",
        "4. 制定PBR材质规范",
        "5. 输出制作规格书",
    ],
    quality_criteria=[
        "摄影参数在品牌范围内",
        "灯光方案可执行",
        "色板符合品牌定位",
        "构图引导符合作品需求",
    ],
    domain_knowledge={
        "焦距选择": "85mm人像/产品标准，35-50mm环境融入，135mm压缩特写",
        "光圈控制": "f/2.8浅景深突出主体，f/8-f/11全清晰产品展示",
        "灯光基础": "三点布光: 主光+补光+背光，柔光箱/雷达罩/标准罩各有用途",
        "色彩理论": "互补色/类似色/三角色 不同配色策略产生不同心理效果",
        "PBR材质": "Roughness控制反光扩散，Metallic控制金属感，Normal控制表面细节",
    }
)

PRODUCER_ROLE = AgentRole(
    title="制作 Producer",
    department="Production",
    seniority="senior",
    responsibilities=[
        "项目排期与进度管理",
        "质量控制与标准执行",
        "输出物规格把控",
        "资源协调与管理",
    ],
    skills=[
        AgentSkill("项目管理", "项目排期和进度跟踪", "expert",
                   ["排期规划", "进度管理", "风险控制"]),
        AgentSkill("质量控制", "输出物质量把控", "expert",
                   ["质量标准", "验收流程", "问题追踪"]),
        AgentSkill("输出管理", "多媒体输出物管理", "senior",
                   ["格式规范", "文件管理", "版本控制"]),
    ],
    workflow_steps=[
        "1. 确认创意方案和执行规格",
        "2. 制定项目排期",
        "3. 执行质量控制",
        "4. 输出物验收",
        "5. 项目复盘",
    ],
    quality_criteria=[
        "项目按时交付",
        "输出物符合规格要求",
        "质量问题有追踪和闭环",
        "项目文档完整",
    ],
    domain_knowledge={
        "排期规划": "研究1d+创意1d+拍摄2d+后期1d+提报1d = 标准5-8工作日",
        "质量标准": "分辨率/色彩空间/文件格式/命名规范",
        "验收流程": "内部审稿→修改→终审→交付",
    }
)


# ── Agent 员工系统 ─────────────────────────────────────

class AgentEmployee:
    """一个Agent员工 — 有角色、技能、知识库"""

    def __init__(self, role: AgentRole, name: str = ""):
        self.role = role
        self.name = name or role.title
        self.experience: List[str] = []  # 项目经验
        self.special_notes: List[str] = []  # 特殊备注

    def introduce(self) -> str:
        """自我介绍 — 岗位能力说明"""
        lines = [
            f"  👤 {self.name} ({self.role.seniority})",
            f"  🏢 {self.role.department} · {self.role.title}",
            "  📋 职责:",
        ]
        for r in self.role.responsibilities:
            lines.append(f"    • {r}")
        lines.append("  🛠️  核心技能:")
        for s in self.role.skills[:3]:
            lines.append(f"    • {s.name}: {s.description} ({s.proficiency})")
        lines.append("  📚 专业知识:")
        for k, v in list(self.role.domain_knowledge.items())[:3]:
            lines.append(f"    • {k}: {v[:50]}...")
        return "\n".join(lines)

    def get_workflow(self) -> str:
        """获取工作流程"""
        lines = [f"  📋 {self.role.title} 工作流程:"]
        for s in self.role.workflow_steps:
            lines.append(f"    {s}")
        return "\n".join(lines)


# ── Agent团队 ─────────────────────────────────────────

class AgentTeam:
    """Agent团队 — 管理所有角色"""

    def __init__(self):
        self.agents: Dict[str, AgentEmployee] = {}
        self._init_default_team()

    def _init_default_team(self):
        """初始化默认团队"""
        self.add_agent(AgentEmployee(PLANNER_ROLE, "策略分析师"))
        self.add_agent(AgentEmployee(CREATIVE_ROLE, "创意总监"))
        self.add_agent(AgentEmployee(ART_ROLE, "美术指导"))
        self.add_agent(AgentEmployee(PRODUCER_ROLE, "制作总监"))

    def add_agent(self, agent: AgentEmployee):
        self.agents[agent.role.title] = agent

    def get_agent(self, title: str) -> Optional[AgentEmployee]:
        return self.agents.get(title)

    def team_intro(self) -> str:
        lines = ["\n  🏢 4A Agent 团队\n"]
        for name, agent in self.agents.items():
            lines.append(f"  {agent.name} ({agent.role.seniority})")
            lines.append(f"    {agent.role.department} · 技能: {len(agent.role.skills)}项")
        return "\n".join(lines)

    def assign_task(self, task_type: str) -> Optional[AgentEmployee]:
        """根据任务类型分配Agent"""
        mapping = {
            "research": "策略策划 Strategic Planner",
            "strategy": "策略策划 Strategic Planner",
            "creative": "创意总监 Creative Director",
            "art_direction": "美术指导 Art Director",
            "production": "制作 Producer",
            "quality": "制作 Producer",
        }
        title = mapping.get(task_type)
        return self.agents.get(title) if title else None
