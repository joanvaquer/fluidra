"""Agent 1, triage: the first look at the question.

It decides whether the question is about pool equipment at all, what kind of help it needs
(the intent), the language, the product and, for a fault, which symptoms of the
troubleshooting table it describes. Its result chooses the route through the other agents.
"""

from pool_assistant.agents.common import detect_language, match_symptoms
from pool_assistant.knowledge import KnowledgeBase
from pool_assistant.schemas import Intent, TriageLLMOutput, TriageResult

# Instructions for the LLM. {products} and {symptoms} are filled in with the lists from the
# knowledge base, so the model picks from them instead of making names up.
SYSTEM_PROMPT = """You classify questions from pool technicians about pool equipment.

Return JSON with:
- in_scope: true if the question is about installing, starting up, maintaining, repairing \
or safely working on pool equipment; false for anything else.
- intent: troubleshooting (something is not working), installation, start_up, maintenance, \
safety, general, or out_of_scope.
- language: ISO 639-1 code of the language the question is written in (en, es, fr...).
- product: the product the question is about, from the list below, or null if it is not named.
- symptom_ids: for troubleshooting, the ids of the symptoms below that the technician \
describes, even if worded differently or in another language. Otherwise an empty list.
- search_query: the question rewritten as a short English search query, using the words \
a pump manual would use.

Products: {products}

Symptoms:
{symptoms}"""


class TriageAgent:
    """Decides whether the question is in scope, what kind of help is needed,
    which product it is about, the language, and the reported symptoms."""

    name = "triage"

    def __init__(self, kb: KnowledgeBase, llm=None):
        self.kb = kb
        self.llm = llm  # None in offline mode

    def run(self, question: str) -> TriageResult:
        # the orchestrator decides the implementation by giving this agent an LLM or not
        return self.run_llm(question) if self.llm else self.run_offline(question)

    # --- LLM mode ---

    def run_llm(self, question: str) -> TriageResult:
        # 1. Build the prompt with the numbered symptom list of every troubleshooting table,
        #    e.g. "3: The pump makes a noise".
        symptoms = "\n".join(
            f"{s.id}: {s.label}" for matrix in self.kb.matrices.values() for s in matrix.symptoms
        ) or "(none)"
        prompt = SYSTEM_PROMPT.format(products=", ".join(self.kb.products), symptoms=symptoms)
        # 2. Ask the LLM; the reply comes back as a validated TriageLLMOutput.
        out = self.llm.chat(prompt, question, schema=TriageLLMOutput)

        # 3. Keep only what exists in the manual: a product name from the list, and symptom
        #    ids from the table, turned into the table's own labels.
        product = out.product if out.product in self.kb.products else None
        matrix = self.kb.matrix_for(product)
        labels = {s.id: s.label for s in matrix.symptoms} if matrix else {}
        symptoms = [labels[i] for i in dict.fromkeys(out.symptom_ids) if i in labels]  # ignore made-up ids

        # 4. Settle the intent: out of scope wins; any symptom found means a fault.
        in_scope = out.in_scope and out.intent != Intent.OUT_OF_SCOPE
        if not in_scope:
            intent = Intent.OUT_OF_SCOPE
        elif symptoms:
            intent = Intent.TROUBLESHOOTING  # the model found symptoms, so something is not working
        else:
            intent = out.intent

        return TriageResult(
            in_scope=in_scope,
            intent=intent,
            language=out.language.lower()[:2] or "en",  # "ES" or "es-ES" -> "es"
            product=product,
            symptoms=symptoms if intent == Intent.TROUBLESHOOTING else [],
            search_query=out.search_query or question,
        )

    # --- offline mode ---

    def run_offline(self, question: str) -> TriageResult:
        # match the product on the first word of its name, e.g. "astral"
        product = next((p for p in self.kb.products if p.split()[0].lower() in question.lower()), None)
        matrix = self.kb.matrix_for(product)

        # in scope if it mentions pool equipment; the intent comes from keyword lists (below)
        in_scope = is_pool_question(question)
        intent = keyword_intent(question) if in_scope else Intent.OUT_OF_SCOPE

        # for a fault, find the symptoms with the keywords stored in the troubleshooting table
        symptoms = []
        if intent == Intent.TROUBLESHOOTING and matrix:
            symptoms = [s.label for s in match_symptoms(question, matrix)]

        return TriageResult(
            in_scope=in_scope,
            intent=intent,
            language=detect_language(question),
            product=product,
            symptoms=symptoms,
            search_query=question,  # no rewriting without an LLM: search with the question itself
        )


# --- keyword lists for offline mode ---

# checked in this order, the first match wins
INTENT_KEYWORDS = {
    Intent.TROUBLESHOOTING: [
        "noise", "noisy", "won't", "will not", "doesn't", "does not", "not work", "stopped", "trip",
        "leak", "problem", "fault", "error", "broken", "flow", "not primed", "hum", "vibrat",
        "overheat", "ruido", "no arranca", "no funciona", "fuga", "problema",
    ],
    Intent.SAFETY: ["safe", "danger", "risk", "electrocut", "rcd", "zone 0", "zone 1", "children"],
    Intent.START_UP: ["start-up", "startup", "start up", "first start", "priming", "prime the pump"],
    Intent.MAINTENANCE: ["maintenance", "maintain", "clean", "replace", "how often", "winter", "freez", "mantenimiento"],
    Intent.INSTALLATION: ["install", "mount", "pipe", "piping", "suction", "cable", "wiring", "connect", "location"],
}

# words that show the question is about pool equipment at all
DOMAIN_WORDS = [
    "pump", "pool", "filter", "motor", "prime", "priming", "valve", "seal", "basket", "impeller",
    "suction", "voltage", "capacitor", "bearing", "junction", "thermal", "flow", "water", "pipe",
    "bomba", "piscina", "filtro", "pompe", "piscine", "pompa", "pumpe", "astral", "astralpool",
]


def is_pool_question(question: str) -> bool:
    """True if the question contains any word about pool equipment."""
    q = question.lower()
    return any(word in q for word in DOMAIN_WORDS)


def keyword_intent(question: str) -> Intent:
    """The first intent whose keywords appear in the question, or GENERAL."""
    q = question.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(k in q for k in keywords):
            return intent
    return Intent.GENERAL
