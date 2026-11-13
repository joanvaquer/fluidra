"""Command-line interface.

    pool-assistant "The pump makes a noise"          # one question
    pool-assistant                                   # interactive session
    pool-assistant --json --mode offline "..."       # full JSON response, no LLM
"""

from __future__ import annotations

import argparse
import logging
import sys

from pool_assistant import config
from pool_assistant.orchestrator import build_orchestrator
from pool_assistant.schemas import AssistantResponse


def render(resp: AssistantResponse, show_trace: bool) -> str:
    out = [resp.answer, ""]
    if resp.sources:
        pages = ", ".join(f"p. {p}" for p in sorted({s.page for s in resp.sources}))
        out.append(f"Sources: {resp.sources[0].product} manual ({pages})")
    status = "verified" if resp.verified else "NOT verified"
    out.append(f"[{resp.intent.value} | {resp.language} | {status} | {resp.llm_mode}]")
    if show_trace:
        out.append("")
        out += [f"  {t.agent:<14}{t.duration_ms:>7} ms  {t.summary}" for t in resp.trace]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask the pool technician assistant a question.")
    parser.add_argument("question", nargs="*", help="question to ask; omit for an interactive session")
    parser.add_argument("--mode", default=config.LLM_MODE, choices=["auto", "claude", "offline"])
    parser.add_argument("--json", action="store_true", help="print the full JSON response")
    parser.add_argument("--trace", action="store_true", help="show the per-agent trace")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    orchestrator = build_orchestrator(args.mode)

    def answer(question: str) -> None:
        resp = orchestrator.ask(question)
        print(resp.model_dump_json(indent=2) if args.json else render(resp, args.trace))

    if args.question:
        answer(" ".join(args.question))
        return 0

    print(f"Pool technician assistant ({orchestrator.mode}). Empty line or Ctrl+C to quit.")
    try:
        while question := input("\n> ").strip():
            answer(question)
    except (EOFError, KeyboardInterrupt):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
