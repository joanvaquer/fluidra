"""Usage: pool-assistant "The pump makes a noise" --mode qwen|llama|gemma|deepseek|auto|offline [--trace]"""

import argparse
import sys

from pool_assistant import config
from pool_assistant.llm import LLMError
from pool_assistant.orchestrator import build_orchestrator


def main():
    parser = argparse.ArgumentParser(description="Ask the pool technician assistant a question.")
    parser.add_argument("question")
    parser.add_argument(
        "--mode", required=True, choices=config.MODES,
        help="an LLM run locally by Ollama (qwen, llama, gemma, deepseek); auto: the LLM only for "
             "triage and writer, search and rules for the rest; or offline: word matching, no LLM",
    )
    parser.add_argument("--trace", action="store_true", help="show what each agent did")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    try:
        response = build_orchestrator(args.mode).ask(args.question)
    except LLMError as e:  # Ollama not running, model not downloaded, or a call failed
        sys.exit(f"error: {e}")

    print(response.answer)
    if response.sources:
        print("\nSources: " + ", ".join(f"p. {p}" for p in sorted({s.page for s in response.sources})))
    if args.trace:
        print(f"\nMode: {response.mode}" + (f" ({response.model})" if response.model else ""))
        for s in response.trace:
            print(f"  {s.agent:<14}{s.duration_ms:>7} ms  {s.summary}")


if __name__ == "__main__":
    main()
