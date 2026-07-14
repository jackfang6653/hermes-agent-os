# NORHOR Brand Project — Hermes Agent OS 模板

This directory provides the **NORHOR brand intelligence project template** for 
Hermes Agent OS. It defines the complete workflow for generating brand-compliant 
product detail page images.

## Directory Structure

```
norhor/
├── brand/              — Brand profile & DNA
├── categories/         — Product category tree
├── products/           — Product schema definitions
├── scenes/             — Scene library & presets
├── prompts/            — Prompt template library
├── detail_pages/       — Detail page structure
├── workflows/          — Pipeline definitions
├── workflows/          — QA checkpoints
└── assets/             — Reference images (gitignored)
```

## Pipeline

```
analyze_product → extract_dna → create_scene → compile_prompt
    → generate_image → qa_check → export
```

## Usage

```bash
# Generate a NORHOR detail page
hermes run norhor-pipeline --sku CS-001 --style nordic

# Validate against brand
hermes validate norhor --product prod-1

# Export
hermes export norhor --project proj-1 --format html
```

## Quick Start

1. Place product images in `assets/products/`
2. Run `hermes analyze product-001.jpg` to extract product data
3. Run `hermes run norhor-pipeline` to generate detail pages
4. Export as HTML or ZIP with `hermes export`

## Configuration

See `docs/hep/HEP-018-NORHOR-Brand-Project/` for full design specification.
