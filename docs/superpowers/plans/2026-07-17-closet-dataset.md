# Closet Dataset Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `synthetic-data/closet/` — 100 clothing items (jsonl + 256px JPEG crops) sampled from the Fashionpedia val split.

**Architecture:** A pure-logic module (`scripts/closet_lib.py`: grouping, filtering, sampling, attribute splitting, naming, synthesis) tested with pytest, plus an I/O script (`scripts/build_closet_dataset.py`) that loads the cached annotations, crops images with Pillow, and writes the dataset with a built-in validation pass.

**Tech Stack:** Python 3, Pillow, pytest. Data already cached in `.fashionpedia-cache/` (annotations JSON + unzipped val/test images).

## Global Constraints

- Seeded RNG: `random.Random(42)` — output must be reproducible run-to-run.
- Output: exactly 100 records in `synthetic-data/closet/items.jsonl`; images `synthetic-data/closet/images/item_001.jpg` … `item_100.jpg`, max side 256px (never upscale), JPEG quality 85.
- Mix targets: 40 tops, 30 bottoms, 30 accessories; shortfall in one bucket fills from others; max 2 items per source photo.
- Min bounding box: 100×100px for tops/bottoms, 60×60px for accessories (accessory boxes are small in Fashionpedia; verified counts support 60px).
- Data reality (verified against `instances_attributes_val2020.json`): accessory instances carry **no attributes**; garment materials come only from attribute supercategories `leather` and `non-textile material type` (there is no denim/cotton/wool in the ontology) — pattern/finish/silhouette/etc. go in `attributes`.
- Category groups by Fashionpedia category id: tops = {0,1,2,3,4,5,9,10,11,12}, bottoms = {6,7,8}, accessories = {13,14,15,17,18,19,21,22,23,24,25,26}. Ids ≥27 (garment parts, closures, decorations) are excluded.

---

### Task 1: Pure selection/synthesis logic (`closet_lib.py`)

**Files:**
- Create: `scripts/closet_lib.py`
- Create: `tests/test_closet_lib.py`
- Modify: `requirements.txt` (append `pillow` and `pytest`)

**Interfaces:**
- Produces (used by Task 2):
  - `group_for(category_id: int) -> str | None` — "tops" | "bottoms" | "accessories" | None
  - `passes_filters(ann: dict) -> bool` — ann is a COCO annotation dict with `category_id`, `bbox`
  - `sample_items(annotations: list[dict], rng: random.Random, max_per_image: int = 2) -> list[dict]` — ~100 picked annotations honoring targets/caps
  - `split_attributes(attribute_ids: list[int], attr_index: dict[int, dict]) -> tuple[list[str], list[str]]` — (materials, other_attributes), names cleaned of parentheticals
  - `make_name(materials: list[str], attributes: list[str], category_name: str) -> str`
  - `synthesize(rng: random.Random) -> tuple[str, str]` — (condition, quality_tier)
  - Constants: `GROUP_TARGETS`, `MIN_BOX`, `MATERIAL_SUPERCATS`

- [ ] **Step 1: Install deps and write the failing test**

```bash
pip install pillow pytest
```

Append to `requirements.txt`:

```
pillow
pytest
```

Create `tests/test_closet_lib.py`:

