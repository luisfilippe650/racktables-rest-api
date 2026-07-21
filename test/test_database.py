from unittest.mock import Mock

from app.core import database as database_module


def test_connect_returns_disconnected_connection_to_pool(monkeypatch):
    connection = Mock()
    connection.is_connected.return_value = False
    pool = Mock()
    pool.get_connection.return_value = connection
    monkeypatch.setattr(database_module, "get_pool", Mock(return_value=pool))

    result = database_module.connect()

    assert result is None
    connection.close.assert_called_once_with()


def test_connect_returns_connected_connection(monkeypatch):
    connection = Mock()
    connection.is_connected.return_value = True
    pool = Mock()
    pool.get_connection.return_value = connection
    monkeypatch.setattr(database_module, "get_pool", Mock(return_value=pool))

    result = database_module.connect()

    assert result is connection
    connection.close.assert_not_called()


def test_connect_with_cursor_closes_connection_when_cursor_creation_fails(monkeypatch):
    connection = Mock()
    connection.cursor.side_effect = RuntimeError("cursor creation failed")
    monkeypatch.setattr(database_module, "connect", Mock(return_value=connection))

    database, cursor = database_module.connect_with_cursor()

    assert database is None
    assert cursor is None
    connection.close.assert_called_once_with()


def test_connect_with_cursor_returns_both_resources(monkeypatch):
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(database_module, "connect", Mock(return_value=connection))

    database, result_cursor = database_module.connect_with_cursor()

    assert database is connection
    assert result_cursor is cursor
    connection.cursor.assert_called_once_with(dictionary=True)
