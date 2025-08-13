import json
import time
from http import HTTPStatus

import typer
from munch import DefaultMunch
from rich.console import Console

from app.clients.ecs_service_deployment_client.api.deployment import (
    get_service,
    post_deployment,
)
from app.clients.ecs_service_deployment_client.models import (
    ServiceDeploymentRequest,
    ServiceResponseStatus,
)
from app.config import env

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def deploy(service_name: str = typer.Argument(..., help="Name of the ECS service to deploy")) -> None:
    """Create an ECS service deployment"""
    try:
        response = post_deployment.sync_detailed(
            client=env.api_client, body=ServiceDeploymentRequest(service_name=service_name)
        )
        parsed = DefaultMunch.fromDict(json.loads(response.content))
        if response.status_code == HTTPStatus.CREATED:
            if parsed.status == ServiceResponseStatus.PENDING:
                console.print(
                    f"Deployment successfully started for service [italic]{service_name}[/italic]", style="cyan"
                )
                return status(service_name)
            else:
                console.print(parsed.status, style="yellow")
        else:
            console.print(parsed.errors, style="red")
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
    console.print(f"Checking status for service [italic]{service_name}[/italic]", end="", style="cyan")
    try:
        while True:
            response = get_service.sync_detailed(service=service_name, client=env.api_client)
            if response.status_code == HTTPStatus.OK:
                if response.parsed.status in [ServiceResponseStatus.PENDING, ServiceResponseStatus.IN_PROGRESS]:
                    console.print(".", end="", style="cyan")
                else:
                    console.print(": DONE", style="cyan")
                    console.print(
                        f"Deployment finished with status {response.parsed.status}",
                        style="green" if response.parsed.status == ServiceResponseStatus.SUCCESSFUL else "red",
                    )
                    break
            else:
                raise Exception(f"Status check failed with status {response.status_code}")
            time.sleep(delay)
    except Exception as e:
        console.print(e, overflow="fold", style="red")
        return typer.Abort()
