from app.utils.objtype import RACK
from app.utils.attribute_ids import HEIGHT

def get_rack_by_id(cursor, rack_id: int):
    sql = "SELECT id FROM Object WHERE id = %s AND objtype_id = %s LIMIT 1"
    cursor.execute(sql, (rack_id, RACK))
    return cursor.fetchone()


def get_rack_height(cursor, rack_id: int):
    sql = f"""
    SELECT av.uint_value
    FROM AttributeValue av
    JOIN Object o ON o.id = av.object_id
    WHERE av.object_id = %s
      AND av.object_tid = {RACK}
      AND av.attr_id = {HEIGHT}
      AND o.objtype_id = {RACK}
    LIMIT 1
    """
    cursor.execute(sql, (rack_id,))
    row = cursor.fetchone()
    if row:
        return row['uint_value'] if isinstance(row, dict) else row[0]
    return None


def get_allocated_spaces_by_object_id(cursor, object_id: int):
    sql = """
    SELECT rack_id, unit_no, atom
    FROM RackSpace
    WHERE object_id = %s
    ORDER BY unit_no ASC, atom ASC
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchall()


def lock_rackspace_for_rack(cursor, rack_id: int):
    sql = """
    SELECT rack_id, unit_no, atom, object_id
    FROM RackSpace
    WHERE rack_id = %s
    FOR UPDATE
    """
    cursor.execute(sql, (rack_id,))
    return cursor.fetchall()


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


def get_occupied_positions_in_range(cursor, rack_id: int, start_unit: int, end_unit: int):
    sql = """
    SELECT unit_no, atom, object_id
    FROM RackSpace
    WHERE rack_id = %s
      AND unit_no BETWEEN %s AND %s
      AND object_id IS NOT NULL
    """
    cursor.execute(sql, (rack_id, end_unit, start_unit))
    return cursor.fetchall()


def delete_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str):
    sql = """
    DELETE FROM RackSpace
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
    """
    cursor.execute(sql, (rack_id, unit_no, atom))


def replace_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str, object_id: int):
    sql = """
    INSERT INTO RackSpace
    (rack_id, unit_no, atom, state, object_id)
    VALUES
    (%s, %s, %s, 'T', %s)
    ON DUPLICATE KEY UPDATE
        state = VALUES(state),
        object_id = VALUES(object_id)
    """
    cursor.execute(sql, (rack_id, unit_no, atom, object_id))


def clear_rack_thumbnail(cursor, rack_id: int):
    sql = "DELETE FROM RackThumbnail WHERE rack_id = %s"
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
