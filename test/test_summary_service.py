from unittest.mock import Mock

from app.service.objects import summary_service


def test_get_summary_closes_disconnected_database(monkeypatch):
    cursor = Mock()
    database = Mock()
    database.cursor.return_value = cursor
    database.is_connected.return_value = False

    monkeypatch.setattr(summary_service, "connect_with_cursor", Mock(return_value=(database, cursor)))
    monkeypatch.setattr(summary_service, "get_object_attributes", Mock(side_effect=RuntimeError("lost connection")))

    response = summary_service.get_object_summary_service(44)

    assert response.status_code == 500
    cursor.close.assert_called_once_with()
    database.close.assert_called_once_with()


def test_get_summary_preserves_response_when_cursor_close_fails(monkeypatch):
    cursor = Mock()
    cursor.close.side_effect = RuntimeError("cursor already closed")
    database = Mock()
    database.cursor.return_value = cursor

    monkeypatch.setattr(summary_service, "connect_with_cursor", Mock(return_value=(database, cursor)))
    monkeypatch.setattr(summary_service, "get_object_attributes", Mock(return_value=None))

    response = summary_service.get_object_summary_service(44)

    assert response.status_code == 404
    database.close.assert_called_once_with()


def test_get_summary_uses_utc_for_date_conversion(monkeypatch):
    cursor = Mock()
    database = Mock()
    database.cursor.return_value = cursor

    monkeypatch.setattr(summary_service, "connect_with_cursor", Mock(return_value=(database, cursor)))
    get_attributes = Mock(return_value={"object_id": 44, "attributes": {}})
    monkeypatch.setattr(summary_service, "get_object_attributes", get_attributes)

    response = summary_service.get_object_summary_service(44)

    assert response.status_code == 200
    cursor.execute.assert_called_once_with("SET SESSION time_zone = '+00:00'")
    get_attributes.assert_called_once_with(cursor, 44, include_options=False)
