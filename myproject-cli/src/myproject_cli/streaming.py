import sys

from rich.console import Console


class CLIStreamHandler:
    def __init__(self, console: Console):
        self.console = console
        self.is_thinking = False
        self.has_started_content = False

    async def handle_reasoning(self, chunk: str):
        if not self.is_thinking:
            # Using 'dim' is the most compatible way to get a "grey" look
            self.console.print("\n[italic dim]🔍 Thinking...[/italic dim]")
            self.is_thinking = True

        # We use the 'style' parameter instead of markup tags
        # to ensure partial chunks don't break the parser.
        self.console.print(chunk, style="italic grey50", end="")
        sys.stdout.flush()

    async def handle_content(self, chunk: str):
        if self.is_thinking:
            self.console.print("\n")
            self.is_thinking = False

        if not self.has_started_content:
            self.console.print("[bold cyan]Assistant:[/bold cyan] ", end="")
            self.has_started_content = True

        self.console.print(chunk, end="")
        sys.stdout.flush()

    async def handle_tool_start(self, name: str, args: dict):
        self.console.print(f"\n[bold green]🛠️  Executing {name}...[/bold green] [dim]({args})[/dim]")

    def reset(self):
        self.is_thinking = False
        self.has_started_content = False
