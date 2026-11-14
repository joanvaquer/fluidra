"""Settings shared by the whole app: file paths, the Ollama models, the modes and a few limits.

Every other module reads its settings from here, so changing a model or a limit is a one-line edit.
"""

import os
from pathlib import Path

# --- file paths ---
# ROOT is the project folder: this file is src/pool_assistant/1_config.py, so two levels up.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PDF_PATH = ROOT / "Fluidra_GenAI_Engineer_Technical_Assessment_v1" / "user_manual.pdf"  # the manual
# the manual's troubleshooting table, transcribed by hand (it also gives the product name)
TROUBLESHOOTING_PATH = DATA_DIR / "curated" / "astral_pool_troubleshooting.json"
INDEX_PATH = DATA_DIR / "index" / "chunks.jsonl"  # the manual split into passages (built on first run)
# The manual repeats its content in 9 languages; only the English pages are indexed.
FIRST_PAGE, LAST_PAGE = 5, 14

# Address of the local Ollama server; can be changed with the OLLAMA_HOST environment variable.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# --- models ---
# Free models served locally by Ollama: name -> Ollama tag. Download one with `ollama pull <tag>`.
MODELS = {
    "qwen": "qwen2.5:3b",          # Alibaba, ~1.9 GB: fast and reliable with JSON
    "llama": "llama3.2:3b",        # Meta, ~2.0 GB
    "gemma": "gemma3:4b",          # Google, ~3.3 GB
    "deepseek": "deepseek-v2:16b", # DeepSeek, ~8.9 GB: mixture of experts, only ~2.4B parameters
                                   # used per token, so about as fast as the 3-4B models on CPU
}
# Reasoning models such as deepseek-r1 don't fit here: they "think" before every reply, which
# takes minutes on CPU and uses up the token limit before the JSON is written.

# --- modes ---
# The user always picks one of these. There is no default and no fallback between them.
# - an LLM from MODELS: every agent uses that model;
# - "auto": the LLM (AUTO_MODEL) only where language understanding matters, triage and
#   writer; retriever, diagnostician and verifier use search and fixed rules;
# - "offline": every agent uses word matching and fixed rules, with no LLM.
AUTO = "auto"
OFFLINE = "offline"
MODES = (*MODELS, AUTO, OFFLINE)        # ("qwen", "llama", "gemma", "deepseek", "auto", "offline")
AUTO_MODEL = "qwen"                    # the fastest model with reliable JSON
AUTO_LLM_AGENTS = {"triage", "writer"}  # the agents that use the LLM in auto mode

# --- limits ---
EVIDENCE_K = 4     # passages passed from the retriever to the other agents
MAX_REVISIONS = 1  # times the writer can rewrite an answer the verifier rejected
