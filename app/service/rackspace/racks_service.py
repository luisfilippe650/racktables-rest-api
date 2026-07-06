import logging

from app.core.database import connect
from app.repository.common_repository import (
    get_object_basic_info,
    delete_file_links,
    delete_tags,
    delete_network_data,
    delete_entity_links,
    delete_mount_data,
    delete_port_data,
    delete_attribute_values,
    insert_history_record,
    update_object_name
)
from app.repository.rackspace.racks_repository import (
    get_row_by_id,
    insert_rack,
    insert_attribute,
    link_rack_to_row,
    get_rack_by_id,
    get_racks_by_name_query,
    check_rack_has_objects,
    check_rack_has_linked_objects,
    delete_rack_thumbnail,
    delete_rackspace_by_rack,
    anonymize_rack,
    delete_rack_object,
    list_racks_basic_info_query,
    list_racks_with_height,
    get_occupied_units_by_rack,
    get_occupied_units_by_rack_ids,
    get_allocated_objects_by_rack_ids,
    get_rack_details_query,
    get_rack_with_height,
    count_rack_name,
    count_racks_query,
)
from app.schema.rackspace.racks_schema import CreateRack
from app.utils.attribute_ids import HEIGHT, SW_FRONT_TYPE
from app.utils.objtype import RACK
from app.utils.responses import success_response, error_response
from app.utils.user_name import USER_NAME
from app.utils.concurrency import acquire_named_locks, build_lock_name, release_named_locks

logger = logging.getLogger(__name__)


def _group_allocated_objects(rows):
    grouped_by_rack = {}

    for row in rows:
        rack_id = row["rack_id"]
        object_id = row["object_id"]
        rack_objects = grouped_by_rack.setdefault(rack_id, {})
        allocated_object = rack_objects.setdefault(object_id, {
            "object_id": object_id,
            "object_name": row["object_name"],
            "service_tag": row["service_tag"],
            "units": []
        })
        allocated_object["units"].append(row["unit_no"])

    result = {}
    for rack_id, rack_objects in grouped_by_rack.items():
        result[rack_id] = []
        for allocated_object in rack_objects.values():
            allocated_object["units"] = sorted(set(allocated_object["units"]), reverse=True)
            allocated_object["height"] = len(allocated_object["units"])
            ascending_units = sorted(allocated_object["units"])
            if not ascending_units:
                allocated_object["allocation_status"] = "inconsistent_empty_allocation"
            elif ascending_units == list(range(ascending_units[0], ascending_units[-1] + 1)):
                allocated_object["allocation_status"] = "valid"
            else:
                allocated_object["allocation_status"] = "inconsistent_non_contiguous"
            result[rack_id].append(allocated_object)

    return result


def _occupied_units_from_allocated_objects(allocated_objects):
    occupied_units = set()
    for allocated_object in allocated_objects:
        occupied_units.update(allocated_object["units"])
    return sorted(occupied_units, reverse=True)


