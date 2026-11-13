"""Rebuild the chunk index from the manuals in data/manuals/manifest.json.

    python scripts/ingest.py
"""

from __future__ import annotations

from collections import Counter

from pool_assistant import config
from pool_assistant.knowledge.ingestion import build_chunks, write_index


def main() -> None:
    chunks = build_chunks()
    write_index(chunks)
    per_doc = Counter(c.doc_id for c in chunks)
    print(f"Wrote {len(chunks)} chunks to {config.INDEX_PATH}")
    for doc_id, n in per_doc.items():
        print(f"  {doc_id}: {n} chunks")


if __name__ == "__main__":
    main()
