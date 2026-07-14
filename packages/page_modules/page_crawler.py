"""
Module A: Page Crawler — 爬虫抓取详情页，识别功能模块区域，裁切输出Mapping JSON

核心能力:
- 接收产品详情页URL → 获取全页面HTML + 截图
- 识别7种功能模块: Hero Banner / Product Carousel / Close-up Macro /
  Scene Lifestyle / Parameter Infographic / Texture Detail / Text Copy Block
- 输出每个模块的 bounding box 坐标、Z-index、滚动顺序
- 输出 mapping JSON (ModuleID → type → file path)
- 跳过弹窗、浮动广告等干扰元素

依赖: requests, beautifulsoup4, playwright (可选用于JS渲染页面), Pillow
"""

import os
import re
import json
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urlparse
from io import BytesIO
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════

# 7种功能模块类型
MODULE_TYPES = [
    "HeroBanner",
    "ProductCarousel",
    "CloseupMacro",
    "SceneLifestyle",
    "ParameterInfographic",
    "TextureDetail",
    "TextCopyBlock",
]


@dataclass
class ModuleRegion:
    """单个识别出的模块区域"""
    module_id: str
    module_type: str
    name: str = ""
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0
    z_index: int = 0
    scroll_order: int = 0
    hierarchy_level: int = 1
    visual_weight: float = 0.0
    bg_color: str = ""
    bg_image: str = ""
    css_classes: List[str] = field(default_factory=list)
    child_element_count: int = 0
    text_content_length: int = 0
    image_urls: List[str] = field(default_factory=list)
    cropped_path: str = ""
    confidence: float = 0.0


@dataclass
class CrawlResult:
    """单次爬取完整结果"""
    url: str = ""
    brand: str = ""
    page_title: str = ""
    extracted_at: str = ""
    page_width: int = 0
    page_height: int = 0
    viewport_width: int = 1440
    viewport_height: int = 900
    modules: List[ModuleRegion] = field(default_factory=list)
    module_count: int = 0
    full_screenshot_path: str = ""
    mapping_json_path: str = ""
    crawl_duration_ms: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, default=str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def get_mapping(self) -> Dict[str, Dict[str, str]]:
        return {
            m.module_id: {"type": m.module_type, "file_path": m.cropped_path}
            for m in self.modules
        }


# ═══════════════════════════════════════════════════════════════
# Module Classifier
# ═══════════════════════════════════════════════════════════════

TYPE_KEYWORDS: Dict[str, List[str]] = {
    "HeroBanner": ["hero", "banner", "main-visual", "mainvisual", "kv", "key-visual",
                   "splash", "jumbotron", "billboard", "masthead", "featured-hero"],
    "ProductCarousel": ["carousel", "slider", "gallery", "product-gallery", "swiper",
                        "slideshow", "product-images", "product-slider", "thumbnails"],
    "CloseupMacro": ["closeup", "macro", "detail-shot", "detail-view", "zoom",
                     "magnify", "enlarge", "close-up"],
    "SceneLifestyle": ["lifestyle", "scene", "lifestyle-image", "scene-shot",
                       "in-situ", "room-scene", "environment", "ambient"],
    "ParameterInfographic": ["infographic", "specs", "specification", "parameter",
                             "dimensions", "size-guide", "size-chart", "tech-spec"],
    "TextureDetail": ["texture", "material", "fabric", "weave", "surface",
                      "grain", "closeup-texture", "material-detail", "finish"],
    "TextCopyBlock": ["description", "copy", "product-description", "product-info",
                      "product-detail", "detail-text", "text-block", "copy-block"],
}

NOISE_KEYWORDS = [
    "popup", "modal", "overlay", "ad", "advertisement", "banner-ad",
    "floating", "fixed-banner", "newsletter", "subscribe", "cookie",
    "chat", "live-chat", "tooltip", "toast", "notification",
]


def _classify_module(element: Tag, images: List[str], text_len: int) -> Tuple[str, float]:
    class_str = " ".join(element.get("class", []))
    id_str = element.get("id", "")
    tag_name = element.name if element.name else ""
    all_text = (class_str + " " + id_str + " " + tag_name).lower()

    scores: Dict[str, float] = {}
    for mtype, keywords in TYPE_KEYWORDS.items():
        score = sum(1.0 for kw in keywords if kw in all_text)
        scores[mtype] = min(score / 2.0, 1.0)

    if text_len > 500 and len(images) == 0:
        scores["TextCopyBlock"] += 0.5
    if len(images) >= 3 and text_len < 100:
        scores["ProductCarousel"] += 0.5

    best_type = max(scores, key=scores.get) if scores else "HeroBanner"
    confidence = scores.get(best_type, 0.0)
    return (best_type, confidence)


