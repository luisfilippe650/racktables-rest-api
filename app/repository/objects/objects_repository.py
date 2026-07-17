from app.utils.chapters import OBJECT_TYPE
from app.utils.objtype import RACK, ROW, LOCATION


def get_objtype_by_id(cursor, objtype_id: int):
    sql = f"""
    SELECT dict_key
    FROM Dictionary
    WHERE chapter_id = {OBJECT_TYPE}
      AND dict_key = %s
    LIMIT 1
    """
    cursor.execute(sql, (objtype_id,))
    return cursor.fetchone()


def count_objects_by_name(cursor, name: str, ignore_id: int = None):
    if ignore_id is not None:
        sql = """
        SELECT COUNT(*) as count
        FROM Object
        WHERE name = %s
          AND id != %s
        """
        cursor.execute(sql, (name, ignore_id))
    else:
        sql = """
        SELECT COUNT(*) as count
        FROM Object
        WHERE name = %s
        """
        cursor.execute(sql, (name,))

    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0]


def count_objects_by_service_tag(cursor, service_tag: str, ignore_id: int = None):
    if ignore_id is not None:
        sql = f"""
        SELECT COUNT(*) as count
        FROM Object
        WHERE asset_no = %s
          AND id != %s
          AND objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
        """
        cursor.execute(sql, (service_tag, ignore_id))
    else:
        sql = f"""
        SELECT COUNT(*) as count
        FROM Object
        WHERE asset_no = %s
          AND objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
        """
        cursor.execute(sql, (service_tag,))

    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0]


def insert_object(cursor, name: str, label: str, objtype_id: int, asset_no):
    sql = """
    INSERT INTO Object
    (name, label, objtype_id, asset_no)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, label, objtype_id, asset_no))
    return cursor.lastrowid


def insert_port(cursor, name: str, object_id: int, label, iif_id: int, port_type: int, l2address):
    sql = """
    INSERT INTO Port
    (name, object_id, label, iif_id, type, l2address)
    VALUES
    (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (name, object_id, label, iif_id, port_type, l2address))


