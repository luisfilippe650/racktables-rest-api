import logging

from app.core.database import connect_with_cursor
from app.utils.database_resources import close_database_resources
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
from app.repository.rackspace.rows_repository import (
    insert_row,
    row_has_linked_racks,
    anonymize_row_before_delete,
    delete_row_object,
    list_rows_query,
    list_complete_rows_query,
    get_location_by_id,
    get_row_by_id,
    get_rows_by_name_query,
    check_location_row_link,
    insert_location_row_link,
    fix_null_location_link,
    count_row_name,
    delete_location_row_link,
    get_location_link_for_row,
    count_rows_query,
)
from app.schema.rackspace.rows_schema import AddRows
from app.utils.objtype import ROW, RACK
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.user_name import USER_NAME
from app.utils.concurrency import acquire_named_locks, build_lock_name, release_named_locks

logger = logging.getLogger(__name__)


def create_row_service(data: AddRows):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("row-name", data.name)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        exists_count = count_row_name(cursor, data.name)

        if exists_count > 0:
            database.rollback()
            return error_response(f"There is already a row with the name '{data.name}'", status_code=400)

        row_id = insert_row(cursor, data.name, ROW)
        insert_history_record(cursor, USER_NAME, row_id)

        database.commit()

        return success_response(
            message="Row created successfully",
            data={
                "row_id": row_id,
                "name": data.name
            },
            status_code=201
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during row creation")
        return error_response("An unexpected error occurred during row creation", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        close_database_resources(database, cursor, logger)


def delete_row_service(row_id: int):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("row-id", row_id)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        row_data = get_object_basic_info(cursor, row_id)

        if row_data is None:
            database.rollback()
            return error_response(f"Row with ID {row_id} not found", status_code=404)

        object_type = row_data['objtype_id']

        if object_type != ROW:
            database.rollback()
            return error_response(f"The ID {row_id} does not belong to a row", status_code=400)

        has_racks = row_has_linked_racks(cursor, row_id)
        if has_racks:
            database.rollback()
            return error_response(
                "Row cannot be deleted because it has linked racks",
                status_code=409,
                detail={
                    "reason": "row_has_linked_racks",
                    "action": "Move or delete all racks linked to this row before deleting it.",
                }
            )

        # Common object cleanup
        delete_file_links(cursor, row_id)
        delete_tags(cursor, row_id)
        delete_network_data(cursor, row_id)
        delete_entity_links(cursor, row_id, entity_type='object')
        delete_mount_data(cursor, row_id)
        delete_port_data(cursor, row_id)
        delete_attribute_values(cursor, row_id)

        # Row-specific cleanup (EntityLink uses 'row' as type)
        delete_entity_links(cursor, row_id, entity_type='row')

        insert_history_record(cursor, USER_NAME, row_id)
        anonymize_row_before_delete(cursor, row_id)
        delete_row_object(cursor, row_id)

        database.commit()

        return success_response(
            message="Row deleted successfully",
            data={
                "row_id": row_id
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during row deletion")
        return error_response("An unexpected error occurred during row deletion", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        close_database_resources(database, cursor, logger)


def list_row_service(page: int = 1, per_page: int = 50):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        offset = (page - 1) * per_page
        total = count_rows_query(cursor, ROW)
        rows = list_rows_query(cursor, ROW, per_page, offset)
        return paginated_response(rows, page, per_page, total)

    except Exception as e:
        logger.exception("Unexpected error while listing rows")
        return error_response("An unexpected error occurred while listing rows", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)


def list_complete_rows_service(page: int = 1, per_page: int = 50):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        offset = (page - 1) * per_page
        total = count_rows_query(cursor, ROW)
        rows = list_complete_rows_query(
            cursor,
            ROW,
            RACK,
            per_page,
            offset
        )
        return paginated_response(rows, page, per_page, total)

    except Exception as e:
        logger.exception("Unexpected error while listing complete rows")
        return error_response("An unexpected error occurred while listing complete rows", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)


def get_row_by_name_service(name: str):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error", status_code=500)


    try:
        cleaned_name = name.strip()
        if not cleaned_name:
            return error_response("Row name cannot be empty", status_code=400)

        result = get_rows_by_name_query(cursor, cleaned_name)
        if not result:
            return error_response("Row not found", status_code=404)
        if len(result) > 1:
            return error_response("Multiple rows found with this name", status_code=409)

        return success_response(data=result[0])

    except Exception as e:
        logger.exception("Unexpected error while searching row by name")
        return error_response("Internal server error", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)


def add_location_to_row_service(row_id: int, location_id: int):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("row-id", row_id),
            build_lock_name("location-id", location_id),
        ]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return error_response("Row not found", status_code=404)

        location_exists = get_location_by_id(cursor, location_id)
        if not location_exists:
            database.rollback()
            return error_response("Location not found", status_code=404)

        existing_location = get_location_link_for_row(cursor, row_id)
        if existing_location:
            current_location_id = existing_location["location_id"] if isinstance(existing_location, dict) else existing_location[0]
            if current_location_id != location_id:
                database.rollback()
                return error_response(
                    f"Row is already linked to location {current_location_id}",
                    status_code=409
                )

        link_exists = check_location_row_link(cursor, location_id, row_id)
        if not link_exists:
            insert_location_row_link(cursor, location_id, row_id)

        fix_null_location_link(cursor, location_id, row_id)

        database.commit()

        return success_response(
            message="Location linked to row successfully",
            data={
                "row_id": row_id,
                "location_id": location_id
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error while linking location to row")
        return error_response("An unexpected error occurred while linking location to row", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        close_database_resources(database, cursor, logger)


def remove_location_from_row_service(row_id: int, location_id: int):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("row-id", row_id),
            build_lock_name("location-id", location_id),
        ]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return error_response("Row not found", status_code=404)

        location_exists = get_location_by_id(cursor, location_id)
        if not location_exists:
            database.rollback()
            return error_response("Location not found", status_code=404)

        link_exists = check_location_row_link(cursor, location_id, row_id)
        if not link_exists:
            database.rollback()
            return error_response("This row is not linked to this location", status_code=400)

        has_racks = row_has_linked_racks(cursor, row_id)
        if has_racks:
            database.rollback()
            return error_response(
                "Location cannot be removed from this row because the row has linked racks",
                status_code=409,
                detail={
                    "reason": "row_has_linked_racks",
                    "action": "Move or delete all racks linked to this row before removing its location.",
                }
            )

        delete_location_row_link(cursor, location_id, row_id)
        insert_history_record(cursor, USER_NAME, row_id)

        database.commit()

        return success_response(
            message="Location successfully removed from row",
            data={
                "row_id": row_id,
                "location_id": location_id
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error while removing location from row")
        return error_response("An unexpected error occurred while removing location from row", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        close_database_resources(database, cursor, logger)


def update_row_name_service(row_id: int, row_name: str):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("row-id", row_id),
            build_lock_name("row-name", row_name),
        ]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return error_response("Row not found", status_code=404)

        name_exists = count_row_name(cursor, row_name, row_id)
        if name_exists > 0:
            database.rollback()
            return error_response(f"There is already a row with the name '{row_name}'", status_code=400)

        update_object_name(cursor, row_id, row_name)
        insert_history_record(cursor, USER_NAME, row_id)

        database.commit()

        return success_response(
            message="Row name updated successfully",
            data={
                "row_id": row_id,
                "new_name": row_name
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during row update")
        return error_response("An unexpected error occurred during row update", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        close_database_resources(database, cursor, logger)
