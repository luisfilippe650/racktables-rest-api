from app.core.database import connect
from app.schema.objects.move_schema import MoveServer
from app.repository.objects.move_repository import (
    get_rack_by_id,
    get_object_by_id,
    get_allocated_spaces_by_object_id,
    get_occupied_position,
    delete_rackspace_position,
    replace_rackspace_position,
    clear_rack_thumbnail,
    create_molecule,
    insert_atom,
    insert_mount_operation,
    get_rack_height,
)
from app.utils.responses import success_response, error_response

ALLOWED_OBJTYPE = 4
RACK_OBJTYPE = 1560
ATOMS = ["front", "interior", "rear"]
USER_NAME = "API - user"


def move_server_to_another_rack_service(data: MoveServer):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("START TRANSACTION")

        # 1. Validate destination rack
        destination_rack_exists = get_rack_by_id(cursor, data.destination_rack_id, RACK_OBJTYPE)
        if not destination_rack_exists:
            database.rollback()
            return error_response("Destination rack not found", status_code=404)

        # 2. Validate object existence and type
        object_row = get_object_by_id(cursor, data.object_id)
        if not object_row:
            database.rollback()
            return error_response("Object not found", status_code=404)

        # Use dictionary access
        if object_row['objtype_id'] != ALLOWED_OBJTYPE:
            database.rollback()
            return error_response("Only Server type objects can be moved in this function", status_code=400)

        # 3. Get current allocation to determine source rack and height automatically
        occupied_spaces = get_allocated_spaces_by_object_id(cursor, data.object_id)
        if not occupied_spaces:
            database.rollback()
            return error_response("This server is not allocated in any rack", status_code=400)

        source_rack_ids = {row['rack_id'] for row in occupied_spaces}
        if len(source_rack_ids) != 1:
            database.rollback()
            return error_response("Inconsistent allocation: object is linked to more than one rack", status_code=500)

        # Automatic discovery of source rack and height
        real_source_rack_id = occupied_spaces[0]['rack_id']
        calculated_height = len(set(row['unit_no'] for row in occupied_spaces))

        # 4. Validate destination rack height and boundaries
        rack_height = get_rack_height(cursor, data.destination_rack_id)
        if rack_height is None:
            database.rollback()
            return error_response("Could not determine destination rack height", status_code=500)

        if data.start_unit > rack_height:
            database.rollback()
            return error_response(
                f"The start unit exceeds the destination rack height ({rack_height})",
                status_code=400
            )

        end_unit = data.start_unit - calculated_height + 1

        if end_unit <= 0:
            database.rollback()
            return error_response(
                "The object height exceeds the lower limit of the rack",
                status_code=400,
                detail=f"Calculated end unit: {end_unit}"
            )

        # 5. Check if target positions are free (ignoring current positions if moving within same rack)
        source_positions = {(row['rack_id'], row['unit_no'], row['atom']) for row in occupied_spaces}

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                occupied = get_occupied_position(cursor, data.destination_rack_id, unit_no, atom)

                if occupied and occupied['object_id'] is not None:
                    # Allow move if the position is already occupied by the SAME object
                    same_old_position = (data.destination_rack_id, unit_no, atom) in source_positions
                    if not same_old_position:
                        database.rollback()
                        return error_response(
                            f"Space occupied on destination rack at U{unit_no} ({atom})",
                            status_code=409,
                            detail=f"Occupied by object ID: {occupied['object_id']}"
                        )

        # 6. Execute the move (Cleanup source and Allocate destination)
        old_molecule_id = create_molecule(cursor)
        for row in occupied_spaces:
            insert_atom(cursor, old_molecule_id, row['rack_id'], row['unit_no'], row['atom'])

        for row in occupied_spaces:
            delete_rackspace_position(cursor, row['rack_id'], row['unit_no'], row['atom'])

        # Optimization: Clear thumbnail only once if it's the same rack, or twice if different
        clear_rack_thumbnail(cursor, real_source_rack_id)
        if real_source_rack_id != data.destination_rack_id:
            clear_rack_thumbnail(cursor, data.destination_rack_id)

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                replace_rackspace_position(
                    cursor,
                    data.destination_rack_id,
                    unit_no,
                    atom,
                    data.object_id
                )

        new_molecule_id = create_molecule(cursor)
        for unit_no in range(end_unit, data.start_unit + 1):
            for atom in ATOMS:
                insert_atom(cursor, new_molecule_id, data.destination_rack_id, unit_no, atom)

        insert_mount_operation(
            cursor=cursor,
            object_id=data.object_id,
            old_molecule_id=old_molecule_id,
            new_molecule_id=new_molecule_id,
            user_name=USER_NAME,
            comment=f"Automated move from rack {real_source_rack_id} to {data.destination_rack_id}"
        )

        database.commit()

        return success_response(
            message="Server moved successfully",
            data={
                "object_id": data.object_id,
                "source_rack_id": real_source_rack_id,
                "destination_rack_id": data.destination_rack_id,
                "start_unit": data.start_unit,
                "end_unit": end_unit,
                "height": calculated_height,
                "old_molecule_id": old_molecule_id,
                "new_molecule_id": new_molecule_id
            }
        )

    except Exception as e:
        database.rollback()
        return error_response("An unexpected error occurred during the move operation", detail=str(e), status_code=500)

    finally:
        cursor.close()
        database.close()
