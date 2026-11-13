"""Orchestrator: the explicit, code-controlled graph that connects the agents.

    question
       │
    [Triage] ── out of scope ──────────────────────────────► polite refusal
       │
    [Retriever]
       │
       ├── intent == troubleshooting ──► [Diagnostician]
       │                                       │
    [Writer] ◄─────────────────────────────────┘
       │      ▲
    [Verifier]│ rejected and revisions left: issues fed back to the writer
       │──────┘
       ▼
    answer (+ sources, diagnosis, verification status, per-agent trace)

The control flow is plain Python rather than an LLM deciding the next step: the routes
are known in advance, which makes behaviour predictable, testable and cheap. The LLM
does the judgement inside each agent.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from pool_assistant import config
from pool_assistant.agents import DiagnosticianAgent, RetrieverAgent, TriageAgent, VerifierAgent, WriterAgent
from pool_assistant.knowledge import KnowledgeBase, load_knowledge_base
from pool_assistant.llm import StructuredLLM, build_llm
from pool_assistant.schemas import AssistantResponse, Intent, Source, TraceStep

log = logging.getLogger(__name__)
T = TypeVar("T")

OUT_OF_SCOPE = {
    "en": "I can only help with technical questions about installing, starting up, maintaining and troubleshooting pool equipment covered by the product manuals.",
    "es": "Solo puedo ayudar con preguntas técnicas sobre instalación, puesta en marcha, mantenimiento y resolución de averías de equipos de piscina incluidos en los manuales.",
    "ca": "Només puc ajudar amb preguntes tècniques sobre instal·lació, posada en marxa, manteniment i resolució d'avaries d'equips de piscina inclosos als manuals.",
    "fr": "Je ne peux répondre qu'aux questions techniques sur l'installation, la mise en service, l'entretien et le dépannage des équipements de piscine couverts par les manuels.",
    "it": "Posso rispondere solo a domande tecniche su installazione, avviamento, manutenzione e risoluzione dei problemi delle apparecchiature per piscine coperte dai manuali.",
    "de": "Ich kann nur technische Fragen zu Installation, Inbetriebnahme, Wartung und Fehlerbehebung von Poolgeräten beantworten, die in den Handbüchern behandelt werden.",
    "pt": "Só posso ajudar com questões técnicas sobre instalação, arranque, manutenção e resolução de avarias de equipamentos de piscina abrangidos pelos manuais.",
}
UNVERIFIED_NOTE = (
    "\n\n> ⚠️ This answer did not pass automatic verification against the manual. "
    "Double-check it with the manual or the Technical Assistance Service before acting on it."
)


class Orchestrator:
    def __init__(self, kb: KnowledgeBase, llm: StructuredLLM | None) -> None:
        self.kb = kb
        self.llm = llm
        self.triage = TriageAgent(llm, kb)
        self.retriever = RetrieverAgent(llm, kb)
        self.diagnostician = DiagnosticianAgent(llm, kb)
        self.writer = WriterAgent(llm)
        self.verifier = VerifierAgent(llm)

    @property
    def mode(self) -> str:
        return self.llm.name if self.llm else "offline"

    def ask(self, question: str) -> AssistantResponse:
        trace: list[TraceStep] = []

        def step(agent, summarize: Callable[[T], str], **inputs) -> T:
            start = time.perf_counter()
            result = agent.run(**inputs)
            mode = "" if agent.last_mode == "llm" else f" [{agent.last_mode}]"
            trace.append(TraceStep(
                agent=agent.name,
                duration_ms=round((time.perf_counter() - start) * 1000),
                summary=summarize(result) + mode,
            ))
            return result

        triage = step(
            self.triage,
            lambda t: f"intent={t.intent.value} lang={t.language} product={t.product} in_scope={t.in_scope}",
            question=question,
        )
        if not triage.in_scope:
            return AssistantResponse(
                question=question,
                answer=OUT_OF_SCOPE.get(triage.language, OUT_OF_SCOPE["en"]),
                language=triage.language,
                intent=Intent.OUT_OF_SCOPE,
                product=None,
                verified=True,
                sources=[],
                diagnosis=None,
                verification_issues=[],
                trace=trace,
                llm_mode=self.mode,
            )

        retrieval = step(
            self.retriever,
            lambda r: f"{len(r.evidence)} passages from pages {sorted({e.chunk.page for e in r.evidence})}",
            question=question,
            triage=triage,
        )
        evidence = retrieval.evidence

        diagnosis = None
        if triage.intent == Intent.TROUBLESHOOTING:
            diagnosis = step(
                self.diagnostician,
                lambda d: f"{len(d.candidates)} candidate causes",
                question=question,
                triage=triage,
                evidence=evidence,
            )

        feedback: list[str] = []
        for attempt in range(config.MAX_REVISIONS + 1):
            draft = step(
                self.writer,
                lambda d: f"draft {attempt + 1}, cites pages {d.cited_pages}",
                question=question,
                triage=triage,
                evidence=evidence,
                diagnosis=diagnosis,
                feedback=feedback,
            )
            verdict = step(
                self.verifier,
                lambda v: "approved" if v.approved else f"rejected: {len(v.issues)} issue(s)",
                question=question,
                triage=triage,
                evidence=evidence,
                diagnosis=diagnosis,
                draft=draft,
            )
            if verdict.approved:
                break
            feedback = verdict.issues

        answer = draft.answer if verdict.approved else draft.answer + UNVERIFIED_NOTE
        return AssistantResponse(
            question=question,
            answer=answer,
            language=triage.language,
            intent=triage.intent,
            product=triage.product or (evidence[0].chunk.product if evidence else None),
            verified=verdict.approved,
            sources=[
                Source(
                    doc_id=ev.chunk.doc_id,
                    product=ev.chunk.product,
                    page=ev.chunk.page,
                    section=ev.chunk.section,
                    snippet=" ".join(ev.chunk.text.split())[:240],
                )
                for ev in evidence
            ],
            diagnosis=diagnosis,
            verification_issues=verdict.issues,
            trace=trace,
            llm_mode=self.mode,
        )


def build_orchestrator(mode: str = config.LLM_MODE) -> Orchestrator:
    return Orchestrator(kb=load_knowledge_base(), llm=build_llm(mode))
