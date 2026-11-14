"""Free local LLMs through Ollama (Qwen, Llama, Gemma, DeepSeek): no API keys, runs on this machine.

The agents never talk to Ollama directly: they call OllamaLLM.chat(), which sends one prompt,
waits for the reply and, when a schema is given, checks it is valid JSON of that shape.
"""

import ollama
from pydantic import BaseModel, ValidationError

from pool_assistant import config


class LLMError(RuntimeError):
    """Any LLM failure: Ollama not running, model not downloaded, timeout, bad reply.
    The CLI and the web app catch it and show the message instead of crashing."""
    pass


# Limits for one reply. They stop a small model that starts repeating itself from running
# for many minutes on a CPU.
MAX_JSON_TOKENS = 512     # every structured reply is far shorter than this
MAX_TEXT_TOKENS = 1024    # the writer's answer
TIMEOUT_SECONDS = 600     # per call; a 7B model on a laptop CPU can need several minutes

class OllamaLLM:
    """One Ollama model, e.g. OllamaLLM("qwen2.5:3b"). The same object is shared by all agents."""

    def __init__(self, model: str, host: str = config.OLLAMA_HOST):
        self.client = ollama.Client(host=host, timeout=TIMEOUT_SECONDS)
        self.model = model  # the Ollama tag, also reported in the response as `model`

    def chat(self, system: str, user: str, schema: type[BaseModel] | None = None):
        """Send one prompt and return the reply.

        With `schema`, Ollama constrains the reply to that JSON shape and it is parsed
        into the Pydantic model; otherwise the plain text is returned.
        """
        # 1. Send the prompt: the system message holds the agent's instructions, the user
        #    message holds the question and the data for this call.
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                # with a schema, Ollama only lets the model write JSON that matches it
                format=schema.model_json_schema() if schema else None,
                options={
                    "temperature": 0,  # always the most likely reply, so runs are repeatable
                    "num_ctx": 8192,   # context window: enough for the prompt plus all passages
                    "num_predict": MAX_JSON_TOKENS if schema else MAX_TEXT_TOKENS,  # stop runaway replies
                },
                keep_alive="30m",  # keep the model loaded between questions
            )
        except Exception as e:  # Ollama not running, model missing, timeout...
            raise LLMError(str(e)) from e

        # 2. A reply cut off at the token limit is incomplete (and its JSON broken): fail clearly.
        if response.done_reason == "length":
            raise LLMError(f"{self.model} did not finish its reply within the token limit")

        # 3. Return plain text, or the JSON parsed into the Pydantic model.
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
    # a name that isn't in config.MODELS is a programming error, not an Ollama problem
    if name not in config.MODELS:
        raise ValueError(f"unknown LLM {name!r}; expected one of {', '.join(config.MODELS)}")
    # check the model is downloaded now, so the user gets the `ollama pull` command up front
    # instead of an obscure error in the middle of the first question
    tag = config.MODELS[name]
    if tag not in installed_models():
        raise LLMError(f"model {tag!r} is not downloaded. Download it with: ollama pull {tag}")
    return OllamaLLM(tag)