```python
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from closet_lib import (
    group_for, passes_filters, sample_items, split_attributes,
    make_name, synthesize, GROUP_TARGETS,
)


def ann(id, category_id, image_id, w, h, attrs=()):
    return {"id": id, "category_id": category_id, "image_id": image_id,
            "bbox": [0, 0, w, h], "attribute_ids": list(attrs)}


def test_group_for():
    assert group_for(6) == "bottoms"      # pants
    assert group_for(10) == "tops"        # dress
    assert group_for(24) == "accessories" # bag, wallet
    assert group_for(31) is None          # sleeve (garment part)


def test_passes_filters_thresholds():
    assert passes_filters(ann(1, 6, 1, 100, 100))        # garment at 100px
    assert not passes_filters(ann(2, 6, 1, 99, 300))     # garment under 100px
    assert passes_filters(ann(3, 24, 1, 60, 60))         # accessory at 60px
    assert not passes_filters(ann(4, 24, 1, 59, 200))    # accessory under 60px
    assert not passes_filters(ann(5, 31, 1, 500, 500))   # excluded category


def test_sample_respects_targets_and_image_cap():
    anns = []
    n = 0
    # 3 candidates per image -> cap of 2/image must bite
    for img in range(200):
        for _ in range(3):
            n += 1
            cid = [6, 0, 24][n % 3]
            size = 60 if cid == 24 else 100
            anns.append(ann(n, cid, img, size, size))
    picked = sample_items(anns, random.Random(42))
    assert len(picked) == sum(GROUP_TARGETS.values()) == 100
    from collections import Counter
    per_img = Counter(a["image_id"] for a in picked)
    assert max(per_img.values()) <= 2
    groups = Counter(group_for(a["category_id"]) for a in picked)
    assert groups == GROUP_TARGETS


def test_sample_is_deterministic():
    anns = [ann(i, 6, i, 120, 120) for i in range(60)]
    a = sample_items(anns, random.Random(42))
    b = sample_items(anns, random.Random(42))
    assert [x["id"] for x in a] == [x["id"] for x in b]


def test_sample_fills_shortfall_from_other_groups():
    # only 5 accessories exist; total candidates still >= 100
    anns = [ann(i, 24, 1000 + i, 80, 80) for i in range(5)]
    anns += [ann(100 + i, 6, i, 120, 120) for i in range(60)]
    anns += [ann(300 + i, 0, 500 + i, 120, 120) for i in range(60)]
    picked = sample_items(anns, random.Random(42))
    assert len(picked) == 100


def test_split_attributes():
    attr_index = {
        1: {"name": "suede", "supercategory": "leather"},
        2: {"name": "plain (pattern)", "supercategory": "textile pattern"},
        3: {"name": "washed", "supercategory": "textile finishing, manufacturing techniques"},
        4: {"name": "metal", "supercategory": "non-textile material type"},
    }
    materials, attrs = split_attributes([1, 2, 3, 4], attr_index)
    assert materials == ["suede", "metal"]
    assert attrs == ["plain", "washed"]


def test_make_name():
    assert make_name(["suede"], ["washed"], "jacket") == "suede washed jacket"
    assert make_name([], [], "bag, wallet") == "bag"
    assert make_name([], ["a", "b", "c"], "pants") == "a b pants"  # capped at 2 descriptors


def test_synthesize_values_and_determinism():
    c, t = synthesize(random.Random(7))
    assert c in {"new", "good", "worn", "needs repair"}
    assert t in {"luxury", "mid", "budget"}
    assert synthesize(random.Random(7)) == (c, t)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_closet_lib.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'closet_lib'`

- [ ] **Step 3: Implement `scripts/closet_lib.py`**

