from app.core.databaseConnection import connect
from app.schema.objects.allocateObjects_schema import AllocateServer
from app.repository.objects.allocateObjects_repository import (
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
)


ALLOWED_OBJTYPE = 4
RACK_OBJTYPE = 1560
ATOMS = ["front", "interior", "rear"]
USER_NAME = "API - user"

#function of allocating server in rack
def allocate_server_to_rack_service(data: AllocateServer):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        #check if the rack exists
        rack_exists = get_rack_by_id(cursor, data.rack_id, RACK_OBJTYPE)
        if not rack_exists:
            database.rollback()
            return {"error": "Rack not found"}

        #checking if the server type object exists
        object_row = get_object_by_id(cursor, data.object_id)
        if not object_row:
            database.rollback()
            return {"error": "server object not found"}

        #checking if the object is of type server
        if object_row[1] != ALLOWED_OBJTYPE:
            database.rollback()
            return {"error": "Only objects of type Server can be allocated in this function"}

        #checking if the server is already allocating to any rack
        already_mounted = get_mounted_object(cursor, data.object_id)
        if already_mounted:
            database.rollback()
            return {"error": "This server is already allocated in a rack"}

        #checking if the height was placed greater than zero
        if data.height <= 0:
            database.rollback()
            return {"error": "The height must be greater than zero"}

        end_unit = data.start_unit - data.height + 1

        #Prevents: pass the lower limit of the rack (below U1) occupy non-existent positions
        if end_unit <= 0:
            database.rollback()
            return {"error": "The reported height exceeds the lower limit of the rack"}

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in ATOMS:
                occupied = get_occupied_position(cursor, data.rack_id, unit_no, atom)

                if occupied and occupied[0] is not None:
                    database.rollback()
                    return {
                        "error": "Space occupied on rack",
                        "rack_id": data.rack_id,
                        "unit_no": unit_no,
                        "atom": atom
                    }

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

        return {
            "message": "Server allocated successfully",
            "rack_id": data.rack_id,
            "object_id": data.object_id,
            "start_unit": data.start_unit,
            "end_unit": end_unit,
            "height": data.height,
            "molecule_id": molecule_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

#rack server deallocation function
def unallocate_server_from_rack_service(object_id: int):
    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        #check if the object exists
        object_row = get_object_by_id(cursor, object_id)
        if not object_row:
            database.rollback()
            return {"error": "Object not found"}

        #checking if the object is of type server
        if object_row[1] != ALLOWED_OBJTYPE:
            database.rollback()
            return {"error": "Only Server type objects can be deallocated in this function"}

        #checking if the server is allocated
        occupied_spaces = get_allocated_spaces_by_object_id(cursor, object_id)
        if not occupied_spaces:
            database.rollback()
            return {"error": "This server is not allocated in any rack"}

        rack_id = occupied_spaces[0][0]
        occupied_units = sorted({row[1] for row in occupied_spaces})

        #deallocating from server to rack
        for unit_no in occupied_units:
            for atom in ATOMS:
                delete_rackspace_position(cursor, rack_id, unit_no, atom)

        clear_rack_thumbnail(cursor, rack_id)

        molecule_id = create_molecule(cursor)

        for unit_no in occupied_units:
            for atom in ATOMS:
                insert_atom(cursor, molecule_id, rack_id, unit_no, atom)

        insert_mount_operation(
            cursor=cursor,
            object_id=object_id,
            old_molecule_id=molecule_id,
            new_molecule_id=None,
            user_name=USER_NAME,
            comment=None
        )

        database.commit()

        return {
            "message": "Server deallocated successfully",
            "object_id": object_id,
            "rack_id": rack_id,
            "units_removed": occupied_units,
            "molecule_id": molecule_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()