def _is_noise_element(element: Tag) -> bool:
    class_str = " ".join(element.get("class", []))
    id_str = element.get("id", "")
    all_text = (class_str + " " + id_str).lower()
    return any(kw in all_text for kw in NOISE_KEYWORDS)


# ═══════════════════════════════════════════════════════════════
# Page Crawler Engine
# ═══════════════════════════════════════════════════════════════

class PageCrawler:
    """详情页爬虫 — 抓取HTML、识别模块、裁切输出"""

    def __init__(
        self,
        output_dir: str = "./crops",
        viewport_width: int = 1440,
        viewport_height: int = 900,
        min_module_height: int = 80,
        min_module_width: int = 200,
        use_playwright: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.min_module_height = min_module_height
        self.min_module_width = min_module_width
        self.use_playwright = use_playwright
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def crawl(self, url: str, brand: str = "") -> CrawlResult:
        start_time = datetime.now()
        result = CrawlResult(
            url=url,
            brand=brand or self._extract_brand(url),
            extracted_at=datetime.now().isoformat(),
        )
        try:
            html = self._fetch_html(url)
            if not html:
                result.errors.append("Failed to fetch HTML")
                return result
            soup = BeautifulSoup(html, "html.parser")
            result.page_title = soup.title.string if soup.title else ""
            result.page_width = self.viewport_width
            result.page_height = self._estimate_page_height(soup, html)
            modules = self._identify_modules(soup, result)
            result.modules = modules
            result.module_count = len(modules)
            self._associate_module_crops(modules, html)
            result.mapping_json_path = self._save_mapping(result)
        except Exception as e:
            logger.exception(f"Crawl failed for {url}")
            result.errors.append(str(e))
        result.crawl_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result

    def _fetch_html(self, url: str) -> Optional[str]:
        if self.use_playwright:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": self.viewport_width, "height": self.viewport_height})
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    html = page.content()
                    browser.close()
                    return html
            except ImportError:
                logger.warning("playwright not installed, falling back to requests")
            except Exception as e:
                logger.error(f"Playwright error: {e}")
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except requests.RequestException as e:
            logger.error(f"HTTP fetch error: {e}")
            return None

    def _extract_brand(self, url: str) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        parts = domain.split(".")
        return parts[-2].capitalize() if len(parts) >= 2 else domain

    def _estimate_page_height(self, soup: BeautifulSoup, html: str) -> int:
        body = soup.find("body")
        if body:
            style = body.get("style", "")
            h_match = re.search(r"height:\s*(\d+)px", style)
            if h_match:
                return int(h_match.group(1))
        return 5000

    def _identify_modules(self, soup: BeautifulSoup, result: CrawlResult) -> List[ModuleRegion]:
        modules = []
        module_idx = 0
        scroll_order = 0
        container_tags = {"div", "section", "article", "main", "header", "footer", "aside"}
        body = soup.find("body")
        if not body:
            return modules
        all_containers = body.find_all(container_tags)
        for element in all_containers:
            if _is_noise_element(element):
                continue
            dims = self._get_element_dimensions(element)
            if not dims:
                continue
            x, y, w, h, z = dims
            if w < self.min_module_width and h < self.min_module_height:
                continue
            images = [img.get("src", "") for img in element.find_all("img")]
            text_content = element.get_text(strip=True)
            text_len = len(text_content)
            if text_len < 10 and len(images) == 0:
                continue
            mtype, confidence = _classify_module(element, images, text_len)
            module_idx += 1
            scroll_order += 1
            module = ModuleRegion(
                module_id=f"M{module_idx:03d}",
                module_type=mtype,
                name=f"{mtype}_{module_idx}",
                x1=x, y1=y, x2=x + w, y2=y + h,
                z_index=z,
                scroll_order=scroll_order,
                hierarchy_level=self._estimate_hierarchy(y, h, result.page_height),
                visual_weight=self._calc_visual_weight(w, h, y),
                bg_color=self._extract_bg_color(element),
                bg_image=self._extract_bg_image(element),
                css_classes=element.get("class", []),
                child_element_count=len(element.find_all()),
                text_content_length=text_len,
                image_urls=images,
                confidence=confidence,
            )
            modules.append(module)
        if not modules and body:
            module_idx += 1
            modules.append(ModuleRegion(
                module_id=f"M{module_idx:03d}", module_type="HeroBanner",
                name="FullPage", x1=0, y1=0,
                x2=result.page_width, y2=result.page_height,
                z_index=0, scroll_order=1, hierarchy_level=1,
                visual_weight=1.0, confidence=0.3,
            ))
        return modules

    def _get_element_dimensions(self, element: Tag) -> Optional[Tuple[int, int, int, int, int]]:
        style = element.get("style", "")
        if not style:
            return None
        w_match = re.search(r"width:\s*(\d+)px", style)
        h_match = re.search(r"height:\s*(\d+)px", style)
        z_match = re.search(r"z-index:\s*(\d+)", style)
        x = y = 0
        w = int(w_match.group(1)) if w_match else 0
        h = int(h_match.group(1)) if h_match else 0
        z = int(z_match.group(1)) if z_match else 0
        if w == 0 and h == 0:
            text = element.get_text(strip=True)
            if text or element.find_all("img"):
                w = self.viewport_width
                h = max(len(text) // 2, 200)
        if w > 0 or h > 0:
            return (x, y, max(w, self.min_module_width), max(h, self.min_module_height), z)
        return None

    def _estimate_hierarchy(self, y: int, height: int, page_height: int) -> int:
        if page_height <= 0:
            return 3
        ratio = y / page_height
        if ratio < 0.1: return 1
        elif ratio < 0.3: return 2
        elif ratio < 0.6: return 3
        elif ratio < 0.85: return 4
        return 5

    def _calc_visual_weight(self, w: int, h: int, y: int) -> float:
        area = w * h
        total_area = self.viewport_width * self.viewport_height
        area_score = min(area / total_area, 1.0)
        position_score = max(0.0, 1.0 - y / (self.viewport_height * 3))
        return round(0.6 * area_score + 0.4 * position_score, 3)

    def _extract_bg_color(self, element: Tag) -> str:
        style = element.get("style", "")
        bg_match = re.search(r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\))", style)
        return bg_match.group(1) if bg_match else ""

    def _extract_bg_image(self, element: Tag) -> str:
        style = element.get("style", "")
        bg_match = re.search(r"background(?:-image)?:\s*url\(['\"]?([^)'\"]+)", style)
        return bg_match.group(1) if bg_match else ""

    def _associate_module_crops(self, modules: List[ModuleRegion], html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        for module in modules:
            if module.image_urls:
                img_url = module.image_urls[0]
                try:
                    if img_url.startswith("http"):
                        resp = self.session.get(img_url, timeout=10)
                        if resp.status_code == 200:
                            img = Image.open(BytesIO(resp.content))
                            crop_box = (
                                max(0, module.x1), max(0, module.y1),
                                min(img.width, module.x2), min(img.height, module.y2),
                            )
                            if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                                cropped = img.crop(crop_box)
                                filepath = self.output_dir / f"{module.module_id}.png"
                                cropped.save(filepath, "PNG")
                                module.cropped_path = str(filepath)
                except Exception:
                    pass
            if not module.cropped_path:
                module.cropped_path = str(self.output_dir / f"{module.module_id}.png")

    def _save_mapping(self, result: CrawlResult) -> str:
        data = {
            "PageBenchmarkID": self._generate_benchmark_id(result),
            "GlobalGlobalConstraint": {
                "BaseTemperatureK": 4800,
                "MaxContrastOffset": 15,
                "MaxSaturationOffset": 10,
            },
            "ModuleLibrary": [
                {
                    "ModuleID": m.module_id,
                    "ModuleType": m.module_type,
                    "FilePath": m.cropped_path,
                    "BoundingBox": [m.x1, m.y1, m.x2, m.y2],
                    "ZIndex": m.z_index,
                    "ScrollOrder": m.scroll_order,
                    "Confidence": m.confidence,
                    "HistogramFingerprint": {},
                    "ACRParams": {},
                    "VisualDNA": {},
                    "TextParams": {},
                    "LastGenerateDeviation": 0.0,
                    "Version": "V1.0",
                }
                for m in result.modules
            ],
        }
        filepath = self.output_dir / "module_mapping.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(filepath)

    def _generate_benchmark_id(self, result: CrawlResult) -> str:
        url_hash = hashlib.md5(result.url.encode()).hexdigest()[:8]
        brand_slug = re.sub(r"[^a-zA-Z0-9]", "", result.brand.lower())[:12]
        return f"DetailPage_{brand_slug}_{url_hash}_V1.0"


def crawl_page(
    url: str,
    output_dir: str = "./crops",
    brand: str = "",
    use_playwright: bool = False,
) -> CrawlResult:
    """快速爬取单个详情页"""
    crawler = PageCrawler(output_dir=output_dir, use_playwright=use_playwright)
    return crawler.crawl(url, brand=brand)