def anonymize_object_before_delete(cursor, object_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
    """, (object_id,))


def delete_object_row(cursor, object_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s", (object_id,))


def object_has_current_mount(cursor, object_id: int):
    sql = """
    SELECT 1
    FROM RackSpace
    WHERE object_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()


def get_current_mount_details(cursor, object_id: int):
    sql = f"""
    SELECT
        rs.rack_id,
        rack.name AS rack_name,
        MIN(rs.unit_no) AS start_unit,
        MAX(rs.unit_no) AS end_unit,
        COUNT(DISTINCT rs.unit_no) AS height
    FROM RackSpace AS rs
    JOIN Object AS rack
      ON rack.id = rs.rack_id
     AND rack.objtype_id = {RACK}
    WHERE rs.object_id = %s
    GROUP BY rs.rack_id, rack.name
    ORDER BY rack.name, rs.rack_id
    """
    cursor.execute(sql, (object_id,))
    rows = cursor.fetchall()
    for row in rows:
        row["rack_id"] = int(row["rack_id"])
        row["start_unit"] = int(row["start_unit"])
        row["end_unit"] = int(row["end_unit"])
        row["height"] = int(row["height"])
    return rows


def object_has_mount_history(cursor, object_id: int):
    sql = """
    SELECT 1
    FROM MountOperation
    WHERE object_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()


def object_has_port_links(cursor, object_id: int):
    sql = """
    SELECT 1
    FROM Link
    WHERE porta IN (SELECT id FROM Port WHERE object_id = %s)
       OR portb IN (SELECT id FROM Port WHERE object_id = %s)
    LIMIT 1
    """
    cursor.execute(sql, (object_id, object_id))
    return cursor.fetchone()


def get_object_port_links(cursor, object_id: int):
    sql = """
    SELECT
        local_port.id AS local_port_id,
        local_port.name AS local_port_name,
        remote_port.id AS remote_port_id,
        remote_port.name AS remote_port_name,
        remote_object.id AS remote_object_id,
        remote_object.name AS remote_object_name,
        link.cable
    FROM Port AS local_port
    JOIN Link AS link
      ON link.porta = local_port.id
      OR link.portb = local_port.id
    JOIN Port AS remote_port
      ON remote_port.id = CASE
          WHEN link.porta = local_port.id THEN link.portb
          ELSE link.porta
      END
    JOIN Object AS remote_object
      ON remote_object.id = remote_port.object_id
    WHERE local_port.object_id = %s
    ORDER BY local_port.name, remote_object.name, remote_port.name
    """
    cursor.execute(sql, (object_id,))
    rows = cursor.fetchall()
    for row in rows:
        row["local_port_id"] = int(row["local_port_id"])
        row["remote_port_id"] = int(row["remote_port_id"])
        row["remote_object_id"] = int(row["remote_object_id"])
    return rows


def count_objects_query(cursor):
    query = f"""
    SELECT COUNT(*) as count
    FROM Object
    WHERE objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
    """
    cursor.execute(query)
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def count_all_objects_query(cursor):
    query = """
    SELECT COUNT(*) as count
    FROM Object
    """
    cursor.execute(query)
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def list_objects_query(cursor, limit: int, offset: int):
    query = f"""
    SELECT
        obj.id AS object_id,
        obj.name AS object_name,
        obj.label AS object_label,
        obj.asset_no,
        obj.objtype_id,
        d.dict_value AS object_type,
        CASE WHEN rs.rack_count = 1 THEN rack.id ELSE NULL END AS rack_id,
        CASE WHEN rs.rack_count = 1 THEN rack.name ELSE NULL END AS rack_name,
        COALESCE(rs.rack_count, 0) AS rack_count,
        CASE
            WHEN COALESCE(rs.rack_count, 0) > 1 THEN 'inconsistent_multiple_racks'
            WHEN COALESCE(rs.rack_count, 0) = 1 THEN 'allocated'
            ELSE 'not_allocated'
        END AS allocation_status
    FROM Object AS obj
    LEFT JOIN Dictionary AS d
        ON d.chapter_id = {OBJECT_TYPE}
       AND d.dict_key = obj.objtype_id
    LEFT JOIN (
        SELECT
            object_id,
            MIN(rack_id) AS rack_id,
            COUNT(DISTINCT rack_id) AS rack_count
        FROM RackSpace
        WHERE object_id IS NOT NULL
        GROUP BY object_id
    ) AS rs
        ON rs.object_id = obj.id
    LEFT JOIN Object AS rack
        ON rack.id = rs.rack_id
       AND rack.objtype_id = {RACK}
    WHERE obj.objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
    ORDER BY obj.name
    LIMIT %s OFFSET %s
    """
    cursor.execute(query, (limit, offset))
    return cursor.fetchall()


def list_all_objects_query(cursor, limit: int, offset: int):
    query = f"""
    SELECT
        obj.id AS object_id,
        obj.name AS object_name,
        obj.label AS object_label,
        obj.asset_no,
        obj.objtype_id,
        d.dict_value AS object_type,
        obj.has_problems,
        obj.comment
    FROM Object AS obj
    LEFT JOIN Dictionary AS d
        ON d.chapter_id = {OBJECT_TYPE}
       AND d.dict_key = obj.objtype_id
    ORDER BY obj.name, obj.id
    LIMIT %s OFFSET %s
    """
    cursor.execute(query, (limit, offset))
    return cursor.fetchall()


def get_objects_by_name_query(cursor, name: str):
    query = f"""
    SELECT
        id AS object_id,
        name
    FROM Object
    WHERE name = %s
      AND objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
    ORDER BY id
    LIMIT 2
    """
    cursor.execute(query, (name,))
    return cursor.fetchall()


def get_objects_by_service_tag_query(cursor, service_tag: str):
    query = f"""
    SELECT
        id AS object_id,
        name,
        asset_no AS service_tag
    FROM Object
    WHERE asset_no = %s
      AND objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
    ORDER BY id
    LIMIT 2
    """
    cursor.execute(query, (service_tag,))
    return cursor.fetchall()


def list_object_types_query(cursor):
    query = f"""
    SELECT
        dict_key AS objtype_id,
        dict_value AS objtype_name
    FROM Dictionary
    WHERE chapter_id = {OBJECT_TYPE}
    ORDER BY dict_value
    """
    cursor.execute(query)
    return cursor.fetchall()

def add_comment(cursor, object_id: int, name: str, label: str | None,
                   has_problems: str, asset_no: str | None, comment: str | None,
                   user_name: str = "admin", record_history: bool = True):
    """
    Updates object fields including comment and optionally records a single
    history entry. `record_history` controls whether an ObjectHistory row is
    inserted. Default True preserves previous behavior; callers can set False
    to avoid duplicate history entries when they already inserted history.
    """
    update_query = """
        UPDATE `Object`
        SET `name` = %s,
            `label` = %s,
            `has_problems` = %s,
            `asset_no` = %s,
            `comment` = %s
        WHERE `id` = %s
    """
    cursor.execute(update_query, (name, label, has_problems, asset_no, comment, object_id))

    if record_history:
        history_query = """
            INSERT INTO ObjectHistory
                (id, name, label, objtype_id, asset_no, has_problems, comment, ctime, user_name)
            SELECT id, name, label, objtype_id, asset_no, has_problems, comment, CURRENT_TIMESTAMP(), %s
            FROM Object
            WHERE id = %s
        """
        cursor.execute(history_query, (user_name, object_id))
