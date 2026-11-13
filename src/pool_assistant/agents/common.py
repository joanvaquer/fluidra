"""Helpers shared by several agents: evidence formatting, citations, symptoms, safety."""

from __future__ import annotations

import re

from pool_assistant.schemas import Evidence, Symptom, TroubleshootingMatrix

# --------------------------------------------------------------------------- evidence


def format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "<evidence>(no passages found)</evidence>"
    parts = []
    for ev in evidence:
        c = ev.chunk
        parts.append(
            f'<passage id="{c.chunk_id}" product="{c.product}" page="{c.page}" section="{c.section}">\n'
            f"{c.text}\n</passage>"
        )
    return "<evidence>\n" + "\n".join(parts) + "\n</evidence>"


_CITATION_RE = re.compile(r"\[(?:pp?|pag|pág|S)\.?\s*([0-9][0-9,\s\-–ypagás\.]*)\]", re.IGNORECASE)


def cited_pages(text: str) -> set[int]:
    """Pages cited as [p. 9], [p. 9, 13], [pp. 9-10] (ranges are expanded)."""
    pages: set[int] = set()
    for group in _CITATION_RE.findall(text):
        for m in re.finditer(r"(\d+)\s*[-–]\s*(\d+)|(\d+)", group):
            if m.group(3):
                lo = hi = int(m.group(3))
            else:
                lo, hi = int(m.group(1)), int(m.group(2))
            if 0 < lo <= hi and hi - lo < 20:
                pages.update(range(lo, hi + 1))
    return pages


# --------------------------------------------------------------------------- symptoms

_NOISE_WORDS = ("noise", "noisy", "hum", "humming", "buzz", "ruido", "bruit")
_NO_START_WORDS = ("not start", "won't start", "doesn't start", "does not start", "no arranca", "no start")


def match_symptoms(text: str, matrix: TroubleshootingMatrix) -> list[Symptom]:
    """Keyword match of free text against the matrix symptoms (offline path only)."""
    t = text.lower()
    matched = [s for s in matrix.symptoms if any(k in t for k in s.keywords)]
    ids = {s.id for s in matched}
    # "Makes a noise but will not start" is its own symptom (5) in the manual.
    if any(w in t for w in _NOISE_WORDS) and any(w in t for w in _NO_START_WORDS):
        ids = (ids - {3, 4}) | {5}
    return [s for s in matrix.symptoms if s.id in ids]


# --------------------------------------------------------------------------- safety

ELECTRICAL_TERMS = (
    "electric", "motor", "junction box", "terminal box", "cable", "wiring", "wire", "voltage",
    "capacitor", "thermal", "phase", "fuse", "rcd", "earth", "ground", "mains", "bearing",
    "mechanical seal", "remove the motor", "eléctric", "condensador", "tensión", "fase",
    "moteur", "tension",
)
DISCONNECT_MARKERS = (
    "disconnect", "desconect", "débranch", "debranch", "déconnect", "scollega", "trennen",
    "desligar", "isolate the power", "switch off the power", "power off",
)
SAFETY_WARNING = (
    "**Safety:** before any electrical or mechanical work, disconnect the pump from the mains, "
    "block all start-up devices, check there is no voltage (including auxiliary circuits) and wait "
    "for the impeller to stop completely [p. 8]. Electrical work must be done by qualified, "
    "authorised personnel [p. 5]."
)


def needs_electrical_warning(*texts: str) -> bool:
    t = " ".join(texts).lower()
    return any(term in t for term in ELECTRICAL_TERMS)


def has_disconnect_warning(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in DISCONNECT_MARKERS)


# --------------------------------------------------------------------------- language

_LANG_STOPWORDS = {
    "en": {"the", "is", "and", "my", "it", "not", "does", "what", "how", "pump", "with", "when"},
    "es": {"el", "la", "los", "las", "es", "y", "mi", "no", "qué", "que", "cómo", "como", "bomba", "con", "hace", "por"},
    "fr": {"le", "la", "les", "est", "et", "ma", "ne", "pas", "pompe", "quoi", "comment", "avec", "fait"},
    "it": {"il", "lo", "la", "gli", "è", "e", "mia", "non", "pompa", "come", "che", "con", "fa"},
    "de": {"der", "die", "das", "ist", "und", "meine", "nicht", "pumpe", "wie", "was", "mit", "macht"},
    "pt": {"o", "a", "os", "as", "é", "e", "minha", "não", "bomba", "como", "que", "com", "faz"},
    "ca": {"el", "la", "els", "les", "és", "i", "meva", "no", "bomba", "com", "què", "amb", "fa"},
}


def detect_language(text: str) -> str:
    words = re.findall(r"[\wàáèéíïòóúüçñ']+", text.lower())
    scores = {lang: sum(w in sw for w in words) for lang, sw in _LANG_STOPWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"
