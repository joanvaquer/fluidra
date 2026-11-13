"""Runtime configuration, read from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("POOL_ASSISTANT_DATA_DIR", ROOT / "data"))
MANUALS_DIR = DATA_DIR / "manuals"
CURATED_DIR = DATA_DIR / "curated"
INDEX_PATH = DATA_DIR / "index" / "chunks.jsonl"
MANIFEST_PATH = MANUALS_DIR / "manifest.json"
# Folder holding the manual PDFs named in the manifest ("file" is relative to it).
PDF_DIR = Path(os.getenv("POOL_ASSISTANT_PDF_DIR", ROOT / "Fluidra_GenAI_Engineer_Technical_Assessment_v1"))

# "auto": use Claude when credentials are present, otherwise run offline.
# "claude": always use Claude (fails if no credentials).
# "offline": deterministic heuristics only, no LLM calls (tests, demos without a key).
LLM_MODE = os.getenv("POOL_ASSISTANT_LLM", "auto").lower()
MODEL = os.getenv("POOL_ASSISTANT_MODEL", "claude-opus-5-5")

# How many times the writer may revise a draft after the verifier rejects it.
MAX_REVISIONS = int(os.getenv("POOL_ASSISTANT_MAX_REVISIONS", "1"))
# BM25 candidates fetched before the retriever agent selects evidence.
RETRIEVAL_CANDIDATES = 12
# Evidence chunks handed to the downstream agents.
EVIDENCE_K = 5
