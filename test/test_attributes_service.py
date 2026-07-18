from unittest.mock import Mock

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
    monkeypatch.setattr(attributes_service, "connect", Mock(return_value=database))
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
