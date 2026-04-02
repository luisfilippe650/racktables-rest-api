from app.core.databaseConnection import connect
from app.schema.objects.objects_schema import CreateObject

def create_object(data: CreateObject):

    user_name = "API - user"

    database = connect()
    cursor = database.cursor()

    # allowed types in this function
    allowed_objtypes = {
        1,     # Generic
        4,     # Server
        7,     # Router
        8,     # Network switch
        9,     # Firewall
        1504,  # PatchPanel
        1505,  # PDU
        1506,  # UPS
    }

    # default ports by type
    default_ports_by_type = {
        4: [
            {"name": "kvm", "iif_id": 1, "type": 33, "label": None, "l2address": None},
            {"name": "eth0", "iif_id": 1, "type": 24, "label": None, "l2address": None},
            {"name": "eth1", "iif_id": 1, "type": 24, "label": None, "l2address": None},
        ],
    }

    try:
        cursor.execute("START TRANSACTION")

        # VALIDATE IF TYPE EXISTS
        check_objtype_sql = """
        SELECT dict_key
        FROM Dictionary
        WHERE chapter_id = 1
          AND dict_key = %s
        LIMIT 1
        """
        cursor.execute(check_objtype_sql, (data.objtype_id,))
        valid_type = cursor.fetchone()

        if not valid_type:
            database.rollback()
            return {"error": f"objtype_id {data.objtype_id} is not valid"}

        # VALIDATE IF THIS TYPE CAN BE CREATED HERE
        if data.objtype_id not in allowed_objtypes:
            database.rollback()
            return {
                "error": "This type cannot be created by this function",
                "objtype_id": data.objtype_id
            }

        # VALIDATE NAME
        check_name_sql = """
        SELECT COUNT(*)
        FROM Object
        WHERE name = %s
          AND id != 0
        """
        cursor.execute(check_name_sql, (data.name,))
        exists_count = cursor.fetchone()[0]

        if exists_count > 0:
            database.rollback()
            return {"error": "An object with this name already exists"}

        # CREATE OBJECT
        insert_object_sql = """
        INSERT INTO Object
        (name, label, objtype_id, asset_no)
        VALUES
        (%s, %s, %s, %s)
        """
        cursor.execute(
            insert_object_sql,
            (data.name, data.label, data.objtype_id, data.asset_no)
        )
        object_id = cursor.lastrowid

        # CREATE DEFAULT PORTS
        default_ports = default_ports_by_type.get(data.objtype_id, [])

        insert_port_sql = """
        INSERT INTO Port
        (name, object_id, label, iif_id, type, l2address)
        VALUES
        (%s, %s, %s, %s, %s, %s)
        """

        for port in default_ports:
            cursor.execute(
                insert_port_sql,
                (
                    port["name"],
                    object_id,
                    port["label"],
                    port["iif_id"],
                    port["type"],
                    port["l2address"]
                )
            )

        # HISTORY
        insert_history_sql = """
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
        cursor.execute(insert_history_sql, (user_name, object_id))

        database.commit()

        return {
            "message": "Object created successfully",
            "object_id": object_id,
            "name": data.name,
            "objtype_id": data.objtype_id,
            "ports_created": len(default_ports)
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def delete_object(object_id: int):
    user_name = "API - user"

    database = connect()
    cursor = database.cursor()

    # allowed types for delete in this function
    allowed_objtypes = {
        1,     # Generic
        4,     # Server
        7,     # Router
        8,     # Network switch
        9,     # Firewall
        1504,  # PatchPanel
        1505,  # PDU
        1506,  # UPS
    }

    try:
        cursor.execute("START TRANSACTION")

        # VALIDATE IF EXISTS AND GET TYPE
        get_object_sql = """
        SELECT id, objtype_id
        FROM Object
        WHERE id = %s
        LIMIT 1
        """
        cursor.execute(get_object_sql, (object_id,))
        result = cursor.fetchone()

        if not result:
            database.rollback()
            return {"error": "Object not found"}

        objtype_id = result[1]

        # BLOCK NON-ALLOWED TYPES
        if objtype_id not in allowed_objtypes:
            database.rollback()
            return {
                "error": "This type cannot be deleted by this function",
                "objtype_id": objtype_id
            }

        # INITIAL CLEANUP
        cursor.execute("""
            DELETE FROM FileLink
            WHERE entity_type = 'object' AND entity_id = %s
        """, (object_id,))

        cursor.execute("""
            DELETE FROM TagStorage
            WHERE entity_realm = 'object' AND entity_id = %s
        """, (object_id,))

        # NETWORK
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (object_id,))

        # RELATIONSHIPS
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
               OR (child_entity_type = 'object' AND child_entity_id = %s)
        """, (object_id, object_id))

        # MOUNT
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

        # VLAN / PORTS
        cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (object_id,))
        cursor.execute("DELETE FROM Port WHERE object_id = %s", (object_id,))

        # HISTORY (BEFORE UPDATE)
        cursor.execute("""
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
        """, (user_name, object_id))

        # UPDATE
        cursor.execute("""
            UPDATE Object
            SET name = NULL,
                label = ''
            WHERE id = %s
        """, (object_id,))

        # FINAL DELETE
        cursor.execute("DELETE FROM Object WHERE id = %s", (object_id,))

        # FINAL CLEANUP
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type IN ('rack', 'row', 'location') AND parent_entity_id = %s)
               OR (child_entity_type IN ('rack', 'row', 'location') AND child_entity_id = %s)
        """, (object_id, object_id))

        database.commit()

        return {
            "message": "Object deleted successfully",
            "object_id": object_id,
            "objtype_id": objtype_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_objects():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
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
        LEFT JOIN RackSpace AS rs
            ON rs.object_id = obj.id
        LEFT JOIN Object AS rack
            ON rack.id = rs.rack_id
           AND rack.objtype_id = 1560
        WHERE obj.objtype_id NOT IN (1560, 1561, 1562)
        ORDER BY obj.name
        """

        cursor.execute(query)
        objects = cursor.fetchall()

        return objects

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_object_types():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
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

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()