"""The knowledge base: the manual passages, a BM25 word search over them, and the
troubleshooting tables. Every agent that needs the manual gets it from here.
"""

import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from pool_assistant import config
from pool_assistant.knowledge import ingestion
from pool_assistant.schemas import Chunk, Evidence, TroubleshootingMatrix

# Words so common they say nothing about what a passage is about; the search ignores them.
STOPWORDS = set(
    "a an the and or of to in on for with is are be by it its this that as at from if do does "
    "not no can should my i we you what how when why which there their after before into".split()
)


def tokenize(text: str) -> list[str]:
    """Split text into the lowercase words the search compares, e.g.
    "The pumps are noisy" -> ["pump", "noisy"]."""
    tokens = []
    for t in re.findall(r"[a-z0-9]+", text.lower()):
        if t in STOPWORDS:
            continue
        # a very simple plural removal, so "pumps" matches "pump" ("glass" stays as it is)
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]  # "pumps" -> "pump"
        tokens.append(t)
    return tokens


class KnowledgeBase:
    """All the manual content, loaded once and shared by the agents."""

    def __init__(self, chunks: list[Chunk], matrices: dict[str, TroubleshootingMatrix], products: list[str]):
        self.chunks = chunks
        self.matrices = matrices  # by product name
        self.products = products
        # BM25 is a classic search ranking: passages that share more (and rarer) words with
        # the query score higher. The section title is added so a heading also counts.
        self.bm25 = BM25Okapi([tokenize(f"{c.section} {c.text}") for c in chunks])

    def search(self, query: str, k: int = 8, product: str | None = None) -> list[Evidence]:
        """The k passages that best match the query, best first (only those of `product` if given)."""
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked:
            # stop at k results, or when the passages no longer share any word with the query
            if scores[i] <= 0 or len(results) == k:
                break
            if product is None or self.chunks[i].product == product:
                results.append(Evidence(chunk=self.chunks[i], score=float(scores[i])))
        return results

    def search_many(self, queries: list[str], k: int, product: str | None = None) -> list[Evidence]:
        """Run several queries and merge the rankings (reciprocal rank fusion)."""
        # Each passage gets 1 / (60 + its rank) from every query that finds it, so a passage
        # ranked well by several queries beats one ranked first by a single query.
        fused = {}
        for query in queries:
            for rank, ev in enumerate(self.search(query, k=k, product=product)):
                fused[ev.chunk.chunk_id] = fused.get(ev.chunk.chunk_id, 0) + 1 / (60 + rank)
        by_id = {c.chunk_id: c for c in self.chunks}
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [Evidence(chunk=by_id[cid], score=fused[cid]) for cid in best]

    def matrix_for(self, product: str | None) -> TroubleshootingMatrix | None:
        """The troubleshooting table of a product, or None if there isn't one."""
        if product:
            return self.matrices.get(product)
        if len(self.matrices) == 1:  # only one product indexed, so it must be that one
            return next(iter(self.matrices.values()))
        return None


def load_knowledge_base(index_path: Path = config.INDEX_PATH) -> KnowledgeBase:
    """Load the index, building it from the PDFs the first time."""
    # 1. The passages: read the saved index, or build it from the PDFs (slow) and save it.
    if index_path.exists():
        chunks = ingestion.read_index(index_path)
    else:
        chunks = ingestion.build_chunks()
        ingestion.write_index(chunks, index_path)

    # 2. The troubleshooting table, which also gives the product name.
    matrix = ingestion.load_troubleshooting()
    return KnowledgeBase(chunks, {matrix.product: matrix}, [matrix.product])
