import json
import time
from collections.abc import Callable
from http import HTTPStatus
from typing import Any

import typer
from rich.console import Console

from maws.clients.ecs_service_deployment_client.api.services import (
    get_service,
    get_services,
    patch_service,
)
from maws.clients.ecs_service_deployment_client.api.tasks import (
    get_task,
    get_tasks,
    patch_task,
)
from maws.clients.ecs_service_deployment_client.models import (
    ServiceDeploymentRequest,
    TaskDeploymentRequest,
)
from maws.clients.ecs_service_deployment_client.types import UNSET
from maws.config import CONFIG_FILE_PATH, get_settings

app = typer.Typer(no_args_is_help=True)
services_app = typer.Typer(no_args_is_help=True)
tasks_app = typer.Typer(no_args_is_help=True)
app.add_typer(services_app, name="services", help="ECS service commands")
app.add_typer(tasks_app, name="tasks", help="ECS task commands")
console = Console()

err_console = Console(stderr=True)

PROFILE_HELP = f"Profile name from {str(CONFIG_FILE_PATH)}"

# EX_CONFIG from sysexits.h: the invocation is no longer valid
DEPRECATED_EXIT_CODE = 78


_DEPRECATED_COMMAND_SETTINGS: dict[str, Any] = {
    "hidden": True,
    "context_settings": {"allow_extra_args": True, "ignore_unknown_options": True},
    "add_help_option": False,
}


def _removed_command_hint(command: str, usage: str) -> None:
    """Print a migration hint for a removed top-level command and exit with EX_CONFIG."""
    err_console.print(
        f"'maws ecs {command}' has been removed. Use one of:\n"
        f"  maws ecs services {command} <service-name> {usage}\n"
        f"  maws ecs tasks {command} <task-name> {usage}",
        style="yellow",
    )
    raise typer.Exit(code=DEPRECATED_EXIT_CODE)


@app.command("deploy", **_DEPRECATED_COMMAND_SETTINGS)
def deprecated_deploy(ctx: typer.Context) -> None:
    """
    Removed: use 'ecs services deploy' or 'ecs tasks deploy'
    """
    _removed_command_hint("deploy", "<image> [OPTIONS]")


@app.command("status", **_DEPRECATED_COMMAND_SETTINGS)
def deprecated_status(ctx: typer.Context) -> None:
    """
    Removed: use 'ecs services status' or 'ecs tasks status'
    """
    _removed_command_hint("status", "[OPTIONS]")


# --- shared helpers ---------------------------------------------------------


def _start_deployment(kind: str, name: str, send: Callable[[], Any]) -> None:
    """Send a deployment request and abort on anything but 201 Created."""
    response = send()
    if response.status_code == HTTPStatus.CREATED:
        console.print(
            f"Deployment successfully started for {kind} [italic]{name}[/italic]",
            style="green",
        )
        return
    content = json.loads(response.content)
    console.print(f"[ERROR] {content.get("message")}", style="red", new_line_start=True)
    raise Exception(f"Deployment failed with status {response.status_code}")


def _wait_for_deployment(kind: str, name: str, delay: int, fetch: Callable[[], Any]) -> None:
    """Poll the deployment status until it succeeds (200) or fails."""
    console.print(
        f"Checking deployment status for {kind} [italic]{name}[/italic]",
        end="",
        style="cyan",
    )
    try:
        while True:
            response = fetch()
            match response.status_code:
                case HTTPStatus.ACCEPTED:
                    console.print(".", end="", style="cyan")
                case HTTPStatus.EXPECTATION_FAILED:
                    console.print(
                        f"\nDeployment failed with status {response.status_code}.",
                        style="red",
                    )
                    raise typer.Exit(code=1)
                case HTTPStatus.OK:
                    console.print(
                        f"\nDeployment succeeded with status {response.status_code}.",
                        style="green",
                    )
                    break
                case _:
                    raise Exception(f"\nDeployment failed with status {response.status_code}.")
            time.sleep(delay)
    except (typer.Exit, typer.Abort):
        raise
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        raise typer.Abort() from e


