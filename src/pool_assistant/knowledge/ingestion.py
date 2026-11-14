"""Turn the manual into chunks, one or more per page.

The manual has the same content in 9 languages, so only the English pages (FIRST_PAGE to
LAST_PAGE in config.py) are indexed. Chunks never cross a page boundary, so every chunk can
be cited with an exact page number.

Steps: read each PDF page -> drop headers and page numbers -> split the page at section
headings -> replace the troubleshooting table (which extracts as garbled text) with the
hand-curated rows -> save everything as one JSON line per chunk.
"""

import re
from pathlib import Path

from pypdf import PdfReader

from pool_assistant import config
from pool_assistant.schemas import Chunk, TroubleshootingMatrix

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
