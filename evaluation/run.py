"""Asks every question in questions.json in every mode and saves the answers and timings.

    python evaluation/run.py                      # all modes
    python evaluation/run.py --modes offline auto # some modes

Each answer is appended to results/answers.jsonl as soon as it is ready, and questions already
answered are skipped, so an interrupted run continues where it stopped (--fresh starts over).
Before a mode's first question the model is loaded with a short warm-up call, so the timings
measure answering, not loading the model from disk.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from pool_assistant import config
from pool_assistant.llm import LLMError
from pool_assistant.orchestrator import build_orchestrator

HERE = Path(__file__).parent
QUESTIONS = HERE / "questions.json"
ANSWERS = HERE / "results" / "answers.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", nargs="+", choices=config.MODES, default=list(config.MODES))
    parser.add_argument("--fresh", action="store_true", help="delete previous answers first")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    ANSWERS.parent.mkdir(exist_ok=True)
    if args.fresh:
        ANSWERS.unlink(missing_ok=True)
    done = set()
    if ANSWERS.exists():
        done = {(r["mode"], r["id"]) for r in map(json.loads, ANSWERS.read_text(encoding="utf-8").splitlines())}

    for mode in args.modes:
        todo = [q for q in questions if (mode, q["id"]) not in done]
        if not todo:
            continue
        try:
            assistant = build_orchestrator(mode)
            if assistant.llm:
                start = time.perf_counter()
                assistant.llm.chat("Reply with OK.", "Hi")  # load the model into memory
                print(f"[{mode}] model loaded in {time.perf_counter() - start:.0f} s", flush=True)
        except LLMError as e:
            print(f"[{mode}] skipped: {e}", flush=True)
            continue

        for q in todo:
            start = time.perf_counter()
            record = {"mode": mode, "id": q["id"], "question": q["question"]}
            try:
                response = assistant.ask(q["question"])
                record |= {"error": None, "response": response.model_dump(mode="json")}
            except LLMError as e:  # a failed call counts as a failed answer, not a crash
                record |= {"error": str(e), "response": None}
            record["seconds"] = round(time.perf_counter() - start, 2)

            with ANSWERS.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            status = "error" if record["error"] else ("verified" if record["response"]["verified"] else "unverified")
            print(f"[{mode}] {q['id']} {record['seconds']:7.1f} s  {status}", flush=True)


if __name__ == "__main__":
    main()
