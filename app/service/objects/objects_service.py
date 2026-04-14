from app.core.databaseConnection import connect
from app.schema.objects.objects_schema import CreateObject
from app.types.port_types import PortDict
from app.repository.objects.objects_repository import (
    get_objtype_by_id,
    count_objects_by_name,
    insert_object,
    insert_port,
    insert_object_history,
    get_object_by_id,
    delete_object_file_links,
    delete_object_tags,
    delete_object_network_data,
    delete_object_relationships,
    delete_object_mount_data,
    delete_object_vlan_and_ports,
    anonymize_object_before_delete,
    delete_object_row,
    final_cleanup_entity_links,
    list_objects_query,
    list_object_types_query,
    update_object_name_query,
    update_object_comment_query,
)

USER_NAME = "API - user"

ALLOWED_OBJTYPES = {
    1,     # Generic
    4,     # Server
    7,     # Router
    8,     # Network switch
    9,     # Firewall
    1504,  # PatchPanel
    1505,  # PDU
    1506,  # UPS
}

DEFAULT_PORTS_BY_TYPE: dict[int, list[PortDict]] = {
    4: [
        {"name": "kvm", "iif_id": 1, "type": 33, "label": None, "l2address": None},
        {"name": "eth0", "iif_id": 1, "type": 24, "label": None, "l2address": None},
        {"name": "eth1", "iif_id": 1, "type": 24, "label": None, "l2address": None},
    ],
}


def create_object_service(data: CreateObject):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # validate if objtype exists in database
        valid_type = get_objtype_by_id(cursor, data.objtype_id)
        if not valid_type:
            database.rollback()
            return {"error": f"objtype_id {data.objtype_id} is not valid"}

        # validate if objtype is allowed by API rules
        if data.objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return {
                "error": "This type cannot be created by this function",
                "objtype_id": data.objtype_id
            }

        # check if object name already exists
        exists_count = count_objects_by_name(cursor, data.name)
        if exists_count > 0:
            database.rollback()
            return {"error": "An object with this name already exists"}

        # insert object into database
        object_id = insert_object(
            cursor=cursor,
            name=data.name,
            label=data.label,
            objtype_id=data.objtype_id,
            asset_no=data.asset_no
        )

        # get default ports for object type
        default_ports: list[PortDict] = DEFAULT_PORTS_BY_TYPE.get(data.objtype_id, [])

        # create default ports
        for port in default_ports:
            insert_port(
                cursor=cursor,
                name=port["name"],
                object_id=object_id,
                label=port["label"],
                iif_id=port["iif_id"],
                port_type=port["type"],
                l2address=port["l2address"]
            )

        # insert history record
        insert_object_history(cursor, USER_NAME, object_id)

        database.commit()

        return {
            "message": "Object created successfully",
            "object_id": object_id,
            "name": data.name,
            "objtype_id": data.objtype_id,
            "ports_created": len(default_ports)
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def delete_object_service(object_id: int):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if object exists
        result = get_object_by_id(cursor, object_id)
        if not result:
            database.rollback()
            return {"error": "Object not found"}

        objtype_id = result[1]

        # validate allowed type
        if objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return {
                "error": "This type cannot be deleted by this function",
                "objtype_id": objtype_id
            }

        # delete all related dependencies
        delete_object_file_links(cursor, object_id)
        delete_object_tags(cursor, object_id)
        delete_object_network_data(cursor, object_id)
        delete_object_relationships(cursor, object_id)
        delete_object_mount_data(cursor, object_id)
        delete_object_vlan_and_ports(cursor, object_id)

        # correct deletion order
        anonymize_object_before_delete(cursor, object_id)
        insert_object_history(cursor, USER_NAME, object_id)
        delete_object_row(cursor, object_id)
        final_cleanup_entity_links(cursor, object_id)

        database.commit()

        return {
            "message": "Object deleted successfully",
            "object_id": object_id,
            "objtype_id": objtype_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_objects_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # list all objects
        return list_objects_query(cursor)

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_object_types_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # get all object types
        result = list_object_types_query(cursor)

        # filter only allowed types
        filtered = [
            obj for obj in result
            if obj["objtype_id"] in ALLOWED_OBJTYPES
        ]

        return filtered

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def update_object_service(object_id: int, object_name: str = None, comment: str = None):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if object exists
        object_row = get_object_by_id(cursor, object_id)
        if not object_row:
            database.rollback()
            return {"error": "Object not found"}

        objtype_id = object_row[1]

        # validate allowed type
        if objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return {
                "error": "This type cannot be changed by this function",
                "objtype_id": objtype_id
            }

        # ensure at least one field is provided
        if object_name is None and comment is None:
            database.rollback()
            return {"error": "No fields were provided for update"}

        # update object name if provided
        if object_name is not None:
            name_exists = count_objects_by_name(cursor, object_name, object_id)
            if name_exists > 0:
                database.rollback()
                return {"error": "There is already an object with that name"}

            update_object_name_query(cursor, object_id, object_name)

        # update comment if provided
        if comment is not None:
            update_object_comment_query(cursor, object_id, comment)

        # insert history record
        insert_object_history(cursor, USER_NAME, object_id)

        database.commit()

        response = {
            "message": "Object updated successfully",
            "object_id": object_id,
            "objtype_id": objtype_id
        }

        if object_name is not None:
            response["new_name"] = object_name

        if comment is not None:
            response["comment"] = comment

        return response

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()