from app.core.database import connect
from app.schema.rackspace.locations_schema import AddLocation
from app.repository.rackspace.locations_repository import (
    count_location_by_name,
    insert_location,
    insert_location_history,
    get_location_by_id,
    delete_location_dependencies,
    list_locations_query,
    list_complete_location_query,
    prepare_location_for_delete,
    delete_location_object,
    delete_location_entity_links,
)
from app.utils.responses import success_response, error_response

ROW_OBJTYPE = 1561
OBJTYPE_LOCATION = 1562
USER_NAME = "API - user"

#function of creating location
def create_location_service(data: AddLocation):

    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        exists = count_location_by_name(cursor, data.name, OBJTYPE_LOCATION)

        #check if location with this name already exists
        if exists > 0:
            database.rollback()
            return error_response(f"Location '{data.name}' already exists", status_code=400)

        location_id = insert_location(cursor, data.name, OBJTYPE_LOCATION)

        #inserting into the history the addition of localization
        insert_location_history(cursor, USER_NAME, location_id)

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
        return error_response("An unexpected error occurred during location creation", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()

#function of deleting location
def delete_location_service(location_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        location = get_location_by_id(cursor, location_id, OBJTYPE_LOCATION)

        if not location:
            return error_response(f"Location {location_id} not found", status_code=404)

        cursor.execute("START TRANSACTION")

        delete_location_dependencies(cursor, location_id)
        prepare_location_for_delete(cursor, location_id)
        insert_location_history(cursor, USER_NAME, location_id)
        delete_location_object(cursor, location_id)
        delete_location_entity_links(cursor, location_id)

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
        return error_response("An unexpected error occurred during location deletion", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()

def list_locations_service():
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        locations = list_locations_query(cursor, OBJTYPE_LOCATION)
        return success_response(
            data=locations,
            count=len(locations)
        )

    except Exception as e:
        return error_response("An unexpected error occurred while listing locations", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()

#function of showing the locations and rows they are using
def list_complete_location_service():
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        locations = list_complete_location_query(
            cursor,
            OBJTYPE_LOCATION,
            ROW_OBJTYPE
        )
        return success_response(
            data=locations,
            count=len(locations)
        )

    except Exception as e:
        return error_response("An unexpected error occurred while listing complete locations", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()
