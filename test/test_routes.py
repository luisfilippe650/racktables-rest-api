from unittest.mock import Mock

from fastapi.responses import JSONResponse


API_PREFIX = "/v1/racktables"


def ok_data(name="ok"):
    return {
        "status": "success",
        "message": "mocked",
        "data": {"route": name},
    }


def assert_success_response(response, route_name):
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["route"] == route_name


def test_health_route_success(client, monkeypatch):
    import app.utils.status_code as status_router

    db = Mock()
    db.is_connected.return_value = True
    monkeypatch.setattr(status_router, "connect", Mock(return_value=db))

    response = client.get(f"{API_PREFIX}/status/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected", "API": "ok"}
    db.close.assert_called_once_with()


def test_health_route_database_unavailable(client, monkeypatch):
    import app.utils.status_code as status_router

    monkeypatch.setattr(status_router, "connect", Mock(return_value=None))

    response = client.get(f"{API_PREFIX}/status/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable", "API": "ok"}


def test_locations_routes(client, monkeypatch, mock_service):
    import app.routers.rackspace.locations_router as router

    create = mock_service(ok_data("create_location"))
    delete = mock_service(ok_data("delete_location"))
    list_locations = mock_service(ok_data("list_locations"))
    by_name = mock_service(ok_data("get_location_by_name"))
    with_rows = mock_service(ok_data("list_locations_with_rows"))

    monkeypatch.setattr(router, "create_location_service", create)
    monkeypatch.setattr(router, "delete_location_service", delete)
    monkeypatch.setattr(router, "list_locations_service", list_locations)
    monkeypatch.setattr(router, "get_location_by_name_service", by_name)
    monkeypatch.setattr(router, "list_complete_location_service", with_rows)

    response = client.post(f"{API_PREFIX}/locations/", json={"name": "Lab A"})
    assert_success_response(response, "create_location")
    assert create.call_args.args[0].name == "Lab A"

    response = client.delete(f"{API_PREFIX}/locations/10")
    assert_success_response(response, "delete_location")
    delete.assert_called_once_with(10)

    response = client.get(f"{API_PREFIX}/locations/?page=2&per_page=25")
    assert_success_response(response, "list_locations")
    list_locations.assert_called_once_with(2, 25)

    response = client.get(f"{API_PREFIX}/locations/by-name?name=Lab%20A")
    assert_success_response(response, "get_location_by_name")
    by_name.assert_called_once_with("Lab A")

    response = client.get(f"{API_PREFIX}/locations/rows?page=3&per_page=20")
    assert_success_response(response, "list_locations_with_rows")
    with_rows.assert_called_once_with(3, 20)


def test_rows_routes(client, monkeypatch, mock_service):
    import app.routers.rackspace.rows_router as router

    create = mock_service(ok_data("create_row"))
    list_rows = mock_service(ok_data("list_rows"))
    with_racks = mock_service(ok_data("list_rows_with_racks"))
    by_name = mock_service(ok_data("get_row_by_name"))
    delete = mock_service(ok_data("delete_row"))
    update = mock_service(ok_data("update_row"))
    add_location = mock_service(ok_data("add_location_to_row"))
    remove_location = mock_service(ok_data("remove_location_from_row"))

    monkeypatch.setattr(router, "create_row_service", create)
    monkeypatch.setattr(router, "list_row_service", list_rows)
    monkeypatch.setattr(router, "list_complete_rows_service", with_racks)
    monkeypatch.setattr(router, "get_row_by_name_service", by_name)
    monkeypatch.setattr(router, "delete_row_service", delete)
    monkeypatch.setattr(router, "update_row_name_service", update)
    monkeypatch.setattr(router, "add_location_to_row_service", add_location)
    monkeypatch.setattr(router, "remove_location_from_row_service", remove_location)

    response = client.post(f"{API_PREFIX}/rows/", json={"name": "Row A"})
    assert_success_response(response, "create_row")
    assert create.call_args.args[0].name == "Row A"

    response = client.get(f"{API_PREFIX}/rows/?page=2&per_page=30")
    assert_success_response(response, "list_rows")
    list_rows.assert_called_once_with(2, 30)

    response = client.get(f"{API_PREFIX}/rows/racks?page=4&per_page=15")
    assert_success_response(response, "list_rows_with_racks")
    with_racks.assert_called_once_with(4, 15)

    response = client.get(f"{API_PREFIX}/rows/by-name?name=Row%20A")
    assert_success_response(response, "get_row_by_name")
    by_name.assert_called_once_with("Row A")

    response = client.delete(f"{API_PREFIX}/rows/11")
    assert_success_response(response, "delete_row")
    delete.assert_called_once_with(11)

    response = client.patch(f"{API_PREFIX}/rows/11", json={"name": "Row B"})
    assert_success_response(response, "update_row")
    update.assert_called_once_with(11, "Row B")

    response = client.put(f"{API_PREFIX}/rows/11/22")
    assert_success_response(response, "add_location_to_row")
    add_location.assert_called_once_with(11, 22)

    response = client.delete(f"{API_PREFIX}/rows/11/22")
    assert_success_response(response, "remove_location_from_row")
    remove_location.assert_called_once_with(11, 22)


