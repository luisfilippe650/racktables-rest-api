def get_rack_by_id(cursor, rack_id: int, rack_objtype: int):
    sql = """
    SELECT id
    FROM Object
    WHERE id = %s
      AND objtype_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (rack_id, rack_objtype))
    return cursor.fetchone()

def get_object_by_id(cursor, object_id: int):
    sql = """
    SELECT id, objtype_id
    FROM Object
    WHERE id = %s
    LIMIT 1
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()

def get_mounted_object(cursor, object_id: int):
    sql = """
    SELECT 1
    FROM RackSpace
    WHERE object_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()

def get_occupied_position(cursor, rack_id: int, unit_no: int, atom: str):
    sql = """
    SELECT object_id
    FROM RackSpace
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
    LIMIT 1
    """
    cursor.execute(sql, (rack_id, unit_no, atom))
    return cursor.fetchone()

def replace_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str, object_id: int):
    delete_sql = """
    DELETE FROM RackSpace
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
    """

    insert_sql = """
    INSERT INTO RackSpace
    (rack_id, unit_no, atom, state)
    VALUES
    (%s, %s, %s, %s)
    """

    update_sql = """
    UPDATE RackSpace
    SET object_id = %s
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
    """

    cursor.execute(delete_sql, (rack_id, unit_no, atom))
    cursor.execute(insert_sql, (rack_id, unit_no, atom, "T"))
    cursor.execute(update_sql, (object_id, rack_id, unit_no, atom))


def clear_rack_thumbnail(cursor, rack_id: int):
    sql = """
    DELETE FROM RackThumbnail
    WHERE rack_id = %s
    """
    cursor.execute(sql, (rack_id,))


def create_molecule(cursor):
    cursor.execute("INSERT INTO Molecule VALUES()")
    return cursor.lastrowid


def insert_atom(cursor, molecule_id: int, rack_id: int, unit_no: int, atom: str):
    sql = """
    INSERT INTO Atom
    (molecule_id, rack_id, unit_no, atom)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (molecule_id, rack_id, unit_no, atom))


def insert_mount_operation(cursor, object_id: int, old_molecule_id, new_molecule_id, user_name: str, comment=None):
    sql = """
    INSERT INTO MountOperation
    (object_id, old_molecule_id, new_molecule_id, user_name, comment)
    VALUES
    (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (object_id, old_molecule_id, new_molecule_id, user_name, comment))


def get_allocated_spaces_by_object_id(cursor, object_id: int):
    sql = """
    SELECT rack_id, unit_no, atom
    FROM RackSpace
    WHERE object_id = %s
    ORDER BY unit_no ASC, atom ASC
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchall()


def delete_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str):
    sql = """
    DELETE FROM RackSpace
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
    """
    cursor.execute(sql, (rack_id, unit_no, atom))