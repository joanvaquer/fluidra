import re

from pool_assistant.schemas import Symptom, TroubleshootingMatrix

NOT_FOUND = (
    "I could not find this in the available product manuals. "
    "Please contact the nearest Technical Assistance Service."
)


def cited_pages(text: str) -> set[int]:
    """Page numbers cited as [p. 9] or [p. 9, 13]."""
    pages = set()
    for group in re.findall(r"\[p\.\s*([\d,\s]+)\]", text):
        pages.update(int(n) for n in re.findall(r"\d+", group))
    return pages


# --- offline mode: language ---

STOPWORDS_BY_LANGUAGE = {
    "en": {"the", "is", "and", "my", "it", "not", "does", "what", "how", "with", "when"},
    "es": {"el", "la", "los", "las", "es", "y", "mi", "no", "qué", "que", "cómo", "como", "con", "hace", "por"},
    "fr": {"le", "la", "les", "est", "et", "ma", "ne", "pas", "pompe", "comment", "avec"},
    "it": {"il", "lo", "gli", "è", "mia", "non", "pompa", "come", "che", "con"},
    "de": {"der", "die", "das", "ist", "und", "meine", "nicht", "pumpe", "wie", "was", "mit"},
    "pt": {"o", "os", "é", "minha", "não", "como", "com", "faz"},
}


def detect_language(text: str) -> str:
    words = re.findall(r"[\wàáèéíïòóúüçñ']+", text.lower())
    scores = {lang: sum(w in stopwords for w in words) for lang, stopwords in STOPWORDS_BY_LANGUAGE.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"


# --- offline mode: symptoms (uses the keywords in data/curated) ---

def match_symptoms(text: str, matrix: TroubleshootingMatrix) -> list[Symptom]:
    text = text.lower()
    ids = {s.id for s in matrix.symptoms if any(k in text for k in s.keywords)}
    # "makes a noise but will not start" is its own symptom (5) in the manual
    if ids & {3, 5} and 4 in ids:
        ids = (ids - {3, 4}) | {5}
    return [s for s in matrix.symptoms if s.id in ids]


# --- offline and auto modes: electrical/mechanical work needs the disconnect-power warning ---
# (in the LLM modes the writer and verifier models decide this; the warning text is shared).
# In auto mode the LLM writer answers in the technician's language, so the words cover the
# languages it writes in.

ELECTRICAL_TERMS = [
    "electric", "motor", "junction box", "terminal box", "cable", "wiring", "voltage",
    "capacitor", "thermal", "phase", "fuse", "mains", "bearing", "mechanical seal",
    "eléctric", "tensión", "condensador", "cableado", "fase",      # es
    "elèctric", "tensió", "cablejat",                              # ca
    "électri", "câbl", "tension",                                  # fr
    "elettric", "cavo", "cavi",                                    # it
    "elektr", "kabel", "spannung",                                 # de
    "elétric", "tensão",                                           # pt
]
DISCONNECT_WORDS = [
    "disconnect", "desconect", "desconnect", "déconnect", "débranch", "disconnett", "disconness",
    "scollega", "trennen", "abklemmen", "desligar",
]
SAFETY_WARNINGS = {
    "en": "**Safety:** before any electrical or mechanical work, disconnect the pump from the mains, "
          "block all start-up devices, check there is no voltage and wait for the impeller to stop "
          "completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].",
    "es": "**Seguridad:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la red, "
          "bloquee los dispositivos de arranque, compruebe que no hay tensión y espere a que el impulsor "
          "se detenga por completo [p. 8]. El trabajo eléctrico debe hacerlo personal cualificado [p. 5].",
}


def needs_safety_warning(*texts: str) -> bool:
    text = " ".join(texts).lower()
    return any(term in text for term in ELECTRICAL_TERMS)


def has_safety_warning(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in DISCONNECT_WORDS)


def safety_warning(language: str) -> str:
    return SAFETY_WARNINGS.get(language, SAFETY_WARNINGS["en"])


LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "ca": "Catalan", "fr": "French",
                  "it": "Italian", "de": "German", "pt": "Portuguese"}
