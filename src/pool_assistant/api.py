"""REST API. Run with: uvicorn pool_assistant.api:app --reload

Each request names its mode: {"question": "...", "mode": "llama"}
(qwen, llama, gemma, deepseek; auto for LLM triage and writer with rule-based other agents;
or offline for word matching with no LLM)."""

from functools import cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from pool_assistant.knowledge import KnowledgeBase, load_knowledge_base
from pool_assistant.llm import LLMError
from pool_assistant.orchestrator import Orchestrator, build_orchestrator
from pool_assistant.schemas import AskRequest, AssistantResponse

app = FastAPI(title="Pool Technician Assistant")
assistants: dict[str, Orchestrator] = {}  # one per mode, built the first time it is asked for


@cache
def knowledge_base() -> KnowledgeBase:
    return load_knowledge_base()


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.post("/ask", response_model=AssistantResponse)
def ask(request: AskRequest):
    try:
        if request.mode not in assistants:
            assistants[request.mode] = build_orchestrator(request.mode, knowledge_base())
        return assistants[request.mode].ask(request.question)
    except LLMError as e:  # Ollama not running, model not downloaded, or a call failed
        raise HTTPException(status_code=503, detail=str(e)) from e
