from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app


API_PREFIX = "/v1/racktables"


@pytest.fixture
def client(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "initialize_pool", Mock(return_value=Mock()))
    with TestClient(app, backend="trio") as test_client:
        yield test_client


def ok_data(name="ok"):
    return {
        "status": "success",
        "message": "mocked",
        "data": {"route": name},
    }


@pytest.fixture
def mock_service():
    def _mock(return_value=None):
        return Mock(return_value=return_value or ok_data())

    return _mock
