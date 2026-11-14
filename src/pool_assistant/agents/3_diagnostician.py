from pool_assistant.knowledge import KnowledgeBase
from pool_assistant.schemas import Diagnosis, DiagnosisCandidate, DiagnosisLLMOutput, TriageResult

SYSTEM_PROMPT = """You diagnose faults in pool equipment using the troubleshooting table of its \
manual.

Below are the rows of the table, each with its number, the symptoms it applies to, the cause \
and the solution. Read the technician's question and return JSON with causes: the rows that \
can explain what the technician describes, the most likely first. For each one give its \
row_id and a likelihood: high, medium or low. Use the details in the question (for example, \
a new installation makes wrong wiring or wrong direction more likely). Only use rows from the \
table; return an empty list if none applies.

Troubleshooting table:
{table}"""


class DiagnosticianAgent:
    """Finds the likely causes of the fault in the manual's troubleshooting table."""

    name = "diagnostician"

    def __init__(self, kb: KnowledgeBase, llm=None):
        self.kb = kb
        self.llm = llm  # None in offline mode

    def run(self, question: str, triage: TriageResult) -> Diagnosis:
        matrix = self.kb.matrix_for(triage.product)
        if not matrix:
            return Diagnosis(matched_symptoms=triage.symptoms, candidates=[])
        return self.run_llm(question, triage, matrix) if self.llm else self.run_offline(triage, matrix)

    # --- LLM mode: the model picks and ranks rows of the table ---

    def run_llm(self, question: str, triage: TriageResult, matrix) -> Diagnosis:
        labels = {s.id: s.label for s in matrix.symptoms}
        table = "\n".join(
            f"{i}. Symptoms: {'; '.join(labels[s] for s in row.symptoms)} | "
            f"Cause: {row.cause} | Solution: {row.solution}"
            for i, row in enumerate(matrix.rows)
        )
        user = f"Question: {question}"
        if triage.symptoms:
            user += "\nSymptoms identified: " + "; ".join(triage.symptoms)
        out = self.llm.chat(SYSTEM_PROMPT.format(table=table), user, schema=DiagnosisLLMOutput)

        candidates, seen = [], set()
        for c in out.causes:
            if 0 <= c.row_id < len(matrix.rows) and c.row_id not in seen:  # only real rows, once
                seen.add(c.row_id)
                row = matrix.rows[c.row_id]
                candidates.append(DiagnosisCandidate(
                    cause=row.cause, solution=row.solution, likelihood=c.likelihood,
                    source_page=matrix.source_page,
                ))
        return Diagnosis(matched_symptoms=triage.symptoms, candidates=candidates)

    # --- offline mode: rows that share the matched symptoms ---

    def run_offline(self, triage: TriageResult, matrix) -> Diagnosis:
        if not triage.symptoms:
            return Diagnosis(matched_symptoms=[], candidates=[])

        ids = {s.id for s in matrix.symptoms if s.label in triage.symptoms}
        rows = [r for r in matrix.rows if ids & set(r.symptoms)]
        # causes that explain more of the reported symptoms go first
        rows.sort(key=lambda r: len(ids & set(r.symptoms)), reverse=True)

        candidates = [
            DiagnosisCandidate(
                cause=r.cause,
                solution=r.solution,
                likelihood="high" if len(ids & set(r.symptoms)) > 1 or len(rows) == 1 else "medium",
                source_page=matrix.source_page,
            )
            for r in rows
        ]
        return Diagnosis(matched_symptoms=triage.symptoms, candidates=candidates)
