"""The knowledge base: the manual split into passages, and a word search over them.

Part 1 builds the index (on first run, or with `python -m pool_assistant.knowledge`): read each English page of the
PDF (FIRST_PAGE to LAST_PAGE in 1_config.py) -> drop headers and page numbers -> split the page
at section headings -> replace the troubleshooting table (which extracts as garbled text) with
the hand-curated rows -> save one JSON line per passage in data/index/chunks.jsonl.
Passages never cross a page boundary, so every one can be cited with an exact page number.

Part 2 loads that index and searches it with BM25. Every agent that needs the manual gets it
from the KnowledgeBase object built by load_knowledge_base().
"""

import re
from pathlib import Path

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

from pool_assistant import config
from pool_assistant.schemas import Chunk, Evidence, TroubleshootingMatrix

# =========================================================================================
# Part 1: build the index from the PDF
# =========================================================================================

# Patterns that recognise the structure of a page's text:
SECTION_RE = re.compile(r"^\s*(\d{1,2})\s?\.\s+([A-Z][A-Z ,\-/']{3,})\s*$")  # "7. TROUBLESHOOTING"
SUBHEADING_RE = re.compile(r"^\s*([A-Z][A-Z ,\-/']{3,})\s*$")               # "PIPING"
# lines to drop: page numbers, the language label and the repeated page header
NOISE_RE = re.compile(r"^\s*(\d{1,3}|ENGLISH|Installation and general maintenance manual - POOL PUMPS\s*\d*)\s*$")
MAX_CHUNK_CHARS = 1200  # a longer block is split, so each passage stays focused


def load_troubleshooting(path: Path = config.TROUBLESHOOTING_PATH) -> TroubleshootingMatrix:
    """The manual's hand-curated troubleshooting table."""
    return TroubleshootingMatrix.model_validate_json(path.read_text(encoding="utf-8"))


def split_page(lines: list[str], section: str, subheading: str):
    """Split a page into (section title, text) blocks.

    The current section and subheading are returned so the next page continues under them.
    """
    blocks, current = [], []  # finished blocks, and the lines of the block being built

    def flush():
        # close the block being built (if any) under the current title
        if current:
            title = f"{section} > {subheading}" if subheading else section
            blocks.append((title, "\n".join(current)))
            current.clear()

    for line in lines:
        if m := SECTION_RE.match(line):
            # a numbered section heading, e.g. "3. INSTALLATION AND ASSEMBLY": start a new section
            flush()
            section, subheading = f"{m.group(1)}. {m.group(2).strip().title()}", ""
        elif SUBHEADING_RE.match(line) and len(line.split()) <= 6:
            # a short line in capitals, e.g. "PIPING": start a new subsection
            flush()
            subheading = line.strip().title()
        else:
            # ordinary text: add it to the current block, starting a new one if it gets too long
            if sum(len(x) for x in current) + len(line) > MAX_CHUNK_CHARS:
                flush()
            current.append(line.strip())
    flush()
    return blocks, section, subheading


def chunk_manual(doc_id: str, product: str) -> list[Chunk]:
    """All the chunks of the manual's English pages."""
    reader = PdfReader(config.PDF_PATH)
    chunks = []
    section, subheading = "Safety Information", ""  # the first pages come before any heading
    for page in range(config.FIRST_PAGE, config.LAST_PAGE + 1):
        text = reader.pages[page - 1].extract_text() or ""  # pypdf counts pages from 0
        # drop empty and noise lines, and use a plain apostrophe so searches match
        lines = [ln.replace("’", "'") for ln in text.splitlines() if ln.strip() and not NOISE_RE.match(ln)]
        # the section and subheading carry over to the next page
        blocks, section, subheading = split_page(lines, section, subheading)
        for i, (title, body) in enumerate(blocks):
            chunks.append(Chunk(
                chunk_id=f"{doc_id}:en:p{page}:{i}",
                doc_id=doc_id,
                product=product,
                language="en",
                page=page,
                section=title,
                text=body,
            ))
    return chunks


def matrix_to_chunks(matrix: TroubleshootingMatrix) -> list[Chunk]:
    """One chunk per troubleshooting row (the PDF table doesn't extract cleanly)."""
    labels = {s.id: s.label for s in matrix.symptoms}
    # each row becomes a short readable passage: "Symptoms: ... Cause: ... Solution: ..."
    return [
        Chunk(
            chunk_id=f"{matrix.doc_id}:en:troubleshooting:{i}",
            doc_id=matrix.doc_id,
            product=matrix.product,
            language="en",
            page=matrix.source_page,
            section="7. Troubleshooting",
            text=f"Symptoms: {'; '.join(labels[s] for s in row.symptoms)}.\n"
                 f"Cause: {row.cause}.\nSolution: {row.solution}.",
        )
        for i, row in enumerate(matrix.rows)
    ]


def build_chunks() -> list[Chunk]:
    """All the chunks: the manual's pages, with the troubleshooting table's curated rows."""
    matrix = load_troubleshooting()
    chunks = chunk_manual(matrix.doc_id, matrix.product)
    # replace the garbled table text with the curated rows
    chunks = [c for c in chunks if not (c.page == matrix.source_page and c.section.startswith("7."))]
    return chunks + matrix_to_chunks(matrix)


def write_index(chunks: list[Chunk], path: Path = config.INDEX_PATH):
    """Save the chunks as JSON Lines: one chunk per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(c.model_dump_json() + "\n" for c in chunks), encoding="utf-8")


def read_index(path: Path = config.INDEX_PATH) -> list[Chunk]:
    """Load the chunks saved by write_index."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Chunk.model_validate_json(line) for line in lines if line.strip()]


# =========================================================================================
# Part 2: load the index and search it
# =========================================================================================

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
        chunks = read_index(index_path)
    else:
        chunks = build_chunks()
        write_index(chunks, index_path)

    # 2. The troubleshooting table, which also gives the product name.
    matrix = load_troubleshooting()
    return KnowledgeBase(chunks, {matrix.product: matrix}, [matrix.product])


# Rebuild the index by hand, after changing the manual, its page range or the troubleshooting
# table:  python -m pool_assistant.knowledge
if __name__ == "__main__":
    chunks = build_chunks()
    write_index(chunks)
    print(f"Wrote {len(chunks)} chunks to {config.INDEX_PATH}")
