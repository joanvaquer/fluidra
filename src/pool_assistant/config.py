import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
MANIFEST_PATH = DATA_DIR / "manuals" / "manifest.json"
CURATED_DIR = DATA_DIR / "curated"
INDEX_PATH = DATA_DIR / "index" / "chunks.jsonl"
PDF_DIR = ROOT / "Fluidra_GenAI_Engineer_Technical_Assessment_v1"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

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

# The user always picks one of these. There is no default and no fallback between them.
# - an LLM from MODELS: every agent uses that model;
# - "auto": the LLM (AUTO_MODEL) only where language understanding matters, triage and
#   writer; retriever, diagnostician and verifier use search and fixed rules;
# - "offline": every agent uses word matching and fixed rules, with no LLM.
AUTO = "auto"
OFFLINE = "offline"
MODES = (*MODELS, AUTO, OFFLINE)
AUTO_MODEL = "qwen"                    # the fastest model with reliable JSON
AUTO_LLM_AGENTS = {"triage", "writer"}  # the agents that use the LLM in auto mode

EVIDENCE_K = 4     # passages passed from the retriever to the other agents
MAX_REVISIONS = 1  # times the writer can rewrite an answer the verifier rejected