def create_rack_service(data: CreateRack):
    database = connect()

    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("rack-name", data.name),
            build_lock_name("row-id", data.row_id),
        ]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        # check if the row exists
        row_exists = get_row_by_id(cursor, data.row_id)

        if not row_exists:
            database.rollback()
            return error_response("Row not found", status_code=404)

        name_exists = count_rack_name(cursor, data.name)
        if name_exists > 0:
            database.rollback()
            return error_response(f"There is already a rack with the name '{data.name}'", status_code=400)

        # insert rack as an object
        rack_id = insert_rack(
            cursor,
            data.name,
            RACK,
            data.asset_no
        )

        # insert history record
        insert_history_record(cursor, USER_NAME, rack_id)

        # rack height attribute
        insert_attribute(cursor, data.rack_height, rack_id, RACK, HEIGHT)

        # sort/guidance attribute (default to 1 as per legacy code)
        insert_attribute(cursor, 1, rack_id, RACK, SW_FRONT_TYPE)

        # link rack to row
        link_rack_to_row(cursor, data.row_id, rack_id)

        database.commit()

        return success_response(
            message="Rack created successfully",
            data={
                "rack_id": rack_id,
                "name": data.name
            },
            status_code=201
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during rack creation")
        return error_response("An unexpected error occurred during rack creation", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()


def delete_rack_service(rack_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("rack-id", rack_id)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        # check if rack exists
        rack = get_rack_by_id(cursor, rack_id)
        if not rack:
            database.rollback()
            return error_response("Rack not found", status_code=404)

        # check if rack has allocated objects
        has_objects = check_rack_has_objects(cursor, rack_id)
        if has_objects:
            database.rollback()
            return error_response("Rack has allocated objects", status_code=409)

        has_linked_objects = check_rack_has_linked_objects(cursor, rack_id)
        if has_linked_objects:
            database.rollback()
            return error_response("Rack has linked objects and cannot be deleted", status_code=409)

        # cleanup specific to rack realm
        delete_file_links(cursor, rack_id, entity_type='rack')
        delete_tags(cursor, rack_id, entity_realm='rack')
        delete_rack_thumbnail(cursor, rack_id)
        delete_rackspace_by_rack(cursor, rack_id)

        # generic object cleanup
        delete_file_links(cursor, rack_id, entity_type='object')
        delete_tags(cursor, rack_id, entity_realm='object')
        delete_network_data(cursor, rack_id)
        delete_entity_links(cursor, rack_id, entity_type='object')
        delete_mount_data(cursor, rack_id)
        delete_port_data(cursor, rack_id)
        delete_attribute_values(cursor, rack_id)

        # pattern observed in RackTables
        insert_history_record(cursor, USER_NAME, rack_id)
        anonymize_rack(cursor, rack_id)
        delete_rack_object(cursor, rack_id)
        
        # Final cleanup for entity links (rack realm)
        delete_entity_links(cursor, rack_id, entity_type='rack')

        database.commit()

        return success_response(
            message="Rack deleted successfully",
            data={
                "rack_id": rack_id
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during rack deletion")
        return error_response("An unexpected error occurred during rack deletion", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()


def list_racks_service(page: int = 1, per_page: int = 50):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        offset = (page - 1) * per_page
        total = count_racks_query(cursor)

        # list racks with basic info (height, row)
        racks = list_racks_basic_info_query(cursor, per_page, offset)
        return success_response(
            data={
                "items": racks,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(racks)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing racks")
        return error_response("An unexpected error occurred while listing racks", status_code=500)

    finally:
        cursor.close()
        database.close()


def list_racks_with_space_service(page: int = 1, per_page: int = 50, include_objects: bool = False):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        offset = (page - 1) * per_page
        total = count_racks_query(cursor)

        # get racks with height info
        racks = list_racks_with_height(cursor, per_page, offset)
        rack_ids = [rack["rack_id"] for rack in racks]
        allocated_objects_by_rack = {}
        if include_objects:
            allocated_rows = get_allocated_objects_by_rack_ids(cursor, rack_ids)
            allocated_objects_by_rack = _group_allocated_objects(allocated_rows)
        else:
            occupied_rows = get_occupied_units_by_rack_ids(cursor, rack_ids)
            occupied_by_rack = {}
            for row in occupied_rows:
                occupied_by_rack.setdefault(row["rack_id"], set()).add(row["unit_no"])

        result = []

        for rack in racks:
            rack_id = rack["rack_id"]
            total_units = rack["total_units"] or 0

            if include_objects:
                allocated_objects = allocated_objects_by_rack.get(rack_id, [])
                occupied_units = _occupied_units_from_allocated_objects(allocated_objects)
            else:
                occupied_units = sorted(occupied_by_rack.get(rack_id, set()), reverse=True)

            # calculate free units
            all_units = set(range(1, total_units + 1))
            free_units = sorted(list(all_units - set(occupied_units)), reverse=True)

            rack_result = {
                "rack_id": rack_id,
                "rack_name": rack["rack_name"],
                "total_units": total_units,
                "occupied_units": occupied_units,
                "free_units": free_units
            }
            if include_objects:
                rack_result["allocated_objects"] = allocated_objects

            result.append(rack_result)

        return success_response(
            data={
                "items": result,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(result)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing racks with space")
        return error_response("An unexpected error occurred while listing racks with space", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_rack_by_name_service(name: str):
    database = connect()
    if not database:
        return error_response("Internal server error", status_code=500)

    cursor = database.cursor(dictionary=True)

    try:
        cleaned_name = name.strip()
        if not cleaned_name:
            return error_response("Rack name cannot be empty", status_code=400)

        result = get_racks_by_name_query(cursor, cleaned_name)
        if not result:
            return error_response("Rack not found", status_code=404)
        if len(result) > 1:
            return error_response("Multiple racks found with this name", status_code=409)

        return success_response(data=result[0])

    except Exception as e:
        logger.exception("Unexpected error while searching rack by name")
        return error_response("Internal server error", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_rack_occupancy_service(rack_id: int, include_objects: bool = False):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        # validate rack existence
        rack_exists = get_rack_by_id(cursor, rack_id)
        if not rack_exists:
            return error_response("Rack not found", status_code=404)

        # get rack with height info
        rack = get_rack_with_height(cursor, rack_id)
        if not rack:
            return error_response("It wasn't possible to get the data from the rack", status_code=500)

        total_units = rack["total_units"] or 0

        allocated_objects = []
        if include_objects:
            allocated_rows = get_allocated_objects_by_rack_ids(cursor, [rack_id])
            allocated_objects_by_rack = _group_allocated_objects(allocated_rows)
            allocated_objects = allocated_objects_by_rack.get(rack_id, [])
            occupied_units = _occupied_units_from_allocated_objects(allocated_objects)
        else:
            occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
            occupied_units = sorted(
                [row["unit_no"] for row in occupied_rows],
                reverse=True
            )

        # calculate free units
        all_units = set(range(1, total_units + 1))
        free_units = sorted(list(all_units - set(occupied_units)), reverse=True)

        data = {
            "rack_id": rack["rack_id"],
            "rack_name": rack["rack_name"],
            "total_units": total_units,
            "occupied_units": occupied_units,
            "free_units": free_units
        }
        if include_objects:
            data["allocated_objects"] = allocated_objects

        return success_response(
            data=data
        )

    except Exception as e:
        logger.exception("Unexpected error while getting rack occupancy")
        return error_response("An unexpected error occurred while getting rack occupancy", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_rack_details_service(rack_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        # get basic object info
        obj = get_object_basic_info(cursor, rack_id)

        if not obj:
            return error_response("Rack not found", status_code=404)

        # validate that object is a rack
        if obj["objtype_id"] != RACK:
            return error_response("The ID entered does not belong to a rack", status_code=400, detail=f"Object type ID: {obj['objtype_id']}")

        # get detailed rack info
        result = get_rack_details_query(cursor, rack_id)
        return success_response(data=result)

    except Exception as e:
        logger.exception("Unexpected error while getting rack details")
        return error_response("An unexpected error occurred while getting rack details", status_code=500)

    finally:
        cursor.close()
        database.close()


def update_rack_name_service(rack_id: int, rack_name: str):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("rack-id", rack_id),
            build_lock_name("rack-name", rack_name),
        ]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        # check if rack exists
        rack_exists = get_rack_by_id(cursor, rack_id)
        if not rack_exists:
            database.rollback()
            return error_response("Rack not found", status_code=404)

        # check if name already exists
        name_exists = count_rack_name(cursor, rack_name, rack_id)
        if name_exists > 0:
            database.rollback()
            return error_response(f"There is already a rack with the name '{rack_name}'", status_code=400)

        # update rack name
        update_object_name(cursor, rack_id, rack_name)

        # insert history record
        insert_history_record(cursor, USER_NAME, rack_id)

        database.commit()

        return success_response(
            message="Rack name updated successfully",
            data={
                "rack_id": rack_id,
                "new_name": rack_name
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during rack update")
        return error_response("An unexpected error occurred during rack update", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()
