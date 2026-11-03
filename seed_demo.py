"""
Seed script for demo data.

Loads synthetic-data/round1 docs as Items into data/items/
No Claude calls needed — just file I/O.

Usage:
    python seed_demo.py
"""

from pathlib import Path
from core import save_json


def main():
    docs_dir = Path("synthetic-data/round1")
    if not docs_dir.exists():
        print(f"ERROR: {docs_dir} not found")
        return

    for doc_path in sorted(docs_dir.glob("*.md")):
        text = doc_path.read_text()
        title = doc_path.stem.replace("-", " ").title()

        item = {
            "title": title,
            "source": "upload",
            "text": text,
            "tags": [],
            "category": "Policy",
            "summary_short": None,
            "summary_long": None,
        }

        item_id = save_json("items", item)
        print(f"Saved {item_id[:8]}... {title}")

    print("\nDemo data seeded. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