```python
"""Pure selection/synthesis logic for the closet dataset (no I/O)."""

TOPS = {0, 1, 2, 3, 4, 5, 9, 10, 11, 12}
BOTTOMS = {6, 7, 8}
ACCESSORIES = {13, 14, 15, 17, 18, 19, 21, 22, 23, 24, 25, 26}

GROUP_TARGETS = {"tops": 40, "bottoms": 30, "accessories": 30}
MIN_BOX = {"tops": 100, "bottoms": 100, "accessories": 60}
MATERIAL_SUPERCATS = {"leather", "non-textile material type"}

CONDITIONS = ["new", "good", "worn", "needs repair"]
CONDITION_WEIGHTS = [0.20, 0.45, 0.25, 0.10]
TIERS = ["luxury", "mid", "budget"]
TIER_WEIGHTS = [0.20, 0.50, 0.30]


def group_for(category_id):
    if category_id in TOPS:
        return "tops"
    if category_id in BOTTOMS:
        return "bottoms"
    if category_id in ACCESSORIES:
        return "accessories"
    return None


def passes_filters(ann):
    group = group_for(ann["category_id"])
    if group is None:
        return False
    min_side = MIN_BOX[group]
    _, _, w, h = ann["bbox"]
    return w >= min_side and h >= min_side


def sample_items(annotations, rng, max_per_image=2):
    buckets = {g: [] for g in GROUP_TARGETS}
    for ann in annotations:
        if passes_filters(ann):
            buckets[group_for(ann["category_id"])].append(ann)
    for bucket in buckets.values():
        rng.shuffle(bucket)

    picked, per_image, leftovers = [], {}, []

    def take(ann):
        if per_image.get(ann["image_id"], 0) >= max_per_image:
            return False
        per_image[ann["image_id"]] = per_image.get(ann["image_id"], 0) + 1
        picked.append(ann)
        return True

    for group, target in GROUP_TARGETS.items():
        taken = 0
        for ann in buckets[group]:
            if taken < target and take(ann):
                taken += 1
            elif taken >= target:
                leftovers.append(ann)

    total = sum(GROUP_TARGETS.values())
    rng.shuffle(leftovers)
    for ann in leftovers:
        if len(picked) >= total:
            break
        take(ann)
    return picked


def _clean(name):
    return name.split("(")[0].strip()


def split_attributes(attribute_ids, attr_index):
    materials, attrs = [], []
    for aid in attribute_ids:
        attr = attr_index.get(aid)
        if attr is None:
            continue
        target = materials if attr["supercategory"] in MATERIAL_SUPERCATS else attrs
        target.append(_clean(attr["name"]))
    return materials, attrs


def make_name(materials, attributes, category_name):
    short_cat = category_name.split(",")[0].strip()
    descriptors = (materials + attributes)[:2]
    return " ".join(descriptors + [short_cat])


def synthesize(rng):
    condition = rng.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
    tier = rng.choices(TIERS, weights=TIER_WEIGHTS)[0]
    return condition, tier
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_closet_lib.py -q`
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/closet_lib.py tests/test_closet_lib.py requirements.txt
git commit -m "feat: closet dataset selection/synthesis logic"
```

---

### Task 2: Build script (`build_closet_dataset.py`) and dataset generation

**Files:**
- Create: `scripts/build_closet_dataset.py`
- Create (generated): `synthetic-data/closet/items.jsonl`, `synthetic-data/closet/images/item_*.jpg`

**Interfaces:**
- Consumes from Task 1: `sample_items(annotations, rng)`, `split_attributes(attribute_ids, attr_index) -> (materials, attrs)`, `make_name(materials, attrs, category_name) -> str`, `synthesize(rng) -> (condition, tier)`, `group_for(category_id)`.
- Produces: the dataset on disk. Acceptance test = the script's own validation pass (no unit tests; it is I/O glue over tested logic, run against real data).

- [ ] **Step 1: Write `scripts/build_closet_dataset.py`**

```python
"""Build synthetic-data/closet/ from the cached Fashionpedia val split.

Prereq: .fashionpedia-cache/ holds instances_attributes_val2020.json and the
unzipped val_test2020 images (URLs in the design doc,
docs/superpowers/specs/2026-07-17-closet-dataset-design.md).
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from closet_lib import group_for, make_name, sample_items, split_attributes, synthesize

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / ".fashionpedia-cache"
OUT = REPO / "synthetic-data" / "closet"
SEED = 42
TARGET_TOTAL = 100
PAD_FRACTION = 0.10
MAX_SIDE = 256
JPEG_QUALITY = 85


def load_data():
    ann_path = CACHE / "instances_attributes_val2020.json"
    if not ann_path.exists():
        sys.exit(f"Missing {ann_path} — download the Fashionpedia val annotations first.")
    return json.loads(ann_path.read_text())


def index_image_files():
    files = {}
    for p in (CACHE / "images").rglob("*.jpg"):
        files[p.name] = p
    if not files:
        sys.exit(f"No images found under {CACHE / 'images'} — unzip val_test2020.zip there.")
    return files


def crop_item(src_path, bbox, dst_path):
    x, y, w, h = bbox
    with Image.open(src_path) as im:
        im = im.convert("RGB")
        pad = PAD_FRACTION * max(w, h)
        left = max(0, int(x - pad))
        top = max(0, int(y - pad))
        right = min(im.width, int(x + w + pad))
        bottom = min(im.height, int(y + h + pad))
        crop = im.crop((left, top, right, bottom))
        crop.thumbnail((MAX_SIDE, MAX_SIDE))  # never upscales
        crop.save(dst_path, "JPEG", quality=JPEG_QUALITY)


def main():
    data = load_data()
    files = index_image_files()
    attr_index = {a["id"]: a for a in data["attributes"]}
    cat_index = {c["id"]: c["name"] for c in data["categories"]}
    images = {i["id"]: i for i in data["images"]}
    licenses = {l["id"]: l for l in data["licenses"]}

    rng = random.Random(SEED)
    picked = sample_items(data["annotations"], rng)

    (OUT / "images").mkdir(parents=True, exist_ok=True)
    records, skipped = [], 0
    for ann in picked:
        img = images[ann["image_id"]]
        src = files.get(img["file_name"])
        if src is None:
            skipped += 1
            print(f"skip: {img['file_name']} not in zip (annotation {ann['id']})")
            continue
        item_id = f"item_{len(records) + 1:03d}"
        image_rel = f"images/{item_id}.jpg"
        try:
            crop_item(src, ann["bbox"], OUT / image_rel)
        except OSError as e:
            skipped += 1
            print(f"skip: {img['file_name']} unreadable ({e})")
            continue
        materials, attrs = split_attributes(ann.get("attribute_ids", []), attr_index)
        condition, tier = synthesize(rng)
        category = cat_index[ann["category_id"]]
        lic = licenses.get(img.get("license"), {})
        records.append({
            "id": item_id,
            "name": make_name(materials, attrs, category),
            "category": category.split(",")[0].strip(),
            "group": group_for(ann["category_id"]),
            "material": materials,
            "attributes": attrs,
            "condition": condition,
            "quality_tier": tier,
            "image": image_rel,
            "source": {
                "fashionpedia_image_id": ann["image_id"],
                "annotation_id": ann["id"],
                "license": lic.get("name", "unknown"),
                "license_url": lic.get("url", ""),
                "original_url": img.get("original_url", ""),
            },
        })

    with open(OUT / "items.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Validation pass
    lines = (OUT / "items.jsonl").read_text().splitlines()
    assert all((OUT / json.loads(l)["image"]).exists() for l in lines), "missing image file"
    print(f"\nwrote {len(lines)} items, skipped {skipped}")
    print("groups:", dict(Counter(json.loads(l)["group"] for l in lines)))
    print("categories:", dict(Counter(json.loads(l)["category"] for l in lines)))
    print("conditions:", dict(Counter(json.loads(l)["condition"] for l in lines)))
    print("tiers:", dict(Counter(json.loads(l)["quality_tier"] for l in lines)))
    materials = Counter(m for l in lines for m in json.loads(l)["material"])
    print("materials:", dict(materials))
    if len(lines) < TARGET_TOTAL:
        sys.exit(f"FAILED: only {len(lines)}/{TARGET_TOTAL} items written")
    print("OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the build**

Run: `python3 scripts/build_closet_dataset.py`
Expected: `wrote 100 items, skipped 0`, group counts `{'tops': 40, 'bottoms': 30, 'accessories': 30}`, then `OK` (exit 0). If it exits nonzero, the shortfall message says how many were written — investigate skips before rerunning.

- [ ] **Step 3: Verify dataset size and reproducibility**

Run: `du -sh synthetic-data/closet && ls synthetic-data/closet/images | wc -l && shasum synthetic-data/closet/items.jsonl && python3 scripts/build_closet_dataset.py >/dev/null && shasum synthetic-data/closet/items.jsonl`
Expected: total well under ~5MB, 100 images, identical checksum after the rerun (reproducible).

- [ ] **Step 4: Commit script + dataset**

```bash
git add scripts/build_closet_dataset.py synthetic-data/closet
git commit -m "feat: build 100-item closet dataset from Fashionpedia val split"
```

---

### Task 3: Spot-check and spec sync

**Files:**
- Modify: `docs/superpowers/specs/2026-07-17-closet-dataset-design.md` (data-reality amendments)

**Interfaces:**
- Consumes: the generated dataset from Task 2.
- Produces: verified dataset + spec that matches reality.

- [ ] **Step 1: Visually spot-check ~5 crops**

Read 5 spread-out images (e.g. `item_001.jpg`, `item_025.jpg`, `item_050.jpg`, `item_075.jpg`, `item_100.jpg`) with the Read tool and compare each against its jsonl record — the crop should plausibly be the named category.
Expected: crops legible, categories match. If a crop is wrong/garbage, note the annotation id and re-check the crop math before shipping.

- [ ] **Step 2: Amend the spec's material/selection sections**

Update the spec: materials come from `leather` + `non-textile material type` supercategories only (no denim/cotton in Fashionpedia); accessories carry no attributes and use a 60×60px minimum box. Keep the rest as written.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-07-17-closet-dataset-design.md
git commit -m "docs: sync closet dataset spec with Fashionpedia data reality"
```
