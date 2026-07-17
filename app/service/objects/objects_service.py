import logging

from app.core.database import connect
from app.repository.common_repository import (
    get_object_basic_info,
    delete_file_links,
    delete_tags,
    delete_network_data,
    delete_entity_links,
    delete_mount_data,
    delete_port_data,
    delete_attribute_values,
    insert_history_record
)
from app.repository.objects.objects_repository import (
    get_objtype_by_id,
    count_objects_by_name,
    count_objects_by_service_tag,
    insert_object,
    insert_port,
    anonymize_object_before_delete,
    delete_object_row,
    list_objects_query,
    list_object_types_query,
    get_objects_by_name_query,
    get_objects_by_service_tag_query,
    add_comment,
    object_has_current_mount,
    get_current_mount_details,
    object_has_port_links,
    get_object_port_links,
    count_objects_query,
    count_all_objects_query,
    list_all_objects_query,
)
from app.schema.objects.objects_schema import CreateObject
from app.types.port_types import PortDict
from app.utils.objtype import ALLOWED_OBJTYPES, SERVER
from app.utils.responses import success_response, error_response
from app.utils.user_name import USER_NAME
from app.utils.concurrency import acquire_named_locks, build_lock_name, release_named_locks
from app.service.objects.attributes_service import update_object_attributes_service

