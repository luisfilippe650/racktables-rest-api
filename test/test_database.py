from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from app.core import database as database_module


def set_required_database_env(monkeypatch):
    monkeypatch.setenv("DB_HOST", "database")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_NAME", "racktables")


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


def test_database_config_includes_timeouts(monkeypatch):
    set_required_database_env(monkeypatch)
    monkeypatch.setenv("DB_POOL_SIZE", "12")
    monkeypatch.setenv("DB_CONNECTION_TIMEOUT", "6")
    monkeypatch.setenv("DB_READ_TIMEOUT", "16")
    monkeypatch.setenv("DB_WRITE_TIMEOUT", "17")

    config = database_module._get_required_db_config()

    assert config["pool_size"] == 12
    assert config["connection_timeout"] == 6
    assert config["read_timeout"] == 16
    assert config["write_timeout"] == 17


def test_database_config_rejects_non_positive_timeout(monkeypatch):
    set_required_database_env(monkeypatch)
    monkeypatch.setenv("DB_READ_TIMEOUT", "0")

    assert database_module._get_required_db_config() is None


def test_initialize_pool_is_thread_safe(monkeypatch):
    set_required_database_env(monkeypatch)
    pool = Mock()
    constructor = Mock(return_value=pool)
    monkeypatch.setattr(database_module, "_connection_pool", None)
    monkeypatch.setattr(database_module.pooling, "MySQLConnectionPool", constructor)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: database_module.initialize_pool(), range(32)))

    assert all(result is pool for result in results)
    constructor.assert_called_once_with(
        pool_name="racktables_pool",
        pool_size=10,
        pool_reset_session=True,
        host="database",
        user="user",
        password="password",
        database="racktables",
        port=3306,
        connection_timeout=5,
        read_timeout=15,
        write_timeout=15,
    )
