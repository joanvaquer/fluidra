# How the Python files fit together

This page maps the code: which file uses which, what happens to one question, and what every
file is for. The arrows come from the real `import` statements in the code. For the design
reasons behind them, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Which file uses which

An arrow `A → B` means *A uses B*. The layers read top to bottom: the entry points start
everything, the orchestrator runs the agents, and the agents use the knowledge base.

```mermaid
flowchart TD
    subgraph entry["Entry points: how a person runs it"]
        WEB["webapp.py<br/><i>Shiny chat</i>"]
        CLI["cli.py<br/><i>command line</i>"]
        RUN["evaluation/run.py<br/><i>asks the test questions</i>"]
        REP["evaluation/report.py<br/><i>scores the answers</i>"]
        ING["scripts/ingest.py<br/><i>rebuilds the index</i>"]
    end

    ORCH["orchestrator.py<br/><i>runs the 5 agents in order</i>"]

    subgraph agents["agents/"]
        INIT["__init__.py<br/><i>loads the numbered files</i>"]
        A1["1_triage.py"]
        A2["2_retriever.py"]
        A3["3_diagnostician.py"]
        A4["4_writer.py"]
        A5["5_verifier.py"]
        COM["common.py<br/><i>citations, language,<br/>safety rules</i>"]
    end

    subgraph knowledge["knowledge/"]
        BASE["base.py<br/><i>BM25 search, tables</i>"]
        INGM["ingestion.py<br/><i>PDF → passages</i>"]
    end

    LLM["llm.py<br/><i>Ollama client</i>"]

    subgraph data["Data files"]
        PDF[("user_manual.pdf")]
        MAN[("data/manuals/manifest.json")]
        CUR[("data/curated/*.json<br/>troubleshooting table")]
        IDX[("data/index/chunks.jsonl")]
        Q[("evaluation/questions.json")]
        ANS[("evaluation/results/answers.jsonl")]
    end

    OLL{{"Ollama server<br/>qwen · llama · gemma · deepseek"}}

    WEB --> ORCH
    CLI --> ORCH
    RUN --> ORCH
    WEB --> BASE
    ING --> INGM
    REP --> COM

    ORCH --> INIT
    ORCH --> BASE
    ORCH --> LLM
    INIT --> A1 & A2 & A3 & A4 & A5

    A1 --> COM
    A4 --> COM
    A5 --> COM
    A1 & A2 & A3 --> BASE
    A4 --> BASE
    A1 & A2 & A3 & A4 & A5 -.->|"chat() on the LLM object<br/>the orchestrator gives them"| LLM

    BASE --> INGM
    LLM --> OLL

    INGM --> PDF & MAN & CUR
    INGM -- writes --> IDX
    BASE -- reads --> IDX
    RUN --> Q
    RUN -- writes --> ANS
    REP --> Q & ANS
```

Not drawn, to keep the graph readable: **almost every file imports `config.py`** (paths,
models, modes, limits) **and `schemas.py`** (the data types passed between them). Neither
imports anything else from the project, so they sit underneath everything.

The dotted arrows: the agents never import `llm.py`. The orchestrator creates one `OllamaLLM`
and hands it to each agent that should use it. An agent given `None` uses its offline rules
instead. That is how one set of agents makes all six modes.

## 2. What happens to one question

The same flow runs whether the question comes from the web app, the CLI or the evaluation.
The names on the arrows are the types from `schemas.py`.

```mermaid
sequenceDiagram
    actor U as Technician
    participant E as webapp.py / cli.py
    participant O as orchestrator.py
    participant T as 1 triage
    participant R as 2 retriever
    participant D as 3 diagnostician
    participant W as 4 writer
    participant V as 5 verifier
    participant K as knowledge/base.py
    participant L as llm.py → Ollama

    U->>E: question + mode
    E->>O: build_orchestrator(mode), then ask(question)
    O->>T: run(question)
    T-->>L: classify (LLM modes, auto)
    T-->>O: TriageResult (intent, language, symptoms, search query)
    alt intent is out_of_scope
        O-->>E: fixed refusal
    end
    O->>R: run(question, triage)
    R->>K: BM25 search (offline, auto) or passage list (LLM modes)
    R-->>L: pick passages (LLM modes)
    R-->>O: list[Evidence] (up to 4 passages)
    opt intent is troubleshooting
        O->>D: run(question, triage)
        D->>K: troubleshooting table
        D-->>L: rank rows (LLM modes)
        D-->>O: Diagnosis (ranked causes)
    end
    loop at most 2 drafts
        O->>W: run(question, triage, evidence, diagnosis, feedback)
        W-->>L: write the answer (LLM modes, auto)
        W-->>O: answer text with [p. N] citations
        O->>V: run(question, answer, evidence, diagnosis)
        V-->>L: check it (LLM modes)
        V-->>O: Verdict (approved, issues)
        Note over O,W: if rejected, the issues become the<br/>feedback for the second draft
    end
    O-->>E: AssistantResponse (answer, sources, diagnosis, trace)
    E-->>U: answer + cited pages (+ trace)
```

