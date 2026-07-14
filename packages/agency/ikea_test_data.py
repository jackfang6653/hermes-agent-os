"""
IKEA 3产品测试数据

模拟IKEA品牌下3款产品的 SceneGraph 分析数据，
用于驱动 Agency 5阶段全流程测试。
"""

IKEA_PRODUCTS = [
    {
        "image": "https://www.ikea.com/example/lack-table.jpg",
        "name": "LACK 拉克边桌",
        "brand": "IKEA",
        "category": "家具/桌类",
        "analysis": {
            "primary_palette": ["#f5f0e8", "#e8d5b7", "#8b7355", "#4a3728", "#2c2c2c"],
            "secondary_palette": ["#d4c5b0", "#a89070", "#6b5b4f"],
            "camera": {
                "focal_length_mm": 50,
                "aperture_f": 8.0,
                "iso": 200,
            },
            "lighting_signature": "大面积柔光 + 顶光补光",
            "lights": [
                {"type": "area", "modifier": "softbox_90cm", "temperature": 5500},
                {"type": "spot", "modifier": "grid", "temperature": 5000},
            ],
            "composition": {
                "rule": "居中对称构图",
                "angle": "45度俯拍",
                "background": "纯白无缝纸",
            },
            "materials": [
                {
                    "name": "刨花板台面",
                    "albedo": "#f5f0e8",
                    "roughness": 0.75,
                    "metallic": 0.05,
                    "normal_strength": 0.3,
                },
            ],
            "elements": [
                {
                    "id": "table_top",
                    "type": "surface",
                    "bbox_size": [55, 55, 3.4],
                    "bbox_center": [0, 0, 45],
                    "material": {"albedo": "#f5f0e8"},
                },
                {
                    "id": "leg_01",
                    "type": "cylinder",
                    "bbox_size": [5, 5, 41.6],
                    "bbox_center": [-22, -22, 22],
                    "material": {"albedo": "#4a3728"},
                },
            ],
        },
    },
    {
        "image": "https://www.ikea.com/example/billy-bookcase.jpg",
        "name": "BILLY 毕利书架",
        "brand": "IKEA",
        "category": "家具/柜类",
        "analysis": {
            "primary_palette": ["#ffffff", "#f0ede6", "#8b7355", "#3b3226", "#1a1a1a"],
            "secondary_palette": ["#d9d0c1", "#a39080"],
            "camera": {
                "focal_length_mm": 35,
                "aperture_f": 11.0,
                "iso": 100,
            },
            "lighting_signature": "均匀柔光 + 双侧补光",
            "lights": [
                {"type": "area", "modifier": "softbox_120cm", "temperature": 5600},
                {"type": "area", "modifier": "softbox_60cm", "temperature": 5500},
            ],
            "composition": {
                "rule": "三分法构图",
                "angle": "正面平拍",
                "background": "浅灰墙",
            },
            "materials": [
                {
                    "name": "刨花板书架面",
                    "albedo": "#ffffff",
                    "roughness": 0.65,
                    "metallic": 0.02,
                    "normal_strength": 0.25,
                },
            ],
            "elements": [
                {
                    "id": "shelf_body",
                    "type": "box",
                    "bbox_size": [80, 202, 28],
                    "bbox_center": [0, 0, 80],
                    "material": {"albedo": "#ffffff"},
                },
                {
                    "id": "shelf_board_01",
                    "type": "plane",
                    "bbox_size": [76, 2, 26],
                    "bbox_center": [0, -60, 80],
                    "material": {"albedo": "#ffffff"},
                },
            ],
        },
    },
    {
        "image": "https://www.ikea.com/example/malm-bed.jpg",
        "name": "MALM 马尔姆床架",
        "brand": "IKEA",
        "category": "家具/床类",
        "analysis": {
            "primary_palette": ["#4a3728", "#3b3226", "#e8d5b7", "#c4a882", "#2c2c2c"],
            "secondary_palette": ["#8b7355", "#a89070"],
            "camera": {
                "focal_length_mm": 24,
                "aperture_f": 5.6,
                "iso": 400,
            },
            "lighting_signature": "暖调氛围光 + 侧逆光",
            "lights": [
                {"type": "area", "modifier": "softbox_90cm", "temperature": 4500},
                {"type": "spot", "modifier": "barn_door", "temperature": 3800},
            ],
            "composition": {
                "rule": "引导线构图",
                "angle": "低角度仰拍",
                "background": "卧室实景",
            },
            "materials": [
                {
                    "name": "实木贴皮床头",
                    "albedo": "#8b7355",
                    "roughness": 0.55,
                    "metallic": 0.05,
                    "normal_strength": 0.45,
                },
            ],
            "elements": [
                {
                    "id": "bed_head",
                    "type": "plane",
                    "bbox_size": [160, 100, 4],
                    "bbox_center": [0, 0, 40],
                    "material": {"albedo": "#8b7355"},
                },
                {
                    "id": "bed_mattress",
                    "type": "box",
                    "bbox_size": [150, 200, 20],
                    "bbox_center": [0, 0, 80],
                    "material": {"albedo": "#ffffff"},
                },
            ],
        },
    },
]

# 竞品
IKEA_COMPETITORS = ["MUJI", "NITORI", "HAY"]

# 品牌摘要
IKEA_BRAND = "IKEA"
