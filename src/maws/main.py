import typer

from maws.commands import ecs

# commands
ecs_commands = typer.Typer(no_args_is_help=True)
ecs_commands.add_typer(ecs.app)

app = typer.Typer(help="Welcome to Skaylink client.", no_args_is_help=True)
app.add_typer(ecs_commands, name="ecs", help="ECS management commands")


def main():
    app()  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
