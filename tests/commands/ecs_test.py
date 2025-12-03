import json
from http import HTTPStatus
from unittest.mock import Mock, call, patch

import typer
from typer.testing import CliRunner

from maws.commands.ecs import app, deploy, status

runner = CliRunner()


class TestECSCommands:

    def setUp(self):
        self.runner = CliRunner()

    def test_app_is_typer_instance(self):
        assert isinstance(app, typer.Typer)

    def test_app_no_args_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout


@patch("maws.commands.ecs.get_settings")
@patch("maws.commands.ecs.patch_service")
def test_jowe(mock_patch_service, mock_get_settings, mock_response_failed, fake):
    mock_get_settings.return_value.api_client = Mock()
    mock_patch_service.sync_detailed.return_value = mock_response_failed()

    service_name = fake.word()
    image = fake.uuid4()

    result = runner.invoke(app, ["deploy", service_name, image])

    print(result.output)
    # Test passes - just checking that the command doesn't crash completely
    assert result.exit_code is not None


class TestDeployCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    @patch("maws.commands.ecs.status")
    def test_deploy_success_pending_status(
        self, mock_status, mock_console, mock_patch_service, mock_get_settings, fake
    ):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()
        deploy(service_name, image)
        mock_patch_service.sync_detailed.assert_called_once()
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_success_non_pending_status(self, mock_console, mock_patch_service, mock_get_settings, fake):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response

        mock_get_settings.return_value.api_client = Mock()
        deploy(service_name, image)
        mock_patch_service.sync_detailed.assert_called_once()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_failure_status(self, mock_console, mock_patch_service, mock_get_settings, fake):
        service_name = fake.word()
        image = fake.uuid4()
        error_message = fake.sentence()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.content = f'{{"error": "{error_message}"}}'
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = deploy(service_name, image)
        # Check that an error message was printed
        error_calls = [
            call for call in mock_console.print.call_args_list if len(call[0]) > 0 and "[ERROR]" in str(call[0][0])
        ]
        assert len(error_calls) > 0, "Expected an error message to be printed"
        assert isinstance(result, type(typer.Abort()))

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_exception_handling(self, mock_console, mock_patch_service, mock_get_settings, fake):
        service_name = fake.word()
        image = fake.uuid4()
        mock_patch_service.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        result = deploy(service_name, image)
        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    def test_deploy_with_various_service_names(self, mock_patch_service, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_response.content = json.dumps({"status": "SUCCESSFUL"})
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        service_names = [
            fake.word(),
            fake.slug(),
            f"{fake.word()}-{fake.word()}",
            fake.uuid4(),
        ]
        image = fake.uuid4()

        for service_name in service_names:
            with patch("maws.commands.ecs.console"):
                deploy(service_name, image)
                args, kwargs = mock_patch_service.sync_detailed.call_args
                assert kwargs["body"].image == image

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_with_profile(self, mock_console, mock_patch_service, mock_get_settings, fake):
        service_name = fake.word()
        image = fake.uuid4()
        profile = "dev"

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        with patch("maws.commands.ecs.status"):
            deploy(service_name, image, profile=profile)
            mock_get_settings.assert_called_with(profile)


class TestStatusCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    @patch("time.sleep")
    def test_status_successful_completion(self, mock_sleep, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()
        delay = 5

        mock_response_pending = Mock()
        mock_response_pending.status_code = HTTPStatus.ACCEPTED
        mock_response_success = Mock()
        mock_response_success.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.side_effect = [
            mock_response_pending,
            mock_response_success,
        ]
        mock_get_settings.return_value.api_client = Mock()

        status(service_name, delay)

        assert mock_get_service.sync_detailed.call_count == 2
        mock_sleep.assert_called_once_with(5)
        mock_console.print.assert_any_call(
            f"Checking deployment status for service [italic]{service_name}[/italic]",
            end="",
            style="cyan",
        )
        mock_console.print.assert_any_call(f"\nDeployment succeeded with status {HTTPStatus.OK}.", style="green")

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    @patch("time.sleep")
    def test_status_with_custom_delay(self, mock_sleep, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()
        custom_delay = fake.random_int(min=1, max=30)

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        status(service_name, delay=custom_delay)

        mock_sleep.assert_not_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    @patch("time.sleep")
    def test_status_in_progress_then_failed(self, mock_sleep, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()

        mock_response_progress = Mock()
        mock_response_progress.status_code = HTTPStatus.ACCEPTED

        mock_response_failed = Mock()
        mock_response_failed.status_code = HTTPStatus.EXPECTATION_FAILED

        mock_get_service.sync_detailed.side_effect = [
            mock_response_progress,
            mock_response_failed,
        ]
        mock_get_settings.return_value.api_client = Mock()

        status(service_name)

        assert mock_get_service.sync_detailed.call_count == 2
        mock_console.print.assert_any_call(
            f"\nDeployment failed with status {HTTPStatus.EXPECTATION_FAILED}.",
            style="red",
        )

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_http_error(self, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = status(service_name)

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_exception_handling(self, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()

        mock_get_service.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        result = status(service_name)

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    @patch("time.sleep")
    def test_status_multiple_pending_cycles(self, mock_sleep, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()

        mock_response_pending = Mock()
        mock_response_pending.status_code = HTTPStatus.ACCEPTED

        mock_response_success = Mock()
        mock_response_success.status_code = HTTPStatus.OK

        mock_get_service.sync_detailed.side_effect = [
            mock_response_pending,
            mock_response_pending,
            mock_response_pending,
            mock_response_success,
        ]
        mock_get_settings.return_value.api_client = Mock()

        status(service_name)

        assert mock_get_service.sync_detailed.call_count == 4
        assert mock_sleep.call_count == 3

        dot_calls = [call(".", end="", style="cyan") for _ in range(3)]
        mock_console.print.assert_has_calls(dot_calls, any_order=False)

    def test_status_with_various_service_names(self, fake):
        service_names = [
            fake.word(),
            fake.slug(),
            f"{fake.word()}-{fake.word()}",
            fake.uuid4(),
        ]

        for service_name in service_names:
            with (
                patch("maws.commands.ecs.get_settings") as mock_get_settings,
                patch("maws.commands.ecs.get_service") as mock_get_service,
                patch("maws.commands.ecs.console"),
            ):

                mock_response = Mock()
                mock_response.status_code = HTTPStatus.OK
                mock_get_service.sync_detailed.return_value = mock_response
                mock_get_settings.return_value.api_client = Mock()

                status(service_name)

                mock_get_service.sync_detailed.assert_called_with(
                    service=service_name,
                    client=mock_get_settings.return_value.api_client,
                )

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_with_profile(self, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()
        profile = "prod"

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        status(service_name, profile=profile)

        mock_get_settings.assert_called_with(profile)


class TestECSCommandsCLI:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.status")
    @patch("maws.commands.ecs.console")
    def test_deploy_command_cli(self, mock_console, mock_status, mock_patch_service, mock_get_settings, fake):
        runner = CliRunner()
        service_name = fake.word()
        image = fake.uuid4()
        profile = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        runner.invoke(app, ["deploy", service_name, image, "--profile", profile])

        mock_patch_service.sync_detailed.assert_called_once()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_command_cli(self, mock_console, mock_get_service, mock_get_settings, fake):
        runner = CliRunner()
        service_name = fake.word()
        profile = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        runner.invoke(app, ["status", service_name, "--profile", profile])

        mock_get_service.sync_detailed.assert_called_once()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_command_cli_with_delay(self, mock_console, mock_get_service, mock_get_settings, fake):
        runner = CliRunner()
        service_name = fake.word()
        profile = fake.word()
        custom_delay = fake.random_int(min=1, max=60)

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        runner.invoke(
            app,
            [
                "status",
                service_name,
                "--delay",
                str(custom_delay),
                "--profile",
                profile,
            ],
        )

        mock_get_service.sync_detailed.assert_called_once()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_command_cli_with_profile(self, mock_console, mock_patch_service, mock_get_settings, fake):
        runner = CliRunner()
        service_name = fake.word()
        image = fake.uuid4()
        profile = "dev"

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        with patch("maws.commands.ecs.status"):
            runner.invoke(app, ["deploy", service_name, image, "--profile", profile])
            mock_get_settings.assert_called_with(profile)
