# Architecture and deployment

## 1. Problem

Field technicians troubleshoot Fluidra equipment without knowing every product in depth.
They need short, correct, **sourced** answers from the official manuals, from a phone next
to the equipment. A wrong answer can damage equipment or injure someone, so grounding and
safety are more important than fluency.

## 2. Agent design

The work is split into five agents, each with **one responsibility and typed inputs and
outputs** (Pydantic models). A plain-Python orchestrator runs them in a fixed order.

The user picks one of **six modes** for every question; there is no default and no fallback
between them:

- **`qwen`, `llama`, `gemma`, `deepseek`**: free local LLMs run with **Ollama** (no paid
  services, as the brief requires). **Every agent makes its decisions with that model.** If a
  call fails, the question fails with an error, so the user knows which mode produced an answer.
- **`auto`**: the LLM (`qwen`, `AUTO_MODEL` in 1_config.py) only for **triage and writer**, the
  two steps that need language understanding. **Retriever, diagnostician and verifier** use
  the offline implementations (§ 2.1.1).
- **`offline`**: every agent uses word matching and fixed rules, with no LLM. Instant and
  deterministic, useful as a baseline to compare the models against.

| Agent | Responsibility | LLM modes | `offline` mode (also used by `auto` for 2, 3 and 5) |
|---|---|---|---|
| **1 Triage** | Is the question in scope? What intent (troubleshooting, installation, maintenance…)? Which language, product and symptoms? | JSON schema output: scope, intent, language, product, symptom ids from the manual's list, and the question rewritten as an English search query | Keyword lists; symptoms from the `keywords` in `data/curated/` |
| **2 Retriever** | Find the manual passages that answer the question | The LLM reads a numbered list of all passages (page, section, first 300 characters) and returns the relevant ones, most useful first | BM25 with the question and the symptom labels |
| **3 Diagnostician** | Troubleshooting only: rank the possible causes and fixes | The LLM picks rows of the troubleshooting table and gives each a likelihood, using the details in the question | Rows that share the matched symptoms; those that explain more symptoms rank first |
| **4 Writer** | Write the answer in the technician's language, with a `[p. N]` citation on every statement | The LLM, given the ranked causes and the excerpts; the prompt tells it when to add the safety warning | English templates; safety warning added when electrical words appear |
| **5 Verifier** | Last check before the answer is returned | The LLM answers yes/no checks (citations from the evidence, every statement supported, safety warning needed and present) and lists the issues | Rules: citations present, cited pages in the evidence, safety warning present |

A rejected answer goes back to the writer with the issues for one rewrite, when the writer is
an LLM (LLM and `auto` modes; offline templates would give the same text again).

```mermaid
flowchart TD
    Q[Technician question + mode] --> T[1 Triage]
    T -- out of scope --> R0[Polite refusal]
    T --> RET[2 Retriever]
    RET -- troubleshooting --> D[3 Diagnostician]
    RET -- other intents --> W[4 Writer]
    D --> W
    W --> V[5 Verifier]
    V -- rejected, first time --> W
    V -- approved --> A[Answer + sources + diagnosis + trace]
    V -- rejected again --> AU[Answer flagged as unverified]
    KB[(Manual chunks<br/>+ troubleshooting table)] -.-> RET
    KB -.-> D
```

### 2.1 Why these boundaries

- **Triage first.** Routing happens before any other work. Out-of-scope questions stop after one step, and only troubleshooting questions go to the diagnostician.
- **Retrieval is separate from writing.** The writer never searches; it only uses the evidence it is given. If nothing is found, it says so instead of guessing.
- **Diagnosis picks from the manual's table, never invents.** The LLM chooses and ranks rows by number; the cause and solution text is copied from the table in code. A row number that doesn't exist is dropped.
- **Writer and verifier are separate.** The verifier is an independent step with its own prompt, and its rejection gives the writer concrete feedback for a rewrite.

#### 2.1.1 Why `auto` splits the agents this way

- **Triage needs the LLM.** Paraphrases ("water barely comes out") and other languages are
  where keyword lists fail. The LLM maps them to the manual's symptom labels and an English
  search query, which is exactly what the offline retriever and diagnostician work with.
