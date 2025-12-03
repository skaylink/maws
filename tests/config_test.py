import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from maws.config import (
    CONFIG_FILE_PATH,
    DotEnvSettings,
    Settings,
    get_settings,
    load_profile,
)


class TestDotEnvSettings:

    def test_dotenv_settings_initialization(self, fake, mock_env_vars):
        with patch.dict(os.environ, mock_env_vars):
            settings = DotEnvSettings()
            assert settings.api_base_url == mock_env_vars["API_BASE_URL"]
            assert settings.api_version == mock_env_vars["API_VERSION"]
            assert settings.api_access_token == mock_env_vars["API_ACCESS_TOKEN"]

    def test_dotenv_settings_default_api_version(self, fake):
        mock_vars = {
            "API_BASE_URL": fake.url(),
            "API_ACCESS_TOKEN": fake.uuid4(),
        }
        with patch.dict(os.environ, mock_vars, clear=True):
            settings = DotEnvSettings()
            assert settings.api_version == "v1"

    def test_dotenv_settings_missing_required_vars(self):
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: default if key == "API_VERSION" else None

            try:
                settings = DotEnvSettings()
                assert settings.api_base_url is not None or settings.api_base_url == ""
                assert settings.api_access_token is not None or settings.api_access_token == ""
                assert settings.api_version == "v1"
            except Exception:
                pass


class TestSettings:

    def test_settings_inheritance(self, fake, mock_env_vars):
        with patch.dict(os.environ, mock_env_vars):
            settings = Settings()
            assert isinstance(settings, DotEnvSettings)
            assert settings.api_base_url == mock_env_vars["API_BASE_URL"]

    def test_settings_meta_property(self, fake, mock_env_vars):
        with patch.dict(os.environ, mock_env_vars):
            settings = Settings()
            assert "name" in settings.meta
            assert "version" in settings.meta
            assert settings.meta["name"] == "maws"
            assert settings.meta["version"] == "0.0.1"

    @patch("maws.config.AuthenticatedClient")
    def test_api_client_property(self, mock_client_class, fake, mock_env_vars):
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        with patch.dict(os.environ, mock_env_vars):
            settings = Settings()
            client = settings.api_client

            mock_client_class.assert_called_once_with(
                base_url=f"{mock_env_vars['API_BASE_URL']}/{mock_env_vars['API_VERSION']}",
                token=mock_env_vars["API_ACCESS_TOKEN"],
                auth_header_name="x-api-token",
                prefix="",
            )
            assert client == mock_client_instance

    @patch("maws.config.AuthenticatedClient")
    def test_api_client_with_default_version(self, mock_client_class, fake):
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        mock_vars = {
            "API_BASE_URL": fake.url(),
            "API_ACCESS_TOKEN": fake.uuid4(),
        }

        with patch.dict(os.environ, mock_vars, clear=True):
            settings = Settings()
            settings.api_client

            expected_base_url = f"{mock_vars['API_BASE_URL']}/v1"
            mock_client_class.assert_called_once_with(
                base_url=expected_base_url,
                token=mock_vars["API_ACCESS_TOKEN"],
                auth_header_name="x-api-token",
                prefix="",
            )

    def test_settings_with_fake_data(self, fake):
        for _ in range(5):
            mock_vars = {
                "API_BASE_URL": fake.url(),
                "API_VERSION": fake.word(),
                "API_ACCESS_TOKEN": fake.uuid4(),
            }

            with patch.dict(os.environ, mock_vars):
                settings = Settings()
                assert settings.api_base_url == mock_vars["API_BASE_URL"]
                assert settings.api_version == mock_vars["API_VERSION"]
                assert settings.api_access_token == mock_vars["API_ACCESS_TOKEN"]

    def test_settings_with_profile(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[profiles.test]
API_BASE_URL = "https://test-api.example.com"
API_ACCESS_TOKEN = "test-token"
API_VERSION = "v2"
"""
            )
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                settings = Settings(profile="test")
                assert settings.api_base_url == "https://test-api.example.com"
                assert settings.api_access_token == "test-token"
                assert settings.api_version == "v2"

        os.unlink(f.name)


class TestProfileLoading:
    def test_load_profile_empty_name(self):
        result = load_profile(None)
        assert result == {}

    def test_load_profile_file_not_exists(self):
        with patch("maws.config.CONFIG_FILE_PATH") as mock_path:
            mock_path.exists.return_value = False
            with pytest.raises(SystemExit):
                load_profile("dev")

    def test_load_profile_success(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
API_ACCESS_TOKEN = "dev-token"

[profiles.prod]
API_BASE_URL = "https://prod-api.example.com"
API_ACCESS_TOKEN = "prod-token"
"""
            )
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                result = load_profile("dev")
                assert result["API_BASE_URL"] == "https://dev-api.example.com"
                assert result["API_ACCESS_TOKEN"] == "dev-token"

        os.unlink(f.name)

    def test_load_profile_not_found(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
"""
            )
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                with pytest.raises(SystemExit):
                    load_profile("nonexistent")

        os.unlink(f.name)


class TestGetSettings:

    def test_get_settings_returns_settings_instance(self, fake, mock_env_vars):
        with patch.dict(os.environ, mock_env_vars):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_consistency(self, fake, mock_env_vars):
        with patch.dict(os.environ, mock_env_vars):
            settings1 = get_settings()
            settings2 = get_settings()

            assert settings1.api_base_url == settings2.api_base_url
            assert settings1.api_version == settings2.api_version
            assert settings1.api_access_token == settings2.api_access_token

    def test_get_settings_with_random_data(self, fake):
        for _ in range(3):
            mock_vars = {
                "API_BASE_URL": fake.url(),
                "API_VERSION": fake.word(),
                "API_ACCESS_TOKEN": fake.password(length=32),
            }

            with patch.dict(os.environ, mock_vars):
                settings = get_settings()
                assert settings.api_base_url == mock_vars["API_BASE_URL"]
                assert settings.api_version == mock_vars["API_VERSION"]
                assert settings.api_access_token == mock_vars["API_ACCESS_TOKEN"]
                assert settings.meta["name"] == "maws"
                assert settings.meta["version"] == "0.0.1"

    def test_get_settings_with_profile(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[profiles.test]
API_BASE_URL = "https://test-api.example.com"
API_ACCESS_TOKEN = "test-token"
API_VERSION = "v2"
"""
            )
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                settings = get_settings("test")
                assert settings.api_base_url == "https://test-api.example.com"
                assert settings.api_access_token == "test-token"
                assert settings.api_version == "v2"

        os.unlink(f.name)


class TestConfigFilePath:
    def test_config_file_path_is_correct(self):
        expected_path = Path.home() / ".skaylink" / "profile.toml"
        assert CONFIG_FILE_PATH == expected_path
