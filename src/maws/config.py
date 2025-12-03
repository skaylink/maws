import os
import tomllib
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from maws.clients.ecs_service_deployment_client import AuthenticatedClient

from . import __app_name__, __version__

CONFIG_FILE_PATH = Path.home() / ".skaylink" / "profile.toml"


def show_config_help():
    console = Console()

    help_text = Text()
    help_text.append(f"Welcome to {__app_name__}! 🦆\n\n", style="bold cyan")
    help_text.append("To get started, create a configuration file at: ", style="white")
    help_text.append(str(CONFIG_FILE_PATH) + "\n\n", style="bold yellow")
    help_text.append("Example configuration:\n\n", style="white")
    help_text.append(
        """[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
API_ACCESS_TOKEN = "your-dev-token"

[profiles.prod]
API_BASE_URL = "https://prod-api.example.com"
API_ACCESS_TOKEN = "your-prod-token"
""",
        style="green",
    )
    help_text.append("\nThen use: ", style="white")
    help_text.append(f"{__app_name__} ecs deploy service image --profile dev", style="bold blue")

    console.print(Panel(help_text, title="Configuration Required", border_style="cyan"))


def load_profile(name: str = None) -> dict:
    if not name:
        return {}

    if not CONFIG_FILE_PATH.exists():
        show_config_help()
        raise SystemExit(1)

    with open(CONFIG_FILE_PATH, "rb") as f:
        data = tomllib.load(f)

    profiles = data.get("profiles", {})
    if name not in profiles:
        console = Console()
        console.print(f"Profile '{name}' not found in {CONFIG_FILE_PATH}", style="red")
        console.print(f"Available profiles: {', '.join(profiles.keys())}", style="yellow")
        raise SystemExit(1)

    return profiles.get(name)


class DotEnvSettings(BaseSettings):
    api_version: str = os.getenv("API_VERSION", "v1")
    api_base_url: Optional[str] = os.getenv("API_BASE_URL")
    api_access_token: Optional[str] = os.getenv("API_ACCESS_TOKEN")


class Settings(DotEnvSettings):
    meta: dict = {
        "name": __app_name__,
        "version": __version__,
    }

    def __init__(cls, profile: str = None):
        """
        Args:
            profile (str, optional): Defaults to None.
        """
        super().__init__()
        if profile:
            data = load_profile(name=profile)
            cls.api_base_url = data.get("API_BASE_URL")
            cls.api_access_token = data.get("API_ACCESS_TOKEN")
            if data.get("API_VERSION"):
                cls.api_version = data.get("API_VERSION")

    @property
    def api_client(cls) -> AuthenticatedClient:
        """
        Get API client

        Returns:
            AuthenticatedClient
        """
        return AuthenticatedClient(
            base_url=f"{cls.api_base_url}/{cls.api_version}",
            token=cls.api_access_token,
            auth_header_name="x-api-token",
            prefix="",
        )


def get_settings(profile: str = None):
    return Settings(profile=profile)


env = get_settings()