- **Retrieval is a search problem.** BM25 over 30 passages finds them in milliseconds, and the
  LLM retriever only sees 300-character previews anyway.
- **Diagnosis is a lookup.** Once triage has named the symptoms, the table rows follow from
  them; the LLM ranking mostly reorders the same rows.
- **The writer needs the LLM** to answer in the technician's language, in natural sentences.
- **The verifier's citation and safety checks are rules**, so a small model can't approve an
  answer with a made-up page or a missing disconnect-power warning. The safety words in
  `agents/0_common.py` cover the languages the writer answers in.
- **Trade-off:** `auto` does not check that each statement is supported by the evidence (the
  LLM verifier's `supported` check), only that the cited pages are real. An answer that says
  "not in the manual" without citing a page is rejected and flagged as unverified.

### 2.2 Key design decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| **Free local LLMs (Ollama), four to choose from** | No paid services; data stays on the machine. 3–4B models (or a mixture of experts like DeepSeek-V2 16B, which uses about 2.4B per token) run on a laptop CPU, and comparing them is one flag. | Slow on CPU and less reliable than a large model (§ 2.3). |
| **Every agent uses the LLM in LLM modes** | The agents judge with language understanding instead of word lists, so paraphrases and other languages work in every step. | Five calls per question (seven with a rewrite): minutes on a CPU. |
| **No fallback between modes** | An answer always comes from the mode the user chose, so comparisons between models are honest and failures are visible. | Without Ollama, only `offline` mode works. |
| **The LLM picks by number, code copies the text** | Symptoms, passages and table rows are chosen by id; unknown ids are dropped. The model can't put words in the manual's mouth. | — |
| **Structured output** | Ollama constrains every decision to the Pydantic model's JSON schema, so the orchestrator gets validated data, not free text. | — |
| **Code-controlled workflow, not an autonomous agent loop** | The routes are known in advance. A fixed flow is predictable, testable and easier to certify for a safety-relevant use case. | Less flexible for multi-step questions. |
| **Hand-curated troubleshooting table** | The PDF table extracts as unaligned text and loses which cause belongs to which symptom. It is the most valuable content for this use case, so it is transcribed from the rendered page (`data/curated/`). Its keywords are used only in offline mode. | Manual step per product. In production, a vision model extracts it and an expert approves it (§ 3.2). |
| **Page-level chunks with carried-over section titles** | Every chunk maps to exactly one page, so `[p. N]` citations are exact and verifiable. | Some passages are split at page breaks. |
| **The whole passage list in the retriever prompt** | One manual is 30 passages (about 3k tokens of previews), so the LLM can see them all. | Doesn't scale to many manuals; production needs a search step first (§ 3.2). |

### 2.3 Limitations of the prototype

- **Small models on CPU.** On a laptop without a GPU, an LLM question takes about 1–4 minutes. The first question is the slowest: Ollama loads the model and processes the passage list (later questions reuse it from Ollama's cache). Observed quality issues:
  - It sometimes picks the wrong symptom or cause (e.g. "the pump won't start" diagnosed as the thermal protection tripping).
  - It sometimes adds generic steps that aren't in the manual, or translates badly.
- **Safety now depends on the model.** In LLM modes, the safety warning is added by the writer and checked by the verifier, both LLM judgements. A small model can miss it. `auto` and `offline` modes check it with rules.
- **A small model checking another small model.** The LLM verifier tends to approve; using a different model for the verifier than for the writer would make it more independent.
- One manual, English section only (pages 5–14). The other languages duplicate the content, and the non-Latin pages extract as garbage without OCR.
- Figures (wiring diagrams, installation zones, priming) are not indexed.
- No conversation memory. Each question stands alone.
- No authentication, rate limiting or persistence.

### 2.4 Improvements

- **A larger model gives better results.** The four models are swapped with `--mode`; a new one is one line in `MODELS` in 1_config.py:
  - A bigger free local model (e.g. `qwen2.5:7b` or `llama3.1:8b` on Ollama) follows instructions, translates and stays on the evidence much better. It needs a GPU to be fast.
  - A hosted model (e.g. Claude, through its API or the cloud provider Fluidra already uses) gives the best quality and speed, paid per token (§ 3.5).
  - The choice should be made with the evaluation set (§ 3.3), with `offline` mode as the baseline and `auto` as the cheap middle option.
- **A different model per agent**, e.g. a small fast one for triage and a stronger one for writing and verifying. `auto` is a first step: the LLM only where it is needed.
- **Fewer calls**: triage and diagnosis could share one call, and the verifier could check only answers that involve electrical work or many claims.
- **Stream the writer's answer** so the technician sees text immediately instead of waiting for the whole reply.

---

## 3. Deploying to production

The prototype runs on one laptop, for one manual. In production the five agents and the
orchestrator stay the same; what changes is around them: a faster model, many manuals,
logins, and checks before every release.

### 3.1 The big picture

```mermaid
flowchart LR
    APP[Technician<br/>web or mobile app] --> SRV["Web app + orchestrator<br/>(containers in the cloud)"]
    SRV --> IDX[(Search index<br/>all manuals)]
    SRV --> LLM[LLM<br/>hosted or on a GPU]
    SRV --> DB[(Database<br/>conversations, feedback)]
    PDF[New or revised manual] --> ING[Ingestion<br/>PDF to passages] --> IDX
```

Each box is a standard managed service on any cloud provider. The simplest choice is the cloud
Fluidra already uses, so billing, accounts and EU data residency stay under existing contracts.

### 3.2 What changes from the prototype

| | Prototype | Production |
|---|---|---|
| **Model** | Small local models (3–4B) on a CPU: 1–4 minutes per answer | A hosted model (e.g. Claude) or a larger open model on a GPU: a few seconds |
| **Manuals** | One PDF; the English pages are set in `1_config.py`; the troubleshooting table is typed by hand | An ingestion step for every new or revised manual: read the PDF, detect languages, extract tables and diagrams with a vision model. **A product expert approves the tables** before they go live |
| **Search** | BM25 word search over 30 passages | Word search plus meaning-based search (embeddings), filtered by product first, since there will be hundreds of similar manuals |
| **Memory** | None: each question stands alone | The conversation is saved per session, so "it still doesn't work" makes sense |
| **Access** | Anyone who can open the app | Company login, and limits on requests per user |
| **Speed tricks** | None | Show the answer as it is written (streaming), and reuse the fixed parts of prompts (prompt caching) |
| **If the LLM is down** | The error is shown | The same, or offer `offline` mode with the answer marked as such |
| **Monitoring** | A per-agent trace in each reply | The same trace stored for every question, with dashboards and alerts on errors, time and cost |

### 3.3 Quality checks before each release

- **A test set** of about 150–300 real technician questions, written with Fluidra's technical
  service team, with the expected pages and facts. It is the `evaluation/` folder, made bigger.
- **Every change** to a prompt, model or search setting reruns it, and a change that makes the
  results worse is not released. The same test set decides which model to use.
- **Feedback in the app** (thumbs up/down, "this was wrong"). Confirmed mistakes are added to
  the test set.

### 3.4 Security and privacy

- Personal data (customer names, addresses) is removed before anything is logged, and data stays
  in the EU (GDPR). With a hosted model, check the provider's data-retention terms.
- The agents can't change anything (they only read and write text), and the LLM's replies are
  checked in code, which limits what a malicious question can do.
- Answers keep their page citations and safety warning, unverified answers are marked, and
  electrical work is always left to qualified personnel, as the manual requires.

### 3.5 Cost

- **Hosted model**: 2–5 calls per question, a few thousand words each: cents per question on a
  top model, much less on a smaller one.
- **Own model on a GPU**: no cost per call, but the GPU is paid for all the time.

### 3.6 Rollout

1. **Internal pilot** with the technical service team, who compare the answers with their own.
2. **A small group of field technicians**, on 2–3 product families.
3. **More products** as their manuals go through ingestion.
