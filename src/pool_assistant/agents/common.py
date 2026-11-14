"""Helpers shared by several agents: reading citations, detecting the language, matching
symptoms by keyword, and the safety warning rules and text. None of them uses an LLM.
"""

import re

from pool_assistant.schemas import Symptom, TroubleshootingMatrix

# The fixed answer when the manual has nothing on the question (writer and verifier use it).
NOT_FOUND = (
    "I could not find this in the available product manuals. "
    "Please contact the nearest Technical Assistance Service."
)


def cited_pages(text: str) -> set[int]:
    """Page numbers cited as [p. 9] or [p. 9, 13]."""
    pages = set()
    # find every "[p. ...]" and take all the numbers inside it
    for group in re.findall(r"\[p\.\s*([\d,\s]+)\]", text):
        pages.update(int(n) for n in re.findall(r"\d+", group))
    return pages


# --- offline mode: language ---

# Short, very common words of each language. The language with most of them in the text wins.
STOPWORDS_BY_LANGUAGE = {
    "en": {"the", "is", "and", "my", "it", "not", "does", "what", "how", "with", "when"},
    "es": {"el", "la", "los", "las", "es", "y", "mi", "no", "qué", "que", "cómo", "como", "con", "hace", "por"},
    "fr": {"le", "la", "les", "est", "et", "ma", "ne", "pas", "pompe", "comment", "avec"},
    "it": {"il", "lo", "gli", "è", "mia", "non", "pompa", "come", "che", "con"},
    "de": {"der", "die", "das", "ist", "und", "meine", "nicht", "pumpe", "wie", "was", "mit"},
    "pt": {"o", "os", "é", "minha", "não", "como", "com", "faz"},
}


def detect_language(text: str) -> str:
    """The language code whose common words appear most in the text; English if none appear."""
    words = re.findall(r"[\wàáèéíïòóúüçñ']+", text.lower())
    scores = {lang: sum(w in stopwords for w in words) for lang, stopwords in STOPWORDS_BY_LANGUAGE.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"


# --- offline mode: symptoms (uses the keywords in data/curated) ---

def match_symptoms(text: str, matrix: TroubleshootingMatrix) -> list[Symptom]:
    """The table's symptoms whose keywords appear in the text."""
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

# Words that show electrical or mechanical work (parts of words, so "eléctric" matches
# "eléctrico" and "eléctrica").
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
# Words that show the answer tells the technician to disconnect the power, in each language.
DISCONNECT_WORDS = [
    "disconnect", "desconect", "desconnect", "déconnect", "débranch", "disconnett", "disconness",
    "scollega", "trennen", "abklemmen", "desligar",
]
# The standard warning, from the manual's safety pages (8 and 5).
SAFETY_WARNINGS = {
    "en": "**Safety:** before any electrical or mechanical work, disconnect the pump from the mains, "
          "block all start-up devices, check there is no voltage and wait for the impeller to stop "
          "completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].",
    "es": "**Seguridad:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la red, "
          "bloquee los dispositivos de arranque, compruebe que no hay tensión y espere a que el impulsor "
          "se detenga por completo [p. 8]. El trabajo eléctrico debe hacerlo personal cualificado [p. 5].",
}


def needs_safety_warning(*texts: str) -> bool:
    """True if any of the texts (e.g. the question and the answer) mentions electrical work."""
    text = " ".join(texts).lower()
    return any(term in text for term in ELECTRICAL_TERMS)


def has_safety_warning(text: str) -> bool:
    """True if the text tells the technician to disconnect the power."""
    text = text.lower()
    return any(word in text for word in DISCONNECT_WORDS)


def safety_warning(language: str) -> str:
    """The standard warning in that language, or in English if it isn't translated."""
    return SAFETY_WARNINGS.get(language, SAFETY_WARNINGS["en"])


# Language codes -> names, for the writer's prompt ("Write the whole answer in Spanish").
LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "ca": "Catalan", "fr": "French",
                  "it": "Italian", "de": "German", "pt": "Portuguese"}
