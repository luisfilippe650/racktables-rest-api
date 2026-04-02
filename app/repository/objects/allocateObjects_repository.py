from app.core.databaseConnection import connect
from app.schema.objects.allocateObjects_schema import AllocateServer

def allocate_server_to_rack(data : AllocateServer):

    user_name= "API - user"

    database = connect()
    cursor = database.cursor()

    allowed_objtype = 4  # Server
    rack_objtype = 1560
    atoms = ["front", "interior", "rear"]

    try:
        cursor.execute("START TRANSACTION")


        # VALIDATE IF THE RACK EXISTS
        check_rack_sql = """
        SELECT id
        FROM Object
        WHERE id = %s
          AND objtype_id = %s
        LIMIT 1
        """
        cursor.execute(check_rack_sql, (data.rack_id, rack_objtype))
        rack_exists = cursor.fetchone()

        if not rack_exists:
            database.rollback()
            return {"error": "Rack n�o encontrado"}

        # VALIDATE IF THE OBJECT EXISTS AND IS A SERVER
        check_object_sql = """
        SELECT id, objtype_id
        FROM Object
        WHERE id = %s
        LIMIT 1
        """
        cursor.execute(check_object_sql, (data.object_id,))
        object_row = cursor.fetchone()

        if not object_row:
            database.rollback()
            return {"error": "Objeto n�o encontrado"}

        if object_row[1] != allowed_objtype:
            database.rollback()
            return {"error": "Somente objetos do tipo Server podem ser alocados nesta fun��o"}

        # VALIDATE IF THE SERVER IS ALREADY MOUNTED
        check_already_mounted_sql = """
        SELECT 1
        FROM RackSpace
        WHERE object_id = %s
        LIMIT 1
        """
        cursor.execute(check_already_mounted_sql, (data.object_id,))
        already_mounted = cursor.fetchone()

        if already_mounted:
            database.rollback()
            return {"error": "Este servidor j� est� alocado em um rack"}


        # VALIDATE HEIGHT
        if data.height <= 0:
            database.rollback()
            return {"error": "A altura deve ser maior que zero"}

        end_unit = data.start_unit - data.height + 1

        if end_unit <= 0:
            database.rollback()
            return {"error": "A altura informada ultrapassa o limite inferior do rack"}


        # VALIDATE FREE SPACE IN THE RACK
        # Checks if any position is already occupied
        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in atoms:
                check_space_sql = """
                SELECT object_id
                FROM RackSpace
                WHERE rack_id = %s
                  AND unit_no = %s
                  AND atom = %s
                LIMIT 1
                """
                cursor.execute(check_space_sql, (data.rack_id, unit_no, atom))
                occupied = cursor.fetchone()

                if occupied and occupied[0] is not None:
                    database.rollback()
                    return {
                        "error": f"Espa�o ocupado no rack",
                        "rack_id": data.rack_id,
                        "unit_no": unit_no,
                        "atom": atom
                    }

        # ALLOCATE IN RACKSPACE
        delete_rackspace_sql = """
        DELETE FROM RackSpace
        WHERE rack_id = %s
          AND unit_no = %s
          AND atom = %s
        """

        insert_rackspace_sql = """
        INSERT INTO RackSpace
        (rack_id, unit_no, atom, state)
        VALUES
        (%s, %s, %s, %s)
        """

        update_rackspace_sql = """
        UPDATE RackSpace
        SET object_id = %s
        WHERE rack_id = %s
          AND unit_no = %s
          AND atom = %s
        """

        for unit_no in range(data.start_unit, end_unit - 1, -1):
            for atom in atoms:
                cursor.execute(delete_rackspace_sql, (data.rack_id, unit_no, atom))
                cursor.execute(insert_rackspace_sql, (data.rack_id, unit_no, atom, "T"))
                cursor.execute(update_rackspace_sql, (data.object_id, data.rack_id, unit_no, atom))

        # CLEAR THUMBNAIL
        delete_thumbnail_sql = """
        DELETE FROM RackThumbnail
        WHERE rack_id = %s
        """
        cursor.execute(delete_thumbnail_sql, (data.rack_id,))

        # CREATE MOLECULE
        cursor.execute("INSERT INTO Molecule VALUES()")
        molecule_id = cursor.lastrowid

        # CREATE ATOMS
        insert_atom_sql = """
        INSERT INTO Atom
        (molecule_id, rack_id, unit_no, atom)
        VALUES
        (%s, %s, %s, %s)
        """

        for unit_no in range(end_unit, data.start_unit + 1):
            for atom in atoms:
                cursor.execute(insert_atom_sql, (molecule_id, data.rack_id, unit_no, atom))

        insert_mount_sql = """
        INSERT INTO MountOperation
        (object_id, old_molecule_id, new_molecule_id, user_name, comment)
        VALUES
        (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_mount_sql, (data.object_id, None, molecule_id, user_name, None))

        database.commit()

        return {
            "message": "Servidor alocado com sucesso",
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


def unallocate_server_from_rack(object_id: int):

    user_name = "API - user"

    database = connect()
    cursor = database.cursor()

    allowed_objtype = 4  # Server
    atoms = ["front", "interior", "rear"]

    try:
        cursor.execute("START TRANSACTION")

        # VALIDATE IF THE OBJECT EXISTS AND IS A SERVER
        check_object_sql = """
        SELECT id, objtype_id
        FROM Object
        WHERE id = %s
        LIMIT 1
        """
        cursor.execute(check_object_sql, (object_id,))
        object_row = cursor.fetchone()

        if not object_row:
            database.rollback()
            return {"error": "Objeto n�o encontrado"}

        if object_row[1] != allowed_objtype:
            database.rollback()
            return {"error": "Somente objetos do tipo Server podem ser desalocados nesta fun��o"}

        # FIND IF IT IS ALLOCATED AND IN WHICH RACK
        get_allocated_space_sql = """
        SELECT rack_id, unit_no, atom
        FROM RackSpace
        WHERE object_id = %s
        ORDER BY unit_no ASC, atom ASC
        """
        cursor.execute(get_allocated_space_sql, (object_id,))
        occupied_spaces = cursor.fetchall()

        if not occupied_spaces:
            database.rollback()
            return {"error": "Este servidor n�o est� alocado em nenhum rack"}

        rack_id = occupied_spaces[0][0]

        # unique occupied units
        occupied_units = sorted({row[1] for row in occupied_spaces})

        # REMOVE FROM RACKSPACE
        delete_rackspace_sql = """
        DELETE FROM RackSpace
        WHERE rack_id = %s
          AND unit_no = %s
          AND atom = %s
        """

        for unit_no in occupied_units:
            for atom in atoms:
                cursor.execute(delete_rackspace_sql, (rack_id, unit_no, atom))

        # CLEAR THUMBNAIL
        delete_thumbnail_sql = """
        DELETE FROM RackThumbnail
        WHERE rack_id = %s
        """
        cursor.execute(delete_thumbnail_sql, (rack_id,))

         # CREATE MOLECULE
        cursor.execute("INSERT INTO Molecule VALUES()")
        molecule_id = cursor.lastrowid

        # CREATE ATOMS
        insert_atom_sql = """
        INSERT INTO Atom
        (molecule_id, rack_id, unit_no, atom)
        VALUES
        (%s, %s, %s, %s)
        """

        for unit_no in occupied_units:
            for atom in atoms:
                cursor.execute(insert_atom_sql, (molecule_id, rack_id, unit_no, atom))

        # REGISTER UNMOUNT
        # old_molecule_id = molecule created now
        # new_molecule_id = NULL
        insert_mount_sql = """
        INSERT INTO MountOperation
        (object_id, old_molecule_id, new_molecule_id, user_name, comment)
        VALUES
        (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_mount_sql, (object_id, molecule_id, None, user_name, None))

        database.commit()

        return {
            "message": "Servidor desalocado com sucesso",
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
