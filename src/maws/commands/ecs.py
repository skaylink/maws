import json
import time
from http import HTTPStatus

import typer
from rich.console import Console

from maws.clients.ecs_service_deployment_client.api.services import (
    get_service,
    patch_service,
)
from maws.clients.ecs_service_deployment_client.models import (
    ServiceDeploymentRequest,
)
from maws.config import CONFIG_FILE_PATH, get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def deploy(
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
    profile: str = typer.Option(None, help=f"Profile name from {str(CONFIG_FILE_PATH)}"),
) -> None:
    """
    ECS Service Deployment Request

    Args:
        service_name (str)
        image (str)
        force (str, Optional):  Defaults to False.
        secret_arns (list[str], Optional)
        profile (str, Optional): Profile name

    Raises:
        Exception
    """
    env = get_settings(profile)
    try:
        response = patch_service.sync_detailed(
            service=service_name,
            client=env.api_client,
            body=ServiceDeploymentRequest(image=image, force=force, secret_arns=secret_arns),
        )
        if response.status_code == HTTPStatus.CREATED:
            console.print(
                f"Deployment successfully started for service [italic]{service_name}[/italic]",
                style="green",
            )
            return status(service_name=service_name, delay=5, profile=profile)
        else:
            content = json.loads(response.content)
            console.print(f"[ERROR] {content.get("error")}", style="red", new_line_start=True)
            raise Exception(f"Deployment failed with status {response.status_code}")
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()


@app.command()
def status(
    service_name: str = typer.Argument(help="Name of the ECS service to check"),
    delay: int = typer.Option(5, help="The delay to check if the ECS service status"),
    profile: str = typer.Option(help=f"Profile name from {str(CONFIG_FILE_PATH)}"),
) -> None:
    """
    Get the status of an ECS service deployment

    Args:
        service_name (str)
        delay (int, optional):  Defaults to 5.
        profile (str, Optional): Profile name

    Raises:
        Exception
    """
    env = get_settings(profile)
    console.print(
        f"Checking deployment status for service [italic]{service_name}[/italic]",
        end="",
        style="cyan",
    )
    try:
        while True:
            response = get_service.sync_detailed(service=service_name, client=env.api_client)
            match response.status_code:
                case HTTPStatus.ACCEPTED:
                    console.print(".", end="", style="cyan")
                case HTTPStatus.EXPECTATION_FAILED:
                    console.print(
                        f"\nDeployment failed with status {response.status_code}.",
                        style="red",
                    )
                    break
                case HTTPStatus.OK:
                    console.print(
                        f"\nDeployment succeeded with status {response.status_code}.",
                        style="green",
                    )
                    break
                case _:
                    raise Exception(f"\nDeployment failed with status {response.status_code}.")
            time.sleep(delay)
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()
