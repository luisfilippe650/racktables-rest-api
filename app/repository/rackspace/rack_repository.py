from app.core.databaseConnection import connect
from app.schema.rackspace.rack_schema import CreateRack


def create_rack(data : CreateRack):

    user_name = "API - user"
    objtype_id = 1560  # Rack

    check_row_exists = """
            SELECT id
            FROM Object
            WHERE id = %s
              AND objtype_id = 1561
            LIMIT 1
            """

    create_rack_sql = """
            INSERT INTO Object
            (name, label, objtype_id, asset_no)
            VALUES
            (%s, %s, %s, %s)
            """

    add_on_history = """
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

    add_height_attribute = """
    INSERT INTO AttributeValue
    (uint_value, object_id, object_tid, attr_id)
    VALUES
    (%s, %s, %s, %s)
    """

    link_rack_to_row = """
            INSERT INTO EntityLink
            (parent_entity_type, parent_entity_id, child_entity_type, child_entity_id)
            VALUES
            (%s, %s, %s, %s)
            """

    add_row_attribute = """
           INSERT INTO AttributeValue
           (uint_value, object_id, object_tid, attr_id)
           VALUES
           (%s, %s, %s, %s)
           """

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # VALIDATE IF THE ROW EXISTS
        cursor.execute(check_row_exists, (data.row_id,))
        row_exists = cursor.fetchone()

        if not row_exists:
            database.rollback()
            return {"error": "Row não encontrado. Não é possível criar rack sem um row válido."}

        # CREATE THE RACK IN OBJECT
        cursor.execute(create_rack_sql, (data.name, None, objtype_id, data.assent_no))
        rack_id = cursor.lastrowid

        # HISTORY
        cursor.execute(add_on_history, (user_name, rack_id))

        # RACK HEIGHT (attr_id = 27)
        cursor.execute(add_height_attribute, (data.rack_height, rack_id, objtype_id, 27))

        # ROW TYPE / ORIENTATION (attr_id = 29)
        # value 1 = based on your test
        cursor.execute(add_row_attribute, (1, rack_id, objtype_id, 29))

        # LINK RACK TO ROW
        cursor.execute(link_rack_to_row, ("row", data.row_id, "rack", rack_id))

        database.commit()

        return {
            "message": "Rack criado com sucesso",
            "rack_id": rack_id,
            "row_id": data.row_id,
            "name": data.name,
            "rack_height": data.rack_height
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def delete_rack(rack_id: int):

    user_name = "API - user"

    # VALIDATE IF THE RACK EXISTS
    check_rack_exists = """
            SELECT id
            FROM Object
            WHERE id = %s
              AND objtype_id = 1560
            LIMIT 1
            """

    # VALIDATE IF THE RACK IS EMPTY
    # does not allow deleting a rack with mounted objects
    check_objects_in_rack = """
           SELECT 1
           FROM RackSpace
           WHERE rack_id = %s
             AND object_id IS NOT NULL
           LIMIT 1
           """

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute(check_rack_exists, (rack_id,))
        rack_exists = cursor.fetchone()

        if not rack_exists:
            database.rollback()
            return {"error": "Rack não encontrado"}

        cursor.execute(check_objects_in_rack, (rack_id,))
        has_objects = cursor.fetchone()

        if has_objects:
            database.rollback()
            return {"error": "Não é possível deletar o rack porque existem objetos/servidores montados nele"}

        #RACK-SPECIFIC CLEANUP
        cursor.execute("""
            DELETE FROM FileLink
            WHERE entity_type = 'rack'
              AND entity_id = %s
        """, (rack_id,))

        cursor.execute("""
            DELETE FROM TagStorage
            WHERE entity_realm = 'rack'
              AND entity_id = %s
        """, (rack_id,))

        cursor.execute("""
            DELETE FROM RackThumbnail
            WHERE rack_id = %s
        """, (rack_id,))

        cursor.execute("""
            DELETE FROM RackSpace
            WHERE rack_id = %s
        """, (rack_id,))

        # CLEANUP AS OBJECT
        cursor.execute("""
            DELETE FROM FileLink
            WHERE entity_type = 'object'
              AND entity_id = %s
        """, (rack_id,))

        cursor.execute("""
            DELETE FROM TagStorage
            WHERE entity_realm = 'object'
              AND entity_id = %s
        """, (rack_id,))

        # NETWORK / IP
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (rack_id,))

        # RELATIONSHIPS AS OBJECT
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
               OR (child_entity_type = 'object' AND child_entity_id = %s)
        """, (rack_id, rack_id))

        # MOUNT / POSITION
        cursor.execute("""
            DELETE FROM Atom
            WHERE molecule_id IN (
                SELECT new_molecule_id
                FROM MountOperation
                WHERE object_id = %s
            )
        """, (rack_id,))

        cursor.execute("""
            DELETE FROM Molecule
            WHERE id IN (
                SELECT new_molecule_id
                FROM MountOperation
                WHERE object_id = %s
            )
        """, (rack_id,))

        cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (rack_id,))

        # VLAN / PORTS
        cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (rack_id,))
        cursor.execute("DELETE FROM Port WHERE object_id = %s", (rack_id,))

        # UPDATE BEFORE DELETING
        cursor.execute("""
            UPDATE Object
            SET name = NULL,
                label = ''
            WHERE id = %s
        """, (rack_id,))

        # HISTORY
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
        """, (user_name,rack_id))

        # FINAL DELETE
        cursor.execute("""
            DELETE FROM Object
            WHERE id = %s
        """, (rack_id,))

        # FINAL HIERARCHY CLEANUP
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type IN ('rack', 'row', 'location') AND parent_entity_id = %s)
               OR (child_entity_type IN ('rack', 'row', 'location') AND child_entity_id = %s)
        """, (rack_id, rack_id))

        database.commit()

        return {
            "message": "Rack deletado com sucesso",
            "rack_id": rack_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def list_racks():

    query = """
            SELECT
                rack.id AS rack_id,
                rack.name AS rack_name,
                row_obj.id AS row_id,
                row_obj.name AS row_name,
                av.uint_value AS rack_height
            FROM Object AS rack
            LEFT JOIN EntityLink AS el
                ON el.child_entity_type = 'rack'
               AND el.child_entity_id = rack.id
               AND el.parent_entity_type = 'row'
            LEFT JOIN Object AS row_obj
                ON row_obj.id = el.parent_entity_id
            LEFT JOIN AttributeValue AS av
                ON av.object_id = rack.id
               AND av.object_tid = 1560
               AND av.attr_id = 27
            WHERE rack.objtype_id = 1560
            ORDER BY rack.name
            """

    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute(query)
        racks = cursor.fetchall()

        return racks

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()


def list_racks_with_space():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # GET ALL RACKS + HEIGHT
        racks_query = """
        SELECT
            r.id AS rack_id,
            r.name AS rack_name,
            av.uint_value AS total_units
        FROM Object r
        LEFT JOIN AttributeValue av
            ON av.object_id = r.id
           AND av.object_tid = 1560
           AND av.attr_id = 27
        WHERE r.objtype_id = 1560
        ORDER BY r.name
        """

        cursor.execute(racks_query)
        racks = cursor.fetchall()

        result = []

        # FOR EACH RACK, CALCULATE OCCUPANCY
        for rack in racks:
            rack_id = rack["rack_id"]
            total_units = rack["total_units"] or 0

            # get occupied positions
            occupied_query = """
            SELECT DISTINCT unit_no
            FROM RackSpace
            WHERE rack_id = %s
              AND object_id IS NOT NULL
            """
            cursor.execute(occupied_query, (rack_id,))
            occupied_rows = cursor.fetchall()

            occupied_units = sorted([row["unit_no"] for row in occupied_rows], reverse=True)

            # calculate free units
            all_units = set(range(1, total_units + 1))
            free_units = sorted(list(all_units - set(occupied_units)), reverse=True)

            result.append({
                "rack_id": rack_id,
                "rack_name": rack["rack_name"],
                "total_units": total_units,
                "occupied_units": occupied_units,
                "free_units": free_units
            })
        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()