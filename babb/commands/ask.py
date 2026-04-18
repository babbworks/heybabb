import os

import typer
from rich.console import Console

from babb import knowledge as k
from babb import responses

app = typer.Typer(help="Ask Babb anything in natural language")
console = Console()

_WORKING_ON = {"working on", "now", "current", "doing", "what's happening", "latest"}
_TOOLS_KW = {"tools", "products", "built", "made", "projects", "building"}
_VISION_KW = {"vision", "future", "where headed", "direction", "goal"}
_STATUS_KW = {"status", "health", "shipped", "released", "releases"}


@app.callback(invoke_without_command=True)
def ask(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Your question"),
    ai: bool = typer.Option(False, "--ai", help="Use Claude for a richer response"),
):
    if ctx.invoked_subcommand:
        return

    knowledge = k.load()
    if not knowledge["tools"] and not knowledge.get("now"):
        responses.no_knowledge()
        return

    if ai:
        _ask_ai(query, knowledge)
        return

    _route(query, knowledge)


def _match_qa(query: str, pairs: list[dict]) -> dict | None:
    import re

    def normalize(text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower())

    q_words = set(normalize(query).split())
    best, best_score = None, 0.0
    for pair in pairs:
        candidates = [pair["question"]] + pair.get("variants", [])
        for candidate in candidates:
            c_words = set(normalize(candidate).split())
            if not c_words:
                continue
            overlap = len(q_words & c_words) / len(c_words)
            if overlap > best_score:
                best_score = overlap
                best = pair
    return best if best_score >= 0.5 else None


def _route(query: str, knowledge: dict):
    qa_pairs = knowledge.get("qa", [])
    if qa_pairs:
        match = _match_qa(query, qa_pairs)
        if match:
            console.print(match["answer"])
            return

    q = query.lower()

    for tool in knowledge["tools"]:
        if tool["id"].lower() in q:
            responses.tool_detail(tool)
            return
        for alias in tool.get("aliases", []):
            if alias.lower() in q:
                responses.tool_detail(tool)
                return

    if any(kw in q for kw in _WORKING_ON):
        responses.working_on(knowledge)
        return

    if any(kw in q for kw in _TOOLS_KW):
        responses.tools_list(knowledge)
        return

    if any(kw in q for kw in _STATUS_KW):
        responses.working_on(knowledge)
        return

    responses.not_found(query)


def _ask_ai(query: str, knowledge: dict):
    try:
        import anthropic
    except ImportError:
        console.print("[red]anthropic package not installed.[/red]")
        raise typer.Exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY not set.[/red]")
        raise typer.Exit(1)

    import json

    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "You are Babb, the voice of Babb Works in the terminal. "
        "You are sharp, direct, and genuinely interested in business and the tools that make it work better. "
        "You don't oversell. Short sentences. No filler. No marketing language. "
        "You only speak from the knowledge base provided — if something isn't in it, say so plainly. "
        "Respond in plain text suitable for a terminal — no markdown headers, no bullet symbols unless natural.\n\n"
        f"Knowledge base:\n{json.dumps(knowledge, indent=2)}"
    )

    with console.status("thinking..."):
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": query}],
        )

    console.print(message.content[0].text)
