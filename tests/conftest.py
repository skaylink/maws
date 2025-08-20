import json
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from faker import Faker


@pytest.fixture(scope="function")
def fake():
    return Faker()


@pytest.fixture(scope="function")
def mock_env_vars(fake):
    return {
        "API_BASE_URL": fake.url(),
        "API_VERSION": "v1",
        "API_ACCESS_TOKEN": fake.uuid4(),
    }


@pytest.fixture(scope="function")
def mock_response_failed(fake) -> callable:
    def make(error: str = fake.sentence()) -> Mock:
        response = Mock()
        response.status_code = HTTPStatus.EXPECTATION_FAILED
        response.content = json.dumps({"error": error})
        return response

    yield make


@pytest.fixture(scope="function")
def mock_post_deployment():
    return Mock()


@pytest.fixture(scope="function")
def mock_console():
    return Mock()


@pytest.fixture(scope="function")
def mock_authenticated_client():
    return Mock()
