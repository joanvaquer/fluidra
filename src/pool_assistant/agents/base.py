"""Common agent shape: an LLM path and a deterministic offline path.

Each agent owns one responsibility and one output schema. `run` uses the LLM when one
is configured and falls back to `run_offline` if there is none or the call fails, so
the pipeline always produces an answer and the failure is visible in the trace.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from pool_assistant.llm import LLMError, StructuredLLM

log = logging.getLogger(__name__)

Out = TypeVar("Out", bound=BaseModel)


class Agent(ABC, Generic[Out]):
    name: str = "agent"

    def __init__(self, llm: StructuredLLM | None) -> None:
        self.llm = llm
        self.last_mode = "offline"  # "llm", "offline" or "fallback"; read by the orchestrator

    def run(self, **inputs) -> Out:
        if self.llm is None:
            self.last_mode = "offline"
            return self.run_offline(**inputs)
        try:
            result = self.run_llm(**inputs)
            self.last_mode = "llm"
            return result
        except LLMError as e:
            log.warning("%s: LLM call failed (%s); using offline fallback", self.name, e)
            self.last_mode = "fallback"
            return self.run_offline(**inputs)

    @abstractmethod
    def run_llm(self, **inputs) -> Out: ...

    @abstractmethod
    def run_offline(self, **inputs) -> Out: ...
