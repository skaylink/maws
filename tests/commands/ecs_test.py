import json
from http import HTTPStatus
from unittest.mock import Mock, call, patch

import pytest
import typer
from typer.testing import CliRunner

from maws.commands.ecs import (
    app,
    deploy_service,
    deploy_task,
    list_services,
    list_tasks,
    service_status,
    task_status,
)

runner = CliRunner()

SCHEDULE = "cron(0 3 * * ? *)"


class TestECSCommands:

    def setUp(self):
        self.runner = CliRunner()

    def test_app_is_typer_instance(self):
        assert isinstance(app, typer.Typer)

    def test_app_no_args_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 2
        assert "Usage:" in result.stdout


@patch("maws.commands.ecs.get_settings")
@patch("maws.commands.ecs.patch_service")
def test_jowe(mock_patch_service, mock_get_settings, mock_response_failed, fake):
    mock_get_settings.return_value.api_client = Mock()
    mock_patch_service.sync_detailed.return_value = mock_response_failed()

    service_name = fake.word()
    image = fake.uuid4()

    result = runner.invoke(app, ["services", "deploy", service_name, image])

    print(result.output)
    # a failed deployment request must not report success
    assert result.exit_code == 1


class TestDeployCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    @patch("maws.commands.ecs.service_status")
    def test_deploy_success_pending_status(
        self, mock_status, mock_console, mock_patch_service, mock_get_settings, fake
    ):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()
        deploy_service(service_name, image)
        mock_patch_service.sync_detailed.assert_called_once()
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    @patch("maws.commands.ecs.service_status")
    def test_deploy_success_non_pending_status(
        self, mock_status, mock_console, mock_patch_service, mock_get_settings, fake
    ):
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response

        mock_get_settings.return_value.api_client = Mock()
        deploy_service(service_name, image)
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

        with pytest.raises(typer.Abort):
            deploy_service(service_name, image)
        # Check that an error message was printed
        error_calls = [
            call for call in mock_console.print.call_args_list if len(call[0]) > 0 and "[ERROR]" in str(call[0][0])
        ]
        assert len(error_calls) > 0, "Expected an error message to be printed"

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_exception_handling(self, mock_console, mock_patch_service, mock_get_settings, fake):
        service_name = fake.word()
        image = fake.uuid4()
        mock_patch_service.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Abort):
            deploy_service(service_name, image)
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.console")
    def test_deploy_propagates_status_failure_exit_code(
        self, mock_console, mock_patch_service, mock_get_settings, fake
    ):
        """A failing status poll after a successful PATCH must not be swallowed by deploy."""
        service_name = fake.word()
        image = fake.uuid4()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        with patch("maws.commands.ecs.service_status", side_effect=typer.Exit(code=1)):
            with pytest.raises(typer.Exit) as exc_info:
                deploy_service(service_name, image)
        assert exc_info.value.exit_code == 1

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
            with patch("maws.commands.ecs.console"), patch("maws.commands.ecs.service_status"):
                deploy_service(service_name, image)
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

        with patch("maws.commands.ecs.service_status"):
            deploy_service(service_name, image, profile=profile)
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

        service_status(service_name, delay)

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

        service_status(service_name, delay=custom_delay)

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

        with pytest.raises(typer.Exit) as exc_info:
            service_status(service_name)

        assert exc_info.value.exit_code == 1
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

        with pytest.raises(typer.Abort):
            service_status(service_name)

        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.console")
    def test_status_exception_handling(self, mock_console, mock_get_service, mock_get_settings, fake):
        service_name = fake.word()

        mock_get_service.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Abort):
            service_status(service_name)

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

        service_status(service_name)

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

                service_status(service_name)

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

        service_status(service_name, profile=profile)

        mock_get_settings.assert_called_with(profile)


class TestServicesCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_lists_service_names(self, mock_console, mock_get_services, mock_get_settings, fake):
        service_names = [fake.word(), fake.slug(), f"{fake.word()}-{fake.word()}"]

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps(service_names)
        mock_get_services.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_services()

        mock_get_services.sync_detailed.assert_called_once_with(client=mock_get_settings.return_value.api_client)
        for service_name in service_names:
            mock_console.print.assert_any_call(service_name)

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_empty_list(self, mock_console, mock_get_services, mock_get_settings):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([])
        mock_get_services.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_services()

        mock_console.print.assert_called_once_with("No ECS services available.", style="yellow")

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_failure_status(self, mock_console, mock_get_services, mock_get_settings, fake):
        error_message = fake.sentence()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.UNAUTHORIZED
        mock_response.content = json.dumps({"error": error_message})
        mock_get_services.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = list_services()

        error_calls = [
            call for call in mock_console.print.call_args_list if len(call[0]) > 0 and "[ERROR]" in str(call[0][0])
        ]
        assert len(error_calls) > 0, "Expected an error message to be printed"
        assert isinstance(result, type(typer.Abort()))

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_exception_handling(self, mock_console, mock_get_services, mock_get_settings):
        mock_get_services.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        result = list_services()

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_with_profile(self, mock_console, mock_get_services, mock_get_settings, fake):
        profile = "prod"

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([fake.word()])
        mock_get_services.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_services(profile=profile)

        mock_get_settings.assert_called_with(profile)


class TestTasksCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_lists_task_names(self, mock_console, mock_get_tasks, mock_get_settings, fake):
        task_names = [fake.word(), fake.slug(), f"{fake.word()}-{fake.word()}"]

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps(task_names)
        mock_get_tasks.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_tasks()

        mock_get_tasks.sync_detailed.assert_called_once_with(client=mock_get_settings.return_value.api_client)
        for task_name in task_names:
            mock_console.print.assert_any_call(task_name)

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_empty_list(self, mock_console, mock_get_tasks, mock_get_settings):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([])
        mock_get_tasks.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_tasks()

        mock_console.print.assert_called_once_with("No ECS tasks available.", style="yellow")

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_failure_status(self, mock_console, mock_get_tasks, mock_get_settings, fake):
        error_message = fake.sentence()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.UNAUTHORIZED
        mock_response.content = json.dumps({"error": error_message})
        mock_get_tasks.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = list_tasks()

        error_calls = [
            call for call in mock_console.print.call_args_list if len(call[0]) > 0 and "[ERROR]" in str(call[0][0])
        ]
        assert len(error_calls) > 0, "Expected an error message to be printed"
        assert isinstance(result, type(typer.Abort()))

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_exception_handling(self, mock_console, mock_get_tasks, mock_get_settings):
        mock_get_tasks.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        result = list_tasks()

        assert isinstance(result, type(typer.Abort()))
        mock_console.print.assert_called()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_with_profile(self, mock_console, mock_get_tasks, mock_get_settings, fake):
        profile = "prod"

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([fake.word()])
        mock_get_tasks.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        list_tasks(profile=profile)

        mock_get_settings.assert_called_with(profile)


class TestECSCommandsCLI:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.service_status")
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

        runner.invoke(app, ["services", "deploy", service_name, image, "--profile", profile])

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

        runner.invoke(app, ["services", "status", service_name, "--profile", profile])

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
                "services",
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
    @patch("maws.commands.ecs.get_services")
    @patch("maws.commands.ecs.console")
    def test_services_command_cli(self, mock_console, mock_get_services, mock_get_settings, fake):
        runner = CliRunner()
        profile = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([fake.word()])
        mock_get_services.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        runner.invoke(app, ["services", "list", "--profile", profile])

        mock_get_services.sync_detailed.assert_called_once()
        mock_get_settings.assert_called_with(profile)

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_tasks")
    @patch("maws.commands.ecs.console")
    def test_tasks_command_cli(self, mock_console, mock_get_tasks, mock_get_settings, fake):
        runner = CliRunner()
        profile = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.content = json.dumps([fake.word()])
        mock_get_tasks.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        runner.invoke(app, ["tasks", "list", "--profile", profile])

        mock_get_tasks.sync_detailed.assert_called_once()
        mock_get_settings.assert_called_with(profile)

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

        with patch("maws.commands.ecs.service_status"):
            runner.invoke(app, ["services", "deploy", service_name, image, "--profile", profile])
            mock_get_settings.assert_called_with(profile)


