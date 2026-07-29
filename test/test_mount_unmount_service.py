import json
from unittest.mock import Mock

from app.schema.objects.mount_unmount_schema import MountServer
from app.service.objects import mount_unmount_service
from app.utils.objtype import SERVER


class FakeDatabase:
    def __init__(self):
        self.cursor_instance = Mock()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def response_body(response):
    return json.loads(response.body)


def setup_common_mocks(monkeypatch, database):
    monkeypatch.setattr(
        mount_unmount_service,
        "connect_with_cursor",
        Mock(return_value=(database, database.cursor_instance)),
    )
    monkeypatch.setattr(mount_unmount_service, "acquire_named_locks", Mock(return_value=(True, None)))
    monkeypatch.setattr(mount_unmount_service, "release_named_locks", Mock())
    monkeypatch.setattr(mount_unmount_service, "get_object_basic_info", Mock(return_value={"objtype_id": SERVER}))


def test_mount_detects_allocation_changed_during_write(monkeypatch):
    database = FakeDatabase()
    setup_common_mocks(monkeypatch, database)
    monkeypatch.setattr(mount_unmount_service, "get_rack_by_id", Mock(return_value={"id": 33}))
    monkeypatch.setattr(mount_unmount_service, "get_mounted_object", Mock(return_value=None))
    monkeypatch.setattr(mount_unmount_service, "get_rack_height", Mock(return_value=42))
    monkeypatch.setattr(mount_unmount_service, "get_occupied_positions_in_range", Mock(return_value=[]))
    monkeypatch.setattr(mount_unmount_service, "replace_rackspace_position", Mock())
    monkeypatch.setattr(
        mount_unmount_service,
        "count_allocated_positions_for_object_in_range",
        Mock(return_value=5),
    )
    monkeypatch.setattr(mount_unmount_service, "clear_rack_thumbnail", Mock())
    monkeypatch.setattr(mount_unmount_service, "create_molecule", Mock())

    response = mount_unmount_service.mount_server_service(
        MountServer(rack_id=33, object_id=815, start_unit=10, height=2)
    )

    assert response.status_code == 409
    assert response_body(response)["message"] == "Rack allocation changed during mount"
    assert database.rolled_back is True
    assert database.committed is False
    mount_unmount_service.clear_rack_thumbnail.assert_not_called()
    mount_unmount_service.create_molecule.assert_not_called()


def test_unmount_detects_allocation_changed_during_delete(monkeypatch):
    database = FakeDatabase()
    setup_common_mocks(monkeypatch, database)
    occupied_spaces = [
        {"rack_id": 33, "unit_no": 9, "atom": "front"},
        {"rack_id": 33, "unit_no": 9, "atom": "interior"},
        {"rack_id": 33, "unit_no": 9, "atom": "rear"},
    ]
    monkeypatch.setattr(
        mount_unmount_service,
        "get_allocated_spaces_by_object_id",
        Mock(side_effect=[occupied_spaces, occupied_spaces]),
    )
    monkeypatch.setattr(mount_unmount_service, "delete_rackspace_position", Mock(return_value=0))
    monkeypatch.setattr(mount_unmount_service, "clear_rack_thumbnail", Mock())
    monkeypatch.setattr(mount_unmount_service, "create_molecule", Mock())

    response = mount_unmount_service.unmount_server_service(815)

    assert response.status_code == 409
    assert response_body(response)["message"] == "Object allocation changed during unmount"
    mount_unmount_service.delete_rackspace_position.assert_called_once_with(
        database.cursor_instance,
        33,
        9,
        "front",
        815,
    )
    assert database.rolled_back is True
    assert database.committed is False
    mount_unmount_service.clear_rack_thumbnail.assert_not_called()
    mount_unmount_service.create_molecule.assert_not_called()
