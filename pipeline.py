"""
Hermes Agent OS — 统一 Pipeline 入口

替代分散的 packages/ 结构。所有功能通过 hermes_os/ 调用。

使用方式:
    from pipeline import HermesPipeline
    pipe = HermesPipeline()
    result = pipe.run(brand="MUJI")
"""
import os, sys, json, time
from typing import Optional, Dict, Any, List
from datetime import datetime


class HermesPipeline:
    """统一 Pipeline — 6 阶段归一化流程"""

    ROOT = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, api_key: Optional[str] = None,
                 output_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.output_dir = output_dir or os.path.join(self.ROOT, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        # 统一知识库
        sys.path.insert(0, self.ROOT)
        from hermes_os.knowledge.unified_knowledge import UnifiedKnowledge
        self.db = UnifiedKnowledge()
        self.db.seed_patterns()

        # 统一类型
        from hermes_os.types import (
            BrandProfile, AgencyCase, PBRMaterial, SceneGraph,
            CameraSystem, Light, SceneElement, ACRParams
        )
        self.types = {
            "BrandProfile": BrandProfile,
            "AgencyCase": AgencyCase,
            "PBRMaterial": PBRMaterial,
            "SceneGraph": SceneGraph,
        }

    def run(self, image_url: Optional[str] = None,
            brand: Optional[str] = None,
            category: str = "furniture") -> Dict[str, Any]:
        """统一入口"""
        result = {
            "brand": brand or f"brand_{abs(hash(str(image_url))) % 10000}",
            "stages": {},
        }
        print(f"\n  🏭 Hermes Pipeline — {brand or 'product'}")

        # 详情页图片生成
        try:
            sys.path.insert(0, os.path.join(self.ROOT, "packages", "norhor", "src"))
            from detail_image_gen import generate_detail_images
            print("  🖼️  生成详情页...")
            out_dir = os.path.join(self.output_dir, (brand or "product").lower().replace(" ", "_"))
            zip_path = generate_detail_images(
                product_name=brand or "产品", category=category,
                brand_style="nordic", output_dir=out_dir)
            result["output"] = {"zip": zip_path}
            result["stages"]["generate"] = "✅"
        except Exception as e:
            result["stages"]["generate"] = f"⚠️ {e}"

        # 存入品牌知识库
        if brand:
            self.db.save_brand(brand, category)
            result["stages"]["save"] = "✅"

        ok = sum(1 for s in result["stages"].values() if s == "✅")
        print(f"  ✅ {ok}/{len(result['stages'])} 阶段完成")
        return result

    def stats(self) -> Dict[str, Any]:
        return {
            "database": self.db.stats(),
            "output_dir": self.output_dir,
        }