class TestExitCodes:
    """The CLI must exit non-zero on failures so shell callers can detect them."""

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    def test_deploy_request_rejected_exits_1(self, mock_patch_service, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.content = json.dumps({"error": fake.sentence()})
        mock_patch_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    def test_deploy_client_exception_exits_1(self, mock_patch_service, mock_get_settings, fake):
        mock_patch_service.sync_detailed.side_effect = Exception("boom")
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.get_service")
    def test_deploy_accepted_then_failed_status_exits_1(
        self, mock_get_service, mock_patch_service, mock_get_settings, fake
    ):
        """PATCH returns 201, polling then reports 417 -> overall failure."""
        mock_patch_response = Mock()
        mock_patch_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_patch_response

        mock_get_response = Mock()
        mock_get_response.status_code = HTTPStatus.EXPECTATION_FAILED
        mock_get_service.sync_detailed.return_value = mock_get_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.get_service")
    def test_deploy_success_exits_0(self, mock_get_service, mock_patch_service, mock_get_settings, fake):
        mock_patch_response = Mock()
        mock_patch_response.status_code = HTTPStatus.CREATED
        mock_patch_service.sync_detailed.return_value = mock_patch_response

        mock_get_response = Mock()
        mock_get_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_get_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 0

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    def test_status_failed_exits_1(self, mock_get_service, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.EXPECTATION_FAILED
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "status", fake.word(), "--profile", fake.word()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    def test_status_unexpected_code_exits_1(self, mock_get_service, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "status", fake.word(), "--profile", fake.word()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_service")
    def test_status_success_exits_0(self, mock_get_service, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get_service.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["services", "status", fake.word(), "--profile", fake.word()])

        assert result.exit_code == 0


class TestTaskDeployCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.console")
    @patch("maws.commands.ecs.task_status")
    def test_deploy_task_success(self, mock_task_status, mock_console, mock_patch_task, mock_get_settings, fake):
        task_name = fake.word()
        image = fake.uuid4()
        profile = fake.word()

        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_task.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        deploy_task(task_name, image, schedule_expression=SCHEDULE, force=False, profile=profile)

        _, kwargs = mock_patch_task.sync_detailed.call_args
        assert kwargs["task"] == task_name
        assert kwargs["body"].image == image
        assert kwargs["body"].schedule_expression == SCHEDULE
        assert kwargs["body"].force is False
        assert kwargs["body"].to_dict() == {"image": image, "schedule_expression": SCHEDULE, "force": False}
        assert kwargs["client"] is mock_get_settings.return_value.api_client
        mock_get_settings.assert_called_with(profile)
        mock_task_status.assert_called_once_with(task_name=task_name, delay=5, profile=profile)

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.console")
    @patch("maws.commands.ecs.task_status")
    def test_deploy_task_failure_status(self, mock_task_status, mock_console, mock_patch_task, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.content = json.dumps({"message": fake.sentence()})
        mock_patch_task.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Abort):
            deploy_task(fake.word(), fake.uuid4())

        mock_task_status.assert_not_called()
        error_calls = [c for c in mock_console.print.call_args_list if c[0] and "[ERROR]" in str(c[0][0])]
        assert error_calls

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.console")
    def test_deploy_task_exception_handling(self, mock_console, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.side_effect = Exception("Test exception")
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Abort):
            deploy_task(fake.word(), fake.uuid4())

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.console")
    def test_deploy_task_propagates_status_failure(self, mock_console, mock_patch_task, mock_get_settings, fake):
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_patch_task.sync_detailed.return_value = mock_response
        mock_get_settings.return_value.api_client = Mock()

        with patch("maws.commands.ecs.task_status", side_effect=typer.Exit(code=1)):
            with pytest.raises(typer.Exit) as exc_info:
                deploy_task(fake.word(), fake.uuid4())
        assert exc_info.value.exit_code == 1


class TestTaskStatusCommand:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_task")
    @patch("maws.commands.ecs.console")
    @patch("time.sleep")
    def test_task_status_pending_then_success(self, mock_sleep, mock_console, mock_get_task, mock_get_settings, fake):
        task_name = fake.word()

        pending = Mock(status_code=HTTPStatus.ACCEPTED)
        success = Mock(status_code=HTTPStatus.OK)
        mock_get_task.sync_detailed.side_effect = [pending, success]
        mock_get_settings.return_value.api_client = Mock()

        task_status(task_name, delay=3)

        assert mock_get_task.sync_detailed.call_count == 2
        mock_get_task.sync_detailed.assert_called_with(task=task_name, client=mock_get_settings.return_value.api_client)
        mock_sleep.assert_called_once_with(3)
        mock_console.print.assert_any_call(
            f"Checking deployment status for task [italic]{task_name}[/italic]",
            end="",
            style="cyan",
        )
        mock_console.print.assert_any_call(f"\nDeployment succeeded with status {HTTPStatus.OK}.", style="green")

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_task")
    @patch("maws.commands.ecs.console")
    def test_task_status_failed(self, mock_console, mock_get_task, mock_get_settings, fake):
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.EXPECTATION_FAILED)
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Exit) as exc_info:
            task_status(fake.word())
        assert exc_info.value.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_task")
    @patch("maws.commands.ecs.console")
    def test_task_status_not_found(self, mock_console, mock_get_task, mock_get_settings, fake):
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.NOT_FOUND)
        mock_get_settings.return_value.api_client = Mock()

        with pytest.raises(typer.Abort):
            task_status(fake.word())


