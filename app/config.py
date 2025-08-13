import os

from pydantic_settings import BaseSettings

from app.clients.api import APIConfig

from . import __app_name__, __version__


class DotEnvSettings(BaseSettings):
    api_base_url: str = os.getenv("API_BASE_URL")
    access_token: str = os.getenv("API_ACCESS_TOKEN")


class Settings(DotEnvSettings):
    meta: dict = {
        "name": __app_name__,
        "version": __version__,
    }

    @property
    def api_config(cls) -> APIConfig:
        """
        Define the API configuration with base URL and optional access token.

        Returns:
            APIConfig
        """
        return APIConfig(base_path=cls.api_base_url, access_token=cls.access_token)


def get_settings():
    return Settings()


env = get_settings()