def test_racks_routes(client, monkeypatch, mock_service):
    import app.routers.rackspace.racks_router as router

    create = mock_service(ok_data("create_rack"))
    list_racks = mock_service(ok_data("list_racks"))
    update = mock_service(ok_data("update_rack"))
    by_name = mock_service(ok_data("get_rack_by_name"))
    occupancy_all = mock_service(ok_data("list_racks_occupancy"))
    occupancy_one = mock_service(ok_data("get_rack_occupancy"))
    details = mock_service(ok_data("get_rack_details"))
    delete = mock_service(ok_data("delete_rack"))

    monkeypatch.setattr(router, "create_rack_service", create)
    monkeypatch.setattr(router, "list_racks_service", list_racks)
    monkeypatch.setattr(router, "update_rack_name_service", update)
    monkeypatch.setattr(router, "get_rack_by_name_service", by_name)
    monkeypatch.setattr(router, "list_racks_with_space_service", occupancy_all)
    monkeypatch.setattr(router, "get_rack_occupancy_service", occupancy_one)
    monkeypatch.setattr(router, "get_rack_details_service", details)
    monkeypatch.setattr(router, "delete_rack_service", delete)

    response = client.post(
        f"{API_PREFIX}/racks/",
        json={"name": "Rack A", "rack_height": 42, "row_id": 11, "asset_no": "RACK-A"},
    )
    assert_success_response(response, "create_rack")
    rack_model = create.call_args.args[0]
    assert rack_model.name == "Rack A"
    assert rack_model.rack_height == 42
    assert rack_model.row_id == 11

    response = client.get(f"{API_PREFIX}/racks/?page=2&per_page=20")
    assert_success_response(response, "list_racks")
    list_racks.assert_called_once_with(2, 20)

    response = client.patch(f"{API_PREFIX}/racks/33", json={"name": "Rack B"})
    assert_success_response(response, "update_rack")
    update.assert_called_once_with(33, "Rack B")

    response = client.get(f"{API_PREFIX}/racks/by-name?name=Rack%20B")
    assert_success_response(response, "get_rack_by_name")
    by_name.assert_called_once_with("Rack B")

    response = client.get(f"{API_PREFIX}/racks/occupancy?page=3&per_page=10&include_objects=true")
    assert_success_response(response, "list_racks_occupancy")
    occupancy_all.assert_called_once_with(3, 10, True)

    response = client.get(f"{API_PREFIX}/racks/33/occupancy?include_objects=true")
    assert_success_response(response, "get_rack_occupancy")
    occupancy_one.assert_called_once_with(33, True)

    response = client.get(f"{API_PREFIX}/racks/33")
    assert_success_response(response, "get_rack_details")
    details.assert_called_once_with(33)

    response = client.delete(f"{API_PREFIX}/racks/33")
    assert_success_response(response, "delete_rack")
    delete.assert_called_once_with(33)


def test_objects_routes(client, monkeypatch, mock_service):
    import app.routers.objects.objects_router as router

    create = mock_service(ok_data("create_object"))
    delete = mock_service(ok_data("delete_object"))
    update = mock_service(ok_data("update_object"))
    list_objects = mock_service(ok_data("list_objects"))
    list_all = mock_service(ok_data("list_all_objects"))
    by_name = mock_service(ok_data("get_object_by_name"))
    by_service_tag = mock_service(ok_data("get_object_by_service_tag"))
    types = mock_service(ok_data("list_object_types"))

    monkeypatch.setattr(router, "create_object_service", create)
    monkeypatch.setattr(router, "delete_object_service", delete)
    monkeypatch.setattr(router, "update_object_service", update)
    monkeypatch.setattr(router, "list_objects_service", list_objects)
    monkeypatch.setattr(router, "list_all_objects_service", list_all)
    monkeypatch.setattr(router, "get_object_by_name_service", by_name)
    monkeypatch.setattr(router, "get_object_by_service_tag_service", by_service_tag)
    monkeypatch.setattr(router, "list_object_types_service", types)

    response = client.post(
        f"{API_PREFIX}/objects/",
        json={"name": "Server A", "label": "srv-a", "asset_no": "ST-1", "comment": "note", "objtype_id": 4},
    )
    assert_success_response(response, "create_object")
    object_model = create.call_args.args[0]
    assert object_model.name == "Server A"
    assert object_model.objtype_id == 4

    response = client.delete(f"{API_PREFIX}/objects/44")
    assert_success_response(response, "delete_object")
    delete.assert_called_once_with(44)

    response = client.patch(f"{API_PREFIX}/objects/44", json={"name": "Server B", "comment": "updated"})
    assert_success_response(response, "update_object")
    args = update.call_args.args
    assert args[0] == 44
    assert args[1] == "Server B"
    assert args[2] == "updated"
    assert args[3] == {"name", "comment"}

    response = client.get(f"{API_PREFIX}/objects/?page=2&per_page=25")
    assert_success_response(response, "list_objects")
    list_objects.assert_called_once_with(2, 25)

    response = client.get(f"{API_PREFIX}/objects/all?page=3&per_page=15")
    assert_success_response(response, "list_all_objects")
    list_all.assert_called_once_with(3, 15)

    response = client.get(f"{API_PREFIX}/objects/by-name?name=Server%20B")
    assert_success_response(response, "get_object_by_name")
    by_name.assert_called_once_with("Server B")

    response = client.get(f"{API_PREFIX}/objects/by-service-tag?service_tag=ST-1")
    assert_success_response(response, "get_object_by_service_tag")
    by_service_tag.assert_called_once_with("ST-1")

    response = client.get(f"{API_PREFIX}/objects/types?page=1&per_page=10")
    assert_success_response(response, "list_object_types")
    types.assert_called_once_with(1, 10)


