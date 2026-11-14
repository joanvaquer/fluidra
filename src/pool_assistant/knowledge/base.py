import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from pool_assistant import config
from pool_assistant.knowledge import ingestion
from pool_assistant.schemas import Chunk, Evidence, TroubleshootingMatrix

STOPWORDS = set(
    "a an the and or of to in on for with is are be by it its this that as at from if do does "
    "not no can should my i we you what how when why which there their after before into".split()
)


def tokenize(text: str) -> list[str]:
    tokens = []
    for t in re.findall(r"[a-z0-9]+", text.lower()):
        if t in STOPWORDS:
            continue
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]  # "pumps" -> "pump"
        tokens.append(t)
    return tokens


class KnowledgeBase:
    def __init__(self, chunks: list[Chunk], matrices: dict[str, TroubleshootingMatrix], products: list[str]):
        self.chunks = chunks
        self.matrices = matrices  # by product name
        self.products = products
        self.bm25 = BM25Okapi([tokenize(f"{c.section} {c.text}") for c in chunks])

    def search(self, query: str, k: int = 8, product: str | None = None) -> list[Evidence]:
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked:
            if scores[i] <= 0 or len(results) == k:
                break
            if product is None or self.chunks[i].product == product:
                results.append(Evidence(chunk=self.chunks[i], score=float(scores[i])))
        return results

    def search_many(self, queries: list[str], k: int, product: str | None = None) -> list[Evidence]:
        """Run several queries and merge the rankings (reciprocal rank fusion)."""
        fused = {}
        for query in queries:
            for rank, ev in enumerate(self.search(query, k=k, product=product)):
                fused[ev.chunk.chunk_id] = fused.get(ev.chunk.chunk_id, 0) + 1 / (60 + rank)
        by_id = {c.chunk_id: c for c in self.chunks}
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [Evidence(chunk=by_id[cid], score=fused[cid]) for cid in best]

    def matrix_for(self, product: str | None) -> TroubleshootingMatrix | None:
        if product:
            return self.matrices.get(product)
        if len(self.matrices) == 1:  # only one product indexed, so it must be that one
            return next(iter(self.matrices.values()))
        return None


def load_knowledge_base(index_path: Path = config.INDEX_PATH) -> KnowledgeBase:
    """Load the index, building it from the PDFs the first time."""
    if index_path.exists():
        chunks = ingestion.read_index(index_path)
    else:
        chunks = ingestion.build_chunks()
        ingestion.write_index(chunks, index_path)

    manuals = ingestion.load_manifest()
    matrices = {}
    for manual in manuals:
        matrix = ingestion.load_troubleshooting(manual)
        if matrix:
            matrices[matrix.product] = matrix
    products = sorted({m["product"] for m in manuals})
    return KnowledgeBase(chunks, matrices, products)
