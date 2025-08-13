from http import HTTPStatus
from typing import Callable

import typer
from rich.console import Console

from app.clients.api import HTTPException
from app.clients.api.models import ECSServiceDeploymentRequest
from app.clients.api.models.V1ServiceResonseStatus import V1ServiceResonseStatus
from app.clients.api.services.DeploymentV1_service import get_service, post_deployment
from app.config import env

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def deploy(
    service_name: str = typer.Argument(..., help="Name of the ECS service to deploy"),
) -> None:
    """Create an ECS service deployment"""

    def start() -> None:
        post_deployment(data=ECSServiceDeploymentRequest(service=service_name), api_config_override=env.api_config)
        console.print(f"Deployment successfully started for service [italic]{service_name}[/italic]", style="cyan")
        status(service_name)

    if not typer.confirm(f"Deploy service '{service_name}'?"):
        console.print("Deployment cancelled", style="yellow")
        return

    return _withExceptionHandler(fn=start)


@app.command()
def status(
    service_name: str = typer.Argument(..., help="Name of the ECS service to check"),
) -> None:
    """Get the status of an ECS service deployment"""

    def check(delay: int = 5) -> None:
        import time

        while True:
            response = get_service(service_name, env.api_config)
            if HTTPStatus.OK == response.status_code:
                loop_status = [V1ServiceResonseStatus("PENDING").value, V1ServiceResonseStatus("IN_PROGRESS").value]
                data = response.json()
                if data.get("status") in loop_status:
                    console.print(".", style="cyan")
                else:
                    console.print("Deployment successfully", style="bold green")
                    break
            else:
                raise HTTPException(status_code=response.status_code, message=response.json())
            time.sleep(delay)

    console.print(f"Checking status for service {service_name}..", style="cyan")

    return _withExceptionHandler(fn=check)


def _withExceptionHandler(fn: Callable) -> None:
    try:
        fn()
    except HTTPException as e:
        console.print("API Error", style="bold red")
        console.print(e, overflow="fold")
        return typer.Abort()
    except Exception as e:
        console.print("Unexpected error", style="red")
        console.print(e, overflow="fold", style="bold red")
        return typer.Abort()
