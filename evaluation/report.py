"""Scores the answers in results/answers.jsonl and writes REPORT.md and results/answers.md.

    python evaluation/report.py

Every check is automatic and objective (see CHECKS). findings.md, written by a person after
reading the answers, is included at the top of the report if it exists.
"""

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from pool_assistant import config
from pool_assistant.agents.common import cited_pages, has_safety_warning

HERE = Path(__file__).parent
QUESTIONS = HERE / "questions.json"
ANSWERS = HERE / "results" / "answers.jsonl"
FINDINGS = HERE / "findings.md"
REPORT = HERE / "REPORT.md"
ANSWERS_MD = HERE / "results" / "answers.md"

SAFETY_PAGES = {5, 8}  # the standard safety warning cites them
LLM_AGENTS = {
    **{m: {"triage", "retriever", "diagnostician", "writer", "verifier"} for m in config.MODELS},
    config.AUTO: config.AUTO_LLM_AGENTS,
    config.OFFLINE: set(),
}

CHECKS = {
    "answered": "No error: the mode returned an answer",
    "scope": "In-scope questions answered, out-of-scope refused",
    "intent": "Triage found the right intent",
    "language": "Triage detected the question's language",
    "answer_language": "The answer is written in the question's language",
    "cause_found": "A correct cause is among the diagnosed causes",
    "top_cause": "The first diagnosed cause is a correct one",
    "page_cited": "The answer cites the page that has the answer",
    "citations_valid": "Every cited page is in the evidence (no made-up pages)",
    "safety": "Disconnect-power warning present when electrical work is involved",
    "facts": "The answer contains the key fact",
    "no_invented_years": "No invented warranty period (the manual gives none)",
}

# words that are frequent in one language and rare in the others, to tell which one an answer uses
LANGUAGE_WORDS = {
    "en": {"the", "and", "is", "check", "pump", "if", "with", "of", "to", "your", "this", "that", "should"},
    "es": {"los", "las", "del", "con", "para", "una", "está", "debe", "compruebe", "revise", "verifique",
           "también", "puede", "cuando", "bomba", "agua", "si", "el", "y"},
    "ca": {"els", "les", "amb", "és", "per", "cal", "dels", "heu", "comproveu", "reviseu", "també", "pot",
           "aquest", "aquesta", "aigua", "si", "el", "i"},
    "fr": {"le", "les", "des", "est", "et", "avec", "pour", "une", "vérifiez", "votre", "pompe", "du", "eau"},
    "it": {"il", "gli", "della", "con", "per", "una", "è", "controllare", "verificare", "pompa", "acqua", "di"},
    "de": {"der", "die", "das", "und", "ist", "mit", "für", "eine", "nicht", "pumpe", "jahr", "sie"},
    "pt": {"os", "as", "da", "do", "com", "para", "uma", "não", "água", "bomba", "verifique", "é", "o"},
}


def answer_language(text: str) -> str:
    text = re.sub(r"\[p\.[^\]]*\]", " ", text.lower())
    words = re.findall(r"[a-zàáèéíïòóúüçñâêôãõäöß']+", text)
    scores = {lang: sum(w in vocab for w in words) for lang, vocab in LANGUAGE_WORDS.items()}
    return max(scores, key=scores.get)


INVENTED_YEARS = re.compile(
    r"\b(\d+|one|two|three|five|ten)[\s-]*(years?|yr)\b.{0,40}warrant|warrant.{0,60}\b(\d+|one|two|three|five|ten)[\s-]*(years?|yr)\b",
    re.IGNORECASE | re.DOTALL,
)


def score(q: dict, record: dict) -> dict[str, bool | None]:
    """check -> passed (True/False), or None when the check doesn't apply to this question."""
    result = dict.fromkeys(CHECKS)
    r = record["response"]
    result["answered"] = r is not None
    if r is None:
        return result

    answer = r["answer"]
    refused = r["intent"] == "out_of_scope"
    if q["intent"] == ["out_of_scope"]:
        result["scope"] = refused
        return result  # the refusal is fixed text, so nothing else applies
    if refused and "out_of_scope" in q["intent"]:  # refusing is acceptable for this question
        result["scope"] = True
        if q.get("trap") == "no_invented_years":
            result["no_invented_years"] = True
        return result
    result["scope"] = not refused

    result["intent"] = r["intent"] in q["intent"]
    result["language"] = r["language"] == q["language"]
    result["answer_language"] = answer_language(answer) == q["language"]

    if q["causes"]:
        causes = [c["cause"] for c in (r["diagnosis"] or {}).get("candidates", [])]
        result["cause_found"] = any(c in q["causes"] for c in causes)
        result["top_cause"] = bool(causes) and causes[0] in q["causes"]

    cited = cited_pages(answer)
    allowed = {s["page"] for s in r["sources"]} | SAFETY_PAGES
    allowed |= {c["source_page"] for c in (r["diagnosis"] or {}).get("candidates", [])}
    if q["pages"]:
        result["page_cited"] = bool(set(q["pages"]) & cited)
    if q.get("trap") != "no_invented_years":
        result["citations_valid"] = bool(cited) and cited <= allowed
    if q["safety"]:
        result["safety"] = has_safety_warning(answer)
    if q["facts"]:
        result["facts"] = any(f in answer.lower() for f in q["facts"])
    if q.get("trap") == "no_invented_years":
        result["no_invented_years"] = not INVENTED_YEARS.search(answer)
    return result


def pct(values) -> str:
    values = [v for v in values if v is not None]
    return f"{100 * sum(values) / len(values):.0f}%" if values else "—"


