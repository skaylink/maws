import json
from unittest.mock import Mock

import pytest
from faker import Faker


@pytest.fixture
def fake():
    return Faker()


@pytest.fixture
def mock_env_vars(fake):
    return {
        "API_BASE_URL": fake.url(),
        "API_VERSION": fake.word(),
        "API_ACCESS_TOKEN": fake.uuid4(),
    }


@pytest.fixture
def mock_authenticated_client():
    return Mock()


@pytest.fixture
def mock_response(fake):
    response = Mock()
    response.status_code = 200
    response.content = json.dumps({"status": "SUCCESSFUL", "message": fake.sentence()})
    response.parsed = Mock()
    response.parsed.status = "SUCCESSFUL"
    return response


@pytest.fixture
def mock_console():
    return Mock()
