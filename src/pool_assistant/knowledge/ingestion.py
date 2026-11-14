"""Turn the manuals listed in the manifest into chunks, one or more per page.

The manual has the same content in 9 languages, so only the page ranges declared in the
manifest are indexed. Chunks never cross a page boundary, so every chunk can be cited
with an exact page number.
"""

import json
import re
from pathlib import Path

from pypdf import PdfReader

from pool_assistant import config
from pool_assistant.schemas import Chunk, TroubleshootingMatrix

SECTION_RE = re.compile(r"^\s*(\d{1,2})\s?\.\s+([A-Z][A-Z ,\-/']{3,})\s*$")  # "7. TROUBLESHOOTING"
SUBHEADING_RE = re.compile(r"^\s*([A-Z][A-Z ,\-/']{3,})\s*$")               # "PIPING"
NOISE_RE = re.compile(r"^\s*(\d{1,3}|ENGLISH|Installation and general maintenance manual - POOL PUMPS\s*\d*)\s*$")
MAX_CHUNK_CHARS = 1200


def load_manifest(path: Path = config.MANIFEST_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["manuals"]


def load_troubleshooting(manual: dict) -> TroubleshootingMatrix | None:
    if not manual.get("troubleshooting"):
        return None
    path = config.CURATED_DIR / manual["troubleshooting"]
    return TroubleshootingMatrix.model_validate_json(path.read_text(encoding="utf-8"))


def split_page(lines: list[str], section: str, subheading: str):
    """Split a page into (section title, text) blocks.

    The current section and subheading are returned so the next page continues under them.
    """
    blocks, current = [], []

    def flush():
        if current:
            title = f"{section} > {subheading}" if subheading else section
            blocks.append((title, "\n".join(current)))
            current.clear()

    for line in lines:
        if m := SECTION_RE.match(line):
            flush()
            section, subheading = f"{m.group(1)}. {m.group(2).strip().title()}", ""
        elif SUBHEADING_RE.match(line) and len(line.split()) <= 6:
            flush()
            subheading = line.strip().title()
        else:
            if sum(len(x) for x in current) + len(line) > MAX_CHUNK_CHARS:
                flush()
            current.append(line.strip())
    flush()
    return blocks, section, subheading


def chunk_manual(manual: dict) -> list[Chunk]:
    reader = PdfReader(config.PDF_DIR / manual["file"])
    chunks = []
    for lang in manual["sections"]:
        section, subheading = "Safety Information", ""
        for page in range(lang["first_page"], lang["last_page"] + 1):
            text = reader.pages[page - 1].extract_text() or ""
            lines = [ln.replace("’", "'") for ln in text.splitlines() if ln.strip() and not NOISE_RE.match(ln)]
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(c.model_dump_json() + "\n" for c in chunks), encoding="utf-8")


def read_index(path: Path = config.INDEX_PATH) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Chunk.model_validate_json(line) for line in lines if line.strip()]
