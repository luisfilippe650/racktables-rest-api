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


def prepare_location_for_delete(cursor, location_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
    """, (location_id,))


def delete_location_object(cursor, location_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s", (location_id,))


def list_locations_query(cursor, OBJTYPE_LOCATION):
    cursor.execute("""
        SELECT id, name FROM Object
        WHERE objtype_id = %s
        ORDER BY name
    """, (OBJTYPE_LOCATION,))
    rows = cursor.fetchall()
    return [r if isinstance(r, dict) else {"id": r[0], "name": r[1]} for r in rows]


def list_complete_location_query(cursor, OBJTYPE_LOCATION, OBJTYPE_ROW):
    cursor.execute("""
        SELECT 
            loc.id        AS location_id,
            loc.name      AS location_name,
            o.id          AS row_id,
            o.name        AS row_name
        FROM Object loc
        LEFT JOIN EntityLink el 
            ON el.parent_entity_id = loc.id
            AND el.parent_entity_type = 'location'
            AND el.child_entity_type  = 'row'
        LEFT JOIN Object o 
            ON o.id = el.child_entity_id
            AND o.objtype_id = %s
        WHERE loc.objtype_id = %s
        ORDER BY loc.name, o.name
    """, (OBJTYPE_ROW, OBJTYPE_LOCATION))

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
