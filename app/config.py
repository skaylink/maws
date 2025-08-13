import os

from pydantic_settings import BaseSettings

from . import __app_name__, __version__


class DotEnvSettings(BaseSettings):
    endpoint: str = os.getenv("ENDPOINT")
    secret: str = os.getenv("SECRET")


class Settings(DotEnvSettings):
    meta: dict = {
        "name": __app_name__,
        "version": __version__,
    }


def get_settings():
    return Settings()


env = get_settings()
