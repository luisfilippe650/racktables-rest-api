from app.core.database import connect
from app.schema.objects.mount_unmount_schema import MountServer
from app.repository.objects.mount_unmount_repository import (
    get_rack_by_id,
    get_object_by_id,
    get_mounted_object,
    get_occupied_position,
    replace_rackspace_position,
    clear_rack_thumbnail,
    create_molecule,
    insert_atom,
    insert_mount_operation,
    get_allocated_spaces_by_object_id,
    delete_rackspace_position,
    get_rack_height,
)
from app.utils.responses import success_response, error_response

ALLOWED_OBJTYPE = 4
RACK_OBJTYPE = 1560
ATOMS = ["front", "interior", "rear"]
USER_NAME = "API - user"


# function of allocating server in rack
def mount_server_service(data: MountServer):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # check if the rack exists
        rack_exists = get_rack_by_id(cursor, data.rack_id, RACK_OBJTYPE)
        if not rack_exists:
            database.rollback()
            return error_response("Rack not found", status_code=404)

        # checking if the server type object exists
        object_row = get_object_by_id(cursor, data.object_id)
        if not object_row:
            database.rollback()
            return error_response("Server object not found", status_code=404)

        # checking if the object is of type server
        if object_row['objtype_id'] != ALLOWED_OBJTYPE:
            database.rollback()
            return error_response("Only objects of type Server can be allocated in this function", status_code=400)

        # checking if the server is already allocated to any rack
        already_mounted = get_mounted_object(cursor, data.object_id)
        if already_mounted:
            database.rollback()
            return error_response("This server is already allocated in a rack", status_code=400)

        # checking if the height was placed greater than zero
        if data.height <= 0:
            database.rollback()
            return error_response("The height must be greater than zero", status_code=400)

        rack_height = get_rack_height(cursor, data.rack_id)
        if rack_height is None:
            database.rollback()
            return error_response("Could not determine rack height", status_code=500)

        if data.start_unit > rack_height:
            database.rollback()
            return error_response(
                f"The start unit exceeds the rack height ({rack_height})",
                status_code=400
            )

        end_unit = data.start_unit - data.height + 1

        # prevents passing the lower limit of the rack (below U1)
        if end_unit <= 0:
            database.rollback()
            return error_response("The reported height exceeds the lower limit of the rack", status_code=400)

        # validate if all target positions are free
        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                occupied = get_occupied_position(cursor, data.rack_id, unit_no, atom)

                if occupied and occupied['object_id'] is not None:
                    database.rollback()
                    return error_response(
                        f"Space occupied on rack at U{unit_no} ({atom})",
                        status_code=409,
                        detail=f"Occupied by object ID: {occupied['object_id']}"
                    )

        # allocate positions
        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                replace_rackspace_position(cursor, data.rack_id, unit_no, atom, data.object_id)

        clear_rack_thumbnail(cursor, data.rack_id)

        molecule_id = create_molecule(cursor)

        for unit_no in range(end_unit, data.start_unit + 1):
            for atom in ATOMS:
                insert_atom(cursor, molecule_id, data.rack_id, unit_no, atom)

        insert_mount_operation(
            cursor=cursor,
            object_id=data.object_id,
            old_molecule_id=None,
            new_molecule_id=molecule_id,
            user_name=USER_NAME,
            comment=None
        )

        database.commit()

        return success_response(
            message="Server allocated successfully",
            data={
                "rack_id": data.rack_id,
                "object_id": data.object_id,
                "start_unit": data.start_unit,
                "end_unit": end_unit,
                "height": data.height,
                "molecule_id": molecule_id
            }
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during the mount operation", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()


# rack server deallocation function
def unmount_server_service(object_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # check if the object exists
        object_row = get_object_by_id(cursor, object_id)
        if not object_row:
            database.rollback()
            return error_response("Object not found", status_code=404)

        # checking if the object is of type server
        if object_row['objtype_id'] != ALLOWED_OBJTYPE:
            database.rollback()
            return error_response("Only Server type objects can be deallocated in this function", status_code=400)

        # checking if the server is allocated
        occupied_spaces = get_allocated_spaces_by_object_id(cursor, object_id)
        if not occupied_spaces:
            database.rollback()
            return error_response("This server is not allocated in any rack", status_code=400)

        rack_ids = {row['rack_id'] for row in occupied_spaces}
        if len(rack_ids) != 1:
            database.rollback()
            return error_response("Inconsistent allocation: object is linked to more than one rack", status_code=500)

        rack_id = occupied_spaces[0]['rack_id']

        # deallocating exact positions returned by the database
        for row in occupied_spaces:
            delete_rackspace_position(cursor, row['rack_id'], row['unit_no'], row['atom'])

        clear_rack_thumbnail(cursor, rack_id)

        molecule_id = create_molecule(cursor)

        # recreate exactly the removed structure for history
        for row in occupied_spaces:
            insert_atom(cursor, molecule_id, row['rack_id'], row['unit_no'], row['atom'])

        insert_mount_operation(
            cursor=cursor,
            object_id=object_id,
            old_molecule_id=molecule_id,
            new_molecule_id=None,
            user_name=USER_NAME,
            comment=None
        )

        database.commit()

        return success_response(
            message="Server deallocated successfully",
            data={
                "object_id": object_id,
                "rack_id": rack_id,
                "units_removed": sorted({row['unit_no'] for row in occupied_spaces}),
                "molecule_id": molecule_id
            }
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during the unmount operation", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()
