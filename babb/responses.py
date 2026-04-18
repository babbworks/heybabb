import re

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

console = Console()

BRAND = "[bold cyan]Babb[/bold cyan]"


def _slot(tool: dict, key: str) -> str:
    return tool.get("knowledge", {}).get(key, "").strip()


def _signals_line(tool: dict) -> str:
    s = tool.get("signals", {})
    parts = []
    if s.get("last_commit"):
        parts.append(f"last commit {s['last_commit']}")
    if s.get("commits_7d") is not None:
        parts.append(f"{s['commits_7d']} commits this week")
    if s.get("open_prs"):
        parts.append(f"{s['open_prs']} open PR{'s' if s['open_prs'] != 1 else ''}")
    if s.get("recent_releases"):
        parts.append(f"latest release {s['recent_releases'][0]}")
    return "  ".join(parts)


def greeting():
    console.print(
        Panel(
            "[bold]Hey. I'm Babb.[/bold]\n\n"
            "I know what Babb Works is building, why, and where it's headed.\n"
            "Ask me anything — or try [cyan]heybabb tools[/cyan] to start.",
            title="[bold cyan]Babb[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def tools_list(knowledge: dict):
    tools = knowledge.get("tools", [])
    if not tools:
        console.print("[dim]No tools indexed yet. Run [cyan]babb sync[/cyan].[/dim]")
        return

    console.print(f"\n[bold]Tools — {knowledge.get('org', 'Babb Works')}[/bold]\n")
    for tool in tools:
        summary = _slot(tool, "summary")
        first_sentence = re.split(r"(?<=[.!?])\s", summary)[0] if summary else "[dim]no summary[/dim]"
        status = _slot(tool, "status")
        status_short = re.split(r"[.\n]", status)[0] if status else ""
        console.print(f"  [cyan bold]{tool['id']}[/cyan bold]")
        console.print(f"  {first_sentence}")
        if status_short:
            console.print(f"  [dim]{status_short}[/dim]")
        console.print()


def tool_detail(tool: dict):
    name = tool["id"]
    summary = _slot(tool, "summary")
    problem = _slot(tool, "problem")
    how = _slot(tool, "how")
    status = _slot(tool, "status")
    vision = _slot(tool, "vision")
    context = _slot(tool, "context")
    signals = _signals_line(tool)

    body = ""
    if summary:
        body += f"{summary}\n\n"
    if problem:
        body += f"[bold]The Problem[/bold]\n{problem}\n\n"
    if how:
        body += f"[bold]How it Works[/bold]\n{how}\n\n"
    if status:
        body += f"[bold]Status[/bold]\n{status}\n\n"
    if vision:
        body += f"[bold]Vision[/bold]\n{vision}\n\n"
    if context:
        body += f"[bold]Industry Context[/bold]\n{context}\n\n"
    if signals:
        body += f"[dim]{signals}[/dim]"

    console.print(
        Panel(
            body.strip(),
            title=f"[bold cyan]{name}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def working_on(knowledge: dict):
    from babb import knowledge as k

    now = knowledge.get("now", "").replace("# Now\n", "").strip()
    top = k.active_tools(knowledge)
    releases = k.recent_releases(knowledge)

    body = ""
    if now:
        body += f"{now}\n\n"

    if top:
        active = [t for t in top if t.get("signals", {}).get("commits_7d", 0) > 0]
        if active:
            body += "[bold]Most active this week[/bold]\n"
            for tool in active[:3]:
                c = tool["signals"]["commits_7d"]
                prs = tool["signals"].get("open_prs", 0)
                pr_str = f", {prs} open PR{'s' if prs != 1 else ''}" if prs else ""
                body += f"  [cyan]{tool['id']}[/cyan] — {c} commit{'s' if c != 1 else ''}{pr_str}\n"
            body += "\n"

    if releases:
        body += "[bold]Recent releases[/bold]\n"
        for tool_id, tag in releases[:4]:
            body += f"  [cyan]{tool_id}[/cyan] {tag}\n"

    if not body.strip():
        body = "Nothing indexed yet. Run [cyan]babb sync[/cyan] to pull the latest."

    console.print(
        Panel(
            body.strip(),
            title=f"{BRAND} — now",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def not_found(query: str = ""):
    console.print("[dim]I don't have that indexed yet.[/dim]")


def no_knowledge():
    console.print(
        "[yellow]No knowledge base found.[/yellow] "
        "Ask a Babb Works admin to run [cyan]babb-admin publish[/cyan] to update the knowledge base."
    )
