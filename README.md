# Pool Technician Assistant

A multi-agent GenAI application that answers pool technicians' technical questions about
Fluidra products, grounded in the official product manuals. The knowledge source is the
**ASTRAL Pool** pump manual provided with the assessment.

- **User-triggered**: the technician asks a question in a web app (Shiny) or a CLI.
- **Multi-agent**: five agents (1 Triage, 2 Retriever, 3 Diagnostician, 4 Writer, 5 Verifier),
  each with one responsibility, run in a fixed order by an orchestrator.
- **Six modes, always chosen by the user**:
  - `qwen`, `llama`, `gemma`, `deepseek`: free LLMs run locally by [Ollama](https://ollama.com).
    Every agent makes its decisions with that model. No paid services or API keys.
  - `auto`: the LLM (`qwen`) only where language understanding matters, triage and writer.
    Retriever, diagnostician and verifier use search and fixed rules. Two LLM calls per
    question instead of five, and the citation and safety checks are rules a model can't skip.
  - `offline`: every agent uses word matching and fixed rules, with no LLM.

  There is no default and no fallback: if an LLM call fails, the question fails with an error.
- **Grounded**: every statement cites a manual page, and a verifier checks the answer before
  it is returned.

Design decisions, limitations and the production deployment plan: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## How it works

```
question → 1 Triage ──(out of scope)──► refusal
              │
           2 Retriever                    picks the manual passages that answer the question
              │
              ├─(troubleshooting)─► 3 Diagnostician   ranked causes from the manual's troubleshooting table
              │                          │
           4 Writer ◄────────────────────┘           answer in the technician's language, with [p. N] citations
              │  ▲
           5 Verifier                                citations, grounding and safety; a rejected answer is rewritten once
              │
           answer + sources + diagnosis + trace
```

| Agent | LLM modes | `auto` mode | `offline` mode |
|---|---|---|---|
| 1 Triage | The LLM decides scope, intent, language, product and symptoms, and writes an English search query | LLM | Keyword lists, and the `keywords` in `data/curated/` for the symptoms |
| 2 Retriever | The LLM reads the list of manual passages and picks the relevant ones | offline | BM25 word search with the question, the search query and the symptom labels |
| 3 Diagnostician | The LLM picks and ranks rows of the troubleshooting table | offline | Rows that share the matched symptoms |
| 4 Writer | The LLM writes the answer and adds the safety warning when needed | LLM | Fixed templates; the safety warning is added when electrical words appear |
| 5 Verifier | The LLM checks citations, grounding and the safety warning | offline | Fixed rules: citations present, cited pages in the evidence, safety warning present |

In `auto` mode the offline agents work from the LLM triage: its symptoms use the manual's
wording and its search query is in English, so paraphrases and other languages still reach
the right passages and table rows. A rejected answer is rewritten by the LLM writer with the
rules' issues. What `auto` doesn't check is whether each statement is backed by the evidence
(the LLM verifier's `supported` check); it only checks that the cited pages are real.

In the LLM modes, code only drops what isn't in the manual: made-up symptom, passage or row
numbers are ignored, and causes and solutions are always copied from the table.

## Setup

Requires Python 3.11+, and [Ollama](https://ollama.com/download) for the LLM modes.

```bash
# 1. The models you want to use
ollama pull qwen2.5:3b
ollama pull llama3.2:3b
ollama pull gemma3:4b
ollama pull deepseek-v2:16b

# 2. Python environment
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

# 3. Build the index from the PDF (also done automatically on first run)
python scripts/ingest.py
```

| Mode | Ollama model | Size | Notes |
|---|---|---|---|
| `qwen` | `qwen2.5:3b` | 1.9 GB | Alibaba. Fast, reliable JSON. |
| `llama` | `llama3.2:3b` | 2.0 GB | Meta. |
| `gemma` | `gemma3:4b` | 3.3 GB | Google. |
| `deepseek` | `deepseek-v2:16b` | 8.9 GB | DeepSeek. Mixture of experts: uses ~2.4B parameters per token, so it runs about as fast as the others on CPU, but needs ~10 GB of RAM. |
| `auto` | `qwen2.5:3b` | 1.9 GB | The LLM for triage and writer only (`AUTO_MODEL` in config.py). |
| `offline` | none | — | No Ollama needed. Answers in milliseconds, English templates only. |

To use a different size (e.g. `llama3.1:8b`), change its tag in `MODELS` in
[config.py](src/pool_assistant/config.py). Reasoning models such as `deepseek-r1` don't work
well here: they reason before every reply, which takes minutes on CPU and uses up the token
limit before the JSON is written.

## Usage

**Web app**

```bash
pool-assistant-web
```

Opens a chat at http://127.0.0.1:8000. Pick the mode in the sidebar (any of the six; there is
no default), type the question, and tick *Show what each agent did* to see the trace. If the
LLM is not available or a call fails, the chat shows the error.

**CLI** (`--mode` is required)

```bash
pool-assistant "Water barely comes out of my pump and I think there's air getting in" --mode llama
pool-assistant "La bomba no arranca" --mode deepseek --trace
pool-assistant "Mi bomba hace ruido" --mode auto
pool-assistant "The pump makes a noise" --mode offline
```

`--trace` shows the mode and model, what each agent did and how long it took. On a laptop CPU
an LLM question takes about 1–4 minutes: five LLM calls, seven with a rewrite. In `auto` mode
it is two calls, three with a rewrite. The first
question after starting is the slowest, because Ollama loads the model and reads the list of
passages for the first time.

If Ollama isn't running or the model isn't downloaded, the CLI stops with an error (and the
`ollama pull` command to run).

## Tests

```bash
pytest
```

The tests run offline mode, and the LLM and auto modes with a fake model, so they take a few seconds and don't need Ollama.

## Project layout

```
Fluidra_GenAI_Engineer_Technical_Assessment_v1/
  user_manual.pdf                the source manual
data/
  manuals/manifest.json          product metadata and which pages are in English
  curated/*_troubleshooting.json troubleshooting table transcribed from the manual (p. 13);
                                 the symptom keywords are only used in offline mode
src/pool_assistant/
  agents/                        the five agents, numbered in run order:
    1_triage.py 2_retriever.py 3_diagnostician.py 4_writer.py 5_verifier.py
    common.py                    shared helpers (keyword matching, citations, safety text)
  knowledge/                     PDF chunking, and BM25 search for offline and auto modes
  llm.py                         Ollama client
  orchestrator.py                runs the agents for a question
  schemas.py                     data passed between agents and returned to the app
  webapp.py, cli.py              entry points: Shiny chat and command line
scripts/ingest.py                rebuilds the index
docs/ARCHITECTURE.md             design, limitations and deployment
docs/MODULES.md                  how the Python files use each other (diagrams)
evaluation/                      comparison of the six modes (REPORT.md)
```
