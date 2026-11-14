"""Runs the agents in order for one question.

1 triage -> 2 retriever -> 3 diagnostician (only for troubleshooting) -> 4 writer <-> 5 verifier

The mode is chosen by the user:
- an LLM (qwen, llama, gemma, deepseek): every agent uses that model;
- auto: triage and writer use the LLM, retriever, diagnostician and verifier use search and rules;
- offline: every agent uses word matching and fixed rules, with no LLM.
If an LLM call fails, `ask` raises LLMError; it never switches to offline mode on its own.
"""

import time

from pool_assistant import config
from pool_assistant.agents import DiagnosticianAgent, RetrieverAgent, TriageAgent, VerifierAgent, WriterAgent
from pool_assistant.knowledge import KnowledgeBase, load_knowledge_base
from pool_assistant.llm import OllamaLLM, build_llm
from pool_assistant.schemas import AssistantResponse, Intent, Source, TraceStep

# The fixed reply for questions that are not about pool equipment.
OUT_OF_SCOPE_ANSWER = (
    "I can only help with technical questions about installing, starting up, maintaining "
    "and troubleshooting the pool equipment covered by the product manuals."
)
# Added to the end of an answer the verifier still rejected after the rewrite.
UNVERIFIED_NOTE = (
    "\n\n> Warning: this answer did not pass the automatic check. "
    "Confirm it with the manual or the Technical Assistance Service before acting on it."
)


class Orchestrator:
    """The five agents of one mode, ready to answer questions. Build it with build_orchestrator()."""

    def __init__(
        self,
        kb: KnowledgeBase,
        llm: OllamaLLM | None,
        mode: str | None = None,
        llm_agents: set[str] | None = None,
    ):
        """llm=None runs offline mode. llm_agents names the agents that get the LLM
        (None: all of them); the others use search and fixed rules."""
        self.llm = llm
        self.mode = mode or (config.OFFLINE if llm is None else llm.model)
        self.model = llm.model if llm else None

        # An agent given the LLM uses its LLM implementation; one given None uses its offline
        # implementation. This is how the three kinds of mode are made from the same agents.
        def llm_for(agent: str):
            return llm if llm_agents is None or agent in llm_agents else None

        self.triage = TriageAgent(kb, llm_for("triage"))
        self.retriever = RetrieverAgent(kb, llm_for("retriever"))
        self.diagnostician = DiagnosticianAgent(kb, llm_for("diagnostician"))
        self.writer = WriterAgent(llm_for("writer"))
        self.verifier = VerifierAgent(llm_for("verifier"))

    def ask(self, question: str) -> AssistantResponse:
        """Answer one question. Each agent's step is timed and recorded in the trace."""
        trace = []

        # --- 1. triage: is it in scope, what is it about? ---
        start = time.perf_counter()
        triage = self.triage.run(question)
        trace.append(step("triage", start, f"intent={triage.intent.value} lang={triage.language} "
                                           f"symptoms={len(triage.symptoms)}"))

        # not about pool equipment: stop here with the fixed refusal
        if triage.intent == Intent.OUT_OF_SCOPE:
            return AssistantResponse(
                question=question, answer=OUT_OF_SCOPE_ANSWER, intent=triage.intent,
                language=triage.language, product=None, verified=True, sources=[],
                diagnosis=None, verification_issues=[], trace=trace, mode=self.mode, model=self.model,
            )

        # --- 2. retriever: the manual passages to answer from ---
        start = time.perf_counter()
        evidence = self.retriever.run(question, triage)
        trace.append(step("retriever", start, f"{len(evidence)} passages, pages {sorted({e.chunk.page for e in evidence})}"))

        # --- 3. diagnostician: only when something is not working ---
        diagnosis = None
        if triage.intent == Intent.TROUBLESHOOTING:
            start = time.perf_counter()
            diagnosis = self.diagnostician.run(question, triage)
            trace.append(step("diagnostician", start, f"{len(diagnosis.candidates)} possible causes"))

        # --- 4 and 5. writer and verifier ---
        # write and verify; if the verifier rejects an LLM answer, the writer gets one more try
        # (offline answers are fixed templates, so rewriting them would give the same text)
        feedback = []
        for attempt in range(1, config.MAX_REVISIONS + 2):  # 1 draft + MAX_REVISIONS rewrites
            start = time.perf_counter()
            answer = self.writer.run(question, triage, evidence, diagnosis, feedback)
            trace.append(step("writer", start, f"draft {attempt}"))

            start = time.perf_counter()
            verdict = self.verifier.run(question, answer, evidence, diagnosis)
            trace.append(step("verifier", start, "approved" if verdict.approved else "; ".join(verdict.issues)))

            if verdict.approved or self.writer.llm is None:
                break
            feedback = verdict.issues  # the next draft is told what to fix

        # --- the result: the answer (flagged if unverified) and everything that led to it ---
        return AssistantResponse(
            question=question,
            answer=answer if verdict.approved else answer + UNVERIFIED_NOTE,
            intent=triage.intent,
            language=triage.language,
            product=triage.product,
            verified=verdict.approved,
            sources=[Source(page=e.chunk.page, section=e.chunk.section, snippet=e.chunk.text[:200]) for e in evidence],
            diagnosis=diagnosis,
            verification_issues=verdict.issues,
            trace=trace,
            mode=self.mode,
            model=self.model,
        )


def step(agent: str, start: float, summary: str) -> TraceStep:
    """A trace entry: the agent, how long it took since `start`, and what it did."""
    return TraceStep(agent=agent, duration_ms=round((time.perf_counter() - start) * 1000), summary=summary)


def build_orchestrator(mode: str, kb: KnowledgeBase | None = None) -> Orchestrator:
    """mode: one of config.MODES, e.g. "llama", "auto" or "offline". Raises LLMError if the model is not available."""
    if mode not in config.MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {', '.join(config.MODES)}")
    kb = kb or load_knowledge_base()
    if mode == config.OFFLINE:
        # no LLM at all
        return Orchestrator(kb, None, mode)
    if mode == config.AUTO:
        # the AUTO_MODEL, given only to the agents in AUTO_LLM_AGENTS (triage and writer)
        return Orchestrator(kb, build_llm(config.AUTO_MODEL), mode, llm_agents=config.AUTO_LLM_AGENTS)
    # an LLM mode: the chosen model for every agent
    return Orchestrator(kb, build_llm(mode), mode)
