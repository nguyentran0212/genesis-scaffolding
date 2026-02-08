import asyncio
from typing import Annotated, Any

import typer
from myproject_core.utils import streamcallback_simple_print
from rich import box, print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils import RichWorkflowRenderer


class GenesisCLI:
    def __init__(self, settings, wm, registry, engine):
        self._console = Console()
        self.settings = settings
        self.wm = wm
        self.registry = registry
        self.engine = engine
        self.app = typer.Typer(help="Genesis CLI")

        # Register the dispatch command
        self._register_commands()

    def _register_commands(self):
        @self.app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
        def run(
            ctx: typer.Context,
            list_workflows: Annotated[
                bool, typer.Option("--list", help="List all available workflows", is_eager=True)
            ] = False,
            workflow_id: Annotated[
                str | None, typer.Argument(help="The ID of the workflow to execute")
            ] = None,
            help: Annotated[
                bool, typer.Option("--help", help="Show help for the command or a specific workflow")
            ] = False,
        ):
            # Handle Global Help (no workflow_id provided)
            if help and not workflow_id:
                print(ctx.get_help())
                raise typer.Exit()

            # Handle listing workflows
            if list_workflows:
                self._print_workflow_list()
                raise typer.Exit()

            # Fetch manifest to ensure it exists and to provide help context
            manifest = self.registry.get_workflow(workflow_id)
            if not manifest:
                print(f"Error: Workflow '{workflow_id}' not found.")
                raise typer.Exit(1)

            # Handle specific workflow help
            if help:
                self._print_workflow_help(manifest)
                raise typer.Exit()

            # Greedy Argument Parsing
            # Collects everything following a --flag into a list
            raw_data: dict[str, Any] = {}
            current_key = None

            for item in ctx.args:
                if item.startswith("--"):
                    current_key = item.lstrip("-").replace("-", "_")
                    raw_data[current_key] = []
                elif current_key:
                    raw_data[current_key].append(item)

            # Data Normalization
            # - No values: treat as boolean True
            # - One value: treat as scalar
            # - Multiple values: keep as list
            final_inputs = {}
            for k, v in raw_data.items():
                if not v:
                    final_inputs[k] = True
                elif len(v) == 1:
                    final_inputs[k] = v[0]
                else:
                    final_inputs[k] = v

            renderer = RichWorkflowRenderer(self._console)
            # Dispatch to Engine
            # Validation and TypeAdapter conversion happen inside engine.run()
            print(f"Starting workflow: {manifest.name}")
            try:
                asyncio.run(self.engine.run(manifest, final_inputs, [renderer]))
            except Exception as e:
                print(f"Execution failed: {e}")
                raise typer.Exit(1)
            finally:
                if renderer.status:
                    renderer.status.stop()

        @self.app.callback(invoke_without_command=True)
        def main_callback(ctx: typer.Context):
            if ctx.invoked_subcommand is None:
                typer.echo("Launching TUI...")
                # self.launch_tui()
                #

        @self.app.command()
        def serve():
            typer.echo("API Server is WIP...")

    def _print_workflow_help(self, manifest):
        """Standard output for workflow-specific options."""
        # Use a Panel for the title and description
        self._console.print(
            Panel(
                f"[white]{manifest.description}[/white]",
                title=f"[bold cyan]Workflow: {manifest.name}[/bold cyan]",
                title_align="left",
                border_style="cyan",
            )
        )

        table = Table(show_header=True, header_style="bold green", box=None)
        table.add_column("Option")
        table.add_column("Type", style="magenta")
        table.add_column("Requirement")
        table.add_column("Description", style="dim")

        for name, defn in manifest.inputs.items():
            flag = f"--{name.replace('_', '-')}"

            # Use red for required, dim for optional
            req = (
                "[bold red]Required[/bold red]" if defn.required else f"[dim]Default: {defn.default}[/dim]"
            )

            # Clean up the Enum display
            type_name = str(defn.type).split(".")[-1]

            table.add_row(flag, type_name, req, defn.description or "")

        self._console.print(table)
        self._console.print(
            "\n[blue]Tips:[/blue] [dim]If you need to input list item for an input, just write --input-name item1 item2 item3[/dim]\n",
            '\n[blue]Tips:[/blue] [dim]Put your string input in quote "my string input"[/dim]\n',
        )

    def _print_workflow_list(self):
        """Displays a clean table of all registered workflows."""
        workflows = self.registry.get_all_workflows()

        table = Table(
            title="Available Workflows",
            title_style="bold magenta",
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE,  # Minimalist, clean look
        )
        table.add_column("ID", style="bright_blue", no_wrap=True)
        table.add_column("Description")
        table.add_column("Version", justify="right", style="dim")

        if not workflows:
            self._console.print("[yellow]No workflows found in the registry.[/yellow]")
            return

        for workflow_id, manifest in workflows.items():
            table.add_row(workflow_id, manifest.description, manifest.version)

        self._console.print(table)
        self._console.print("\n[dim]Usage: myproject run <ID> [OPTIONS][/dim]")

    def __call__(self):
        self.app()
