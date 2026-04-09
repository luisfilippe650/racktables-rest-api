def count_rows_by_name(cursor, name: str, objtype_id: int):
    sql = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
      AND objtype_id = %s
    """
    cursor.execute(sql, (name, objtype_id))
    return cursor.fetchone()[0]


def insert_row(cursor, name: str, objtype_id: int):
    sql = """
    INSERT INTO Object
    (name, label, objtype_id, asset_no)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, None))
    return cursor.lastrowid


def insert_row_history(cursor, user_name: str, row_id: int):
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
    cursor.execute(sql, (user_name, row_id))


def get_object_by_id(cursor, row_id: int):
    sql = """
    SELECT id, name, objtype_id
    FROM Object
    WHERE id = %s
    LIMIT 1
    """
    cursor.execute(sql, (row_id,))
    return cursor.fetchone()


def get_row_by_id(cursor, row_id: int):
    sql = """
    SELECT id
    FROM Object
    WHERE id = %s
      AND objtype_id = 1561
    LIMIT 1
    """
    cursor.execute(sql, (row_id,))
    return cursor.fetchone()


def get_location_by_id(cursor, location_id: int):
    sql = """
    SELECT id
    FROM Object
    WHERE id = %s
      AND objtype_id = 1562
    LIMIT 1
    """
    cursor.execute(sql, (location_id,))
    return cursor.fetchone()


def update_row_name(cursor, row_id: int, row_name: str):
    sql = """
    UPDATE Object
    SET name = %s
    WHERE id = %s
      AND objtype_id = 1561
    """
    cursor.execute(sql, (row_name, row_id))


def update_row_after_unlink(cursor, row_id: int, row_name: str):
    sql = """
    UPDATE Object
    SET
        name = %s,
        label = NULL,
        has_problems = 'no',
        asset_no = NULL,
        comment = NULL
    WHERE id = %s
      AND objtype_id = 1561
    """
    cursor.execute(sql, (row_name, row_id))


def update_row_name_query(cursor, row_id: int, row_name: str):
    sql = """
    UPDATE Object
    SET
        name = %s,
        label = NULL,
        has_problems = 'no',
        asset_no = NULL,
        comment = NULL
    WHERE id = %s
      AND objtype_id = 1561
    """
    cursor.execute(sql, (row_name, row_id))


def row_has_linked_racks(cursor, row_id: int):
    sql = """
    SELECT 1
    FROM EntityLink
    WHERE parent_entity_type = 'row'
      AND parent_entity_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (row_id,))
    return cursor.fetchone()


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


def count_row_name(cursor, row_name: str, row_id: int):
    sql = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
      AND id != %s
      AND objtype_id = 1561
    """
    cursor.execute(sql, (row_name, row_id))
    return cursor.fetchone()[0]


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


def delete_row_file_links(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM FileLink
        WHERE entity_type = 'object' AND entity_id = %s
    """, (row_id,))


def delete_row_tags(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM TagStorage
        WHERE entity_realm = 'object' AND entity_id = %s
    """, (row_id,))


def delete_row_network_data(cursor, row_id: int):
    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (row_id,))


def delete_row_object_relationships(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
           OR (child_entity_type = 'object' AND child_entity_id = %s)
    """, (row_id, row_id))


def delete_row_relationships(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = 'row' AND parent_entity_id = %s)
           OR (child_entity_type = 'row' AND child_entity_id = %s)
    """, (row_id, row_id))


def delete_row_mount_data(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM Atom
        WHERE molecule_id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
    """, (row_id,))

    cursor.execute("""
        DELETE FROM Molecule
        WHERE id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
    """, (row_id,))

    cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (row_id,))


def delete_row_vlan_and_ports(cursor, row_id: int):
    cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (row_id,))
    cursor.execute("DELETE FROM Port WHERE object_id = %s", (row_id,))


def anonymize_row_before_delete(cursor, row_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL, label = ''
        WHERE id = %s
          AND objtype_id = 1561
    """, (row_id,))


def delete_row_object(cursor, row_id: int):
    cursor.execute("""
        DELETE FROM Object
        WHERE id = %s
          AND objtype_id = 1561
    """, (row_id,))


def list_rows_query(cursor, row_objtype_id: int):
    query = """
    SELECT id, name, label
    FROM Object
    WHERE objtype_id = %s
    ORDER BY name
    """
    cursor.execute(query, (row_objtype_id,))
    return cursor.fetchall()


def list_complete_rows_query(cursor, row_objtype_id: int, rack_objtype_id: int):
    query_rows = """
    SELECT id, name, label
    FROM Object
    WHERE objtype_id = %s
    ORDER BY name
    """

    cursor.execute(query_rows, (row_objtype_id,))
    rows = cursor.fetchall()

    result = []

    for row in rows:
        row_id = row["id"]

        query_racks = """
        SELECT o.id, o.name
        FROM EntityLink el
        JOIN Object o ON o.id = el.child_entity_id
        WHERE el.parent_entity_type = 'row'
          AND el.parent_entity_id = %s
          AND el.child_entity_type = 'rack'
          AND o.objtype_id = %s
        ORDER BY o.name
        """

        cursor.execute(query_racks, (row_id, rack_objtype_id))
        racks = cursor.fetchall()

        result.append({
            "row_id": row["id"],
            "row_name": row["name"],
            "label": row["label"],
            "racks": racks
        })

    return result