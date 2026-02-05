from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def hello(name: Annotated[str, typer.Argument(help="The person to greet")] = "World"):
    """
    A simple command to verify the CLI is working.
    """
    typer.echo(f"Success! Hello {name}. The CLI is connected.")


if __name__ == "__main__":
    app()
