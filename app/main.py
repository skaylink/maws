import typer

from app.commands import ecs

# commands
ecs_commands = typer.Typer(no_args_is_help=True)
ecs_commands.add_typer(ecs.app)

app = typer.Typer(help="Welcome to skaylink deployment client.", no_args_is_help=True)
app.add_typer(ecs_commands, name="ecs")

if __name__ == "__main__":
    app()
