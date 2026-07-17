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
        name = _clean(attr["name"])
        if name.startswith("no "):  # negative markers like "no non-textile material"
            continue
        target = materials if attr["supercategory"] in MATERIAL_SUPERCATS else attrs
        target.append(name)
    return materials, attrs


def make_name(materials, attributes, category_name):
    short_cat = category_name.split(",")[0].strip()
    descriptors = (materials + attributes)[:2]
    return " ".join(descriptors + [short_cat])


def synthesize(rng):
    condition = rng.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
    tier = rng.choices(TIERS, weights=TIER_WEIGHTS)[0]
    return condition, tier
