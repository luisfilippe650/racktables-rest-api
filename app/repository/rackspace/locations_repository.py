def count_location_by_name(cursor, name: str, objtype_id: int):
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
    return result[0] if result else 0


def insert_location(cursor, name: str, objtype_id: int):
    sql = """
    INSERT INTO Object (name, label, objtype_id, asset_no)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, None))
    return cursor.lastrowid


def get_location_by_id(cursor, location_id: int, objtype_id: int):
    sql = """
    SELECT id, name
    FROM Object
    WHERE id = %s
      AND objtype_id = %s
    """
    cursor.execute(sql, (location_id, objtype_id))
    row = cursor.fetchone()
    if row:
        if isinstance(row, dict):
            return row
        return {"id": row[0], "name": row[1]}
    return None


def count_rows_linked_to_location(cursor, location_id: int):
    sql = """
    SELECT COUNT(*) as count
    FROM EntityLink
    WHERE parent_entity_type = 'location'
      AND parent_entity_id = %s
      AND child_entity_type = 'row'
    """
    cursor.execute(sql, (location_id,))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def count_racks_linked_to_location(cursor, location_id: int):
    sql = """
    SELECT COUNT(DISTINCT rack_link.child_entity_id) as count
    FROM EntityLink location_link
    JOIN EntityLink rack_link
      ON rack_link.parent_entity_type = 'row'
     AND rack_link.parent_entity_id = location_link.child_entity_id
     AND rack_link.child_entity_type = 'rack'
    WHERE location_link.parent_entity_type = 'location'
      AND location_link.parent_entity_id = %s
      AND location_link.child_entity_type = 'row'
    """
    cursor.execute(sql, (location_id,))
    result = cursor.fetchone()
    via_rows = result['count'] if isinstance(result, dict) else (result[0] if result else 0)

    direct_sql = """
    SELECT COUNT(*) as count
    FROM EntityLink
    WHERE parent_entity_type = 'location'
      AND parent_entity_id = %s
      AND child_entity_type = 'rack'
    """
    cursor.execute(direct_sql, (location_id,))
    direct_result = cursor.fetchone()
    direct = direct_result['count'] if isinstance(direct_result, dict) else (direct_result[0] if direct_result else 0)

    return via_rows + direct


def prepare_location_for_delete(cursor, location_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
    """, (location_id,))


def delete_location_object(cursor, location_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s", (location_id,))


def count_locations_query(cursor, OBJTYPE_LOCATION):
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM Object
        WHERE objtype_id = %s
    """, (OBJTYPE_LOCATION,))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def list_locations_query(cursor, OBJTYPE_LOCATION, limit: int, offset: int):
    cursor.execute("""
        SELECT id, name FROM Object
        WHERE objtype_id = %s
        ORDER BY name
        LIMIT %s OFFSET %s
    """, (OBJTYPE_LOCATION, limit, offset))
    rows = cursor.fetchall()
    return [r if isinstance(r, dict) else {"id": r[0], "name": r[1]} for r in rows]


def list_complete_location_query(cursor, OBJTYPE_LOCATION, OBJTYPE_ROW, limit: int, offset: int):
    cursor.execute("""
        SELECT 
            loc.id        AS location_id,
            loc.name      AS location_name,
            o.id          AS row_id,
            o.name        AS row_name
        FROM (
            SELECT id, name
            FROM Object
            WHERE objtype_id = %s
            ORDER BY name
            LIMIT %s OFFSET %s
        ) loc
        LEFT JOIN EntityLink el 
            ON el.parent_entity_id = loc.id
            AND el.parent_entity_type = 'location'
            AND el.child_entity_type  = 'row'
        LEFT JOIN Object o 
            ON o.id = el.child_entity_id
            AND o.objtype_id = %s
        ORDER BY loc.name, o.name
    """, (OBJTYPE_LOCATION, limit, offset, OBJTYPE_ROW))

    result = {}
    for r in cursor.fetchall():
        if isinstance(r, dict):
            loc_id = r['location_id']
            loc_name = r['location_name']
            row_id = r['row_id']
            row_name = r['row_name']
        else:
            loc_id, loc_name, row_id, row_name = r

        if loc_id not in result:
            result[loc_id] = {
                "location_id": loc_id,
                "location_name": loc_name,
                "rows": []
            }
        if row_id is not None:
            result[loc_id]["rows"].append({"id": row_id, "name": row_name})

    return list(result.values())
