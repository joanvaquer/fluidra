"""Turn the manuals listed in the manifest into page-cited chunks.

The manual is multilingual (9 languages, ~10 pages each). The manifest declares which
page range holds which language, so only those ranges are indexed and every chunk keeps
its page number for citations. Chunks never span pages; the current section heading is
carried across pages so a chunk on page 12 still knows it belongs to "5. MAINTENANCE".
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

from pool_assistant import config
from pool_assistant.schemas import Chunk, TroubleshootingMatrix

# "3. INSTALLATION AND ASSEMBLY", "7. TROUBLESHOOTING"
SECTION_RE = re.compile(r"^\s*(\d{1,2})\s?\.\s+([A-Z][A-Z ,\-/']{3,})\s*$")
# "PIPING", "WARNINGS DURING START-UP", "ELECTRICAL INSTALLATION"
SUBHEADING_RE = re.compile(r"^\s*([A-Z][A-Z ,\-/']{3,})\s*$")
# Running headers/footers and language tabs that add noise to retrieval.
NOISE_RE = re.compile(
    r"^\s*(\d{1,3}|ENGLISH|Installation and general maintenance manual - POOL PUMPS\s*\d*)\s*$"
)
MAX_CHUNK_CHARS = 1200


def load_manifest(path: Path = config.MANIFEST_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["manuals"]


def _clean_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.replace("’", "'").replace(" ", " ").rstrip()
        if not line.strip() or NOISE_RE.match(line):
            continue
        lines.append(line)
    return lines


def _split_blocks(
    lines: list[str], section: str, subheading: str
) -> tuple[list[tuple[str, str]], str, str]:
    """Group a page's lines into (section, text) blocks at headings and size limits.

    The section and sub-heading in force at the end of the page are returned so the
    next page continues under them.
    """
    blocks: list[tuple[str, str]] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            label = f"{section} > {subheading}" if subheading else section
            body = "\n".join(current).strip()
            if body:
                blocks.append((label, body))
            current.clear()

    for line in lines:
        if m := SECTION_RE.match(line):
            flush()
            section = f"{m.group(1)}. {m.group(2).strip().title()}"
            subheading = ""
            continue
        if SUBHEADING_RE.match(line) and len(line.split()) <= 6:
            flush()
            subheading = line.strip().title()
            continue
        if sum(len(x) for x in current) + len(line) > MAX_CHUNK_CHARS:
            flush()
        current.append(line.strip())
    flush()
    return blocks, section, subheading


def chunk_manual(manual: dict, pdf_dir: Path = config.PDF_DIR) -> list[Chunk]:
    reader = PdfReader(pdf_dir / manual["file"])
    chunks: list[Chunk] = []
    for lang_section in manual["sections"]:
        section, subheading = "Safety Information", ""
        for page_no in range(lang_section["first_page"], lang_section["last_page"] + 1):
            text = reader.pages[page_no - 1].extract_text() or ""
            blocks, section, subheading = _split_blocks(_clean_lines(text), section, subheading)
            for i, (label, body) in enumerate(blocks):
                chunks.append(
                    Chunk(
                        chunk_id=f"{manual['doc_id']}:{lang_section['language']}:p{page_no}:{i}",
                        doc_id=manual["doc_id"],
                        product=manual["product"],
                        language=lang_section["language"],
                        page=page_no,
                        section=label,
                        text=body,
                    )
                )
    return chunks


def load_troubleshooting(manual: dict, curated_dir: Path = config.CURATED_DIR) -> TroubleshootingMatrix | None:
    name = manual.get("troubleshooting")
    if not name:
        return None
    return TroubleshootingMatrix.model_validate_json((curated_dir / name).read_text(encoding="utf-8"))


def matrix_to_chunks(matrix: TroubleshootingMatrix) -> list[Chunk]:
    """Index each troubleshooting row as its own chunk, since the PDF table extracts badly."""
    labels = {s.id: s.label for s in matrix.symptoms}
    chunks = []
    for i, row in enumerate(matrix.rows):
        symptoms = "; ".join(labels[s] for s in row.symptoms)
        chunks.append(
            Chunk(
                chunk_id=f"{matrix.doc_id}:en:troubleshooting:{i}",
                doc_id=matrix.doc_id,
                product=matrix.product,
                language="en",
                page=matrix.source_page,
                section="7. Troubleshooting",
                text=f"Symptoms: {symptoms}.\nCause: {row.cause}.\nSolution: {row.solution}.",
            )
        )
    return chunks


def build_chunks(manifest_path: Path = config.MANIFEST_PATH) -> list[Chunk]:
    chunks: list[Chunk] = []
    for manual in load_manifest(manifest_path):
        page_chunks = chunk_manual(manual)
        matrix = load_troubleshooting(manual, manifest_path.parent.parent / "curated")
        if matrix:
            # The curated rows replace the garbled table text extracted from that page.
            page_chunks = [
                c for c in page_chunks
                if not (c.page == matrix.source_page and c.section.startswith("7."))
            ]
            page_chunks += matrix_to_chunks(matrix)
        chunks += page_chunks
    return chunks


def write_index(chunks: list[Chunk], path: Path = config.INDEX_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")


def read_index(path: Path = config.INDEX_PATH) -> list[Chunk]:
    with path.open(encoding="utf-8") as f:
        return [Chunk.model_validate_json(line) for line in f if line.strip()]
