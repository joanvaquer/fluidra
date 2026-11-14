"""Turn the manuals listed in the manifest into chunks, one or more per page.

The manual has the same content in 9 languages, so only the page ranges declared in the
manifest are indexed. Chunks never cross a page boundary, so every chunk can be cited
with an exact page number.

Steps: read each PDF page -> drop headers and page numbers -> split the page at section
headings -> replace the troubleshooting table (which extracts as garbled text) with the
hand-curated rows -> save everything as one JSON line per chunk.
"""

import json
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


def load_manifest(path: Path = config.MANIFEST_PATH) -> list[dict]:
    """The list of manuals: file, product, page ranges to index, troubleshooting table file."""
    return json.loads(path.read_text(encoding="utf-8"))["manuals"]


def load_troubleshooting(manual: dict) -> TroubleshootingMatrix | None:
    """The manual's curated troubleshooting table, or None if it has none."""
    if not manual.get("troubleshooting"):
        return None
    path = config.CURATED_DIR / manual["troubleshooting"]
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


def chunk_manual(manual: dict) -> list[Chunk]:
    """All the chunks of one manual, for the page ranges listed in the manifest."""
    reader = PdfReader(config.PDF_DIR / manual["file"])
    chunks = []
    for lang in manual["sections"]:  # e.g. the English pages, 5 to 14
        section, subheading = "Safety Information", ""  # the first pages come before any heading
        for page in range(lang["first_page"], lang["last_page"] + 1):
            text = reader.pages[page - 1].extract_text() or ""  # pypdf counts pages from 0
            # drop empty and noise lines, and use a plain apostrophe so searches match
            lines = [ln.replace("’", "'") for ln in text.splitlines() if ln.strip() and not NOISE_RE.match(ln)]
            # the section and subheading carry over to the next page
            blocks, section, subheading = split_page(lines, section, subheading)
            for i, (title, body) in enumerate(blocks):
                chunks.append(Chunk(
                    chunk_id=f"{manual['doc_id']}:{lang['language']}:p{page}:{i}",
                    doc_id=manual["doc_id"],
                    product=manual["product"],
                    language=lang["language"],
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
    """The chunks of every manual in the manifest."""
    chunks = []
    for manual in load_manifest():
        manual_chunks = chunk_manual(manual)
        matrix = load_troubleshooting(manual)
        if matrix:
            # replace the garbled table text with the curated rows
            manual_chunks = [
                c for c in manual_chunks
                if not (c.page == matrix.source_page and c.section.startswith("7."))
            ]
            manual_chunks += matrix_to_chunks(matrix)
        chunks += manual_chunks
    return chunks


def write_index(chunks: list[Chunk], path: Path = config.INDEX_PATH):
    """Save the chunks as JSON Lines: one chunk per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(c.model_dump_json() + "\n" for c in chunks), encoding="utf-8")


def read_index(path: Path = config.INDEX_PATH) -> list[Chunk]:
    """Load the chunks saved by write_index."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Chunk.model_validate_json(line) for line in lines if line.strip()]
