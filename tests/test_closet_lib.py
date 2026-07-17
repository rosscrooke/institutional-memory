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
        5: {"name": "no non-textile material", "supercategory": "non-textile material type"},
        6: {"name": "no waistline", "supercategory": "waistline"},
    }
    materials, attrs = split_attributes([1, 2, 3, 4, 5, 6], attr_index)
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
