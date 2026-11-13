"""Typed contracts between agents.

Models suffixed with ``Output`` are what an LLM-backed agent must return. They are
passed to Claude as structured-output schemas, so they avoid defaults and numeric
constraints and keep every field required.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    INSTALLATION = "installation"
    START_UP = "start_up"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    GENERAL = "general"
    OUT_OF_SCOPE = "out_of_scope"


# --------------------------------------------------------------------------- knowledge


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


class TroubleshootingRow(BaseModel):
    cause: str
    solution: str
    symptoms: list[int]


class Symptom(BaseModel):
    id: int
    label: str
    keywords: list[str] = Field(default_factory=list)


class TroubleshootingMatrix(BaseModel):
    doc_id: str
    product: str
    source_page: int
    symptoms: list[Symptom]
    rows: list[TroubleshootingRow]


# --------------------------------------------------------------------------- agent outputs


class TriageOutput(BaseModel):
    """Triage agent: what is being asked, about which product, in which language."""

    in_scope: bool
    intent: Intent
    language: str  # ISO 639-1 code of the technician's question, e.g. "en", "es"
    product: str | None  # name from the product catalog, or null when not identifiable
    symptoms: list[str]  # observed symptoms, paraphrased in English
    search_queries: list[str]  # 1-3 English queries for the manual index
    reasoning: str


class EvidenceSelectionOutput(BaseModel):
    """Retriever agent: which candidate passages actually answer the question."""

    selected_chunk_ids: list[str]
    missing_information: str  # what the passages do not cover; empty string if nothing


class DiagnosisCandidate(BaseModel):
    cause: str
    solution: str
    likelihood: str  # "high" | "medium" | "low"
    rationale: str
    source_page: int


class DiagnosisOutput(BaseModel):
    """Diagnostician agent: ranked likely causes and checks, grounded in the manual."""

    matched_symptoms: list[str]
    candidates: list[DiagnosisCandidate]
    recommended_first_check: str


class DraftAnswerOutput(BaseModel):
    """Writer agent: the answer shown to the technician."""

    answer: str  # Markdown, in the technician's language, with [p. N] citations
    cited_pages: list[int]


class VerdictOutput(BaseModel):
    """Verifier agent: is the draft grounded, complete and safe to send?"""

    approved: bool
    issues: list[str]  # concrete problems the writer must fix; empty when approved


# --------------------------------------------------------------------------- API response


class Source(BaseModel):
    doc_id: str
    product: str
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
    language: str
    intent: Intent
    product: str | None
    verified: bool
    sources: list[Source]
    diagnosis: DiagnosisOutput | None
    verification_issues: list[str]
    trace: list[TraceStep]
    llm_mode: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
