"""Usage: pool-assistant "The pump makes a noise" --mode qwen|llama|gemma|deepseek|auto|offline [--trace]

The command-line way to ask one question. The `pool-assistant` command is set up in
pyproject.toml ([project.scripts]) to call main() below.
"""

import argparse
import sys

from pool_assistant import config
from pool_assistant.llm import LLMError
from pool_assistant.orchestrator import build_orchestrator


def main():
    # --- read the arguments: the question, the mode (required) and --trace ---
    parser = argparse.ArgumentParser(description="Ask the pool technician assistant a question.")
    parser.add_argument("question")
    parser.add_argument(
        "--mode", required=True, choices=config.MODES,  # any other value is rejected with an error
        help="an LLM run locally by Ollama (qwen, llama, gemma, deepseek); auto: the LLM only for "
             "triage and writer, search and rules for the rest; or offline: word matching, no LLM",
    )
    parser.add_argument("--trace", action="store_true", help="show what each agent did")
    args = parser.parse_args()

    # --- answer the question ---
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    try:
        response = build_orchestrator(args.mode).ask(args.question)
    except LLMError as e:  # Ollama not running, model not downloaded, or a call failed
        sys.exit(f"error: {e}")  # print the reason and stop with an error exit code

    # --- print the answer, the cited pages and, with --trace, each agent's step ---
    print(response.answer)
    if response.sources:
        print("\nSources: " + ", ".join(f"p. {p}" for p in sorted({s.page for s in response.sources})))
    if args.trace:
        print(f"\nMode: {response.mode}" + (f" ({response.model})" if response.model else ""))
        for s in response.trace:
            seconds = f"{s.duration_ms / 1000:.1f} s" if s.duration_ms >= 100 else "<0.1 s"  # e.g. "20.2 s"
            print(f"  {s.agent:<14}{seconds:>8}  {s.summary}")


# lets the file also be run as: python -m pool_assistant.cli "..." --mode offline
if __name__ == "__main__":
    main()
