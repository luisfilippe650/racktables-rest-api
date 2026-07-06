import logging

from app.core.database import connect
from app.schema.rackspace.locations_schema import AddLocation
from app.repository.rackspace.locations_repository import (
    count_location_by_name,
    insert_location,
    get_location_by_id,
    get_locations_by_name_query,
    list_locations_query,
    list_complete_location_query,
    prepare_location_for_delete,
    delete_location_object,
    count_rows_linked_to_location,
    count_racks_linked_to_location,
    count_locations_query,
)
from app.repository.common_repository import (
    delete_file_links,
    delete_tags,
    delete_network_data,
    delete_entity_links,
    delete_mount_data,
    delete_port_data,
    delete_attribute_values,
    insert_history_record,
)
from app.utils.responses import success_response, error_response
from app.utils.objtype import LOCATION, ROW
from app.utils.user_name import USER_NAME
from app.utils.concurrency import acquire_named_locks, build_lock_name, release_named_locks

logger = logging.getLogger(__name__)


#function of creating location
def create_location_service(data: AddLocation):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("location-name", data.name)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        #search if exist name locations in database for no repeat
        exists = count_location_by_name(cursor, data.name, LOCATION)

        #check if location with this name already exists
        if exists > 0:
            database.rollback()
            return error_response(f"Location '{data.name}' already exists", status_code=400)

        location_id = insert_location(cursor, data.name, LOCATION)

        #inserting into the history the addition of localization
        insert_history_record(cursor, USER_NAME, location_id)

        database.commit()

        return success_response(
            message="Location successfully created",
            data={
                "id": location_id,
                "name": data.name
            },
            status_code=201
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during location creation")
        return error_response("An unexpected error occurred during location creation", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()

#function of deleting location
def delete_location_service(location_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("location-id", location_id)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

        cursor.execute("START TRANSACTION")

        location = get_location_by_id(cursor, location_id, LOCATION)

        if not location:
            database.rollback()
            return error_response(f"Location {location_id} not found", status_code=404)

        linked_rows = count_rows_linked_to_location(cursor, location_id)
        linked_racks = count_racks_linked_to_location(cursor, location_id)

        if linked_rows > 0 or linked_racks > 0:
            database.rollback()
            return error_response(
                "Location cannot be deleted because it has linked rows or racks",
                detail=f"Linked rows: {linked_rows}; linked racks: {linked_racks}",
                status_code=409
            )

        # Generic object cleanup
        delete_file_links(cursor, location_id, entity_type='object')
        delete_tags(cursor, location_id, entity_realm='object')
        delete_network_data(cursor, location_id)
        delete_entity_links(cursor, location_id, entity_type='object')
        delete_mount_data(cursor, location_id)
        delete_port_data(cursor, location_id)
        delete_attribute_values(cursor, location_id)

        # Location-specific cleanup
        delete_file_links(cursor, location_id, entity_type='location')
        delete_tags(cursor, location_id, entity_realm='location')
        delete_entity_links(cursor, location_id, entity_type='location')
        # Also handle rack and row types if they are parents/children
        delete_entity_links(cursor, location_id, entity_type='rack')
        delete_entity_links(cursor, location_id, entity_type='row')

        insert_history_record(cursor, USER_NAME, location_id)
        prepare_location_for_delete(cursor, location_id)
        delete_location_object(cursor, location_id)

        database.commit()

        return success_response(
            message="Location successfully deleted",
            data={
                "id": location_id,
                "name": location["name"]
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during location deletion")
        return error_response("An unexpected error occurred during location deletion", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()

def list_locations_service(page: int = 1, per_page: int = 50):
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
        total = count_locations_query(cursor, LOCATION)
        locations = list_locations_query(cursor, LOCATION, per_page, offset)
        return success_response(
            data={
                "items": locations,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(locations)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing locations")
        return error_response("An unexpected error occurred while listing locations", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_location_by_name_service(name: str):
    database = connect()
    if not database:
        return error_response("Internal server error", status_code=500)

    cursor = database.cursor(dictionary=True)

    try:
        cleaned_name = name.strip()
        if not cleaned_name:
            return error_response("Location name cannot be empty", status_code=400)

        result = get_locations_by_name_query(cursor, cleaned_name, LOCATION)
        if not result:
            return error_response("Location not found", status_code=404)
        if len(result) > 1:
            return error_response("Multiple locations found with this name", status_code=409)

        return success_response(data=result[0])

    except Exception as e:
        logger.exception("Unexpected error while searching location by name")
        return error_response("Internal server error", status_code=500)

    finally:
        cursor.close()
        database.close()


#function of showing the locations and rows they are using
def list_complete_location_service(page: int = 1, per_page: int = 50):
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
        total = count_locations_query(cursor, LOCATION)
        locations = list_complete_location_query(
            cursor,
            LOCATION,
            ROW,
            per_page,
            offset
        )
        return success_response(
            data={
                "items": locations,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(locations)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing complete locations")
        return error_response("An unexpected error occurred while listing complete locations", status_code=500)

    finally:
        cursor.close()
        database.close()