class TestTaskCommandsCLI:

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.get_task")
    def test_tasks_deploy_success_exits_0(self, mock_get_task, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.CREATED)
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.OK)
        mock_get_settings.return_value.api_client = Mock()
        profile = fake.word()

        result = CliRunner().invoke(app, ["tasks", "deploy", fake.word(), fake.uuid4(), "--profile", profile])

        assert result.exit_code == 0
        mock_patch_task.sync_detailed.assert_called_once()
        mock_get_settings.assert_called_with(profile)

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.get_task")
    def test_tasks_deploy_then_failed_exits_1(self, mock_get_task, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.CREATED)
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.EXPECTATION_FAILED)
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["tasks", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    def test_tasks_deploy_rejected_exits_1(self, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.return_value = Mock(
            status_code=HTTPStatus.BAD_REQUEST, content=json.dumps({"message": fake.sentence()})
        )
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["tasks", "deploy", fake.word(), fake.uuid4()])

        assert result.exit_code == 1

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.get_task")
    def test_tasks_deploy_cli_passes_schedule_and_force(self, mock_get_task, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.CREATED)
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.OK)
        mock_get_settings.return_value.api_client = Mock()
        image = fake.uuid4()

        result = CliRunner().invoke(
            app, ["tasks", "deploy", fake.word(), image, "--schedule-expression", "rate(1 hour)", "--force"]
        )

        assert result.exit_code == 0
        body = mock_patch_task.sync_detailed.call_args.kwargs["body"]
        assert body.to_dict() == {"image": image, "schedule_expression": "rate(1 hour)", "force": True}

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.patch_task")
    @patch("maws.commands.ecs.get_task")
    def test_tasks_deploy_without_schedule_expression(self, mock_get_task, mock_patch_task, mock_get_settings, fake):
        mock_patch_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.CREATED)
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.OK)
        mock_get_settings.return_value.api_client = Mock()
        image = fake.uuid4()

        result = CliRunner().invoke(app, ["tasks", "deploy", fake.word(), image])

        assert result.exit_code == 0
        body = mock_patch_task.sync_detailed.call_args.kwargs["body"]
        assert body.to_dict() == {"image": image, "force": False}
        assert "schedule_expression" not in body.to_dict()

    @patch("maws.commands.ecs.get_settings")
    @patch("maws.commands.ecs.get_task")
    def test_tasks_status_cli(self, mock_get_task, mock_get_settings, fake):
        mock_get_task.sync_detailed.return_value = Mock(status_code=HTTPStatus.OK)
        mock_get_settings.return_value.api_client = Mock()

        result = CliRunner().invoke(app, ["tasks", "status", fake.word(), "--delay", "1"])

        assert result.exit_code == 0
        mock_get_task.sync_detailed.assert_called_once()

    def test_top_level_status_removed(self, fake):
        assert CliRunner().invoke(app, ["status", fake.word()]).exit_code == 78


class TestDeprecatedStatusCommand:

    @pytest.mark.parametrize(
        "extra_args",
        [
            [],
            ["--help"],
            ["--profile", "dev"],
            ["--delay", "1", "--profile", "prod"],
        ],
    )
    @patch("maws.commands.ecs.get_service")
    @patch("maws.commands.ecs.get_task")
    def test_old_status_prints_hint_and_exits_78(self, mock_get_task, mock_get_service, extra_args, fake):
        result = CliRunner().invoke(app, ["status", fake.word(), *extra_args])

        assert result.exit_code == 78
        assert "maws ecs services status" in result.output
        assert "maws ecs tasks status" in result.output
        mock_get_service.sync_detailed.assert_not_called()
        mock_get_task.sync_detailed.assert_not_called()

    def test_old_status_without_args_exits_78(self):
        assert CliRunner().invoke(app, ["status"]).exit_code == 78

    def test_old_status_hidden_from_help(self):
        result = CliRunner().invoke(app, ["--help"])
        assert "status" not in result.output


class TestDeprecatedDeployCommand:

    @pytest.mark.parametrize(
        "extra_args",
        [
            [],
            ["--help"],
            ["--profile", "dev"],
            ["--force", "--secret-arns", "arn:aws:secretsmanager:eu-central-1:123456789012:secret:x"],
        ],
    )
    @patch("maws.commands.ecs.patch_service")
    @patch("maws.commands.ecs.patch_task")
    def test_old_deploy_prints_hint_and_exits_78(self, mock_patch_task, mock_patch_service, extra_args, fake):
        result = CliRunner().invoke(app, ["deploy", fake.word(), fake.uuid4(), *extra_args])

        assert result.exit_code == 78
        assert "maws ecs services deploy" in result.output
        assert "maws ecs tasks deploy" in result.output
        mock_patch_service.sync_detailed.assert_not_called()
        mock_patch_task.sync_detailed.assert_not_called()

    def test_old_deploy_without_args_exits_78(self):
        assert CliRunner().invoke(app, ["deploy"]).exit_code == 78

    def test_old_deploy_hidden_from_help(self):
        result = CliRunner().invoke(app, ["--help"])
        assert "deploy" not in result.output
