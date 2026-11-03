#!/usr/bin/env python3
"""Seed the app with real client data from synthetic-data/clients/."""

import sys
from pathlib import Path
from core import save_json

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent))

def extract_frontmatter_and_content(file_path):
    """Extract YAML frontmatter and markdown content from a file."""
    text = Path(file_path).read_text()

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    frontmatter_text = parts[1].strip()
    content = parts[2].strip()

    # Parse simple YAML frontmatter
    frontmatter = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip("'\"")

    return frontmatter, content


def seed_clients():
    """Load all client documents from synthetic-data/clients/ into data/items/."""
    clients_dir = Path("synthetic-data/clients").resolve()

    if not clients_dir.exists():
        print(f"Directory {clients_dir} not found")
        return

    item_count = 0
    for client_file in sorted(clients_dir.rglob("*.md")):
        fm, content = extract_frontmatter_and_content(client_file)

        client = fm.get("client", "Unknown")
        doc_type = fm.get("type", "document")
        date = fm.get("date", "")
        title = fm.get("title", client_file.stem)

        # Create item record
        item = {
            "title": f"[{doc_type}] {title}",
            "source": "document",
            "text": content,
            "tags": [client.lower().replace(" ", "-"), doc_type],
            "category": client,
            "metadata": {
                "client": client,
                "doc_type": doc_type,
                "date": date,
                "file": str(client_file.name),
            },
        }

        item_id = save_json("items", item)
        item_count += 1
        print(f"✓ {title[:50]}... ({client})")

    print(f"\n✓ Seeded {item_count} items")


if __name__ == "__main__":
    seed_clients()
