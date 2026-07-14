"""
客户简报系统 — 接领需求 (Briefing Phase)

4A标准流程第一步:
接收客户需求 → 内部对齐 → 项目立项
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ClientBrief:
    """客户简报 — 结构化需求"""
    # 基础信息
    brand_name: str = ""
    project_name: str = ""
    project_type: str = ""  # product_detail / brand_identity / campaign
    
    # 品牌背景
    brand_background: str = ""
    brand_positioning: str = ""
    target_audience: str = ""
    
    # 产品信息
    product_category: str = ""
    product_images: List[str] = field(default_factory=list)  # 多产品图
    product_descriptions: List[str] = field(default_factory=list)
    
    # 项目要求
    desired_outputs: List[str] = field(default_factory=list)  # detail_page/vi/campaign
    design_references: List[str] = field(default_factory=list)
    budget_range: str = ""
    deadline: str = ""
    
    # 竞品
    competitors: List[str] = field(default_factory=list)
    
    # 状态
    status: str = "draft"  # draft/review/approved
    created_at: str = ""
    brief_id: str = ""


class Briefing:
    """简报系统 — 接收和管理客户需求"""

    def __init__(self):
        self._projects: Dict[str, ClientBrief] = {}

    def receive_brief(self, brand: str, images: List[str] = None, **kwargs) -> ClientBrief:
        """接收客户需求"""
        brief = ClientBrief(
            brand_name=brand,
            product_images=images or [],
            created_at=datetime.utcnow().isoformat(),
            brief_id=f"BR-{hash(brand+str(datetime.utcnow()))%10000:04d}",
            **{k:v for k,v in kwargs.items() if hasattr(ClientBrief, k)}
        )
        self._projects[brief.brief_id] = brief
        print(f"  📋 [Briefing] 新项目立项: {brief.brief_id} - {brand}")
        print(f"    产品图数: {len(brief.product_images)}")
        print(f"    需求类型: {brief.project_type or '品牌研究'}")
        return brief

    def multi_product_brief(self, brand: str, products: List[Dict]) -> ClientBrief:
        """多产品简报 — 批量输入多个产品"""
        brief = ClientBrief(
            brand_name=brand,
            product_images=[p.get("image","") for p in products[:20]],
            product_descriptions=[p.get("name","") for p in products[:20]],
            product_category=products[0].get("category","") if products else "",
            created_at=datetime.utcnow().isoformat(),
            brief_id=f"BR-{hash(brand+str(datetime.utcnow()))%10000:04d}",
        )
        self._projects[brief.brief_id] = brief
        print(f"  📋 [Briefing] 多产品简报: {brief.brief_id}")
        print(f"    产品数: {len(products)}, 品牌: {brand}")
        return brief

    def get_brief(self, brief_id: str) -> Optional[ClientBrief]:
        return self._projects.get(brief_id)

    def list_projects(self) -> List[str]:
        return list(self._projects.keys())
