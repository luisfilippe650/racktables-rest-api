from app.core.databaseConnection import connect
from app.schema.rackspace.manageLocations_schema import AddLocation
from app.repository.rackspace.manageLocations_repository import (
    count_location_by_name,
    insert_location,
    insert_location_history,
    get_location_by_id,
    delete_location_dependencies,
    list_complete_location_query
)

ROW_OBJTYPE = 1561
OBJTYPE_LOCATION = 1562
USER_NAME = "API - user"

#function of creating location
def create_location_service(data: AddLocation):

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        exists = count_location_by_name(cursor, data.name)

        #check if location with this name already exists
        if exists > 0:
            database.rollback()
            return {"error": f"Location '{data.name}' already exists"}

        location_id = insert_location(cursor, data.name, OBJTYPE_LOCATION)

        #inserting into the history the addition of localization
        insert_location_history(cursor, USER_NAME, location_id)

        database.commit()

        return {
            "message": "Location successfully created",
            "id": location_id,
            "name": data.name
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#function of deleting location
def delete_location_service(location_id: int):

    database = connect()
    cursor = database.cursor()

    try:
        location = get_location_by_id(cursor, location_id, OBJTYPE_LOCATION)

        # check if location with this name already exists
        if not location:
            return {"error": f"Location {location_id} not found"}

        cursor.execute("START TRANSACTION")

        delete_location_dependencies(cursor, location_id)

        # inserting into the history the delete of localization
        insert_location_history(cursor, USER_NAME, location_id)

        cursor.execute("""
        UPDATE Object
        SET name = NULL, label = ''
        WHERE id = %s
        """, (location_id,))

        cursor.execute("DELETE FROM Object WHERE id = %s", (location_id,))

        database.commit()

        return {
            "message": "Location successfully deleted",
            "id": location_id,
            "name": location[1]
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_locations_service():
    database = connect()
    cursor = database.cursor()

    try:
        #searching for all localizations
        cursor.execute("""
        SELECT id, name
        FROM Object
        WHERE objtype_id = %s
        ORDER BY name
        """, (OBJTYPE_LOCATION,))

        return [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    finally:
        cursor.close()
        database.close()

#function of showing the locations and rows they are using
def list_complete_location_service():
    database = connect()
    cursor = database.cursor()

    try:
        return list_complete_location_query(
            cursor,
            OBJTYPE_LOCATION,
            ROW_OBJTYPE
        )

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()