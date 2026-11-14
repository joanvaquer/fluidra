"""The five agents, numbered in the order the orchestrator runs them.

Every agent has two implementations, and the mode the user picks chooses one:
- an LLM model (qwen, llama, gemma, deepseek): the agent decides with the LLM;
- offline: the agent decides with word matching and fixed rules, and no LLM is used;
- auto: triage and writer use the LLM, retriever, diagnostician and verifier the offline rules.
There is no fallback between them: if an LLM call fails, the question fails.

The file names start with a number, which `import` statements can't use, so they are
loaded with importlib.
"""

from importlib import import_module

TriageAgent = import_module("pool_assistant.agents.1_triage").TriageAgent
RetrieverAgent = import_module("pool_assistant.agents.2_retriever").RetrieverAgent
DiagnosticianAgent = import_module("pool_assistant.agents.3_diagnostician").DiagnosticianAgent
WriterAgent = import_module("pool_assistant.agents.4_writer").WriterAgent
VerifierAgent = import_module("pool_assistant.agents.5_verifier").VerifierAgent

__all__ = ["TriageAgent", "RetrieverAgent", "DiagnosticianAgent", "WriterAgent", "VerifierAgent"]
