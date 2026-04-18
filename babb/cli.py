import typer
from rich.console import Console

from babb import knowledge as k
from babb import responses
from babb.commands import ask

app = typer.Typer(
    name="babb",
    help="Babb — your guide to Babb Works.",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()

app.add_typer(ask.app, name="ask")


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        responses.greeting()


@app.command()
def tools():
    """List all tools Babb Works is building."""
    responses.tools_list(k.load())


@app.command()
def tool(name: str = typer.Argument(..., help="Tool name, e.g. bitpads")):
    """Get the full breakdown of a specific tool."""
    knowledge = k.load()
    t = k.get_tool(knowledge, name)
    if not t:
        console.print(f"[dim]No tool named '{name}' in the index.[/dim]")
        raise typer.Exit(1)
    responses.tool_detail(t)


@app.command()
def now():
    """What Babb Works is working on right now."""
    responses.working_on(k.load())


@app.command()
def version():
    """Show build info."""
    knowledge = k.load()
    built = knowledge.get("built_at", "unknown")
    org = knowledge.get("org", "unknown")
    tool_count = len(knowledge.get("tools", []))
    console.print(f"[cyan]babb[/cyan] 0.1.0  |  org: {org}  |  {tool_count} tool(s) indexed  |  built {built[:10] if built else 'never'}")
