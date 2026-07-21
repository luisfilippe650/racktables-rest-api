from unittest.mock import Mock

from app.utils.database_resources import close_database_resources


def test_close_database_resources_closes_cursor_before_connection():
    calls = []
    cursor = Mock()
    database = Mock()
    cursor.close.side_effect = lambda: calls.append("cursor")
    database.close.side_effect = lambda: calls.append("database")

    close_database_resources(database, cursor)

    assert calls == ["cursor", "database"]


def test_close_database_resources_closes_connection_when_cursor_close_fails():
    cursor = Mock()
    cursor.close.side_effect = RuntimeError("cursor close failed")
    database = Mock()
    logger = Mock()

    close_database_resources(database, cursor, logger)

    database.close.assert_called_once_with()
    logger.exception.assert_called_once_with("Failed to close database cursor")


def test_close_database_resources_handles_connection_close_failure():
    cursor = Mock()
    database = Mock()
    database.close.side_effect = RuntimeError("connection close failed")
    logger = Mock()

    close_database_resources(database, cursor, logger)

    cursor.close.assert_called_once_with()
    logger.exception.assert_called_once_with("Failed to close database connection")


def test_close_database_resources_accepts_missing_resources():
    close_database_resources()
