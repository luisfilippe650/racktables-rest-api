def delete_file_links(cursor, entity_id: int, entity_type: str = 'object'):
    cursor.execute("""
        DELETE FROM FileLink
        WHERE entity_type = %s AND entity_id = %s
    """, (entity_type, entity_id))

def delete_tags(cursor, entity_id: int, entity_realm: str = 'object'):
    cursor.execute("""
        DELETE FROM TagStorage
        WHERE entity_realm = %s AND entity_id = %s
    """, (entity_realm, entity_id))

def delete_attribute_values(cursor, object_id: int):
    """
    Explicitly deletes attribute values for an object.
    Even with CASCADE, this ensures clean removal.
    """
    cursor.execute("DELETE FROM AttributeValue WHERE object_id = %s", (object_id,))

def delete_network_data(cursor, object_id: int):
    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (object_id,))

def delete_entity_links(cursor, entity_id: int, entity_type: str = 'object'):
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = %s AND parent_entity_id = %s)
           OR (child_entity_type = %s AND child_entity_id = %s)
    """, (entity_type, entity_id, entity_type, entity_id))

def delete_mount_data(cursor, object_id: int):
    cursor.execute("""
        SELECT old_molecule_id AS molecule_id
        FROM MountOperation
        WHERE object_id = %s
          AND old_molecule_id IS NOT NULL
        UNION
        SELECT new_molecule_id AS molecule_id
        FROM MountOperation
        WHERE object_id = %s
          AND new_molecule_id IS NOT NULL
    """, (object_id, object_id))
    molecule_ids = [
        row["molecule_id"] if isinstance(row, dict) else row[0]
        for row in cursor.fetchall()
    ]

    if molecule_ids:
        placeholders = ", ".join(["%s"] * len(molecule_ids))
        cursor.execute(f"DELETE FROM Atom WHERE molecule_id IN ({placeholders})", tuple(molecule_ids))
        cursor.execute(f"DELETE FROM Molecule WHERE id IN ({placeholders})", tuple(molecule_ids))

    cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (object_id,))

def delete_port_data(cursor, object_id: int):
    # Remove physical links first to avoid orphans in the Link table
    cursor.execute("""
        DELETE FROM Link
        WHERE porta IN (SELECT id FROM Port WHERE object_id = %s)
           OR portb IN (SELECT id FROM Port WHERE object_id = %s)
    """, (object_id, object_id))

    cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM Port WHERE object_id = %s", (object_id,))

def insert_history_record(cursor, user_name: str, object_id: int):
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
    cursor.execute(sql, (user_name, object_id))

def get_object_basic_info(cursor, object_id: int):
    sql = "SELECT id, objtype_id FROM Object WHERE id = %s LIMIT 1"
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()

def get_object_basic_info_for_update(cursor, object_id: int):
    sql = "SELECT id, objtype_id FROM Object WHERE id = %s LIMIT 1 FOR UPDATE"
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()

def update_object_name(cursor, object_id: int, name: str):
    sql = "UPDATE Object SET name = %s WHERE id = %s"
    cursor.execute(sql, (name, object_id))

def update_object_comment(cursor, object_id: int, comment: str):
    sql = "UPDATE Object SET comment = %s WHERE id = %s"
    cursor.execute(sql, (comment, object_id))
