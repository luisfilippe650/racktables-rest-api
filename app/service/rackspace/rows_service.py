from app.core.databaseConnection import connect
from app.schema.rackspace.rows_schema import AddManageRows
from app.repository.rackspace.rows_repository import (
    count_rows_by_name,
    insert_row,
    insert_row_history,
    get_object_by_id,
    row_has_linked_racks,
    delete_row_file_links,
    delete_row_tags,
    delete_row_network_data,
    delete_row_object_relationships,
    delete_row_relationships,
    delete_row_mount_data,
    delete_row_vlan_and_ports,
    anonymize_row_before_delete,
    delete_row_object,
    delete_row_entity_links_final,
    list_rows_query,
    list_complete_rows_query,
    get_location_by_id,
    get_row_by_id,
    update_row_name,
    check_location_row_link,
    insert_location_row_link,
    fix_null_location_link,
    count_row_name,
    delete_location_row_link,
)

ROW_OBJTYPE_ID = 1561
RACK_OBJTYPE_ID = 1560
USER_NAME = "API - user"


def create_row_service(data: AddManageRows):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        exists_count = count_rows_by_name(cursor, data.name, ROW_OBJTYPE_ID)

        if exists_count > 0:
            database.rollback()
            return {
                "status": "error",
                "message": f"There is already a row with the name '{data.name}'"
            }

        row_id = insert_row(cursor, data.name, ROW_OBJTYPE_ID)
        insert_row_history(cursor, USER_NAME, row_id)

        database.commit()

        return {
            "message": "Row created successfully",
            "row_id": row_id,
            "name": data.name
        }

    except Exception as e:
        database.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        database.close()


def delete_row_service(row_id: int):
    database = connect()
    cursor = database.cursor()

    try:
        row_data = get_object_by_id(cursor, row_id)

        if row_data is None:
            return {"error": f"row with id {row_id} does not exist"}

        _, object_name, object_type = row_data

        if object_type != ROW_OBJTYPE_ID:
            return {"error": f"the id {row_id}, does not belong to a row"}

        cursor.execute("START TRANSACTION")

        has_racks = row_has_linked_racks(cursor, row_id)
        if has_racks:
            database.rollback()
            return {"error": "it is not possible to delete the Row because it has linked racks"}

        delete_row_file_links(cursor, row_id)
        delete_row_tags(cursor, row_id)
        delete_row_network_data(cursor, row_id)
        delete_row_object_relationships(cursor, row_id)
        delete_row_relationships(cursor, row_id)
        delete_row_mount_data(cursor, row_id)
        delete_row_vlan_and_ports(cursor, row_id)

        anonymize_row_before_delete(cursor, row_id)
        insert_row_history(cursor, USER_NAME, row_id)
        delete_row_object(cursor, row_id)
        delete_row_entity_links_final(cursor, row_id)

        database.commit()

        return {
            "message": "Row deleted successfully",
            "row_id": row_id,
            "row_name": object_name
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_row_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        return list_rows_query(cursor, ROW_OBJTYPE_ID)

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_complete_rows_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        return list_complete_rows_query(
            cursor,
            ROW_OBJTYPE_ID,
            RACK_OBJTYPE_ID
        )

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def add_location_to_row_service(row_id: int, location_id: int):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return {"error": "Row not found"}

        location_exists = get_location_by_id(cursor, location_id)
        if not location_exists:
            database.rollback()
            return {"error": "Location not found"}

        link_exists = check_location_row_link(cursor, location_id, row_id)
        if not link_exists:
            insert_location_row_link(cursor, location_id, row_id)

        fix_null_location_link(cursor, location_id, row_id)

        database.commit()

        return {
            "message": "Location linked to row successfully",
            "row_id": row_id,
            "location_id": location_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def remove_location_from_row_service(row_id: int, location_id: int):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return {"error": "Row not found"}

        location_exists = get_location_by_id(cursor, location_id)
        if not location_exists:
            database.rollback()
            return {"error": "Location not found"}

        link_exists = check_location_row_link(cursor, location_id, row_id)
        if not link_exists:
            database.rollback()
            return {"error": "This row is not linked to this location"}

        delete_location_row_link(cursor, location_id, row_id)
        insert_row_history(cursor, USER_NAME, row_id)

        database.commit()

        return {
            "message": "Location successfully removed from row",
            "row_id": row_id,
            "location_id": location_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def update_row_name_service(row_id: int, row_name: str):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        row_exists = get_row_by_id(cursor, row_id)
        if not row_exists:
            database.rollback()
            return {"error": "Row not found"}

        name_exists = count_row_name(cursor, row_name, row_id)
        if name_exists > 0:
            database.rollback()
            return {"error": "There is already a row with that name"}

        update_row_name(cursor, row_id, row_name)
        insert_row_history(cursor, USER_NAME, row_id)

        database.commit()

        return {
            "message": "Row name updated successfully",
            "row_id": row_id,
            "new_name": row_name
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()