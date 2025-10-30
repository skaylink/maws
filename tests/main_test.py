from unittest.mock import patch

import typer
from typer.testing import CliRunner

from rubber_duck.main import app, ecs_commands


class TestMainApp:

    def setUp(self):
        self.runner = CliRunner()

    def test_app_is_typer_instance(self):
        assert isinstance(app, typer.Typer)

    def test_ecs_commands_is_typer_instance(self):
        assert isinstance(ecs_commands, typer.Typer)

    def test_app_help_message(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Welcome to skaylink deployment client." in result.stdout

    def test_app_no_args_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_ecs_command_available(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ecs" in result.stdout

    def test_ecs_subcommand_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["ecs", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_ecs_no_args_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["ecs"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_invalid_command(self, fake):
        runner = CliRunner()
        invalid_command = fake.word()
        result = runner.invoke(app, [invalid_command])
        assert result.exit_code != 0

    def test_app_structure(self):
        assert hasattr(app, "registered_commands")

    def test_multiple_help_calls(self):
        runner = CliRunner()
        for _ in range(3):
            result = runner.invoke(app, ["--help"])
            assert result.exit_code == 0
            assert "Welcome to skaylink deployment client." in result.stdout

    def test_ecs_commands_configuration(self):
        runner = CliRunner()
        result = runner.invoke(ecs_commands, [])
        assert result.exit_code == 0

    @patch("rubber_duck.main.app")
    def test_main_execution(self, mock_rubber_duck):
        mock_rubber_duck.return_value = None

        import rubber_duck.main

        assert hasattr(rubber_duck.main, "app")
        assert callable(rubber_duck.main.app)

    def test_app_with_fake_commands(self, fake):
        runner = CliRunner()

        fake_commands = [fake.word() for _ in range(5)]
        for cmd in fake_commands:
            result = runner.invoke(app, [cmd])
            assert result.exit_code != 0
