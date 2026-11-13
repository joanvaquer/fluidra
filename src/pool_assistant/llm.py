"""LLM access behind one narrow interface: `structured(system, user, schema, effort)`.

Agents only ever ask for a validated Pydantic object, which keeps them provider-
agnostic and lets tests inject a fake. `build_llm` returns None in offline mode;
agents then use their deterministic fallback logic (the brief allows mocking).
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, TypeVar

from pydantic import BaseModel

from pool_assistant import config

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """The model call failed or returned something unusable; callers fall back."""


class StructuredLLM(Protocol):
    name: str

    def structured(self, *, system: str, user: str, schema: type[T], effort: str = "medium") -> T: ...


class ClaudeLLM:
    """Claude via the Anthropic SDK, using structured outputs for every agent call."""

    def __init__(self, model: str = config.MODEL, client=None) -> None:
        import anthropic

        self._anthropic = anthropic
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.name = f"claude:{model}"

    def structured(self, *, system: str, user: str, schema: type[T], effort: str = "medium") -> T:
        anthropic = self._anthropic
        try:
            response = self.client.beta.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
                output_config={"effort": effort},
                # If a safety classifier declines, retry server-side on Anthropic's
                # recommended fallback model instead of failing the request.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as e:
            raise LLMError(f"rate limited: {e.message}") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"connection error: {e}") from e

        if response.stop_reason == "refusal":
            raise LLMError("model declined the request")
        if response.stop_reason == "max_tokens":
            raise LLMError("response truncated at max_tokens")
        if response.parsed_output is None:
            raise LLMError("no structured output returned")
        return response.parsed_output


def _has_anthropic_credentials() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def build_llm(mode: str = config.LLM_MODE) -> StructuredLLM | None:
    mode = mode.lower()
    if mode == "offline":
        return None
    if mode == "claude":
        return ClaudeLLM()
    if mode == "auto":
        if _has_anthropic_credentials():
            return ClaudeLLM()
        log.info("No Anthropic credentials found; running in offline mode.")
        return None
    raise ValueError(f"Unknown LLM mode {mode!r}; expected auto, claude or offline")
