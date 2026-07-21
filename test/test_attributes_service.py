from unittest.mock import Mock
import json

from app.service.objects import attributes_service


class FakeDatabase:
    def __init__(self):
        self.cursor_instance = Mock()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, dictionary=True):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def is_connected(self):
        return not self.closed

    def close(self):
        self.closed = True


def test_storage_object_type_can_be_updated_from_summary(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(attributes_service, "connect_with_cursor", Mock(return_value=(database, database.cursor_instance)))
    monkeypatch.setattr(attributes_service, "acquire_named_locks", Mock(return_value=(True, None)))
    monkeypatch.setattr(attributes_service, "release_named_locks", Mock())
    monkeypatch.setattr(attributes_service, "get_object_basic_info", Mock(return_value={"objtype_id": 50022}))
    monkeypatch.setattr(attributes_service, "get_available_attributes", Mock(return_value=[]))
    monkeypatch.setattr(attributes_service, "count_object_name", Mock(return_value=0))
    monkeypatch.setattr(attributes_service, "update_fixed_object_fields", Mock())
    monkeypatch.setattr(attributes_service, "insert_history_record", Mock())

    response = attributes_service.update_object_attributes_service(592, {"name": "Storage A"})

    assert response.status_code == 200
    attributes_service.update_fixed_object_fields.assert_called_once_with(
        database.cursor_instance,
        592,
        {"name": "Storage A"},
    )
    assert database.committed is True
    assert database.rolled_back is False


def setup_update_mocks(monkeypatch, attributes):
    database = FakeDatabase()
    monkeypatch.setattr(attributes_service, "connect_with_cursor", Mock(return_value=(database, database.cursor_instance)))
    monkeypatch.setattr(attributes_service, "acquire_named_locks", Mock(return_value=(True, None)))
    monkeypatch.setattr(attributes_service, "release_named_locks", Mock())
    monkeypatch.setattr(attributes_service, "get_object_basic_info", Mock(return_value={"objtype_id": 4}))
    monkeypatch.setattr(attributes_service, "get_available_attributes", Mock(return_value=attributes))
    monkeypatch.setattr(attributes_service, "count_object_name", Mock(return_value=0))
    monkeypatch.setattr(attributes_service, "count_object_service_tag", Mock(return_value=0))
    monkeypatch.setattr(attributes_service, "update_fixed_object_fields", Mock())
    monkeypatch.setattr(attributes_service, "upsert_attribute_value", Mock())
    monkeypatch.setattr(attributes_service, "insert_history_record", Mock())
    return database


def response_body(response):
    return json.loads(response.body)


def test_summary_rejects_non_string_fixed_fields(monkeypatch):
    database = setup_update_mocks(monkeypatch, [])

    response = attributes_service.update_object_attributes_service(44, {"name": 123})

    assert response.status_code == 400
    assert response_body(response)["message"] == "Field 'name' must be a string"
    attributes_service.update_fixed_object_fields.assert_not_called()
    assert database.rolled_back is True


def test_summary_accepts_long_comment_as_text(monkeypatch):
    database = setup_update_mocks(monkeypatch, [])
    comment = "a" * 1000

    response = attributes_service.update_object_attributes_service(44, {"comment": comment})

    assert response.status_code == 200
    attributes_service.update_fixed_object_fields.assert_called_once_with(
        database.cursor_instance,
        44,
        {"comment": comment},
    )


def test_summary_rejects_structured_value_for_string_attribute(monkeypatch):
    database = setup_update_mocks(monkeypatch, [{
        "attr_id": 1,
        "attr_name": "Serial",
        "attr_type": "string",
        "chapter_id": None,
    }])

    response = attributes_service.update_object_attributes_service(
        44,
        {"Serial": {"clear": False}},
    )

    assert response.status_code == 400
    assert response_body(response)["message"] == "Attribute 'Serial' must be a string"
    attributes_service.upsert_attribute_value.assert_not_called()
    assert database.rolled_back is True


def test_summary_converts_dates_to_utc_timestamp(monkeypatch):
    database = setup_update_mocks(monkeypatch, [{
        "attr_id": 2,
        "attr_name": "Warranty date",
        "attr_type": "date",
        "chapter_id": None,
    }])

    response = attributes_service.update_object_attributes_service(
        44,
        {"Warranty date": "1970-01-01"},
    )

    assert response.status_code == 200
    attributes_service.upsert_attribute_value.assert_called_once_with(
        database.cursor_instance,
        44,
        4,
        2,
        0,
        "date",
    )
    assert all(
        call.args[0] != "SET SESSION time_zone = '+00:00'"
        for call in database.cursor_instance.execute.call_args_list
    )
