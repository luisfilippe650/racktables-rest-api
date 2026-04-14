def get_objtype_by_id(cursor, objtype_id: int):
    sql = """
    SELECT dict_key
    FROM Dictionary
    WHERE chapter_id = 1
      AND dict_key = %s
    LIMIT 1
    """
    cursor.execute(sql, (objtype_id,))
    return cursor.fetchone()


def count_objects_by_name(cursor, name: str, ignore_id: int = None):
    if ignore_id is not None:
        sql = """
        SELECT COUNT(*)
        FROM Object
        WHERE name = %s
          AND id != %s
        """
        cursor.execute(sql, (name, ignore_id))
    else:
        sql = """
        SELECT COUNT(*)
        FROM Object
        WHERE name = %s
        """
        cursor.execute(sql, (name,))

    return cursor.fetchone()[0]


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


def insert_object_history(cursor, user_name: str, object_id: int):
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


def get_object_by_id(cursor, object_id: int):
    sql = """
    SELECT id, objtype_id
    FROM Object
    WHERE id = %s
    LIMIT 1
    """
    cursor.execute(sql, (object_id,))
    return cursor.fetchone()


def delete_object_file_links(cursor, object_id: int):
    cursor.execute("""
        DELETE FROM FileLink
        WHERE entity_type = 'object' AND entity_id = %s
    """, (object_id,))


def delete_object_tags(cursor, object_id: int):
    cursor.execute("""
        DELETE FROM TagStorage
        WHERE entity_realm = 'object' AND entity_id = %s
    """, (object_id,))


def delete_object_network_data(cursor, object_id: int):
    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (object_id,))


def delete_object_relationships(cursor, object_id: int):
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
           OR (child_entity_type = 'object' AND child_entity_id = %s)
    """, (object_id, object_id))


def delete_object_mount_data(cursor, object_id: int):
    cursor.execute("""
        DELETE FROM Atom
        WHERE molecule_id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
    """, (object_id,))

    cursor.execute("""
        DELETE FROM Molecule
        WHERE id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
    """, (object_id,))

    cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (object_id,))


def delete_object_vlan_and_ports(cursor, object_id: int):
    cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (object_id,))
    cursor.execute("DELETE FROM Port WHERE object_id = %s", (object_id,))


def anonymize_object_before_delete(cursor, object_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
    """, (object_id,))


def delete_object_row(cursor, object_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s", (object_id,))


def final_cleanup_entity_links(cursor, object_id: int):
    cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type IN ('rack', 'row', 'location') AND parent_entity_id = %s)
           OR (child_entity_type IN ('rack', 'row', 'location') AND child_entity_id = %s)
    """, (object_id, object_id))


def list_objects_query(cursor):
    query = """
    SELECT
        obj.id AS object_id,
        obj.name AS object_name,
        obj.label AS object_label,
        obj.asset_no,
        obj.objtype_id,
        d.dict_value AS object_type,
        rack.id AS rack_id,
        rack.name AS rack_name
    FROM Object AS obj
    LEFT JOIN Dictionary AS d
        ON d.chapter_id = 1
       AND d.dict_key = obj.objtype_id
    LEFT JOIN (
        SELECT object_id, MIN(rack_id) AS rack_id
        FROM RackSpace
        WHERE object_id IS NOT NULL
        GROUP BY object_id
    ) AS rs
        ON rs.object_id = obj.id
    LEFT JOIN Object AS rack
        ON rack.id = rs.rack_id
       AND rack.objtype_id = 1560
    WHERE obj.objtype_id NOT IN (1560, 1561, 1562)
    ORDER BY obj.name
    """
    cursor.execute(query)
    return cursor.fetchall()

def list_object_types_query(cursor):
    query = """
    SELECT
        dict_key AS objtype_id,
        dict_value AS objtype_name
    FROM Dictionary
    WHERE chapter_id = 1
    ORDER BY dict_value
    """
    cursor.execute(query)
    return cursor.fetchall()


def update_object_name_query(cursor, object_id: int, object_name: str):
    sql = """
    UPDATE Object
    SET name = %s
    WHERE id = %s
    """
    cursor.execute(sql, (object_name, object_id))


def update_object_comment_query(cursor, object_id: int, comment: str):
    sql = """
    UPDATE Object
    SET comment = %s
    WHERE id = %s
    """
    cursor.execute(sql, (comment, object_id))