def seconds(s: float) -> str:
    return f"{s:.0f} s" if s >= 10 else f"{s:.1f} s" if s >= 0.1 else "<0.1 s"


def main():
    questions = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    records = {}
    for line in ANSWERS.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        records[(r["mode"], r["id"])] = r  # a re-run of the same question replaces the old one
    modes = [m for m in config.MODES if any(k[0] == m for k in records)]

    scores = {k: score(questions[k[1]], r) for k, r in records.items()}

    def mode_checks(mode):
        return [v for (m, _), s in scores.items() if m == mode for v in s.values()]

    out = ["# Evaluation: six modes, ten questions", ""]
    out += [
        f"Every mode answered the same {len(questions)} questions, in {len(set(q['language'] for q in questions.values()))} "
        "languages, some with typos or missing accents, plus an out-of-scope question and one whose answer "
        "is not in the manual. All models run locally with Ollama on the same laptop CPU, at temperature 0. "
        "Each model was loaded before its first question, so the times are answering time only.",
        "",
        "Questions: [questions.json](questions.json). Every answer: [results/answers.md](results/answers.md). "
        "Re-run with `python evaluation/run.py`, then `python evaluation/report.py`.",
        "",
    ]
    if FINDINGS.exists():
        out += [FINDINGS.read_text(encoding="utf-8").strip(), ""]

    # --- summary ---
    out += ["## Summary", "",
            "| Mode | Model | Score | Mean time | Median | Slowest | LLM calls / question | Verified | Errors |",
            "|---|---|---|---|---|---|---|---|---|"]
    for mode in modes:
        recs = [r for (m, _), r in records.items() if m == mode]
        times = [r["seconds"] for r in recs]
        ok = [r for r in recs if r["response"]]
        calls = [sum(s["agent"] in LLM_AGENTS[mode] for s in r["response"]["trace"]) for r in ok]
        model = next((r["response"]["model"] for r in ok if r["response"]["model"]), None) or "—"
        out.append(
            f"| `{mode}` | {model} | **{pct(mode_checks(mode))}** | {seconds(statistics.mean(times))} | "
            f"{seconds(statistics.median(times))} | {seconds(max(times))} | "
            f"{statistics.mean(calls):.1f} | {sum(r['response']['verified'] for r in ok)}/{len(recs)} | "
            f"{len(recs) - len(ok)} |"
        )
    out += ["", "*Score*: share of the applicable checks below that passed, over all ten questions. "
            "*Verified*: answers the mode's own verifier approved (it is not a measure of correctness). "
            "*LLM calls*: 2 in `auto` and 5 in the LLM modes, plus 1 or 2 when an answer is rewritten.", ""]

    # --- per check ---
    out += ["## Results by check", "", "| Check | " + " | ".join(f"`{m}`" for m in modes) + " |",
            "|---|" + "---|" * len(modes)]
    for check, label in CHECKS.items():
        cells = [pct(s[check] for (m, _), s in scores.items() if m == mode) for mode in modes]
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    out.append("")

    # --- per question ---
    out += ["## Results by question", "",
            "Score of each answer (checks passed / applicable) and its time.", "",
            "| Question | Lang | Variant | " + " | ".join(f"`{m}`" for m in modes) + " |",
            "|---|---|---|" + "---|" * len(modes)]
    for qid, q in questions.items():
        cells = []
        for mode in modes:
            if (mode, qid) not in records:
                cells.append("—")
                continue
            s = [v for v in scores[(mode, qid)].values() if v is not None]
            r = records[(mode, qid)]
            mark = "error" if not r["response"] else f"{sum(s)}/{len(s)}"
            cells.append(f"{mark} · {seconds(r['seconds'])}")
        short = q["question"] if len(q["question"]) <= 48 else q["question"][:45] + "…"
        out.append(f"| {qid}: {short} | {q['language']} | {q['variant']} | " + " | ".join(cells) + " |")
    out.append("")

    # --- failed checks, to see what went wrong ---
    out += ["## Failed checks", ""]
    for mode in modes:
        fails = [f"{qid} {check}" for (m, qid), s in sorted(scores.items()) if m == mode
                 for check, v in s.items() if v is False]
        out.append(f"- `{mode}`: " + (", ".join(fails) if fails else "none"))
    out.append("")

    REPORT.write_text("\n".join(out), encoding="utf-8")

    # --- every answer, for reading ---
    lines = ["# Every answer", ""]
    for qid, q in questions.items():
        lines += [f"## {qid} ({q['language']}, {q['variant']}): {q['question']}", "", f"*Expected:* {q['note']}", ""]
        for mode in modes:
            r = records.get((mode, qid))
            if not r:
                continue
            failed = [c for c, v in scores[(mode, qid)].items() if v is False]
            lines.append(f"### `{mode}` · {seconds(r['seconds'])}" + (f" · failed: {', '.join(failed)}" if failed else ""))
            lines.append("")
            if r["response"]:
                resp = r["response"]
                causes = [c["cause"] for c in (resp["diagnosis"] or {}).get("candidates", [])]
                lines.append(f"*intent* {resp['intent']} · *language* {resp['language']} · *verified* {resp['verified']}"
                             + (f" · *causes* {'; '.join(causes)}" if causes else ""))
                lines += ["", "> " + resp["answer"].replace("\n", "\n> "), ""]
            else:
                lines += [f"**Error:** {r['error']}", ""]
    ANSWERS_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT} and {ANSWERS_MD}")


if __name__ == "__main__":
    main()
