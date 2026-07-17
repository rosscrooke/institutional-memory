#!/usr/bin/env bash
# Download the Polyvore Outfits dataset (Stylique/Polyvore mirror on Hugging Face)
# into data/polyvore/ (git-ignored). ~2.75 GB after skipping the legacy HGLMM
# feature files (14 GB of pre-LLM text features we don't use).
#
# Usage: ./scripts/download_polyvore.sh [--with-images]
#   default:       metadata + outfit splits + hard negatives (~250 MB)
#   --with-images: also fetch images.zip (2.5 GB) and unzip it
set -euo pipefail

REPO="https://huggingface.co/datasets/Stylique/Polyvore/resolve/main"
DEST="$(cd "$(dirname "$0")/.." && pwd)/data/polyvore"
mkdir -p "$DEST"

FILES=(
  categories.csv
  polyvore_item_metadata.json
  polyvore_outfit_titles.json
  disjoint/compatibility_test.txt
  disjoint/compatibility_train.txt
  disjoint/compatibility_valid.txt
  disjoint/fill_in_blank_test.json
  disjoint/fill_in_blank_train.json
  disjoint/fill_in_blank_valid.json
  disjoint/test.json
  disjoint/train.json
  disjoint/valid.json
  disjoint/typespaces.p
  nondisjoint/compatibility_test.txt
  nondisjoint/compatibility_train.txt
  nondisjoint/compatibility_valid.txt
  nondisjoint/fill_in_blank_test.json
  nondisjoint/fill_in_blank_train.json
  nondisjoint/fill_in_blank_valid.json
  nondisjoint/test.json
  nondisjoint/train.json
  nondisjoint/valid.json
  nondisjoint/typespaces.p
  maryland_polyvore_hardneg/compatibility_test.txt
  maryland_polyvore_hardneg/compatibility_train.txt
  maryland_polyvore_hardneg/compatibility_valid.txt
  maryland_polyvore_hardneg/fill_in_blank_test.json
  maryland_polyvore_hardneg/fill_in_blank_train.json
  maryland_polyvore_hardneg/fill_in_blank_valid.json
)

for f in "${FILES[@]}"; do
  out="$DEST/$f"
  if [[ -s "$out" ]]; then
    echo "skip (exists): $f"
    continue
  fi
  echo "downloading: $f"
  curl -fSL --retry 3 --create-dirs -o "$out" "$REPO/$f"
done

if [[ "${1:-}" == "--with-images" ]]; then
  if [[ ! -d "$DEST/images" ]]; then
    if [[ ! -s "$DEST/images.zip" ]]; then
      echo "downloading: images.zip (2.5 GB)"
      curl -fSL --retry 3 -C - -o "$DEST/images.zip" "$REPO/images.zip"
    fi
    echo "unzipping images.zip"
    unzip -q "$DEST/images.zip" -d "$DEST"
  else
    echo "skip (exists): images/"
  fi
fi

echo "done → $DEST"
