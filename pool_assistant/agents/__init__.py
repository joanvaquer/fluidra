"""The five agents, numbered in the order the orchestrator runs them (0_common.py holds the
rules they share).

Every agent has two implementations, and the mode the user picks chooses one:
- an LLM model (qwen, llama, gemma, deepseek): the agent decides with the LLM;
- offline: the agent decides with word matching and fixed rules, and no LLM is used;
- auto: triage and writer use the LLM, retriever, diagnostician and verifier the offline rules.
There is no fallback between them: if an LLM call fails, the question fails.

The files are imported by their names without the number (see pool_assistant/__init__.py):
`triage` is 1_triage.py, and so on. Other modules can then write
`from pool_assistant.agents import TriageAgent`.
"""

from pool_assistant.agents.triage import TriageAgent
from pool_assistant.agents.retriever import RetrieverAgent
from pool_assistant.agents.diagnostician import DiagnosticianAgent
from pool_assistant.agents.writer import WriterAgent
from pool_assistant.agents.verifier import VerifierAgent

__all__ = ["TriageAgent", "RetrieverAgent", "DiagnosticianAgent", "WriterAgent", "VerifierAgent"]
