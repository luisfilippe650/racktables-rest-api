def count_location_by_name(cursor, name: str):
    # Counts how many locations exist with the given name
    sql = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
    """
    cursor.execute(sql, (name,))
    return cursor.fetchone()[0]


def insert_location(cursor, name: str, objtype_id: int):
    # Inserts a new location into Object table
    sql = """
    INSERT INTO Object (name, label, objtype_id, asset_no)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, None))
    return cursor.lastrowid


def insert_location_history(cursor, user_name: str, location_id: int):
    # Inserts a history record for the created location
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
    # Retrieves a location by ID and validates its type
    sql = """
    SELECT id, name
    FROM Object
    WHERE id = %s
      AND objtype_id = %s
    """
    cursor.execute(sql, (location_id, objtype_id))
    return cursor.fetchone()


def delete_location_dependencies(cursor, location_id: int):
    # cleanup of attachments and tags from location realm
    cursor.execute(
        "DELETE FROM FileLink WHERE entity_type = 'location' AND entity_id = %s",
        (location_id,)
    )
    cursor.execute(
        "DELETE FROM TagStorage WHERE entity_realm = 'location' AND entity_id = %s",
        (location_id,)
    )

    # cleanup of attachments and tags from object realm
    cursor.execute(
        "DELETE FROM FileLink WHERE entity_type = 'object' AND entity_id = %s",
        (location_id,)
    )
    cursor.execute(
        "DELETE FROM TagStorage WHERE entity_realm = 'object' AND entity_id = %s",
        (location_id,)
    )

    # cleanup of network-related tables
    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (location_id,))

    # cleanup of generic object links
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
           OR (child_entity_type = 'object' AND child_entity_id = %s)
    """, (location_id, location_id))

    # cleanup of structures related to mount operations
    cursor.execute("""
        DELETE FROM Atom
        WHERE molecule_id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
              AND new_molecule_id IS NOT NULL
        )
    """, (location_id,))

    cursor.execute("""
        DELETE FROM Molecule
        WHERE id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
              AND new_molecule_id IS NOT NULL
        )
    """, (location_id,))

    # cleanup of physical mounting
    cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (location_id,))

    # cleanup of port and VLAN auxiliary tables
    cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (location_id,))
    cursor.execute("DELETE FROM Port WHERE object_id = %s", (location_id,))


def prepare_location_for_delete(cursor, location_id: int):
    # prepares the object for deletion (nullifies name and resets label)
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
    """, (location_id,))


def delete_location_object(cursor, location_id: int):
    # deletes the location from Object table
    cursor.execute(
        "DELETE FROM Object WHERE id = %s",
        (location_id,)
    )


def delete_location_entity_links(cursor, location_id: int):
    # removes links between location, rack and row entities
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type IN ('rack', 'row', 'location') AND parent_entity_id = %s)
           OR (child_entity_type IN ('rack', 'row', 'location') AND child_entity_id = %s)
    """, (location_id, location_id))


def list_complete_location_query(cursor, location_objtype_id: int, row_objtype_id: int):
    # lists all locations with their related rows
    cursor.execute("""
        SELECT id, name
        FROM Object
        WHERE objtype_id = %s
        ORDER BY name
    """, (location_objtype_id,))

    locations_data = cursor.fetchall()
    result = []

    for location in locations_data:
        location_id = location[0]
        location_name = location[1]

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

        rows_list = [
            {"id": row[0], "name": row[1]}
            for row in rows
        ]

        result.append({
            "location_id": location_id,
            "location_name": location_name,
            "rows": rows_list
        })

    return result