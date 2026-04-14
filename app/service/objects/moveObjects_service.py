from app.core.databaseConnection import connect
from app.schema.objects.moveObject_schema import MoveServer
from app.repository.objects.moveObjects_repository import (
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

ALLOWED_OBJTYPE = 4
RACK_OBJTYPE = 1560
ATOMS = ["front", "interior", "rear"]
USER_NAME = "API - user"


def move_server_to_another_rack_service(data: MoveServer):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        destination_rack_exists = get_rack_by_id(cursor, data.destination_rack_id, RACK_OBJTYPE)
        if not destination_rack_exists:
            database.rollback()
            return {"error": "Destination rack not found"}

        source_rack_exists = get_rack_by_id(cursor, data.source_rack_id, RACK_OBJTYPE)
        if not source_rack_exists:
            database.rollback()
            return {"error": "Source rack not found"}

        object_row = get_object_by_id(cursor, data.object_id)
        if not object_row:
            database.rollback()
            return {"error": "Object not found"}

        if object_row[1] != ALLOWED_OBJTYPE:
            database.rollback()
            return {"error": "Only Server type objects can be moved in this function"}

        occupied_spaces = get_allocated_spaces_by_object_id(cursor, data.object_id)
        if not occupied_spaces:
            database.rollback()
            return {"error": "This server is not allocated in any rack"}

        source_rack_ids = {row[0] for row in occupied_spaces}
        if len(source_rack_ids) != 1:
            database.rollback()
            return {"error": "Inconsistent allocation: object is linked to more than one rack"}

        real_source_rack_id = occupied_spaces[0][0]

        if real_source_rack_id != data.source_rack_id:
            database.rollback()
            return {
                "error": "The server is not allocated in the reported source rack",
                "real_source_rack_id": real_source_rack_id
            }

        rack_height = get_rack_height(cursor, data.destination_rack_id)
        if rack_height is None:
            database.rollback()
            return {"error": "Could not determine destination rack height"}

        if data.height <= 0:
            database.rollback()
            return {"error": "Height must be greater than zero"}

        if data.start_unit > rack_height:
            database.rollback()
            return {
                "error": "The start unit exceeds the destination rack height",
                "rack_height": rack_height
            }

        end_unit = data.start_unit - data.height + 1

        if end_unit <= 0:
            database.rollback()
            return {"error": "The object height exceeds the lower limit of the destination rack"}

        source_positions = {(row[0], row[1], row[2]) for row in occupied_spaces}

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                occupied = get_occupied_position(cursor, data.destination_rack_id, unit_no, atom)

                if occupied and occupied[0] is not None:
                    same_old_position = (data.destination_rack_id, unit_no, atom) in source_positions
                    if not same_old_position:
                        database.rollback()
                        return {
                            "error": "Space occupied on destination rack",
                            "rack_id": data.destination_rack_id,
                            "unit_no": unit_no,
                            "atom": atom
                        }

        old_molecule_id = create_molecule(cursor)
        for rack_id_row, unit_no, atom in occupied_spaces:
            insert_atom(cursor, old_molecule_id, rack_id_row, unit_no, atom)

        for rack_id_row, unit_no, atom in occupied_spaces:
            delete_rackspace_position(cursor, rack_id_row, unit_no, atom)

        clear_rack_thumbnail(cursor, data.source_rack_id)

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                replace_rackspace_position(
                    cursor,
                    data.destination_rack_id,
                    unit_no,
                    atom,
                    data.object_id
                )

        clear_rack_thumbnail(cursor, data.destination_rack_id)

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
            comment=None
        )

        database.commit()

        return {
            "message": "Server moved successfully",
            "object_id": data.object_id,
            "source_rack_id": data.source_rack_id,
            "destination_rack_id": data.destination_rack_id,
            "start_unit": data.start_unit,
            "end_unit": end_unit,
            "height": data.height,
            "old_molecule_id": old_molecule_id,
            "new_molecule_id": new_molecule_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()