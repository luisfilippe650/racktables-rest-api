from app.core.databaseConnection import connect
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
    list_rows_query,
    list_complete_rows_query,
)
from app.schema.rackspace.rows_schema import AddManageRows


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
                "message": f"Já existe uma row com o nome '{data.name}'"
            }

        row_id = insert_row(cursor, data.name, ROW_OBJTYPE_ID)

        insert_row_history(cursor, USER_NAME, row_id)

        database.commit()

        return {
            "status": "success",
            "message": "Row criada com sucesso",
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
            return {"error": f"Objeto com id {row_id} não existe"}

        object_id, object_name, object_type = row_data

        if object_type != ROW_OBJTYPE_ID:
            return {"error": f"O id {row_id} existe, mas não pertence a uma row"}

        cursor.execute("START TRANSACTION")

        has_racks = row_has_linked_racks(cursor, row_id)

        if has_racks:
            database.rollback()
            return {"error": "Row possui racks vinculados"}

        delete_row_file_links(cursor, row_id)
        delete_row_tags(cursor, row_id)
        delete_row_network_data(cursor, row_id)
        delete_row_object_relationships(cursor, row_id)
        delete_row_relationships(cursor, row_id)
        delete_row_mount_data(cursor, row_id)
        delete_row_vlan_and_ports(cursor, row_id)

        insert_row_history(cursor, USER_NAME, row_id)

        anonymize_row_before_delete(cursor, row_id)
        delete_row_object(cursor, row_id)

        database.commit()

        return {
            "message": "Row deletado com sucesso",
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