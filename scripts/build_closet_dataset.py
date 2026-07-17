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
