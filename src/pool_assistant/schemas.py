from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from pool_assistant import config


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
    chunk_id: str
    doc_id: str
    product: str
    language: str
    page: int
    section: str
    text: str


class Evidence(BaseModel):
    chunk: Chunk
    score: float


class Symptom(BaseModel):
    id: int
    label: str
    keywords: list[str]


class TroubleshootingRow(BaseModel):
    cause: str
    solution: str
    symptoms: list[int]


class TroubleshootingMatrix(BaseModel):
    doc_id: str
    product: str
    source_page: int
    symptoms: list[Symptom]
    rows: list[TroubleshootingRow]


# --- agent outputs ---

# The *LLMOutput models are what each agent asks the LLM for (sent to Ollama as a JSON schema).
# The lists have a maximum length: small models in JSON mode can otherwise repeat items until
# the context is full, which takes many minutes on a CPU.

class TriageLLMOutput(BaseModel):
    in_scope: bool
    intent: Intent
    language: str
    product: str | None
    symptom_ids: list[int] = Field(max_length=6)
    search_query: str


class RetrievalLLMOutput(BaseModel):
    passage_ids: list[int] = Field(max_length=config.EVIDENCE_K)


class RankedCause(BaseModel):
    row_id: int
    likelihood: Literal["high", "medium", "low"]


class DiagnosisLLMOutput(BaseModel):
    causes: list[RankedCause] = Field(max_length=6)


class VerificationLLMOutput(BaseModel):
    citations_ok: bool
    supported: bool
    needs_safety_warning: bool
    has_safety_warning: bool
    issues: list[str] = Field(max_length=5)


class TriageResult(BaseModel):
    in_scope: bool
    intent: Intent
    language: str          # ISO 639-1 code, e.g. "en", "es"
    product: str | None
    symptoms: list[str]    # symptom labels from the troubleshooting table
    search_query: str      # the question as an English search query


class DiagnosisCandidate(BaseModel):
    cause: str
    solution: str
    likelihood: str  # high | medium | low
    source_page: int


class Diagnosis(BaseModel):
    matched_symptoms: list[str]
    candidates: list[DiagnosisCandidate]


class Verdict(BaseModel):
    approved: bool
    issues: list[str]


# --- response returned to the CLI and the web app ---


class Source(BaseModel):
    page: int
    section: str
    snippet: str


class TraceStep(BaseModel):
    agent: str
    duration_ms: int
    summary: str


class AssistantResponse(BaseModel):
    question: str
    answer: str
    intent: Intent
    language: str
    product: str | None
    verified: bool
    sources: list[Source]
    diagnosis: Diagnosis | None
    verification_issues: list[str]
    trace: list[TraceStep]
    mode: str          # qwen, llama, gemma, deepseek, auto or offline
    model: str | None  # Ollama model used, None in offline mode
