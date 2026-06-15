from app.core.database import connect
from app.schema.objects.objects_schema import CreateObject
from app.types.port_types import PortDict
from app.repository.objects.objects_repository import (
    get_objtype_by_id,
    count_objects_by_name,
    insert_object,
    insert_port,
    anonymize_object_before_delete,
    delete_object_row,
    list_objects_query,
    list_object_types_query,
)
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
    update_object_name,
    update_object_comment
)
from app.utils.responses import success_response, error_response
from app.utils.objtype import ALLOWED_OBJTYPES, SERVER
from app.utils.user_name import USER_NAME

DEFAULT_PORTS_BY_TYPE: dict[int, list[PortDict]] = {
    SERVER: [
        {"name": "kvm", "iif_id": 1, "type": 33, "label": None, "l2address": None},
        {"name": "eth0", "iif_id": 1, "type": 24, "label": None, "l2address": None},
        {"name": "eth1", "iif_id": 1, "type": 24, "label": None, "l2address": None},
    ],
}


def create_object_service(data: CreateObject):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # validate if objtype exists in database
        valid_type = get_objtype_by_id(cursor, data.objtype_id)
        if not valid_type:
            database.rollback()
            return error_response(f"Object type ID {data.objtype_id} is not valid", status_code=400)

        # validate if objtype is allowed by API rules
        if data.objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return error_response("This object type cannot be created by this function", status_code=400, detail=f"Object type ID: {data.objtype_id}")

        # check if object name already exists
        exists_count = count_objects_by_name(cursor, data.name)
        if exists_count > 0:
            database.rollback()
            return error_response(f"An object with the name '{data.name}' already exists", status_code=400)

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
        insert_history_record(cursor, USER_NAME, object_id)

        database.commit()

        return success_response(
            message="Object created successfully",
            data={
                "object_id": object_id,
                "name": data.name,
                "objtype_id": data.objtype_id,
                "ports_created": len(default_ports)
            },
            status_code=201
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during object creation", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()


def delete_object_service(object_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # check if object exists
        result = get_object_basic_info(cursor, object_id)
        if not result:
            database.rollback()
            return error_response("Object not found", status_code=404)

        objtype_id = result['objtype_id']

        # validate allowed type
        if objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return error_response("This object type cannot be deleted by this function", status_code=400, detail=f"Object type ID: {objtype_id}")

        # delete all related dependencies
        delete_file_links(cursor, object_id)
        delete_tags(cursor, object_id)
        delete_network_data(cursor, object_id)
        delete_entity_links(cursor, object_id)
        delete_mount_data(cursor, object_id)
        delete_port_data(cursor, object_id)
        delete_attribute_values(cursor, object_id) # Preventive cleanup

        # correct deletion order
        anonymize_object_before_delete(cursor, object_id)
        insert_history_record(cursor, USER_NAME, object_id)
        delete_object_row(cursor, object_id)
        # Final cleanup for entity links where object could be parent or child
        delete_entity_links(cursor, object_id) 

        database.commit()

        return success_response(
            message="Object deleted successfully",
            data={
                "object_id": object_id,
                "objtype_id": objtype_id
            }
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during object deletion", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()


def list_objects_service():
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        # list all objects
        objects = list_objects_query(cursor)
        return success_response(
            data=objects,
            count=len(objects)
        )

    except Exception as e:
        return error_response("An unexpected error occurred while listing objects", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()


def list_object_types_service():
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        # get all object types
        result = list_object_types_query(cursor)

        # filter only allowed types
        filtered = [
            obj for obj in result
            if obj["objtype_id"] in ALLOWED_OBJTYPES
        ]

        return success_response(
            data=filtered,
            count=len(filtered)
        )

    except Exception as e:
        return error_response("An unexpected error occurred while listing object types", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()


def update_object_service(object_id: int, object_name: str = None, comment: str = None):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # check if object exists
        object_row = get_object_basic_info(cursor, object_id)
        if not object_row:
            database.rollback()
            return error_response("Object not found", status_code=404)

        objtype_id = object_row['objtype_id']

        # validate allowed type
        if objtype_id not in ALLOWED_OBJTYPES:
            database.rollback()
            return error_response("This object type cannot be modified by this function", status_code=400, detail=f"Object type ID: {objtype_id}")

        # ensure at least one field is provided
        if object_name is None and comment is None:
            database.rollback()
            return error_response("No fields were provided for update", status_code=400)

        # update object name if provided
        if object_name is not None:
            name_exists = count_objects_by_name(cursor, object_name, object_id)
            if name_exists > 0:
                database.rollback()
                return error_response(f"An object with the name '{object_name}' already exists", status_code=400)

            update_object_name(cursor, object_id, object_name)

        # update comment if provided
        if comment is not None:
            update_object_comment(cursor, object_id, comment)

        # insert history record
        insert_history_record(cursor, USER_NAME, object_id)

        database.commit()

        response_data = {
            "object_id": object_id,
            "objtype_id": objtype_id
        }

        if object_name is not None:
            response_data["new_name"] = object_name

        if comment is not None:
            response_data["comment"] = comment

        return success_response(
            message="Object updated successfully",
            data=response_data
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during object update", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()
