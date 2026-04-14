from app.core.databaseConnection import connect
from app.repository.rackspace.rack_repository import (
    get_row_by_id,
    insert_rack,
    insert_history,
    insert_attribute,
    link_rack_to_row,
    get_rack_by_id,
    check_rack_has_objects,
    delete_rack_file_links,
    delete_rack_tags,
    delete_rack_thumbnail,
    delete_rackspace_by_rack,
    delete_object_file_links,
    delete_object_tags,
    delete_object_network,
    delete_object_entity_links,
    delete_object_mount_data,
    delete_object_ports,
    anonymize_rack,
    delete_rack_object,
    delete_rack_entity_links_final,
    list_racks_with_height,
    get_occupied_units_by_rack,
    get_object_basic_info,
    get_rack_details_query,
    get_rack_with_height,
    count_rack_name,
    update_rack_name_query,
    insert_rack_history,
)
from app.schema.rackspace.rack_schema import CreateRack

OBJTYPE_RACK = 1560
USER_NAME = "API - user"


def create_rack_service(data: CreateRack):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if the row exists
        row_exists = get_row_by_id(cursor, data.row_id)

        if not row_exists:
            database.rollback()
            return {"error": "Row not found"}

        # insert rack as an object
        rack_id = insert_rack(
            cursor,
            data.name,
            OBJTYPE_RACK,
            data.assent_no
        )

        # insert history record
        insert_history(cursor, USER_NAME, rack_id)

        # rack height attribute (attr_id = 27)
        insert_attribute(cursor, data.rack_height, rack_id, OBJTYPE_RACK, 27)

        # sort/guidance attribute (attr_id = 29)
        insert_attribute(cursor, 1, rack_id, OBJTYPE_RACK, 29)

        # link rack to row
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

        # check if rack exists
        rack = get_rack_by_id(cursor, rack_id)
        if not rack:
            database.rollback()
            return {"error": "Rack not found"}

        # check if rack has allocated objects
        has_objects = check_rack_has_objects(cursor, rack_id)
        if has_objects:
            database.rollback()
            return {"error": "Rack has allocated objects"}

        # cleanup specific to rack realm
        delete_rack_file_links(cursor, rack_id)
        delete_rack_tags(cursor, rack_id)
        delete_rack_thumbnail(cursor, rack_id)
        delete_rackspace_by_rack(cursor, rack_id)

        # generic object cleanup
        delete_object_file_links(cursor, rack_id)
        delete_object_tags(cursor, rack_id)
        delete_object_network(cursor, rack_id)
        delete_object_entity_links(cursor, rack_id)
        delete_object_mount_data(cursor, rack_id)
        delete_object_ports(cursor, rack_id)

        # pattern observed in RackTables
        anonymize_rack(cursor, rack_id)
        insert_history(cursor, USER_NAME, rack_id)
        delete_rack_object(cursor, rack_id)
        delete_rack_entity_links_final(cursor, rack_id)

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


def list_racks_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # list racks with basic info (height, row)
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


def list_racks_with_space_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # get racks with height info
        racks = list_racks_with_height(cursor)
        result = []

        for rack in racks:
            rack_id = rack["rack_id"]
            total_units = rack["total_units"] or 0

            # get occupied units
            occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
            occupied_units = sorted(
                [row["unit_no"] for row in occupied_rows],
                reverse=True
            )

            # calculate free units
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


def get_rack_occupancy_service(rack_id: int):
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # validate rack existence
        rack_exists = get_rack_by_id(cursor, rack_id)
        if not rack_exists:
            return {"error": "Rack not found"}

        # get rack with height info
        rack = get_rack_with_height(cursor, rack_id)
        if not rack:
            return {"error": "It wasn't possible to get the data from the rack"}

        total_units = rack["total_units"] or 0

        # get occupied units
        occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
        occupied_units = sorted(
            [row["unit_no"] for row in occupied_rows],
            reverse=True
        )

        # calculate free units
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


def get_rack_details_service(rack_id: int):
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # get basic object info
        obj = get_object_basic_info(cursor, rack_id)

        if not obj:
            return {"error": "rack not found"}

        # validate that object is a rack
        if obj["objtype_id"] != OBJTYPE_RACK:
            return {
                "error": "The ID entered does not belong to a rack",
                "objtype_id": obj["objtype_id"]
            }

        # get detailed rack info
        result = get_rack_details_query(cursor, rack_id)
        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def update_rack_name_service(rack_id: int, rack_name: str):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if rack exists
        rack_exists = get_rack_by_id(cursor, rack_id)
        if not rack_exists:
            database.rollback()
            return {"error": "Rack not found"}

        # check if name already exists
        name_exists = count_rack_name(cursor, rack_name, rack_id)
        if name_exists > 0:
            database.rollback()
            return {"error": "There is already a rack with that name"}

        # update rack name
        update_rack_name_query(cursor, rack_id, rack_name)

        # insert history record
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