def test_summary_routes(client, monkeypatch, mock_service):
    import app.routers.objects.summary_router as router

    get_summary = mock_service(ok_data("get_summary"))
    patch_summary = mock_service(ok_data("patch_summary"))

    monkeypatch.setattr(router, "get_object_summary_service", get_summary)
    monkeypatch.setattr(router, "update_object_attributes_service", patch_summary)

    response = client.get(f"{API_PREFIX}/summary/815")
    assert_success_response(response, "get_summary")
    get_summary.assert_called_once_with(815)

    response = client.patch(
        f"{API_PREFIX}/summary/815",
        json={"name": "Server B", "has_problems": False, "Serial number": "ABC"},
    )
    assert_success_response(response, "patch_summary")
    patch_summary.assert_called_once_with(
        815,
        {"name": "Server B", "has_problems": False, "Serial number": "ABC"},
    )


def test_dictionary_route(client, monkeypatch, mock_service):
    import app.routers.objects.dictionary_router as router

    dictionary = mock_service(ok_data("dictionary"))
    monkeypatch.setattr(router, "get_dictionary", dictionary)

    response = client.get(f"{API_PREFIX}/dictionary/11?page=2&per_page=30")

    assert_success_response(response, "dictionary")
    dictionary.assert_called_once_with(11, 2, 30)


def test_mount_routes(client, monkeypatch, mock_service):
    import app.routers.objects.mount_unmount_router as router

    mount = mock_service(ok_data("mount"))
    unmount = mock_service(ok_data("unmount"))

    monkeypatch.setattr(router, "mount_server_service", mount)
    monkeypatch.setattr(router, "unmount_server_service", unmount)

    response = client.post(
        f"{API_PREFIX}/mount/",
        json={"rack_id": 33, "object_id": 815, "start_unit": 10, "height": 2},
    )
    assert_success_response(response, "mount")
    mount_model = mount.call_args.args[0]
    assert mount_model.rack_id == 33
    assert mount_model.object_id == 815
    assert mount_model.start_unit == 10
    assert mount_model.height == 2

    response = client.delete(f"{API_PREFIX}/mount/815")
    assert_success_response(response, "unmount")
    unmount.assert_called_once_with(815)


def test_move_route(client, monkeypatch, mock_service):
    import app.routers.objects.move_router as router

    move = mock_service(ok_data("move"))
    monkeypatch.setattr(router, "move_server_to_another_rack_service", move)

    response = client.post(
        f"{API_PREFIX}/move/",
        json={
            "object_id": 815,
            "source_rack_id": 33,
            "destination_rack_id": 34,
            "start_unit": 20,
            "height": 2,
        },
    )

    assert_success_response(response, "move")
    move_model = move.call_args.args[0]
    assert move_model.object_id == 815
    assert move_model.source_rack_id == 33
    assert move_model.destination_rack_id == 34
    assert move_model.start_unit == 20
    assert move_model.height == 2


def test_basic_validation_errors_are_returned_by_fastapi(client):
    invalid_requests = [
        ("post", f"{API_PREFIX}/locations/", {"name": "   "}),
        ("post", f"{API_PREFIX}/rows/", {"name": "   "}),
        ("post", f"{API_PREFIX}/racks/", {"name": "Rack", "rack_height": 0, "row_id": 1}),
        ("post", f"{API_PREFIX}/objects/", {"name": "Server", "objtype_id": 0}),
        ("post", f"{API_PREFIX}/mount/", {"rack_id": 0, "object_id": 1, "start_unit": 1, "height": 1}),
        ("post", f"{API_PREFIX}/move/", {"object_id": 1, "destination_rack_id": 0, "start_unit": 1}),
    ]

    for method, url, payload in invalid_requests:
        response = getattr(client, method)(url, json=payload)
        assert response.status_code == 422


def test_router_can_return_jsonresponse_from_service(client, monkeypatch):
    import app.routers.objects.summary_router as router

    service = Mock(return_value=JSONResponse(content={"status": "custom"}, status_code=202))
    monkeypatch.setattr(router, "get_object_summary_service", service)

    response = client.get(f"{API_PREFIX}/summary/815")

    assert response.status_code == 202
    assert response.json() == {"status": "custom"}
