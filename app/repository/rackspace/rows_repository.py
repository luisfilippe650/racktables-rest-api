from app.utils.objtype import ROW, LOCATION


def count_rows_by_name(cursor, name: str, objtype_id: int):
    sql = """
    SELECT COUNT(*) as count
    FROM Object
    WHERE name = %s
      AND objtype_id = %s
    """
    cursor.execute(sql, (name, objtype_id))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0]


def insert_row(cursor, name: str, objtype_id: int):
    sql = """
    INSERT INTO Object
    (name, label, objtype_id, asset_no)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, None))
    return cursor.lastrowid


def get_row_by_id(cursor, row_id: int):
    sql = "SELECT id FROM Object WHERE id = %s AND objtype_id = %s LIMIT 1"
    cursor.execute(sql, (row_id, ROW))
    return cursor.fetchone()


def get_location_by_id(cursor, location_id: int):
    sql = "SELECT id FROM Object WHERE id = %s AND objtype_id = %s LIMIT 1"
    cursor.execute(sql, (location_id, LOCATION))
    return cursor.fetchone()


def update_row_name_query(cursor, row_id: int, row_name: str):
    sql = "UPDATE Object SET name = %s WHERE id = %s AND objtype_id = %s"
    cursor.execute(sql, (row_name, row_id, ROW))


def row_has_linked_racks(cursor, row_id: int):
    sql = """
    SELECT COUNT(*) as count
    FROM EntityLink
    WHERE parent_entity_type = 'row'
      AND parent_entity_id = %s
      AND child_entity_type = 'rack'
    """
    cursor.execute(sql, (row_id,))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count'] > 0
    return result[0] > 0


def check_location_row_link(cursor, location_id: int, row_id: int):
    sql = """
    SELECT 1
    FROM EntityLink
    WHERE parent_entity_type = 'location'
      AND parent_entity_id = %s
      AND child_entity_type = 'row'
      AND child_entity_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (location_id, row_id))
    return cursor.fetchone()


def get_location_link_for_row(cursor, row_id: int):
    sql = """
    SELECT parent_entity_id AS location_id
    FROM EntityLink
    WHERE parent_entity_type = 'location'
      AND child_entity_type = 'row'
      AND child_entity_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (row_id,))
    return cursor.fetchone()


def count_row_name(cursor, row_name: str, row_id: int = None):
    if row_id is None:
        sql = f"SELECT COUNT(*) as count FROM Object WHERE name = %s AND objtype_id = {ROW}"
        cursor.execute(sql, (row_name,))
    else:
        sql = f"SELECT COUNT(*) as count FROM Object WHERE name = %s AND id != %s AND objtype_id = {ROW}"
        cursor.execute(sql, (row_name, row_id))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0]


def insert_location_row_link(cursor, location_id: int, row_id: int):
    sql = """
    INSERT INTO EntityLink
    (parent_entity_type, parent_entity_id, child_entity_type, child_entity_id)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, ("location", location_id, "row", row_id))


def delete_location_row_link(cursor, location_id: int, row_id: int):
    sql = """
    DELETE FROM EntityLink
    WHERE parent_entity_type = 'location'
      AND parent_entity_id = %s
      AND child_entity_type = 'row'
      AND child_entity_id = %s
    """
    cursor.execute(sql, (location_id, row_id))


def fix_null_location_link(cursor, location_id: int, row_id: int):
    sql = """
    UPDATE EntityLink
    SET parent_entity_id = %s
    WHERE parent_entity_type = 'location'
      AND parent_entity_id IS NULL
      AND child_entity_type = 'row'
      AND child_entity_id = %s
    """
    cursor.execute(sql, (location_id, row_id))


def anonymize_row_before_delete(cursor, row_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL, label = ''
        WHERE id = %s
          AND objtype_id = %s
    """, (row_id, ROW))


def delete_row_object(cursor, row_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s AND objtype_id = %s", (row_id, ROW))


def count_rows_query(cursor, row_objtype_id: int):
    query = "SELECT COUNT(*) as count FROM Object WHERE objtype_id = %s"
    cursor.execute(query, (row_objtype_id,))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def list_rows_query(cursor, row_objtype_id: int, limit: int, offset: int):
    query = """
    SELECT id, name, label
    FROM Object
    WHERE objtype_id = %s
    ORDER BY name
    LIMIT %s OFFSET %s
    """
    cursor.execute(query, (row_objtype_id, limit, offset))
    return cursor.fetchall()


def list_complete_rows_query(cursor, row_objtype_id: int, rack_objtype_id: int, limit: int, offset: int):
    query = """
    SELECT
        row_obj.id AS row_id,
        row_obj.name AS row_name,
        row_obj.label,
        rack.id AS rack_id,
        rack.name AS rack_name
    FROM (
        SELECT id, name, label
        FROM Object
        WHERE objtype_id = %s
        ORDER BY name
        LIMIT %s OFFSET %s
    ) row_obj
    LEFT JOIN EntityLink el
        ON el.parent_entity_type = 'row'
       AND el.parent_entity_id = row_obj.id
       AND el.child_entity_type = 'rack'
    LEFT JOIN Object rack
        ON rack.id = el.child_entity_id
       AND rack.objtype_id = %s
    ORDER BY row_obj.name, rack.name
    """
    cursor.execute(query, (row_objtype_id, limit, offset, rack_objtype_id))

    rows_by_id = {}
    for row in cursor.fetchall():
        row_id = row["row_id"]
        if row_id not in rows_by_id:
            rows_by_id[row_id] = {
                "row_id": row_id,
                "row_name": row["row_name"],
                "label": row["label"],
                "racks": []
            }

        if row["rack_id"] is not None:
            rows_by_id[row_id]["racks"].append({
                "id": row["rack_id"],
                "name": row["rack_name"]
            })

    return list(rows_by_id.values())
