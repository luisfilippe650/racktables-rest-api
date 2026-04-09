def count_location_by_name(cursor, name: str):
    sql = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
      AND id != 0
    """
    cursor.execute(sql, (name,))
    return cursor.fetchone()[0]


def insert_location(cursor, name: str, objtype_id: int):
    sql = """
    INSERT INTO Object (name, label, objtype_id, asset_no)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, None))
    return cursor.lastrowid


def insert_location_history(cursor, user_name: str, location_id: int):
    sql = """
    INSERT INTO ObjectHistory
        (id, name, label, objtype_id, asset_no, has_problems, comment, ctime, user_name)
    SELECT
        id,
        name,
        label,
        objtype_id,
        asset_no,
        has_problems,
        comment,
        CURRENT_TIMESTAMP(),
        %s
    FROM Object
    WHERE id = %s
    """
    cursor.execute(sql, (user_name, location_id))


def get_location_by_id(cursor, location_id: int, objtype_id: int):
    sql = """
    SELECT id, name
    FROM Object
    WHERE id = %s
      AND objtype_id = %s
    """
    cursor.execute(sql, (location_id, objtype_id))
    return cursor.fetchone()

def delete_location_dependencies(cursor, location_id: int):

    cursor.execute("DELETE FROM FileLink WHERE entity_type = 'location' AND entity_id = %s", (location_id,))
    cursor.execute("DELETE FROM TagStorage WHERE entity_realm = 'location' AND entity_id = %s", (location_id,))

    cursor.execute("DELETE FROM FileLink WHERE entity_type = 'object' AND entity_id = %s", (location_id,))
    cursor.execute("DELETE FROM TagStorage WHERE entity_realm = 'object' AND entity_id = %s", (location_id,))

    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (location_id,))

    cursor.execute("""
    DELETE FROM EntityLink
    WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
       OR (child_entity_type = 'object' AND child_entity_id = %s)
    """, (location_id, location_id))

    cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM Port WHERE object_id = %s", (location_id,))


def list_complete_location_query(cursor, location_objtype_id: int, row_objtype_id: int):
    cursor.execute("""
    SELECT id, name
    FROM Object
    WHERE objtype_id = %s
    ORDER BY name
    """, (location_objtype_id,))

    locations_data = cursor.fetchall()

    result = []

    for loc in locations_data:
        location_id = loc[0]
        location_name = loc[1]

        cursor.execute("""
        SELECT o.id, o.name
        FROM EntityLink el
        JOIN Object o ON o.id = el.child_entity_id
        WHERE el.parent_entity_type = 'location'
          AND el.parent_entity_id = %s
          AND el.child_entity_type = 'row'
          AND o.objtype_id = %s
        ORDER BY o.name
        """, (location_id, row_objtype_id))

        rows = cursor.fetchall()

        rows_list = []

        for r in rows:
            rows_list.append({
                "id": r[0],
                "name": r[1]
            })

        result.append({
            "location_id": location_id,
            "location_name": location_name,
            "rows": rows_list
        })

    return result