import logging

from app.core.database import connect
from app.repository.common_repository import get_object_basic_info
from app.repository.objects.mount_unmount_repository import (
    get_rack_by_id,
    get_mounted_object,
    get_occupied_positions_in_range,
    replace_rackspace_position,
    clear_rack_thumbnail,
    create_molecule,
    insert_atom,
    insert_mount_operation,
    get_allocated_spaces_by_object_id,
    delete_rackspace_position,
    get_rack_height,
)
from app.schema.objects.mount_unmount_schema import MountServer
from app.utils.objtype import MOUNTABLE_TYPES
from app.utils.responses import success_response, error_response
from app.utils.user_name import USER_NAME

ATOMS = ["front", "interior", "rear"]
logger = logging.getLogger(__name__)


def _validate_allocated_layout(occupied_spaces):
    units = sorted({row['unit_no'] for row in occupied_spaces})
    if not units:
        return "Object has no rack allocation"

    expected_units = list(range(units[0], units[-1] + 1))
    if units != expected_units:
        return "Current allocation is not contiguous"

    expected_positions = {
        (unit_no, atom)
        for unit_no in units
        for atom in ATOMS
    }
    actual_positions = {
        (row['unit_no'], row['atom'])
        for row in occupied_spaces
    }
    if actual_positions != expected_positions:
        return "Current allocation has incomplete rack atoms"

    return None


# function of allocating object in rack
def mount_server_service(data: MountServer):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # check if the rack exists
        rack_exists = get_rack_by_id(cursor, data.rack_id)
        if not rack_exists:
            database.rollback()
            return error_response("Rack not found", status_code=404)

        # checking if the object exists
        object_row = get_object_basic_info(cursor, data.object_id)
        if not object_row:
            database.rollback()
            return error_response("Object not found", status_code=404)

        # checking if the object is of a mountable type
        if object_row['objtype_id'] not in MOUNTABLE_TYPES:
            database.rollback()
            return error_response("This object type cannot be allocated in a rack via this function", status_code=400)

        # checking if the object is already allocated to any rack
        already_mounted = get_mounted_object(cursor, data.object_id)
        if already_mounted:
            database.rollback()
            return error_response("This object is already allocated in a rack", status_code=400)

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
        occupied_positions = get_occupied_positions_in_range(
            cursor,
            data.rack_id,
            data.start_unit,
            end_unit
        )
        if occupied_positions:
            occupied = occupied_positions[0]
            database.rollback()
            return error_response(
                f"Space occupied on rack at U{occupied['unit_no']} ({occupied['atom']})",
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
            comment=f"Automated mount in rack {data.rack_id}: units {end_unit}-{data.start_unit}"
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
        logger.exception("Unexpected error during mount operation")
        return error_response("An unexpected error occurred during the mount operation", status_code=500)

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
        object_row = get_object_basic_info(cursor, object_id)
        if not object_row:
            database.rollback()
            return error_response("Object not found", status_code=404)

        # checking if the object is of a mountable type
        if object_row['objtype_id'] not in MOUNTABLE_TYPES:
            database.rollback()
            return error_response("This object type cannot be deallocated in this function", status_code=400)

        # checking if the server is allocated
        occupied_spaces = get_allocated_spaces_by_object_id(cursor, object_id)
        if not occupied_spaces:
            database.rollback()
            return error_response("This object is not allocated in any rack", status_code=400)

        rack_ids = {row['rack_id'] for row in occupied_spaces}
        if len(rack_ids) != 1:
            database.rollback()
            return error_response("Inconsistent allocation: object is linked to more than one rack", status_code=500)

        rack_id = occupied_spaces[0]['rack_id']

        layout_error = _validate_allocated_layout(occupied_spaces)
        if layout_error:
            database.rollback()
            return error_response(layout_error, status_code=409)

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
            comment=f"Automated unmount from rack {rack_id}: units {min(row['unit_no'] for row in occupied_spaces)}-{max(row['unit_no'] for row in occupied_spaces)}"
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
        logger.exception("Unexpected error during unmount operation")
        return error_response("An unexpected error occurred during the unmount operation", status_code=500)

    finally:
        cursor.close()
        database.close()
