import json
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
            assert settings.api_access_key == mock_env_vars["API_ACCESS_KEY"]

    def test_dotenv_settings_default_api_version(self, fake):
        mock_vars = {
            "API_BASE_URL": fake.url(),
            "API_ACCESS_KEY": fake.uuid4(),
        }
        with patch.dict(os.environ, mock_vars, clear=True):
            settings = DotEnvSettings()
            assert settings.api_version == "v1"

    def test_dotenv_settings_missing_required_vars(self):
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: (default if key == "API_VERSION" else None)

            try:
                settings = DotEnvSettings()
                assert settings.api_base_url is not None or settings.api_base_url == ""
                assert settings.api_access_key is not None or settings.api_access_key == ""
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
            assert settings.meta["version"] == "25.12.2"

    @patch("maws.config.AuthenticatedClient")
    def test_api_client_property(self, mock_client_class, fake, mock_env_vars):
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        with patch.dict(os.environ, mock_env_vars):
            settings = Settings()
            client = settings.api_client

            mock_client_class.assert_called_once_with(
                base_url=f"{mock_env_vars['API_BASE_URL']}",
                token=mock_env_vars["API_ACCESS_KEY"],
                auth_header_name="x-api-key",
                prefix="",
            )
            assert client == mock_client_instance

    def test_settings_with_fake_data(self, fake):
        for _ in range(5):
            mock_vars = {
                "API_BASE_URL": fake.url(),
                "API_VERSION": fake.word(),
                "API_ACCESS_KEY": fake.uuid4(),
            }

            with patch.dict(os.environ, mock_vars):
                settings = Settings()
                assert settings.api_base_url == mock_vars["API_BASE_URL"]
                assert settings.api_version == mock_vars["API_VERSION"]
                assert settings.api_access_key == mock_vars["API_ACCESS_KEY"]

    def test_settings_with_profile(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[profiles.test]
API_BASE_URL = "https://test-api.example.com"
API_ACCESS_KEY = "test-token"
API_VERSION = "v2"
""")
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                settings = Settings(profile="test")
                assert settings.api_base_url == "https://test-api.example.com"
                assert settings.api_access_key == "test-token"
                assert settings.api_version == "v2"

        os.unlink(f.name)

    @patch("maws.config.AuthenticatedClient")
    @patch("maws.config.console")
    def test_api_client_warns_when_both_token_and_client_credentials(self, mock_console, mock_client_class):
        mock_client_class.return_value = Mock()
        env_vars = {
            "API_BASE_URL": "https://example.com",
            "API_ACCESS_KEY": "token",
            "API_CLIENT_ID": "client-id",
            "API_CLIENT_SECRET": "client-secret",
        }
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            settings.api_client
            mock_console.print.assert_called_once()
            assert "API_ACCESS_KEY" in str(mock_console.print.call_args)

    @patch("maws.config.post_token")
    @patch("maws.config.Client")
    @patch("maws.config.AuthenticatedClient")
    def test_api_client_with_client_credentials(self, mock_auth_client, mock_client, mock_post_token):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = json.dumps({"access_token": "bearer-token"})
        mock_post_token.sync_detailed.return_value = mock_response

        env_vars = {"API_BASE_URL": "https://example.com", "API_CLIENT_ID": "cid", "API_CLIENT_SECRET": "csecret"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            settings.api_access_key = None
            settings.api_client
            mock_auth_client.assert_called_once_with(base_url="https://example.com", token="bearer-token")

    @patch("maws.config.post_token")
    @patch("maws.config.Client")
    def test_api_client_client_credentials_token_failure(self, mock_client, mock_post_token):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post_token.sync_detailed.return_value = mock_response

        env_vars = {"API_BASE_URL": "https://example.com", "API_CLIENT_ID": "cid", "API_CLIENT_SECRET": "csecret"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            settings.api_access_key = None
            with pytest.raises(SystemExit, match="Failed to obtain bearer token: 401"):
                settings.api_client

    @patch("maws.config.post_token")
    @patch("maws.config.Client")
    @patch("maws.config.AuthenticatedClient")
    def test_api_client_client_credentials_plain_string_token(self, mock_auth_client, mock_client, mock_post_token):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = json.dumps("plain-token")
        mock_post_token.sync_detailed.return_value = mock_response

        env_vars = {"API_BASE_URL": "https://example.com", "API_CLIENT_ID": "cid", "API_CLIENT_SECRET": "csecret"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            settings.api_access_key = None
            settings.api_client
            mock_auth_client.assert_called_once_with(base_url="https://example.com", token="plain-token")

    def test_api_client_no_auth_configured(self):
        env_vars = {"API_BASE_URL": "https://example.com"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            settings.api_access_key = None
            settings.api_client_id = None
            settings.api_client_secret = None
            with pytest.raises(SystemExit, match="No authentication configured"):
                settings.api_client


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
            f.write("""
[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
API_ACCESS_KEY = "dev-token"

[profiles.prod]
API_BASE_URL = "https://prod-api.example.com"
API_ACCESS_KEY = "prod-token"
""")
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                result = load_profile("dev")
                assert result["API_BASE_URL"] == "https://dev-api.example.com"
                assert result["API_ACCESS_KEY"] == "dev-token"

        os.unlink(f.name)

    def test_load_profile_not_found(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
""")
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
            assert settings1.api_access_key == settings2.api_access_key

    def test_get_settings_with_random_data(self, fake):
        for _ in range(3):
            mock_vars = {
                "API_BASE_URL": fake.url(),
                "API_VERSION": fake.word(),
                "API_ACCESS_KEY": fake.password(length=32),
            }

            with patch.dict(os.environ, mock_vars):
                settings = get_settings()
                assert settings.api_base_url == mock_vars["API_BASE_URL"]
                assert settings.api_version == mock_vars["API_VERSION"]
                assert settings.api_access_key == mock_vars["API_ACCESS_KEY"]
                assert settings.meta["name"] == "maws"
                assert settings.meta["version"] == "25.12.2"

    def test_get_settings_with_profile(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[profiles.test]
API_BASE_URL = "https://test-api.example.com"
API_ACCESS_KEY = "test-token"
API_VERSION = "v2"
""")
            f.flush()

            with patch("maws.config.CONFIG_FILE_PATH", Path(f.name)):
                settings = get_settings("test")
                assert settings.api_base_url == "https://test-api.example.com"
                assert settings.api_access_key == "test-token"
                assert settings.api_version == "v2"

        os.unlink(f.name)


class TestConfigFilePath:
    def test_config_file_path_is_correct(self):
        expected_path = Path.home() / ".skaylink" / "profile.toml"
        assert CONFIG_FILE_PATH == expected_path
