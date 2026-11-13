# Pool Technician Assistant

A multi-agent GenAI application that answers pool technicians' technical questions about
Fluidra products, grounded in the official product manuals. Built for the Fluidra GenAI
Engineer technical assessment, using the AstralPool **Victoria Plus Silent** pump manual
as the knowledge source.

- **User-triggered**: a technician submits a question through the REST API or the CLI.
- **Multi-agent**: five agents (Triage, Retriever, Diagnostician, Writer, Verifier) with
  separate responsibilities, connected by an explicit orchestrator.
- **Grounded and safe**: every statement cites a manual page, a verifier checks the
  answer against the evidence, and electrical work always comes with the manual's
  disconnect-power warning.
- **Runs without paid services**: with no API key it runs in a deterministic offline mode
  (as the brief allows). With a key, every agent uses Claude.

Design and production deployment: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## How it works

```
question → Triage ──(out of scope)──► polite refusal
             │
         Retriever  (BM25 candidates → LLM selects evidence)
             │
             ├─(troubleshooting)─► Diagnostician  (symptoms → ranked causes from the manual's matrix)
             │                          │
           Writer ◄─────────────────────┘   answer in the technician's language, [p. N] citations
             │  ▲
          Verifier  policy checks + grounding review; a rejection sends issues back to the writer
             │
          answer + sources + diagnosis + verification status + per-agent trace
```

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

python scripts/ingest.py          # build the index (also built automatically on first run)
```

### Choosing the LLM mode

| `POOL_ASSISTANT_LLM` | Behaviour |
|---|---|
| `auto` (default) | Claude if `ANTHROPIC_API_KEY` is set, otherwise offline |
| `claude` | Always Claude (`POOL_ASSISTANT_MODEL`, default `claude-opus-5-5`) |
| `offline` | No LLM calls. Each agent uses its deterministic fallback |

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # optional
```

### CLI

```bash
pool-assistant "The pump makes a noise but will not start" --trace
pool-assistant --mode offline "How often should I replace the mechanical seal?"
pool-assistant --json "Mi bomba hace ruido, ¿qué hago?"
pool-assistant                           # interactive session
```

Example output (offline mode):

```
**Reported symptom(s):** The pump is not primed; The pump only releases a small flow of water.

**Likely causes, most likely first:**
1. **Air entering the suction pipe** (high) - Check the condition of connections and seals on the suction pipe [p. 13]
2. **Motor turning in wrong direction** (high) - Invert 2 power phases [p. 13]
3. **Wrong voltage** (high) - Check the voltage on the rating plate and that of the mains [p. 13]
...
**Safety:** before any electrical or mechanical work, disconnect the pump from the mains, ... [p. 8]

Sources: Victoria Plus Silent manual (p. 9, p. 13)
[troubleshooting | en | verified | offline]

  triage              2 ms  intent=troubleshooting lang=en product=Victoria Plus Silent in_scope=True [offline]
  retriever           5 ms  5 passages from pages [9, 13] [offline]
  diagnostician       1 ms  6 candidate causes [offline]
  writer              2 ms  draft 1, cites pages [5, 8, 13] [offline]
  verifier            0 ms  approved [offline]
```

### REST API

```bash
uvicorn pool_assistant.api:app --reload
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "The motor has stopped and the thermal protection trips"}'
```

Interactive docs are at `http://localhost:8000/docs`. The response contains `answer`,
`intent`, `language`, `product`, `verified`, `sources` (page, section, snippet),
`diagnosis`, `verification_issues` and the per-agent `trace`.

## Tests

```bash
pytest
```

The tests need no API key. They cover ingestion and retrieval, the offline pipeline, the
REST API, and the LLM path with a scripted fake LLM. That includes the verifier → writer
revision loop, the "unverified" flag, fallback when an LLM call fails, dropping
hallucinated product names, and the Claude adapter's request and refusal handling.

## Project layout

```
Fluidra_GenAI_Engineer_Technical_Assessment_v1/
  user_manual.pdf                source manual (PDFs named in the manifest are read from here)
data/
  manuals/manifest.json          product metadata + which pages hold which language
  curated/*_troubleshooting.json troubleshooting matrix transcribed from the manual (p. 13)
  index/chunks.jsonl             generated chunk index
src/pool_assistant/
  orchestrator.py                agent graph, revision loop, trace
  agents/                        triage, retriever, diagnostician, writer, verifier (+ shared helpers)
  knowledge/                     PDF ingestion/chunking, BM25 knowledge base
  llm.py                         Claude adapter (structured outputs) and mode selection
  schemas.py                     typed contracts between agents and the API response
  api.py, cli.py                 entry points
scripts/ingest.py                rebuild the index
tests/                           offline, scripted-LLM and API tests
docs/ARCHITECTURE.md             design rationale and production deployment plan
```

## Adding a manual

1. Put the PDF in `Fluidra_GenAI_Engineer_Technical_Assessment_v1/` (or set `POOL_ASSISTANT_PDF_DIR`) and add an entry to `data/manuals/manifest.json` (file name, product and language page ranges).
2. Optionally add a curated troubleshooting matrix in `data/curated/`.
3. Run `python scripts/ingest.py`.
