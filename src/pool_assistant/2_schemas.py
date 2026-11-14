"""The data passed between the parts of the app, as Pydantic models.

Pydantic checks every field's type when an object is created, so an agent can't hand the next
one malformed data. There are four groups:
- knowledge base: the manual split into passages, and the troubleshooting table;
- *LLMOutput: the JSON each agent asks the LLM for;
- agent results: what each agent passes to the next ones;
- AssistantResponse: the final result shown by the CLI and the web app.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from pool_assistant import config


# What the technician wants. Decided by triage; it chooses the route through the agents
# (only TROUBLESHOOTING goes to the diagnostician, OUT_OF_SCOPE stops right away).
# (Comments, not docstrings, on the models sent to Ollama: Pydantic would add a docstring to
# the JSON schema, and so to the prompt.)
class Intent(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    INSTALLATION = "installation"
    START_UP = "start_up"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    GENERAL = "general"
    OUT_OF_SCOPE = "out_of_scope"


# --- knowledge base ---

class Chunk(BaseModel):
    """One passage of a manual. It never crosses a page, so it can be cited as [p. N]."""
    chunk_id: str  # e.g. "astral-pool-iom:en:p9:2" (document : language : page : block)
    doc_id: str
    product: str
    language: str
    page: int
    section: str   # e.g. "3. Installation And Assembly > Piping"
    text: str


class Evidence(BaseModel):
    """A passage found by a search, with its score (higher = more relevant)."""
    chunk: Chunk
    score: float


class Symptom(BaseModel):
    """A symptom of the troubleshooting table, e.g. 3: "The pump makes a noise"."""
    id: int
    label: str
    keywords: list[str]  # words that point to this symptom; only used in offline mode


class TroubleshootingRow(BaseModel):
    """One row of the table: a cause, its fix, and the symptoms (ids) it can explain."""
    cause: str
    solution: str
    symptoms: list[int]


class TroubleshootingMatrix(BaseModel):
    """A manual's whole troubleshooting table, loaded from data/curated/*.json."""
    doc_id: str
    product: str
    source_page: int  # the manual page the table is on, used in citations
    symptoms: list[Symptom]
    rows: list[TroubleshootingRow]


# --- agent outputs ---

# The *LLMOutput models are what each agent asks the LLM for (sent to Ollama as a JSON schema).
# The lists have a maximum length: small models in JSON mode can otherwise repeat items until
# the context is full, which takes many minutes on a CPU.

# What triage asks the LLM for.
class TriageLLMOutput(BaseModel):
    in_scope: bool
    intent: Intent
    language: str
    product: str | None
    symptom_ids: list[int] = Field(max_length=6)  # ids from the table, not free text
    search_query: str                             # the question rewritten in English


# What the retriever asks the LLM for: the numbers of the passages that answer the question.
class RetrievalLLMOutput(BaseModel):
    passage_ids: list[int] = Field(max_length=config.EVIDENCE_K)


# One table row picked by the diagnostician's LLM, with how likely it is.
class RankedCause(BaseModel):
    row_id: int
    likelihood: Literal["high", "medium", "low"]


# What the diagnostician asks the LLM for: rows of the table, most likely first.
class DiagnosisLLMOutput(BaseModel):
    causes: list[RankedCause] = Field(max_length=6)


# What the verifier asks the LLM for: yes/no checks plus the problems found.
class VerificationLLMOutput(BaseModel):
    citations_ok: bool
    supported: bool
    needs_safety_warning: bool
    has_safety_warning: bool
    issues: list[str] = Field(max_length=5)


# What each agent returns, whichever implementation (LLM or rules) produced it.

class TriageResult(BaseModel):
    """Triage's decision, read by every later agent."""
    in_scope: bool
    intent: Intent
    language: str          # ISO 639-1 code, e.g. "en", "es"
    product: str | None
    symptoms: list[str]    # symptom labels from the troubleshooting table
    search_query: str      # the question as an English search query


class DiagnosisCandidate(BaseModel):
    """A possible cause of the fault, with its fix, copied from the table."""
    cause: str
    solution: str
    likelihood: str  # high | medium | low
    source_page: int


class Diagnosis(BaseModel):
    """The diagnostician's result: the symptoms it worked from and the ranked causes."""
    matched_symptoms: list[str]
    candidates: list[DiagnosisCandidate]


class Verdict(BaseModel):
    """The verifier's result. If not approved, `issues` tells the writer what to fix."""
    approved: bool
    issues: list[str]


# --- response returned to the CLI and the web app ---


class Source(BaseModel):
    """A manual passage the answer was based on, shown as a source."""
    page: int
    section: str
    snippet: str  # the first 200 characters of the passage


class TraceStep(BaseModel):
    """One agent's step, shown with --trace / "Show what each agent did"."""
    agent: str
    duration_ms: int
    summary: str


class AssistantResponse(BaseModel):
    """Everything about one answered question."""
    question: str
    answer: str
    intent: Intent
    language: str
    product: str | None
    verified: bool                  # whether the verifier approved the answer
    sources: list[Source]
    diagnosis: Diagnosis | None     # only for troubleshooting questions
    verification_issues: list[str]  # why the verifier rejected it, if it did
    trace: list[TraceStep]
    mode: str          # qwen, llama, gemma, deepseek, auto or offline
    model: str | None  # Ollama model used, None in offline mode
