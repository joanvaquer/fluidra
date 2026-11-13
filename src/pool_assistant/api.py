"""REST API. Run with: uvicorn pool_assistant.api:app --reload"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse

from pool_assistant.orchestrator import Orchestrator, build_orchestrator
from pool_assistant.schemas import AskRequest, AssistantResponse

_state: dict[str, Orchestrator] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state.setdefault("orchestrator", build_orchestrator())
    yield


app = FastAPI(
    title="Pool Technician Assistant",
    description="Multi-agent assistant that answers technical questions from product manuals.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    orch = _state["orchestrator"]
    return {"status": "ok", "llm_mode": orch.mode, "chunks": len(orch.kb.chunks), "products": orch.kb.products}


@app.post("/ask", response_model=AssistantResponse)
async def ask(request: AskRequest) -> AssistantResponse:
    # The agent pipeline is synchronous (blocking SDK calls); keep the event loop free.
    return await run_in_threadpool(_state["orchestrator"].ask, request.question)
