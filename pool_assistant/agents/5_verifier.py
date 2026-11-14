"""Agent 5, verifier: the last check before the answer is returned.

It checks that the answer cites pages that are really in the evidence, sticks to the evidence
(LLM mode only) and has the disconnect-power warning when electrical work is involved. A
rejected answer goes back to the writer once; if it is rejected again, it is returned with a
warning that it didn't pass the check.
"""

from pool_assistant.agents.common import NOT_FOUND, cited_pages, has_safety_warning, needs_safety_warning
from pool_assistant.schemas import Diagnosis, Evidence, Verdict, VerificationLLMOutput

SAFETY_PAGES = {5, 8}  # cited by the standard safety warning

# Instructions for the LLM. {pages} is the list of pages the answer may cite.
SYSTEM_PROMPT = """You check answers written for pool technicians before they are sent. \
Compare the answer with the manual excerpts and likely causes it was written from.

Return JSON with:
- citations_ok: true if every statement cites a manual page as [p. N] and every cited page is \
one of these: {pages}.
- supported: true if every statement in the answer is backed by the excerpts or the likely \
causes, with no invented values, parts or procedures.
- needs_safety_warning: true if the answer involves electrical or mechanical work on the \
equipment (motor, wiring, cables, junction box, voltage, bearings, seals...).
- has_safety_warning: true if the answer tells the technician to disconnect the power before \
that work.
- issues: one short sentence for each problem found, written as an instruction to fix it. \
An empty list if there are none."""


class VerifierAgent:
    """Checks the answer before it is returned: it must cite real pages from the evidence,
    stick to the evidence, and include the safety warning when electrical work is involved."""

    name = "verifier"

    def __init__(self, llm=None):
        self.llm = llm  # None in offline mode

    def run(self, question: str, answer: str, evidence: list[Evidence], diagnosis: Diagnosis | None) -> Verdict:
        # the fixed "not found" message has nothing to check
        if answer == NOT_FOUND:
            return Verdict(approved=True, issues=[])
        # the pages the answer may cite: those of the passages and of the diagnosed causes,
        # plus the two pages the safety warning cites
        allowed = {ev.chunk.page for ev in evidence} | SAFETY_PAGES
        if diagnosis:
            allowed |= {c.source_page for c in diagnosis.candidates}
        if self.llm:
            return self.run_llm(question, answer, evidence, diagnosis, allowed)
        return self.run_offline(question, answer, allowed)

    # --- LLM mode: the model reviews the answer against the evidence ---

    def run_llm(self, question, answer, evidence, diagnosis, allowed: set[int]) -> Verdict:
        # the model gets the answer together with everything it was written from
        parts = [f"Question: {question}", f"Answer to check:\n{answer}"]
        if diagnosis and diagnosis.candidates:
            parts.append("Likely causes:\n" + "\n".join(
                f"- {c.cause} -> {c.solution} [p. {c.source_page}]" for c in diagnosis.candidates
            ))
        if evidence:
            parts.append("Manual excerpts:\n" + "\n\n".join(
                f"[p. {e.chunk.page}] {e.chunk.section}\n{e.chunk.text}" for e in evidence
            ))
        prompt = SYSTEM_PROMPT.format(pages=", ".join(str(p) for p in sorted(allowed)))
        out = self.llm.chat(prompt, "\n\n".join(parts), schema=VerificationLLMOutput)

        # the verdict follows the model's yes/no answers; its own issue list explains them
        # (each key is the instruction given to the writer if that check fails and the model
        # didn't list any issues itself)
        checks = {
            "Cite a page from the excerpts as [p. N] after each statement.": out.citations_ok,
            "Only state what the excerpts and likely causes say.": out.supported,
            "Add the disconnect-power safety warning.": out.has_safety_warning or not out.needs_safety_warning,
        }
        approved = all(checks.values())
        issues = [] if approved else (out.issues or [fix for fix, ok in checks.items() if not ok])
        return Verdict(approved=approved, issues=issues)

    # --- offline mode: fixed rules ---

    def run_offline(self, question: str, answer: str, allowed: set[int]) -> Verdict:
        issues = []
        # rule 1: at least one [p. N] citation, and only pages from the evidence
        pages = cited_pages(answer)
        if not pages:
            issues.append("The answer has no [p. N] citations.")
        elif pages - allowed:
            issues.append(f"Pages {sorted(pages - allowed)} are cited but not in the evidence.")

        # rule 2: electrical words in the question or answer require the disconnect-power warning
        if needs_safety_warning(question, answer) and not has_safety_warning(answer):
            issues.append("Electrical or mechanical work without the disconnect-power warning.")

        return Verdict(approved=not issues, issues=issues)
