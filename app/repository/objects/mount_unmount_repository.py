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


def get_mounted_object(cursor, object_id: int):
    sql = "SELECT 1 FROM RackSpace WHERE object_id = %s LIMIT 1"
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


def replace_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str, object_id: int):
    sql = """
    INSERT INTO RackSpace
    (rack_id, unit_no, atom, state, object_id)
    VALUES
    (%s, %s, %s, 'T', %s)
    ON DUPLICATE KEY UPDATE
        state = CASE
            WHEN object_id IS NULL THEN VALUES(state)
            ELSE state
        END,
        object_id = CASE
            WHEN object_id IS NULL THEN VALUES(object_id)
            ELSE object_id
        END
    """
    cursor.execute(sql, (rack_id, unit_no, atom, object_id))


def count_allocated_positions_for_object_in_range(cursor, rack_id: int, start_unit: int, end_unit: int, object_id: int) -> int:
    sql = """
    SELECT COUNT(*) AS allocated_count
    FROM RackSpace
    WHERE rack_id = %s
      AND unit_no BETWEEN %s AND %s
      AND atom IN ('front', 'interior', 'rear')
      AND object_id = %s
    """
    cursor.execute(sql, (rack_id, end_unit, start_unit, object_id))
    row = cursor.fetchone()
    if isinstance(row, dict):
        return row["allocated_count"]
    return row[0] if row else 0


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


def get_allocated_spaces_by_object_id(cursor, object_id: int):
    sql = """
    SELECT rack_id, unit_no, atom
    FROM RackSpace
    WHERE object_id = %s
    ORDER BY unit_no ASC, atom ASC
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchall()


def delete_rackspace_position(cursor, rack_id: int, unit_no: int, atom: str, object_id: int):
    sql = """
    DELETE FROM RackSpace
    WHERE rack_id = %s
      AND unit_no = %s
      AND atom = %s
      AND object_id = %s
    """
    cursor.execute(sql, (rack_id, unit_no, atom, object_id))
    return cursor.rowcount
