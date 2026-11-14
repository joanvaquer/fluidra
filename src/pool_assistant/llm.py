"""Free local LLMs through Ollama (Qwen, Llama, Gemma, DeepSeek): no API keys, runs on this machine."""

import ollama
from pydantic import BaseModel, ValidationError

from pool_assistant import config


class LLMError(RuntimeError):
    pass


MAX_JSON_TOKENS = 512     # every structured reply is far shorter than this
MAX_TEXT_TOKENS = 1024    # the writer's answer
TIMEOUT_SECONDS = 600     # per call; a 7B model on a laptop CPU can need several minutes

class OllamaLLM:
    def __init__(self, model: str, host: str = config.OLLAMA_HOST):
        self.client = ollama.Client(host=host, timeout=TIMEOUT_SECONDS)
        self.model = model

    def chat(self, system: str, user: str, schema: type[BaseModel] | None = None):
        """Send one prompt and return the reply.

        With `schema`, Ollama constrains the reply to that JSON shape and it is parsed
        into the Pydantic model; otherwise the plain text is returned.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                format=schema.model_json_schema() if schema else None,
                options={
                    "temperature": 0,
                    "num_ctx": 8192,
                    "num_predict": MAX_JSON_TOKENS if schema else MAX_TEXT_TOKENS,  # stop runaway replies
                },
                keep_alive="30m",  # keep the model loaded between questions
            )
        except Exception as e:  # Ollama not running, model missing, timeout...
            raise LLMError(str(e)) from e

        if response.done_reason == "length":
            raise LLMError(f"{self.model} did not finish its reply within the token limit")

        text = response.message.content.strip()
        if schema is None:
            return text
        try:
            return schema.model_validate_json(text)
        except ValidationError as e:
            raise LLMError(f"the model returned invalid JSON: {e}") from e


def installed_models(host: str = config.OLLAMA_HOST) -> list[str]:
    """Tags of the models downloaded in Ollama; raises LLMError if Ollama is not running."""
    try:
        return [m.model for m in ollama.Client(host=host).list().models]
    except Exception as e:
        raise LLMError(f"Ollama is not running at {host}. Start it, or install it from https://ollama.com") from e


def build_llm(name: str) -> OllamaLLM:
    """The model called `name` (a key of config.MODELS).

    Raises LLMError if Ollama is not running or the model is not downloaded.
    """
    if name not in config.MODELS:
        raise ValueError(f"unknown LLM {name!r}; expected one of {', '.join(config.MODELS)}")
    tag = config.MODELS[name]
    if tag not in installed_models():
        raise LLMError(f"model {tag!r} is not downloaded. Download it with: ollama pull {tag}")
    return OllamaLLM(tag)
