"""Rebuild the chunk index from the manuals in data/manuals/manifest.json.

    python scripts/ingest.py

Run it after adding or changing a manual. (The app also builds the index by itself the first
time, if data/index/chunks.jsonl doesn't exist.)
"""

from __future__ import annotations

from collections import Counter

from pool_assistant import config
from pool_assistant.knowledge.ingestion import build_chunks, write_index


def main() -> None:
    # read the PDFs, split them into passages and save them to data/index/chunks.jsonl
    chunks = build_chunks()
    write_index(chunks)
    # print how many passages each manual produced, as a quick check
    per_doc = Counter(c.doc_id for c in chunks)
    print(f"Wrote {len(chunks)} chunks to {config.INDEX_PATH}")
    for doc_id, n in per_doc.items():
        print(f"  {doc_id}: {n} chunks")


if __name__ == "__main__":
    main()
