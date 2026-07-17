# Dataset samples

Small committed slices of each dataset so you can see the shapes and start
building without downloading anything. Regenerate with
`python3 scripts/make_samples.py`; get the full data with
`scripts/download_polyvore.sh --with-images` (goes to git-ignored `data/`).

## polyvore/ — outfit compatibility (the pairing dataset)

Full set: 251k items, 68k outfits. Source: [Stylique/Polyvore on HF](https://huggingface.co/datasets/Stylique/Polyvore).

- `outfits_sample.json` — 3 outfits; each is `{set_id, items: [{item_id, index}]}`
- `items_sample.json` — metadata for those outfits' 15 items, keyed by `item_id`:
  `url_name`, `description`, `category_id`, `semantic_category` (tops/bottoms/shoes/bags/…).
  Note the dataset's typo: the field is spelled `catgeories`.
- `images/` — the 15 item photos (flat catalog shots, `<item_id>.jpg`)
- `categories.csv` — full mapping: `category_id, fine-grained name, semantic_category`
- `compatibility_sample.txt` — the compatibility task: `1|0 <set_id>_<index> ...`
  (1 = human-curated outfit, 0 = negative). Full train has ~17k lines.
- `fill_in_blank_sample.json` — the FITB task: `question` (outfit minus one item),
  `answers` (4 candidates), `blank_position`

Caveat: the mirror claims MIT but licensing is murky (Polyvore shut down in 2018).
Fine for this assignment; don't ship it.

## fashionpedia/ — per-garment attributes (the metadata schema)

Full set: 48k images with segmentation masks. Source: [fashionpedia.github.io](https://fashionpedia.github.io/home/Fashionpedia_download.html).

- `categories.json` — the FULL 46-category garment taxonomy (id, name, supercategory)
- `attributes.json` — the FULL 294-attribute vocabulary (silhouette, pattern,
  neckline, fit…) — useful as-is for our outfit-judging schema
- `annotations_sample.json` — 2 CC-licensed images + their 26 garment annotations
  (`category_id`, `attribute_ids`, `bbox`, segmentation polygons), COCO format
- `images/` — those 2 photos (from their original Flickr URLs; licenses included
  in the sample JSON)

## sanzo-wada/ — color harmony (this is the ENTIRE dataset, 85 KB)

Source: [sanzo-wada.dmbk.io](https://sanzo-wada.dmbk.io/) (Sanzo Wada's 1930s
"Dictionary of Color Combinations").

- `colors.json` — 157 colors with `hex`, `rgb_array`, `cmyk_array`, and
  `combinations` (ids of the 348 curated combination groups a color belongs to).
  Two colors sharing a combination id = "goes together" per Wada.
