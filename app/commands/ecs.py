import time
from http import HTTPStatus

import typer
from rich.console import Console
from rich.prompt import Confirm

from app.clients.ecs_service_deployment_client.api.deployment_v1 import (
    get_service,
    post_deployment,
)
from app.clients.ecs_service_deployment_client.models import (
    V1ECSServiceDeploymentRequest,
    V1ServiceResonseStatus,
)
from app.clients.ecs_service_deployment_client.types import Response
from app.config import env

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def deploy(service_name: str = typer.Argument(..., help="Name of the ECS service to deploy")) -> None:
    """Create an ECS service deployment"""
    if Confirm.ask(f"[bold yellow]Deploy service [italic]{service_name}[/italic]?[/]", default=False) is False:
        console.print("Deployment cancelled", style="yellow")
        return

    try:
        response: Response[None] = post_deployment.sync_detailed(
            client=env.api_client, body=V1ECSServiceDeploymentRequest(service=service_name)
        )
        if response.status_code == HTTPStatus.CREATED:
            console.print(f"Deployment successfully started for service [italic]{service_name}[/italic]", style="cyan")
            status(service_name)
        else:
            raise Exception(f"Deployment failed with status {response.status_code}")

    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()


@app.command()
def status(
    service_name: str = typer.Argument(..., help="Name of the ECS service to check"),
    delay: int = typer.Option(5, help="The delay to check if the ECS service status"),
) -> None:
    """Get the status of an ECS service deployment"""
    console.print(f"Checking status for service {service_name}", end="", style="cyan")
    try:
        while True:
            response = get_service.sync_detailed(service=service_name, client=env.api_client)
            if response.status_code == HTTPStatus.OK:
                if response.parsed.status in [V1ServiceResonseStatus.PENDING, V1ServiceResonseStatus.IN_PROGRESS]:
                    console.print(".", end="", style="cyan")
                else:
                    console.print(": DONE", style="cyan")
                    console.print(
                        f"Deployment finished with status {response.parsed.status}",
                        style="green" if response.parsed.status == V1ServiceResonseStatus.SUCCESSFUL else "red",
                    )
                    break
            else:
                raise Exception(f"Status check failed with status {response.status_code}")
            time.sleep(delay)
    except Exception as e:
        console.print("API Error", style="bold red")
        console.print(e, overflow="fold")
        return typer.Abort()
