from app.core.databaseConnection import connect
from app.schema.rackspace.rows_schema import AddManageRows

def create_row(data: AddManageRows):

    user_name = "API - user"
    objtype_id = 1561 #Row

    # validate duplicate
    check_if_exists = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
      AND objtype_id = %s
    """

    insert_row_sql = """
    INSERT INTO Object
    (name, label, objtype_id, asset_no)
    VALUES
    (%s, %s, %s, %s) 
    """

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

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if a row with this name already exists
        cursor.execute(check_if_exists, (data.name, objtype_id))
        exists_count = cursor.fetchone()[0]

        if exists_count > 0:
            database.rollback()
            return {
                "status": "error",
                "message": f"Já existe uma row com o nome '{data.name}'"
            }

        # insert row
        cursor.execute(
            insert_row_sql,
            (
                data.name,
                None,
                objtype_id,
                None
            )
        )

        # get id
        row_id = cursor.lastrowid

        # history
        cursor.execute(
            insert_history_sql,
            (
                user_name,
                row_id
            )
        )

        database.commit()

        return {
            "status": "success",
            "message": "Row criada com sucesso",
            "row_id": row_id,
            "name": data.name
        }

    except Exception as e:
        database.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        database.close()

def delete_row(row_id: int):

    row_objtype_id = 1561
    user_name = "API - user"

    # Check if the object exists
    check_object_sql = """
        SELECT id, name, objtype_id
        FROM Object
        WHERE id = %s
        LIMIT 1
    """

    # Check if the row has linked racks
    validation_query = """
        SELECT 1
        FROM EntityLink
        WHERE parent_entity_type = 'row'
          AND parent_entity_id = %s
        LIMIT 1
    """

    database = connect()
    cursor = database.cursor()

    try:
        # validate before transaction
        cursor.execute(check_object_sql, (row_id,))
        row_data = cursor.fetchone()

        if row_data is None:
            return {"error": f"Objeto com id {row_id} não existe"}

        object_id, object_name, object_type = row_data

        if object_type != row_objtype_id:
            return {"error": f"O id {row_id} existe, mas não pertence a uma row"}

        cursor.execute("START TRANSACTION")

        cursor.execute(validation_query, (row_id,))
        has_racks = cursor.fetchone()

        if has_racks:
            database.rollback()
            return {"error": "Row possui racks vinculados"}

        # cleanup
        cursor.execute("""
            DELETE FROM FileLink
            WHERE entity_type = 'object' AND entity_id = %s
        """, (row_id,))

        cursor.execute("""
            DELETE FROM TagStorage
            WHERE entity_realm = 'object' AND entity_id = %s
        """, (row_id,))

        # network and IP
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (row_id,))

        # RELATIONSHIPS (OBJECT)
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
               OR (child_entity_type = 'object' AND child_entity_id = %s)
        """, (row_id, row_id))

        # RELATIONSHIPS (ROW)
        cursor.execute("""
            DELETE FROM EntityLink
            WHERE (parent_entity_type = 'row' AND parent_entity_id = %s)
               OR (child_entity_type = 'row' AND child_entity_id = %s)
        """, (row_id, row_id))

        # MOUNT / POSITION
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

        # VLAN / PORTS
        cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (row_id,))
        cursor.execute("DELETE FROM Port WHERE object_id = %s", (row_id,))

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
        """, (user_name, row_id))

        # UPDATE
        cursor.execute("""
            UPDATE Object
            SET name = NULL, label = ''
            WHERE id = %s
        """, (row_id,))

        # FINAL DELETE
        cursor.execute("DELETE FROM Object WHERE id = %s", (row_id,))

        database.commit()

        return {
            "message": "Row deletado com sucesso",
            "row_id": row_id,
            "row_name": object_name
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def list_row():

    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        query = """
            SELECT id, name, label
            FROM Object
            WHERE objtype_id = 1561
            ORDER BY name
            """

        cursor.execute(query)
        rows = cursor.fetchall()

        return rows

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def list_complete_rows():

    row_objtype_id = 1561
    rack_objtype_id = 1560

    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        # fetch all rows
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

            # fetch racks linked to the row
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

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()