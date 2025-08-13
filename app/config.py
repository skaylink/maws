import os

from pydantic_settings import BaseSettings

from app.clients.ecs_service_deployment_client import AuthenticatedClient

from . import __app_name__, __version__


class DotEnvSettings(BaseSettings):
    api_base_url: str = os.getenv("API_BASE_URL")
    api_version: str = os.getenv("API_VERSION", "v1")
    api_access_token: str = os.getenv("API_ACCESS_TOKEN")


class Settings(DotEnvSettings):
    meta: dict = {
        "name": __app_name__,
        "version": __version__,
    }

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


def get_settings():
    return Settings()


env = get_settings()
