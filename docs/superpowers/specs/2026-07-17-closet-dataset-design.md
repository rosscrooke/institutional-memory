# Closet Dataset Design — ~100 items from Fashionpedia

**Date:** 2026-07-17
**Status:** Approved (approach A)

## Purpose

Build a small (~100 item) clothing dataset for the clueless memory-agent demo: a
"closet" of individual items (tops, bottoms, accessories) that vary on category,
material, and quality. The agent reasons over structured metadata; small images sit
alongside each item for display in a demo UI (and optional vision calls later).

## Source

Fashionpedia validation split:

- Images: `https://s3.amazonaws.com/ifashionist-dataset/images/val_test2020.zip` (236MB, ~3,200 photos)
- Annotations: `https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_val2020.json` (14.5MB)

Annotations are COCO-format with per-garment bounding boxes, 27 apparel categories,
and 294 fine-grained attributes (materials, silhouettes, styles). Individual garments
are cropped out of outfit photos to become closet items.

Downloads go to `.fashionpedia-cache/` (gitignored); the pipeline never re-downloads
if the files are present.

## Output

`synthetic-data/closet/` — committed to the repo (small enough that teammates never
run the pipeline):

- `items.jsonl` — 100 records, one per line
- `images/item_NNN.jpg` — one crop per item, max side 256px, JPEG quality ~85 (~10–30KB each)

### Record schema

```json
{
  "id": "item_001",
  "name": "washed straight-leg denim pants",
  "category": "pants",
  "group": "bottoms",
  "material": ["denim"],
  "attributes": ["straight-leg", "washed"],
  "condition": "good",
  "quality_tier": "mid",
  "image": "images/item_001.jpg",
  "source": {"fashionpedia_image_id": 12345, "annotation_id": 67890, "license": "CC BY 2.0"}
}
```

- `category`, `material`, `attributes` come straight from Fashionpedia. `material`
  holds attribute names from the `leather` and `non-textile material type`
  supercategories — the only material-like supercategories in the ontology (there is
  no denim/cotton/wool attribute in Fashionpedia); `attributes` holds the rest
  (silhouette, length, neckline, pattern, finish). Negative markers ("no waistline",
  "no non-textile material", …) are dropped. Accessory instances carry no attributes
  at all in Fashionpedia, so accessories have empty `material`/`attributes` and are
  named by bare category.
- `condition` (new | good | worn | needs repair) and `quality_tier`
  (luxury | mid | budget) are synthesized with a seeded RNG (fixed seed, weighted
  toward a realistic closet mix) so output is reproducible.
- `name` is composed from attributes + category for readability.
- `source.license` carries the Flickr CC license from the image metadata for attribution.

## Selection rules

Target mix: ~40 tops (shirt/blouse, top/t-shirt/sweatshirt, sweater, cardigan,
jacket, coat, dress), ~30 bottoms (pants, shorts, skirt), ~30 accessories (bag/wallet,
shoe, glasses, hat, belt, watch, scarf/tie, headband).

Filters:

- Bounding box ≥ 100×100px for tops/bottoms; ≥ 60×60px for accessories (accessory
  boxes are small — watches/glasses almost never reach 100px)
- At most 2 items per source photo (variety)
- Crops get ~10% padding around the bbox, clamped to image bounds

If a bucket falls short after filtering, the pipeline reports the shortfall and fills
from the other buckets rather than failing.

## Pipeline

One script: `scripts/build_closet_dataset.py`

1. Verify cache (download annotations + zip if missing, unzip)
2. Index annotations; bucket candidate instances by category group
3. Sample per the mix with a fixed seed
4. Crop/resize with Pillow; write JPEGs
5. Synthesize condition/quality_tier; compose names; write `items.jsonl`
6. Validate: 100 records, every referenced image exists, print counts per
   category/group/material

Errors: skip degenerate bboxes, unreadable images, and annotations whose image file
is missing from the zip; log each skip. Fail loudly (non-zero exit) if the total
falls below 100 after fallbacks.

## Testing

The validation pass in step 6 is the acceptance test. Additionally, spot-check ~5
crops visually and eyeball a few jsonl records for sane names/materials.

## Out of scope

Price/value, brands, wear history (user deselected); sending images to the model via
Files API; train-split download (4x+ larger, unnecessary for 100 items).
