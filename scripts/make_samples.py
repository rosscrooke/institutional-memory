#!/usr/bin/env python3
"""Generate the committed samples/ directory from the full datasets in data/.

Prereqs:
  - scripts/download_polyvore.sh has run (metadata at minimum; --with-images
    for the sample images to be copied)
  - data/fashionpedia/instances_attributes_val2020.json (14.5 MB):
    curl -fsSL -o data/fashionpedia/instances_attributes_val2020.json \
      https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_val2020.json

Run: python3 scripts/make_samples.py
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SAMPLES = ROOT / "samples"

N_OUTFITS = 3
N_COMPAT_LINES = 5  # per label (5 positive + 5 negative)
N_FITB = 2
N_FASHIONPEDIA_IMAGES = 2


def sample_polyvore():
    src = DATA / "polyvore"
    out = SAMPLES / "polyvore"
    out.mkdir(parents=True, exist_ok=True)

    metadata = json.loads((src / "polyvore_item_metadata.json").read_text())
    outfits = json.loads((src / "nondisjoint" / "train.json").read_text())

    # Pick the first N outfits of 4+ items whose items all have metadata
    picked = []
    for o in outfits:
        ids = [i["item_id"] for i in o["items"]]
        if len(ids) >= 4 and all(i in metadata for i in ids):
            picked.append(o)
        if len(picked) == N_OUTFITS:
            break

    item_ids = [i["item_id"] for o in picked for i in o["items"]]
    (out / "outfits_sample.json").write_text(json.dumps(picked, indent=2))
    (out / "items_sample.json").write_text(
        json.dumps({i: metadata[i] for i in item_ids}, indent=2)
    )

    # Compatibility task lines: "1 <set_id>_<index> ..." = compatible outfit, "0 ..." = not
    pos, neg = [], []
    with open(src / "nondisjoint" / "compatibility_train.txt") as f:
        for line in f:
            (pos if line.startswith("1") else neg).append(line)
            if len(pos) >= N_COMPAT_LINES and len(neg) >= N_COMPAT_LINES:
                break
    (out / "compatibility_sample.txt").write_text(
        "".join(pos[:N_COMPAT_LINES] + neg[:N_COMPAT_LINES])
    )

    fitb = json.loads((src / "nondisjoint" / "fill_in_blank_train.json").read_text())
    (out / "fill_in_blank_sample.json").write_text(json.dumps(fitb[:N_FITB], indent=2))

    shutil.copy(src / "categories.csv", out / "categories.csv")

    images = src / "images"
    if images.is_dir():
        img_out = out / "images"
        img_out.mkdir(exist_ok=True)
        missing = 0
        for i in item_ids:
            f = images / f"{i}.jpg"
            if f.exists():
                shutil.copy(f, img_out / f.name)
            else:
                missing += 1
        print(f"polyvore: copied {len(item_ids) - missing} images ({missing} missing)")
    else:
        print("polyvore: images/ not unzipped yet — rerun after --with-images finishes")
    print(f"polyvore: {len(picked)} outfits, {len(item_ids)} items")


def sample_fashionpedia():
    src = DATA / "fashionpedia" / "instances_attributes_val2020.json"
    out = SAMPLES / "fashionpedia"
    out.mkdir(parents=True, exist_ok=True)
    d = json.loads(src.read_text())

    # Full label space — small and exactly what a builder needs
    (out / "categories.json").write_text(json.dumps(d["categories"], indent=2))
    (out / "attributes.json").write_text(json.dumps(d["attributes"], indent=2))

    # Pick CC-licensed images that have several annotated garments
    lic_ok = {l["id"] for l in d["licenses"] if "creativecommons" in l.get("url", "")}
    by_image = {}
    for a in d["annotations"]:
        by_image.setdefault(a["image_id"], []).append(a)
    picked = [
        img for img in d["images"]
        if img["license"] in lic_ok and len(by_image.get(img["id"], [])) >= 4
    ][:N_FASHIONPEDIA_IMAGES]

    anns = [a for img in picked for a in by_image[img["id"]]]
    licenses = [l for l in d["licenses"] if l["id"] in {i["license"] for i in picked}]
    (out / "annotations_sample.json").write_text(
        json.dumps({"images": picked, "annotations": anns, "licenses": licenses}, indent=2)
    )

    img_out = out / "images"
    img_out.mkdir(exist_ok=True)
    for img in picked:
        dest = img_out / img["file_name"]
        if not dest.exists():
            subprocess.run(
                ["curl", "-fsSL", "-o", str(dest), img["original_url"]], check=True
            )
    print(f"fashionpedia: {len(picked)} images, {len(anns)} annotations")


def sample_sanzo_wada():
    out = SAMPLES / "sanzo-wada"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "colors.json"
    if not dest.exists():
        subprocess.run(
            ["curl", "-fsSL", "-o", str(dest), "https://sanzo-wada.dmbk.io/assets/colors.json"],
            check=True,
        )
    n = len(json.loads(dest.read_text())["colors"])
    print(f"sanzo-wada: full dataset committed ({n} colors)")


if __name__ == "__main__":
    sample_polyvore()
    sample_fashionpedia()
    sample_sanzo_wada()
