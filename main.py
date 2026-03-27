"""
Multi-Agent System — Main Entry Point
Run: python main.py
"""

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

console = Console()


def check_env():
    """Check that the claude CLI is available."""
    import shutil
    if not shutil.which("claude"):
        console.print("[bold red]⚠️  'claude' CLI not found. Install Claude Code first.[/bold red]")
        return False
    return True


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]🤖 Multi-Agent AI System[/bold cyan]\n"
        "[dim]Supervisor · Intelligence · Todo · Research[/dim]\n\n"
        "[yellow]Commands:[/yellow]\n"
        "  [green]news[/green]        → get latest AI news\n"
        "  [green]todo[/green]        → manage your tasks\n"
        "  [green]research[/green]    → market research on ideas\n"
        "  [green]anything[/green]    → supervisor auto-routes\n"
        "  [green]quit / exit[/green] → goodbye",
        border_style="cyan"
    ))


def main():
    print_banner()

    if not check_env():
        return

    from agents.supervisor import SupervisorAgent
    supervisor = SupervisorAgent()

    console.print("\n[bold green]✅ All agents loaded. Ready![/bold green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold blue]You[/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            console.print("[dim]Goodbye! 👋[/dim]")
            break

        console.print("\n[dim]Thinking...[/dim]")
        try:
            response = supervisor.run(user_input)
            console.print(Panel(Markdown(response), title="[bold cyan]Assistant[/bold cyan]", border_style="cyan"))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print()


if __name__ == "__main__":
    main()
