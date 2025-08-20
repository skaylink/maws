import time
from http import HTTPStatus

import typer
from rich.console import Console

from app.clients.ecs_service_deployment_client.api.deployment import (
    get_service,
    post_deployment,
)
from app.clients.ecs_service_deployment_client.models import ServiceDeploymentRequest
from app.config import env

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def deploy(
    service_name: str = typer.Argument(help="The name of the service to be updated"),
    image: str = typer.Argument(help="The container image to use for the service"),
    force: bool = typer.Option(False, help="Force new deployment, event if images has not changed"),
) -> None:
    """

    ECS Service Deployment Request

    Args:
        service_name (str)
        image (str)
        force (str, Optional):  Defaults to False.

    Raises:
        Exception
    """
    try:
        response = post_deployment.sync_detailed(
            client=env.api_client, body=ServiceDeploymentRequest(service_name=service_name, image=image, force=force)
        )
        if response.status_code == HTTPStatus.CREATED:
            console.print(f"Deployment successfully started for service [italic]{service_name}[/italic]", style="green")
            return status(service_name=service_name, delay=5)
        else:
            console.print(f"[ERROR] {response.parsed.error}", style="red")
            raise Exception(f"Deployment failed with status {response.status_code}")
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()


@app.command()
def status(
    service_name: str = typer.Argument(help="Name of the ECS service to check"),
    delay: int = typer.Option(5, help="The delay to check if the ECS service status"),
) -> None:
    """
    Get the status of an ECS service deployment

    Args:
        service_name (str)
        delay (int, optional):  Defaults to 5.

    Raises:
        Exception
    """
    console.print(f"Checking deployment status for service [italic]{service_name}[/italic]", end="", style="cyan")
    try:
        while True:
            response = get_service.sync_detailed(service=service_name, client=env.api_client)
            match response.status_code:
                case HTTPStatus.ACCEPTED:
                    console.print(".", end="", style="cyan")
                case HTTPStatus.EXPECTATION_FAILED:
                    console.print(f"\nDeployment failed with status {response.status_code}.", style="red")
                    break
                case HTTPStatus.OK:
                    console.print(f"\nDeployment succeeded with status {response.status_code}.", style="green")
                    break
                case _:
                    raise Exception(f"Deployment failed with status {response.status_code}.")
            time.sleep(delay)
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()
