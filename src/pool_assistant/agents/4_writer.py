from pool_assistant.agents.common import (
    LANGUAGE_NAMES, NOT_FOUND, SAFETY_WARNINGS, has_safety_warning, needs_safety_warning, safety_warning,
)
from pool_assistant.knowledge.base import tokenize
from pool_assistant.schemas import Diagnosis, Evidence, TriageResult

SYSTEM_PROMPT = """You are an assistant for professional pool technicians. Answer the \
technician's question using ONLY the manual excerpts and the likely causes given below.

Rules:
- Write the whole answer in {language}, translating the causes and fixes if needed.
- Do not repeat the question. Be brief and practical: numbered steps, or a list of the likely causes with how to fix each one.
- If likely causes are given, answer only with those causes, in that order. Do not add other causes.
- After each statement, cite the manual page in this exact format: [p. 13]. Only cite pages \
that appear in the excerpts or the likely causes.
- If the excerpts do not answer the question, say so and recommend contacting the Technical \
Assistance Service.
- Never invent values, parts or procedures that are not in the excerpts.
- If the answer involves any electrical or mechanical work on the equipment (motor, wiring, \
cables, junction box, voltage, bearings, seals...), end with this safety warning, translated \
into {language}:
{safety}"""


class WriterAgent:
    """Writes the answer from the diagnosis and the retrieved passages, with page citations."""

    name = "writer"

    def __init__(self, llm=None):
        self.llm = llm  # None in offline mode

    def run(
        self,
        question: str,
        triage: TriageResult,
        evidence: list[Evidence],
        diagnosis: Diagnosis | None,
        feedback: list[str],
    ) -> str:
        if not evidence and not (diagnosis and diagnosis.candidates):
            return NOT_FOUND
        if self.llm:
            return self.write_llm(question, triage, evidence, diagnosis, feedback)
        return self.write_offline(question, evidence, diagnosis)

    # --- LLM mode ---

    def write_llm(self, question, triage, evidence, diagnosis, feedback) -> str:
        parts = [f"Question: {question}"]
        if diagnosis and diagnosis.candidates:
            causes = "\n".join(
                f"{i}. {c.cause} ({c.likelihood}) -> {c.solution} [p. {c.source_page}]"
                for i, c in enumerate(diagnosis.candidates, 1)
            )
            parts.append(f"Likely causes, from the manual's troubleshooting table:\n{causes}")
        if evidence:
            excerpts = "\n\n".join(f"[p. {e.chunk.page}] {e.chunk.section}\n{e.chunk.text}" for e in evidence)
            parts.append(f"Manual excerpts:\n{excerpts}")
        if feedback:
            parts.append("Your previous answer was rejected. Fix these problems:\n" + "\n".join(f"- {f}" for f in feedback))

        language = LANGUAGE_NAMES.get(triage.language, "English")
        prompt = SYSTEM_PROMPT.format(language=language, safety=SAFETY_WARNINGS["en"])
        return self.llm.chat(prompt, "\n\n".join(parts))

    # --- offline mode: fixed templates ---

    def write_offline(self, question: str, evidence: list[Evidence], diagnosis: Diagnosis | None) -> str:
        if diagnosis and diagnosis.candidates:
            lines = [f"**Reported symptoms:** {'; '.join(diagnosis.matched_symptoms)}.", "", "**Likely causes:**"]
            for i, c in enumerate(diagnosis.candidates, 1):
                lines.append(f"{i}. **{c.cause}** ({c.likelihood}): {c.solution} [p. {c.source_page}]")
            lines += ["", f"**Check first:** {diagnosis.candidates[0].solution}."]
        else:
            lines = [f"From the {evidence[0].chunk.product} manual:"]
            for ev in evidence[:3]:
                lines.append(f"- **{ev.chunk.section}:** {excerpt(ev.chunk.text, question)} [p. {ev.chunk.page}]")
        answer = "\n".join(lines)

        if needs_safety_warning(question, answer) and not has_safety_warning(answer):
            answer += "\n\n" + safety_warning("en")
        return answer


def excerpt(text: str, question: str, limit: int = 450) -> str:
    """The lines of a passage that best match the question, up to `limit` characters."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    query = set(tokenize(question))
    best = max(range(len(lines)), key=lambda i: len(query & set(tokenize(lines[i]))))
    start = max(0, best - 1)

    result = ""
    for line in lines[start:]:
        if len(result) + len(line) > limit:
            break
        result = f"{result} {line}".strip()
    result = result or text[:limit]

    if start > 0:
        result = "... " + result
    if len(result) < len(" ".join(lines[start:])):
        result += " ..."
    return result
