import typer
from pydantic import BaseModel, HttpUrl
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


class schema(BaseModel):
    foo: HttpUrl


@app.command()
def deploy() -> None:

    console.print("Deployment started", overflow="fold", style="bold green")
