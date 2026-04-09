from app.core.databaseConnection import connect
from app.repository.rackspace.rack_repository import (
    get_row_by_id,
    insert_rack,
    insert_history,
    insert_attribute,
    link_rack_to_row,
    get_rack_by_id,
    check_rack_has_objects,
    list_racks_with_height,
    get_occupied_units_by_rack, get_object_basic_info, get_rack_details_query, get_rack_with_height, count_rack_name,
    update_rack_name_query, insert_rack_history,
)
from app.schema.rackspace.rack_schema import CreateRack


OBJTYPE_RACK = 1560
USER_NAME = "API - user"

def create_rack_service(data: CreateRack):

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")


        row_exists = get_row_by_id(cursor, data.row_id)

        #checking if row exists
        if not row_exists:
            database.rollback()
            return {"error": "Row not found"}

        rack_id = insert_rack(
            cursor,
            data.name,
            OBJTYPE_RACK,
            data.assent_no
        )
        #inserting into the history
        insert_history(cursor, USER_NAME, rack_id)

        # rack height (attr_id = 27)
        insert_attribute(cursor, data.rack_height, rack_id, OBJTYPE_RACK, 27)

        # guidance (attr_id = 29)
        insert_attribute(cursor, 1, rack_id, OBJTYPE_RACK, 29)

        link_rack_to_row(cursor, data.row_id, rack_id)

        database.commit()

        return {
            "message": "Rack created successfully",
            "rack_id": rack_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def delete_rack_service(rack_id: int):

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        rack = get_rack_by_id(cursor, rack_id)
        #checking if rack exists
        if not rack:
            database.rollback()
            return {"error": "Rack not found"}

        has_objects = check_rack_has_objects(cursor, rack_id)
        #verifying that the existence of servers allocated in the rack does not compromise integrity
        if has_objects:
            database.rollback()
            return {"error": "Rack has allocated objects"}

        #Here you keep your cleanup heavy (you can extract it later)
        cursor.execute("DELETE FROM RackThumbnail WHERE rack_id = %s", (rack_id,))
        cursor.execute("DELETE FROM RackSpace WHERE rack_id = %s", (rack_id,))

        # inserting into the history
        insert_history(cursor, USER_NAME, rack_id)

        cursor.execute("DELETE FROM Object WHERE id = %s", (rack_id,))

        database.commit()

        return {
            "message": "Rack deleted successfully",
            "rack_id": rack_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#function of listing all existing racks
def list_racks_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("""
        SELECT
            rack.id AS rack_id,
            rack.name AS rack_name,
            av.uint_value AS rack_height,
            row_obj.id AS row_id,
            row_obj.name AS row_name
        FROM Object AS rack

        LEFT JOIN AttributeValue av
            ON av.object_id = rack.id
           AND av.attr_id = 27
           AND av.object_tid = 1560

        LEFT JOIN EntityLink el
            ON el.child_entity_type = 'rack'
           AND el.child_entity_id = rack.id
           AND el.parent_entity_type = 'row'

        LEFT JOIN Object AS row_obj
            ON row_obj.id = el.parent_entity_id

        WHERE rack.objtype_id = 1560
        ORDER BY rack.name
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        database.close()

#function of listing all racks and their storage
def list_racks_with_space_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        racks = list_racks_with_height(cursor)

        result = []

        for rack in racks:
            rack_id = rack["rack_id"]
            total_units = rack["total_units"] or 0

            occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
            occupied_units = sorted(
                [row["unit_no"] for row in occupied_rows],
                reverse=True
            )

            all_units = set(range(1, total_units + 1))
            free_units = sorted(list(all_units - set(occupied_units)), reverse=True)

            result.append({
                "rack_id": rack_id,
                "rack_name": rack["rack_name"],
                "total_units": total_units,
                "occupied_units": occupied_units,
                "free_units": free_units
            })

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#function of listing occupancy of only one rack
def get_rack_occupancy_service(rack_id: int):
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        rack_exists = get_rack_by_id(cursor, rack_id)
        #checking if the rack exists
        if not rack_exists:
            return {"error": "Rack not found"}

        rack = get_rack_with_height(cursor, rack_id)

        if not rack:
            return {"error": "It wasn't possible to get the data from the rack"}

        total_units = rack["total_units"] or 0

        occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
        occupied_units = sorted(
            [row["unit_no"] for row in occupied_rows],
            reverse=True
        )

        all_units = set(range(1, total_units + 1))
        free_units = sorted(list(all_units - set(occupied_units)), reverse=True)

        return {
            "rack_id": rack["rack_id"],
            "rack_name": rack["rack_name"],
            "total_units": total_units,
            "occupied_units": occupied_units,
            "free_units": free_units
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#function list the details of a rack
def get_rack_details_service(rack_id: int):
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        obj = get_object_basic_info(cursor, rack_id)

        #checking if the rack exists
        if not obj:
            return {"error": "rack not found"}

        #checking if id is of type rack
        if obj["objtype_id"] != OBJTYPE_RACK:
            return {
                "error": "The ID entered does not belong to a rack",
                "objtype_id": obj["objtype_id"]
            }

        result = get_rack_details_query(cursor, rack_id)
        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#function to change rack name
def update_rack_name_service(rack_id: int, rack_name: str):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        #check if rack exists
        rack_exists = get_rack_by_id(cursor, rack_id)
        if not rack_exists:
            database.rollback()
            return {"error": "Rack not found"}

        #checking if there is an existing same name
        name_exists = count_rack_name(cursor, rack_name, rack_id)
        if name_exists > 0:
            database.rollback()
            return {"error": "There is already a rack with that name"}

        update_rack_name_query(cursor, rack_id, rack_name)

        #adding the information in the historical
        insert_rack_history(cursor, USER_NAME, rack_id)

        database.commit()

        return {
            "message": "Rack name updated successfully",
            "rack_id": rack_id,
            "new_name": rack_name
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()