from app.service.rackspace.racks_service import _build_rack_layout_units


def test_build_rack_layout_units_marks_free_and_occupied_units():
    allocated_objects = [
        {
            "object_id": 815,
            "object_name": "Server A",
            "service_tag": "ST-815",
            "units": [3, 2],
            "height": 2,
            "allocation_status": "valid",
        }
    ]

    result = _build_rack_layout_units(
        total_units=4,
        occupied_units=[3, 2],
        allocated_objects=allocated_objects,
    )

    assert [unit["unit_no"] for unit in result] == [4, 3, 2, 1]
    assert [unit["status"] for unit in result] == ["free", "occupied", "occupied", "free"]
    assert result[1]["object"]["object_id"] == 815
    assert result[1]["object"]["units"] == [3, 2]
    assert result[2]["object"]["object_name"] == "Server A"
