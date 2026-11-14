from pool_assistant import config
from pool_assistant.knowledge import KnowledgeBase
from pool_assistant.schemas import Evidence, RetrievalLLMOutput, TriageResult

SYSTEM_PROMPT = """You find the passages of a pool equipment manual that answer a technician's \
question.

Below is the list of passages, each with its number, page, section and the start of its text. \
Return JSON with passage_ids: the numbers of the passages needed to answer the question, the \
most useful first, at most {k}. Return an empty list if none of them is relevant.

Passages:
{catalog}"""

PREVIEW_CHARS = 300  # how much of each passage the LLM sees when choosing


class RetrieverAgent:
    """Finds the manual passages related to the question."""

    name = "retriever"

    def __init__(self, kb: KnowledgeBase, llm=None):
        self.kb = kb
        self.llm = llm  # None in offline mode

    def run(self, question: str, triage: TriageResult) -> list[Evidence]:
        return self.run_llm(question, triage) if self.llm else self.run_offline(question, triage)

    # --- LLM mode: the model reads the list of passages and picks the relevant ones ---

    def run_llm(self, question: str, triage: TriageResult) -> list[Evidence]:
        chunks = [c for c in self.kb.chunks if triage.product is None or c.product == triage.product]
        catalog = "\n".join(
            f"{i}. [p. {c.page}] {c.section}: {' '.join(c.text.split())[:PREVIEW_CHARS]}"
            for i, c in enumerate(chunks)
        )
        user = f"Question: {question}\nIn the manual's words: {triage.search_query}"
        if triage.symptoms:
            user += "\nReported symptoms: " + "; ".join(triage.symptoms)

        prompt = SYSTEM_PROMPT.format(k=config.EVIDENCE_K, catalog=catalog)
        out = self.llm.chat(prompt, user, schema=RetrievalLLMOutput)

        ids = [i for i in dict.fromkeys(out.passage_ids) if 0 <= i < len(chunks)]  # ignore made-up ids
        return [
            Evidence(chunk=chunks[i], score=1 / (rank + 1))
            for rank, i in enumerate(ids[: config.EVIDENCE_K])
        ]

    # --- offline mode: BM25 word search ---

    def run_offline(self, question: str, triage: TriageResult) -> list[Evidence]:
        # the symptom labels use the manual's wording, so they also find passages
        # when the question is paraphrased
        queries = list(dict.fromkeys([question, triage.search_query, *triage.symptoms]))
        return self.kb.search_many(queries, k=config.EVIDENCE_K, product=triage.product)
