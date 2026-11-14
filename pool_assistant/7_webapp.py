"""Web app: a chat with the assistant. Run with: pool-assistant-web
(or: python -m pool_assistant.webapp) and open http://127.0.0.1:8000.

The mode is picked in the sidebar for every question; as in the CLI, there is no default.

A Shiny app has two parts: the UI (app_ui, the page layout) and the server (server(), the
code that reacts to what the user does). Here the server answers each chat message.
"""

import asyncio
import threading
from functools import cache

from shiny import App, run_app, ui

from pool_assistant import config
from pool_assistant.knowledge import KnowledgeBase, load_knowledge_base
from pool_assistant.llm import LLMError
from pool_assistant.orchestrator import Orchestrator, build_orchestrator
from pool_assistant.schemas import AssistantResponse

# The options of the mode drop-down: value -> label shown. The empty value means "not chosen".
MODE_LABELS = {
    "": "Choose a mode…",
    **{name: f"{name} ({tag}): every agent uses the LLM" for name, tag in config.MODELS.items()},
    config.AUTO: f"auto ({config.MODELS[config.AUTO_MODEL]}): LLM for triage and writer only",
    config.OFFLINE: "offline: word matching and rules, no LLM",
}

# --- the page: a sidebar with the settings, and the chat ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("mode", "Mode", MODE_LABELS),                    # read as input.mode()
        ui.input_checkbox("trace", "Show what each agent did"),          # read as input.trace()
        ui.markdown(
            "The LLM modes run on this machine with Ollama and take 1–4 minutes per question "
            "on a CPU. `offline` answers instantly."
        ),
        width=320,
    ),
    ui.chat_ui(
        "chat",
        placeholder="Ask about the ASTRAL Pool pump, e.g. “The pump makes a noise”",
        greeting="Hi! Pick a mode on the left and ask a technical question about the pump.",
    ),
    title="Pool Technician Assistant",
    fillable=True,  # the chat fills the window height
)


# --- answering questions (plain Python, no Shiny: the tests call these directly) ---

@cache  # load the manual once, the first time it's needed, and reuse it
def knowledge_base() -> KnowledgeBase:
    return load_knowledge_base()


assistants: dict[str, Orchestrator] = {}  # one per mode, built the first time it is asked for
assistants_lock = threading.Lock()        # so two users can't build the same mode at once


def ask(mode: str, question: str) -> AssistantResponse:
    """Raises LLMError if the model is not available or a call fails."""
    with assistants_lock:
        if mode not in assistants:
            assistants[mode] = build_orchestrator(mode, knowledge_base())
    return assistants[mode].ask(question)


def format_response(response: AssistantResponse, trace: bool) -> str:
    """The chat message for a response, in Markdown."""
    parts = [response.answer]
    if response.sources:
        parts.append("**Sources:** " + ", ".join(f"p. {p}" for p in sorted({s.page for s in response.sources})))
    if trace:
        # a table with one row per agent step: agent | time | what it did
        # e.g. "20.2 s"; the offline steps take a few milliseconds, shown as "<0.1 s"
        rows = "\n".join(
            f"| {s.agent} | {f'{s.duration_ms / 1000:.1f} s' if s.duration_ms >= 100 else '<0.1 s'} | {s.summary} |"
            for s in response.trace
        )
        model = f" ({response.model})" if response.model else ""
        parts.append(f"*Mode: {response.mode}{model}*\n\n| Agent | Time | What it did |\n|---|---|---|\n{rows}")
    return "\n\n".join(parts)


# --- the server: runs once per browser session ---

def server(input, output, session):
    chat = ui.Chat("chat")  # connects to the ui.chat_ui("chat") on the page

    # called every time the user sends a message
    @chat.on_user_submit
    async def answer(question: str):
        # read the settings now, as they were when the message was sent
        mode, trace = input.mode(), input.trace()
        if not mode:
            await chat.append_message("Choose a mode in the sidebar first.")
            return
        if len(question.strip()) < 3:
            await chat.append_message("Please write a longer question.")
            return
        try:
            # in a thread, so a slow LLM doesn't freeze the app for other users
            response = await asyncio.to_thread(ask, mode, question)
        except LLMError as e:  # Ollama not running, model not downloaded, or a call failed
            await chat.append_message(f"**Error ({mode}):** {e}")
            return
        await chat.append_message(format_response(response, trace))


# the app object that `shiny run` and run_app() serve
app = App(app_ui, server)


def main():
    """Entry point of the `pool-assistant-web` command (see pyproject.toml): start the server
    and open the app in the browser."""
    run_app("pool_assistant.webapp:app", launch_browser=True)


if __name__ == "__main__":
    main()
