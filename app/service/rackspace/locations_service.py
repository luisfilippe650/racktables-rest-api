import logging

from app.core.database import connect_with_cursor
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
    delete_entity_links,
    insert_history_record,
)
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.database_resources import close_database_resources
from app.utils.objtype import LOCATION, ROW
from app.utils.user_name import USER_NAME
from app.utils.concurrency import acquire_named_locks, build_lock_name, release_named_locks

logger = logging.getLogger(__name__)


#function of creating location
def create_location_service(data: AddLocation):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
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
        close_database_resources(database, cursor, logger)

#function of deleting location
def delete_location_service(location_id: int):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
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
                status_code=409,
                detail={
                    "reason": "location_has_linked_resources",
                    "action": "Remove linked rows and racks before deleting this location.",
                    "linked_rows": linked_rows,
                    "linked_racks": linked_racks,
                }
            )

        # Locations are rows in Object, so older RackTables relations can
        # reference the same id through the generic "object" realm.
        delete_file_links(cursor, location_id, entity_type='object')
        delete_tags(cursor, location_id, entity_realm='object')
        delete_entity_links(cursor, location_id, entity_type='object')

        # Newer rackspace endpoints store location metadata with the explicit
        # "location" realm/type. Keep this separate from generic object cleanup.
        delete_file_links(cursor, location_id, entity_type='location')
        delete_tags(cursor, location_id, entity_realm='location')
        delete_entity_links(cursor, location_id, entity_type='location')

        # Defensive cleanup for legacy or inconsistent EntityLink rows that
        # may have used the location id while tagging the relation as row/rack.
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
        close_database_resources(database, cursor, logger)

def list_locations_service(page: int = 1, per_page: int = 50):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        offset = (page - 1) * per_page
        total = count_locations_query(cursor, LOCATION)
        locations = list_locations_query(cursor, LOCATION, per_page, offset)
        return paginated_response(locations, page, per_page, total)

    except Exception as e:
        logger.exception("Unexpected error while listing locations")
        return error_response("An unexpected error occurred while listing locations", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)


def get_location_by_name_service(name: str):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error", status_code=500)


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
        close_database_resources(database, cursor, logger)


#function of showing the locations and rows they are using
def list_complete_location_service(page: int = 1, per_page: int = 50):
    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    

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
        return paginated_response(locations, page, per_page, total)

    except Exception as e:
        logger.exception("Unexpected error while listing complete locations")
        return error_response("An unexpected error occurred while listing complete locations", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)
