import json
from unittest.mock import Mock

from app.service.objects import dictionary_service


class FakeDatabase:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def response_body(response):
    return json.loads(response.body)


def test_get_dictionary_closes_resources_on_success(monkeypatch):
    database = FakeDatabase()
    cursor = Mock()
    monkeypatch.setattr(dictionary_service, "connect_with_cursor", Mock(return_value=(database, cursor)))
    monkeypatch.setattr(dictionary_service, "dictionary_chapter_exists", Mock(return_value=True))
    monkeypatch.setattr(dictionary_service, "count_dictionary_options_for_chapter", Mock(return_value=1))
    monkeypatch.setattr(
        dictionary_service,
        "get_dictionary_options_for_chapter",
        Mock(return_value=[{"id": 10, "name": "Server"}]),
    )

    response = dictionary_service.get_dictionary(11, page=1, per_page=50)

    assert response.status_code == 200
    cursor.close.assert_called_once_with()
    assert database.closed is True


def test_get_dictionary_closes_resources_on_repository_error(monkeypatch):
    database = FakeDatabase()
    cursor = Mock()
    monkeypatch.setattr(dictionary_service, "connect_with_cursor", Mock(return_value=(database, cursor)))
    monkeypatch.setattr(dictionary_service, "dictionary_chapter_exists", Mock(side_effect=RuntimeError("db error")))

    response = dictionary_service.get_dictionary(11, page=1, per_page=50)

    assert response.status_code == 500
    cursor.close.assert_called_once_with()
    assert database.closed is True


def test_get_dictionary_rejects_large_offset_before_opening_connection(monkeypatch):
    connect = Mock()
    monkeypatch.setattr(dictionary_service, "connect_with_cursor", connect)

    response = dictionary_service.get_dictionary(11, page=1002, per_page=100)

    assert response.status_code == 400
    assert response_body(response)["message"] == "Page offset is too large"
    connect.assert_not_called()