logger = logging.getLogger(__name__)

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
    acquired_locks = []

    try:
        acquired_locks = [
            build_lock_name("object-name", data.name),
        ]
        if data.asset_no:
            acquired_locks.append(build_lock_name("object-service-tag", data.asset_no))

        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

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

        if data.asset_no:
            service_tag_exists = count_objects_by_service_tag(cursor, data.asset_no)
            if service_tag_exists > 0:
                database.rollback()
                return error_response(f"An object with the service tag '{data.asset_no}' already exists", status_code=400)

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

        '''
        Inserting a comment after adding the object to the system, 
        as this is the application's standard behavior. Use add_comment to
        update the object and create a single history entry reflecting the
        final state (including any comment) to avoid duplicate history rows.
        If no comment was provided, just record the creation history to
        avoid performing an unnecessary UPDATE.
        '''
        if data.comment is not None and str(data.comment).strip() != "":
            # Update object including comment and insert a history entry
            add_comment(cursor, object_id, data.name, data.label, 'no', data.asset_no, data.comment, USER_NAME)
        else:
            # No comment: only record the creation in history
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
        logger.exception("Unexpected error during object creation")
        return error_response("An unexpected error occurred during object creation", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()


def delete_object_service(object_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)
    acquired_locks = []

    try:
        acquired_locks = [build_lock_name("object-id", object_id)]
        locked, _ = acquire_named_locks(cursor, acquired_locks)
        if not locked:
            return error_response("Resource is busy; try again", status_code=409)

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

        if object_has_current_mount(cursor, object_id):
            mounted_in = get_current_mount_details(cursor, object_id)
            database.rollback()
            return error_response(
                "Object cannot be deleted because it is currently mounted in a rack",
                status_code=409,
                detail={
                    "reason": "current_rack_allocation",
                    "action": "Unmount the object before deleting it.",
                    "mounted_in": mounted_in,
                }
            )

        if object_has_port_links(cursor, object_id):
            physical_links = get_object_port_links(cursor, object_id)
            database.rollback()
            return error_response(
                "Object cannot be deleted because its ports have physical links",
                status_code=409,
                detail={
                    "reason": "physical_port_links",
                    "action": "Disconnect the physical links before deleting this object.",
                    "links": physical_links,
                }
            )

        # delete all related dependencies
        delete_file_links(cursor, object_id)
        delete_tags(cursor, object_id)
        delete_network_data(cursor, object_id)
        delete_entity_links(cursor, object_id)
        delete_mount_data(cursor, object_id)
        delete_port_data(cursor, object_id)
        delete_attribute_values(cursor, object_id) # Preventive cleanup

        # correct deletion order
        insert_history_record(cursor, USER_NAME, object_id)
        anonymize_object_before_delete(cursor, object_id)
        delete_object_row(cursor, object_id)
        # Final cleanup for entity links where object could be parented or child
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
        logger.exception("Unexpected error during object deletion")
        return error_response("An unexpected error occurred during object deletion", status_code=500)

    finally:
        release_named_locks(cursor, acquired_locks)
        cursor.close()
        database.close()


def list_objects_service(page: int = 1, per_page: int = 50):
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
        total = count_objects_query(cursor)

        # list all objects
        objects = list_objects_query(cursor, per_page, offset)
        return success_response(
            data={
                "items": objects,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(objects)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing objects")
        return error_response("An unexpected error occurred while listing objects", status_code=500)

    finally:
        cursor.close()
        database.close()


def list_all_objects_service(page: int = 1, per_page: int = 50):
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
        total = count_all_objects_query(cursor)
        objects = list_all_objects_query(cursor, per_page, offset)

        return success_response(
            data={
                "items": objects,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(objects)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing all objects")
        return error_response("An unexpected error occurred while listing all objects", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_object_by_name_service(name: str):
    database = connect()
    if not database:
        return error_response("Internal server error", status_code=500)

    cursor = database.cursor(dictionary=True)

    try:
        cleaned_name = name.strip()
        if not cleaned_name:
            return error_response("Object name cannot be empty", status_code=400)

        result = get_objects_by_name_query(cursor, cleaned_name)
        if not result:
            return error_response("Object not found", status_code=404)
        if len(result) > 1:
            return error_response("Multiple objects found with this name", status_code=409)

        return success_response(data=result[0])

    except Exception as e:
        logger.exception("Unexpected error while searching object by name")
        return error_response("Internal server error", status_code=500)

    finally:
        cursor.close()
        database.close()


def get_object_by_service_tag_service(service_tag: str):
    database = connect()
    if not database:
        return error_response("Internal server error", status_code=500)

    cursor = database.cursor(dictionary=True)

    try:
        cleaned_service_tag = service_tag.strip()
        if not cleaned_service_tag:
            return error_response("Service tag cannot be empty", status_code=400)

        result = get_objects_by_service_tag_query(cursor, cleaned_service_tag)
        if not result:
            return error_response("Object not found", status_code=404)
        if len(result) > 1:
            return error_response("Multiple objects found with this service tag", status_code=409)

        return success_response(data=result[0])

    except Exception as e:
        logger.exception("Unexpected error while searching object by service tag")
        return error_response("Internal server error", status_code=500)

    finally:
        cursor.close()
        database.close()


def list_object_types_service(page: int = 1, per_page: int = 50):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        if page < 1:
            return error_response("Page must be greater than or equal to 1", status_code=400)
        if per_page < 1 or per_page > 100:
            return error_response("Per page must be between 1 and 100", status_code=400)

        # get all object types
        result = list_object_types_query(cursor)

        # filter only allowed types
        filtered = [
            obj for obj in result
            if obj["objtype_id"] in ALLOWED_OBJTYPES
        ]
        total = len(filtered)
        start = (page - 1) * per_page
        paginated = filtered[start:start + per_page]

        return success_response(
            data={
                "items": paginated,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(paginated)
        )

    except Exception as e:
        logger.exception("Unexpected error while listing object types")
        return error_response("An unexpected error occurred while listing object types", status_code=500)

    finally:
        cursor.close()
        database.close()


def update_object_service(
    object_id: int,
    object_name: str = None,
    comment: str = None,
    provided_fields: set[str] | None = None
):
    """
    Standardizes the update to use the dynamic attributes service logic,
    ensuring consistent validations and history recording.
    """
    updates = {}
    provided_fields = provided_fields or set()
    if object_name is not None:
        updates["name"] = object_name
    if "comment" in provided_fields:
        updates["comment"] = comment
    
    if not updates:
        return error_response("No fields were provided for update", status_code=400)

    # We reuse the logic already implemented in attributes_service
    # which already handles Server, VM and BlackBox restrictions, 
    # history and validations.
    return update_object_attributes_service(object_id, updates)