Which agents call the LLM depends on the mode:

| Mode | 1 triage | 2 retriever | 3 diagnostician | 4 writer | 5 verifier |
|---|---|---|---|---|---|
| `qwen`, `llama`, `gemma`, `deepseek` | LLM | LLM | LLM | LLM | LLM |
| `auto` | LLM | rules | rules | LLM | rules |
| `offline` | rules | rules | rules | rules | rules |

## 3. What every file is for

**The app** (`src/pool_assistant/`)

| File | What it does | Used by |
|---|---|---|
| [config.py](../src/pool_assistant/config.py) | Paths, the Ollama models, the six modes, limits | almost everything |
| [schemas.py](../src/pool_assistant/schemas.py) | The data types passed between files (Pydantic) | almost everything |
| [llm.py](../src/pool_assistant/llm.py) | Sends prompts to Ollama, checks the JSON replies, reports failures as `LLMError` | orchestrator (creates it), agents (call it), entry points (catch its errors) |
| [orchestrator.py](../src/pool_assistant/orchestrator.py) | Builds the agents for a mode and runs them in order for each question | webapp, cli, evaluation/run |
| [agents/\_\_init\_\_.py](../src/pool_assistant/agents/__init__.py) | Loads the five numbered agent files under plain names | orchestrator |
| [agents/1_triage.py](../src/pool_assistant/agents/1_triage.py) | Scope, intent, language, product, symptoms | orchestrator |
| [agents/2_retriever.py](../src/pool_assistant/agents/2_retriever.py) | Finds the manual passages to answer from | orchestrator |
| [agents/3_diagnostician.py](../src/pool_assistant/agents/3_diagnostician.py) | Ranks causes from the troubleshooting table | orchestrator |
| [agents/4_writer.py](../src/pool_assistant/agents/4_writer.py) | Writes the answer with citations and the safety warning | orchestrator |
| [agents/5_verifier.py](../src/pool_assistant/agents/5_verifier.py) | Checks citations and the safety warning (and grounding, in LLM modes) | orchestrator |
| [agents/common.py](../src/pool_assistant/agents/common.py) | Shared rules: citations, language, symptom keywords, safety words and text | triage, writer, verifier, evaluation/report |
| [knowledge/base.py](../src/pool_assistant/knowledge/base.py) | Loads the passages and tables; BM25 word search | orchestrator, webapp, agents |
| [knowledge/ingestion.py](../src/pool_assistant/knowledge/ingestion.py) | Splits the PDF into page-sized passages and saves the index | knowledge/base, scripts/ingest |
| [cli.py](../src/pool_assistant/cli.py) | `pool-assistant "question" --mode ...` | you |
| [webapp.py](../src/pool_assistant/webapp.py) | `pool-assistant-web`: the Shiny chat | you |

**Scripts and evaluation**

| File | What it does |
|---|---|
| [scripts/ingest.py](../scripts/ingest.py) | Rebuilds `data/index/chunks.jsonl` from the PDF (run after changing a manual) |
| [evaluation/run.py](../evaluation/run.py) | Asks the 10 questions in every mode and saves the answers and times |
| [evaluation/report.py](../evaluation/report.py) | Scores the saved answers and writes `REPORT.md` |

**Tests** (`tests/`, run with `pytest`, no Ollama needed)

| File | What it checks |
|---|---|
| [conftest.py](../tests/conftest.py) | Shared setup: the knowledge base, an offline assistant, a fake LLM |
| [test_knowledge.py](../tests/test_knowledge.py) | PDF splitting, search, symptom and language helpers |
| [test_orchestrator.py](../tests/test_orchestrator.py) | Whole questions in offline mode |
| [test_llm_agents.py](../tests/test_llm_agents.py) | Each agent's LLM mode, `auto` mode and mode selection, with a fake LLM |
| [test_webapp.py](../tests/test_webapp.py) | The web app's answering and formatting code |
