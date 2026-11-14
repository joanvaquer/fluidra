"""Agent 3, diagnostician: for a fault, the likely causes and fixes from the manual's
troubleshooting table, most likely first. Only troubleshooting questions get here.

Whatever the mode, the causes and solutions are always copied from the table: the LLM only
chooses rows by number, so it can't invent a cause.
"""

from pool_assistant.knowledge import KnowledgeBase
from pool_assistant.schemas import Diagnosis, DiagnosisCandidate, DiagnosisLLMOutput, TriageResult

# Instructions for the LLM. {table} is the troubleshooting table, one numbered row per line.
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
        # without a troubleshooting table for the product there is nothing to diagnose from
        matrix = self.kb.matrix_for(triage.product)
        if not matrix:
            return Diagnosis(matched_symptoms=triage.symptoms, candidates=[])
        return self.run_llm(question, triage, matrix) if self.llm else self.run_offline(triage, matrix)

    # --- LLM mode: the model picks and ranks rows of the table ---

    def run_llm(self, question: str, triage: TriageResult, matrix) -> Diagnosis:
        # 1. The table as numbered lines: "0. Symptoms: ... | Cause: ... | Solution: ..."
        labels = {s.id: s.label for s in matrix.symptoms}
        table = "\n".join(
            f"{i}. Symptoms: {'; '.join(labels[s] for s in row.symptoms)} | "
            f"Cause: {row.cause} | Solution: {row.solution}"
            for i, row in enumerate(matrix.rows)
        )
        # 2. The question, plus the symptoms triage found, as a hint.
        user = f"Question: {question}"
        if triage.symptoms:
            user += "\nSymptoms identified: " + "; ".join(triage.symptoms)
        out = self.llm.chat(SYSTEM_PROMPT.format(table=table), user, schema=DiagnosisLLMOutput)

        # 3. Turn the chosen row numbers into causes, in the model's order. The text is copied
        #    from the table; the model only contributes the order and the likelihood.
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
        # no symptoms found by triage -> no row can be chosen
        if not triage.symptoms:
            return Diagnosis(matched_symptoms=[], candidates=[])

        # the ids of the reported symptoms, and every row that explains at least one of them
        ids = {s.id for s in matrix.symptoms if s.label in triage.symptoms}
        rows = [r for r in matrix.rows if ids & set(r.symptoms)]
        # causes that explain more of the reported symptoms go first
        rows.sort(key=lambda r: len(ids & set(r.symptoms)), reverse=True)

        # likelihood: "high" if the row explains several reported symptoms, or is the only
        # candidate; "medium" otherwise
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
