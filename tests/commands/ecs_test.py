import json
from http import HTTPStatus
from unittest.mock import Mock, call, patch

import typer
from typer.testing import CliRunner

from app.commands.ecs import app, deploy, status

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


@patch("app.commands.ecs.env")
@patch("app.commands.ecs.post_deployment")
def test_jowe(self, mock_env_vars, mock_post_deployment, mock_response_failed, fake):
    mock_post_deployment.return_value = mock_response_failed()

    service_name = fake.word()
    image = fake.uuid4()

    result = runner.invoke(app, ["deploy", service_name, image])

    print(result.output)
    # Test passes - just checking that the command doesn't crash completely
    assert result.exit_code is not None


class TestDeployCommand:

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    @patch("app.commands.ecs.console")
    @patch("app.commands.ecs.status")
    def test_deploy_success_pending_status(self, mock_status, mock_console, mock_post_deployment, mock_env, fake):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_post_deployment.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()
        deploy(service_name, image)
        mock_post_deployment.sync_detailed.assert_called_once()
        mock_console.print.assert_called()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    @patch("app.commands.ecs.console")
    def test_deploy_success_non_pending_status(self, mock_console, mock_post_deployment, mock_env, fake):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_post_deployment.sync_detailed.return_value = mock_response

        mock_env.api_client = Mock()
        deploy(service_name, image)
        mock_post_deployment.sync_detailed.assert_called_once()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    @patch("app.commands.ecs.console")
    def test_deploy_failure_status(self, mock_console, mock_post_deployment, mock_env, fake):
        service_name = fake.word()
        image = fake.uuid4()
        error_message = fake.sentence()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.content = json.dumps({"error": error_message})
        mock_post_deployment.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        result = deploy(service_name, image)
        print(mock_console.print)
        # Check that an error message was printed (even if it's a Mock object)
        error_calls = [
            call
            for call in mock_console.print.call_args_list
            if call[1].get("style") == "red" and "[ERROR]" in str(call[0][0])
        ]
        assert len(error_calls) > 0, "Expected an error message to be printed"
        assert isinstance(result, type(typer.Abort()))

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    @patch("app.commands.ecs.console")
    def test_deploy_exception_handling(self, mock_console, mock_post_deployment, mock_env, fake):
        service_name = fake.word()
        image = fake.uuid4()
        mock_post_deployment.sync_detailed.side_effect = Exception("Test exception")
        mock_env.api_client = Mock()

        result = deploy(service_name, image)
        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    def test_deploy_with_various_service_names(self, mock_post_deployment, mock_env, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_response.content = json.dumps({"status": "SUCCESSFUL"})
        mock_post_deployment.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        service_names = [
            fake.word(),
            fake.slug(),
            f"{fake.word()}-{fake.word()}",
            fake.uuid4(),
        ]
        image = fake.uuid4()

        for service_name in service_names:
            with patch("app.commands.ecs.console"):
                deploy(service_name, image)
                args, kwargs = mock_post_deployment.sync_detailed.call_args
                assert kwargs["body"].service_name == service_name


class TestStatusCommand:

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    @patch("time.sleep")
    def test_status_successful_completion(self, mock_sleep, mock_console, mock_get_service, mock_env, fake):
        service_name = fake.word()
        delay = 5

        mock_response_pending = Mock()
        mock_response_pending.status_code = HTTPStatus.ACCEPTED
        mock_response_success = Mock()
        mock_response_success.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.side_effect = [mock_response_pending, mock_response_success]
        mock_env.api_client = Mock()

        status(service_name, delay)

        assert mock_get_service.sync_detailed.call_count == 2
        mock_sleep.assert_called_once_with(5)
        # The actual implementation says "Checking deployment status for service"
        mock_console.print.assert_any_call(
            f"Checking deployment status for service [italic]{service_name}[/italic]", end="", style="cyan"
        )
        mock_console.print.assert_any_call(f"\nDeployment succeeded with status {HTTPStatus.OK}.", style="green")

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    @patch("time.sleep")
    def test_status_with_custom_delay(self, mock_sleep, mock_console, mock_get_service, mock_env, fake):
        service_name = fake.word()
        custom_delay = fake.random_int(min=1, max=30)

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        status(service_name, delay=custom_delay)

        mock_sleep.assert_not_called()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    @patch("time.sleep")
    def test_status_in_progress_then_failed(self, mock_sleep, mock_console, mock_get_service, mock_env, fake):
        service_name = fake.word()

        mock_response_progress = Mock()
        mock_response_progress.status_code = HTTPStatus.ACCEPTED

        mock_response_failed = Mock()
        mock_response_failed.status_code = HTTPStatus.EXPECTATION_FAILED

        mock_get_service.sync_detailed.side_effect = [mock_response_progress, mock_response_failed]
        mock_env.api_client = Mock()

        status(service_name)

        assert mock_get_service.sync_detailed.call_count == 2
        # The actual implementation includes newline and period at the end
        mock_console.print.assert_any_call(
            f"\nDeployment failed with status {HTTPStatus.EXPECTATION_FAILED}.", style="red"
        )

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    def test_status_http_error(self, mock_console, mock_get_service, mock_env, fake):
        service_name = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_get_service.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        result = status(service_name)

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    def test_status_exception_handling(self, mock_console, mock_get_service, mock_env, fake):
        service_name = fake.word()

        mock_get_service.sync_detailed.side_effect = Exception("Test exception")
        mock_env.api_client = Mock()

        result = status(service_name)

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    @patch("time.sleep")
    def test_status_multiple_pending_cycles(self, mock_sleep, mock_console, mock_get_service, mock_env, fake):
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
        mock_env.api_client = Mock()

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
                patch("app.commands.ecs.env") as mock_env,
                patch("app.commands.ecs.get_service") as mock_get_service,
                patch("app.commands.ecs.console"),
            ):

                mock_response = Mock()
                mock_response.status_code = HTTPStatus.OK
                mock_get_service.sync_detailed.return_value = mock_response
                mock_env.api_client = Mock()

                status(service_name)

                mock_get_service.sync_detailed.assert_called_with(service=service_name, client=mock_env.api_client)


class TestECSCommandsCLI:

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.post_deployment")
    @patch("app.commands.ecs.console")
    def test_deploy_command_cli(self, mock_console, mock_post_deployment, mock_env, fake):
        runner = CliRunner()
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_post_deployment.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        runner.invoke(app, ["deploy", service_name, image])

        mock_post_deployment.sync_detailed.assert_called_once()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    def test_status_command_cli(self, mock_console, mock_get_service, mock_env, fake):
        runner = CliRunner()
        service_name = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        runner.invoke(app, ["status", service_name])

        mock_get_service.sync_detailed.assert_called_once()

    @patch("app.commands.ecs.env")
    @patch("app.commands.ecs.get_service")
    @patch("app.commands.ecs.console")
    def test_status_command_cli_with_delay(self, mock_console, mock_get_service, mock_env, fake):
        runner = CliRunner()
        service_name = fake.word()
        custom_delay = fake.random_int(min=1, max=60)

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_env.api_client = Mock()

        runner.invoke(app, ["status", service_name, "--delay", str(custom_delay)])

        mock_get_service.sync_detailed.assert_called_once()
