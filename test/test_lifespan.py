from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_application_does_not_start_when_pool_initialization_fails(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "initialize_pool", Mock(return_value=None))

    with pytest.raises(RuntimeError, match="Database connection pool could not be initialized"):
        with TestClient(app, backend="trio"):
            pass