def _list(kind: str, fetch: Callable[[], Any]) -> typer.Abort | None:
    """Print the names returned by a list endpoint."""
    try:
        response = fetch()
        if response.status_code == HTTPStatus.OK:
            names = json.loads(response.content)
            if not names:
                console.print(f"No ECS {kind} available.", style="yellow")
                return None
            for name in names:
                console.print(name)
            return None
        content = json.loads(response.content)
        console.print(f"[ERROR] {content.get("error")}", style="red", new_line_start=True)
        raise Exception(f"Listing {kind} failed with status {response.status_code}")
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()


# --- services ---------------------------------------------------------------


@services_app.command("deploy")
def deploy_service(
    service_name: str = typer.Argument(help="The name of the service to be updated"),
    image: str = typer.Argument(help="The container image to use for the service"),
    force: bool = typer.Option(
        False,
        help="Force new deployment, event if images has not changed",
    ),
    secret_arns: list[str] = typer.Option(
        [],
        help="List of secret ARNs to attach to the service",
    ),
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> None:
    """
    Deploy a new image to an ECS service
    """
    env = get_settings(profile)
    try:
        _start_deployment(
            "service",
            service_name,
            lambda: patch_service.sync_detailed(
                service=service_name,
                client=env.api_client,
                body=ServiceDeploymentRequest(image=image, force=force, secret_arns=secret_arns),
            ),
        )
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        raise typer.Abort() from e
    service_status(service_name=service_name, delay=5, profile=profile)


@services_app.command("status")
def service_status(
    service_name: str = typer.Argument(help="Name of the ECS service to check"),
    delay: int = typer.Option(5, help="The delay to check if the ECS service status"),
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> None:
    """
    Get the status of an ECS service deployment
    """
    env = get_settings(profile)
    _wait_for_deployment(
        "service",
        service_name,
        delay,
        lambda: get_service.sync_detailed(service=service_name, client=env.api_client),
    )


@services_app.command("list")
def list_services(
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> typer.Abort | None:
    """
    List the available ECS services
    """
    env = get_settings(profile)
    return _list("services", lambda: get_services.sync_detailed(client=env.api_client))


# --- tasks ------------------------------------------------------------------


@tasks_app.command("deploy")
def deploy_task(
    task_name: str = typer.Argument(help="The name of the scheduled task to be updated"),
    image: str = typer.Argument(help="The container image to use for the task"),
    schedule_expression: str | None = typer.Option(
        None,
        help="The schedule expression for the task, e.g. 'cron(0 3 * * ? *)' or 'rate(1 hour)'",
    ),
    force: bool = typer.Option(
        False,
        help="Force new deployment, even if the image has not changed",
    ),
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> None:
    """
    Deploy a new image to an ECS scheduled task
    """
    env = get_settings(profile)
    try:
        _start_deployment(
            "task",
            task_name,
            lambda: patch_task.sync_detailed(
                task=task_name,
                client=env.api_client,
                body=TaskDeploymentRequest(
                    image=image,
                    force=force,
                    # omit the field entirely when not given; the API falls back to None
                    schedule_expression=schedule_expression if schedule_expression is not None else UNSET,
                ),
            ),
        )
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        raise typer.Abort() from e
    task_status(task_name=task_name, delay=5, profile=profile)


@tasks_app.command("status")
def task_status(
    task_name: str = typer.Argument(help="Name of the ECS scheduled task to check"),
    delay: int = typer.Option(5, help="The delay to check if the ECS task status"),
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> None:
    """
    Get the status of an ECS scheduled task deployment
    """
    env = get_settings(profile)
    _wait_for_deployment(
        "task",
        task_name,
        delay,
        lambda: get_task.sync_detailed(task=task_name, client=env.api_client),
    )


@tasks_app.command("list")
def list_tasks(
    profile: str = typer.Option(None, help=PROFILE_HELP),
) -> typer.Abort | None:
    """
    List the available ECS tasks
    """
    env = get_settings(profile)
    return _list("tasks", lambda: get_tasks.sync_detailed(client=env.api_client))
