from unittest.mock import Mock

from app.service.objects import objects_service


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

    def close(self):
        self.closed = True


def setup_delete_mocks(monkeypatch, database, current_mount=None, port_links=None):
    monkeypatch.setattr(objects_service, "connect", Mock(return_value=database))
    monkeypatch.setattr(objects_service, "acquire_named_locks", Mock(return_value=(True, None)))
    monkeypatch.setattr(objects_service, "release_named_locks", Mock())
    monkeypatch.setattr(objects_service, "get_object_basic_info", Mock(return_value={"objtype_id": 4}))
    monkeypatch.setattr(objects_service, "object_has_current_mount", Mock(return_value=current_mount))
    monkeypatch.setattr(objects_service, "get_current_mount_details", Mock(return_value=[
        {"rack_id": 10, "rack_name": "Rack A", "start_unit": 1, "end_unit": 2, "height": 2}
    ]))
    monkeypatch.setattr(objects_service, "object_has_port_links", Mock(return_value=port_links))
    monkeypatch.setattr(objects_service, "get_object_port_links", Mock(return_value=[
        {
            "local_port_id": 1,
            "local_port_name": "eth0",
            "remote_port_id": 2,
            "remote_port_name": "Gi1/0/1",
            "remote_object_id": 20,
            "remote_object_name": "Switch A",
            "cable": "CAB-1",
        }
    ]))
    monkeypatch.setattr(objects_service, "delete_file_links", Mock())
    monkeypatch.setattr(objects_service, "delete_tags", Mock())
    monkeypatch.setattr(objects_service, "delete_network_data", Mock())
    monkeypatch.setattr(objects_service, "delete_entity_links", Mock())
    monkeypatch.setattr(objects_service, "delete_mount_data", Mock())
    monkeypatch.setattr(objects_service, "delete_port_data", Mock())
    monkeypatch.setattr(objects_service, "delete_attribute_values", Mock())
    monkeypatch.setattr(objects_service, "insert_history_record", Mock())
    monkeypatch.setattr(objects_service, "anonymize_object_before_delete", Mock())
    monkeypatch.setattr(objects_service, "delete_object_row", Mock())


def test_delete_object_blocks_when_object_is_currently_mounted(monkeypatch):
    database = FakeDatabase()
    setup_delete_mocks(monkeypatch, database, current_mount={"exists": 1}, port_links=None)

    response = objects_service.delete_object_service(815)

    assert response.status_code == 409
    body = response.body.decode()
    assert "currently mounted in a rack" in body
    assert "current_rack_allocation" in body
    assert "Rack A" in body
    objects_service.delete_mount_data.assert_not_called()
    objects_service.delete_object_row.assert_not_called()
    assert database.rolled_back is True
    assert database.committed is False


def test_delete_object_allows_mount_history_when_not_currently_mounted(monkeypatch):
    database = FakeDatabase()
    setup_delete_mocks(monkeypatch, database, current_mount=None, port_links=None)

    response = objects_service.delete_object_service(759)

    assert response.status_code == 200
    objects_service.object_has_current_mount.assert_called_once_with(database.cursor_instance, 759)
    objects_service.delete_mount_data.assert_called_once_with(database.cursor_instance, 759)
    objects_service.delete_object_row.assert_called_once_with(database.cursor_instance, 759)
    assert database.committed is True
    assert database.rolled_back is False


def test_delete_object_reports_physical_link_details(monkeypatch):
    database = FakeDatabase()
    setup_delete_mocks(monkeypatch, database, current_mount=None, port_links={"exists": 1})

    response = objects_service.delete_object_service(815)

    assert response.status_code == 409
    body = response.body.decode()
    assert "physical links" in body
    assert "physical_port_links" in body
    assert "eth0" in body
    assert "Switch A" in body
    objects_service.delete_mount_data.assert_not_called()
    objects_service.delete_object_row.assert_not_called()
    assert database.rolled_back is True
    assert database.committed is False


def test_list_object_types_uses_repository_pagination(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(objects_service, "connect", Mock(return_value=database))
    monkeypatch.setattr(objects_service, "count_object_types_query", Mock(return_value=25))
    monkeypatch.setattr(objects_service, "list_object_types_query", Mock(return_value=[
        {"objtype_id": 4, "objtype_name": "Server"}
    ]))

    response = objects_service.list_object_types_service(page=3, per_page=10)

    assert response.status_code == 200
    objects_service.count_object_types_query.assert_called_once_with(
        database.cursor_instance,
        objects_service.ALLOWED_OBJTYPES,
    )
    objects_service.list_object_types_query.assert_called_once_with(
        database.cursor_instance,
        objects_service.ALLOWED_OBJTYPES,
        10,
        20,
    )
    body = response.body.decode()
    assert '"page":3' in body
    assert '"per_page":10' in body
    assert '"total":25' in body
