"""Knowledge base: chunk store + lexical index + curated troubleshooting tables.

BM25 is enough for one 10-page manual and runs with no model or service. In
production this sits behind the same `search` interface but is backed by hybrid
(BM25 + embeddings) search in a managed vector store; see docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rank_bm25 import BM25Okapi

from pool_assistant import config
from pool_assistant.knowledge import ingestion
from pool_assistant.schemas import Chunk, Evidence, TroubleshootingMatrix

_STOPWORDS = set(
    "a an the and or of to in on for with is are be by it its this that as at from if do does "
    "not no can should my i we you what how when why which there their after before into".split()
)


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for t in tokens:
        if t in _STOPWORDS:
            continue
        # Crude plural folding so "pumps" matches "pump" without a stemmer dependency.
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.append(t)
    return out


@dataclass
class KnowledgeBase:
    chunks: list[Chunk]
    matrices: dict[str, TroubleshootingMatrix] = field(default_factory=dict)  # by product
    products: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._by_id = {c.chunk_id: c for c in self.chunks}
        self._bm25 = BM25Okapi([tokenize(f"{c.section} {c.text}") for c in self.chunks])

    def get(self, chunk_id: str) -> Chunk | None:
        return self._by_id.get(chunk_id)

    def search(self, query: str, k: int = 8, product: str | None = None) -> list[Evidence]:
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        hits = []
        for i in ranked:
            chunk = self.chunks[i]
            if scores[i] <= 0:
                break
            if product and chunk.product != product:
                continue
            hits.append(Evidence(chunk=chunk, score=float(scores[i])))
            if len(hits) == k:
                break
        return hits

    def search_many(self, queries: list[str], k: int, product: str | None = None) -> list[Evidence]:
        """Run several queries and fuse them with reciprocal-rank fusion."""
        fused: dict[str, float] = {}
        for query in queries:
            for rank, ev in enumerate(self.search(query, k=k, product=product)):
                fused[ev.chunk.chunk_id] = fused.get(ev.chunk.chunk_id, 0.0) + 1.0 / (60 + rank)
        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [Evidence(chunk=self._by_id[cid], score=round(s, 5)) for cid, s in ordered]


def load_knowledge_base(
    manifest_path: Path = config.MANIFEST_PATH,
    index_path: Path = config.INDEX_PATH,
) -> KnowledgeBase:
    """Load the prebuilt index, or build it from the manuals on first run."""
    if index_path.exists():
        chunks = ingestion.read_index(index_path)
    else:
        chunks = ingestion.build_chunks(manifest_path)
        ingestion.write_index(chunks, index_path)

    manuals = ingestion.load_manifest(manifest_path)
    curated_dir = manifest_path.parent.parent / "curated"
    matrices = {}
    for manual in manuals:
        matrix = ingestion.load_troubleshooting(manual, curated_dir)
        if matrix:
            matrices[matrix.product] = matrix
    products = sorted({m["product"] for m in manuals})
    return KnowledgeBase(chunks=chunks, matrices=matrices, products=products)
