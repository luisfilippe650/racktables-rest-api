from app.core.databaseConnection import connect
from app.schema.rackspace.manageLocations_schema import AddLocation

def create_location(data : AddLocation):

    user_name = "API - user"
    objtype_id = 1562 #Location

    check_if_exists = """
    SELECT COUNT(*)
    FROM Object
    WHERE name = %s
      AND id != 0
    """

    create_location_sql = """
    INSERT INTO Object (name, label, objtype_id, asset_no)
    VALUES (%s, %s, %s, %s)
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

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # check if it already exists
        cursor.execute(check_if_exists,(data.name,))
        exists_count = cursor.fetchone()[0]

        if exists_count > 0:
            raise ValueError(f"A location '{data.name}' já existe.")

        # create the location
        values = (data.name, None, objtype_id, None)
        cursor.execute(create_location_sql, values)

        # get the generated id
        last_id = cursor.lastrowid

        # add to history
        cursor.execute(add_on_history, (user_name, last_id ))

        database.commit()

        return {
            "id": last_id,
            "name": data.name,
            "message": "Location criada com sucesso"
        }

    except Exception:
        database.rollback()
        raise

    finally:
        cursor.close()
        database.close()


def delete_location(location_id: int):

    location_objtype_id = 1562
    user_name = "API - user"

    database = connect()
    cursor = database.cursor()

    try:
        # Check if the object exists and if it is really a location
        check_location_sql = """
        SELECT id, name
        FROM Object
        WHERE id = %s
          AND objtype_id = %s
        """

        cursor.execute(check_location_sql, (location_id, location_objtype_id))
        location = cursor.fetchone()

        if location is None:
            return {
                "status": "error",
                "message": f"Nenhuma location válida encontrada com id {location_id}"
            }

        # Start transaction only after validation
        cursor.execute("START TRANSACTION")

        # Location-specific cleanup
        cursor.execute(
            "DELETE FROM FileLink WHERE entity_type = 'location' AND entity_id = %s",
            (location_id,)
        )
        cursor.execute(
            "DELETE FROM TagStorage WHERE entity_realm = 'location' AND entity_id = %s",
            (location_id,)
        )

        # Cleanup as object
        cursor.execute(
            "DELETE FROM FileLink WHERE entity_type = 'object' AND entity_id = %s",
            (location_id,)
        )
        cursor.execute(
            "DELETE FROM TagStorage WHERE entity_realm = 'object' AND entity_id = %s",
            (location_id,)
        )

        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM IPv4Allocation WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM IPv6Allocation WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM IPv4NAT WHERE object_id = %s", (location_id,))

        cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type = 'object' AND parent_entity_id = %s)
           OR (child_entity_type = 'object' AND child_entity_id = %s)
        """, (location_id, location_id))

        cursor.execute("""
        DELETE FROM Atom
        WHERE molecule_id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
        """, (location_id,))

        cursor.execute("""
        DELETE FROM Molecule
        WHERE id IN (
            SELECT new_molecule_id
            FROM MountOperation
            WHERE object_id = %s
        )
        """, (location_id,))

        cursor.execute("DELETE FROM MountOperation WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM RackSpace WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM PortVLANMode WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM PortNativeVLAN WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM PortAllowedVLAN WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM CachedPVM WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM VLANSwitch WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM IPv4LB WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM VSEnabledIPs WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM VSEnabledPorts WHERE object_id = %s", (location_id,))
        cursor.execute("DELETE FROM Port WHERE object_id = %s", (location_id,))

        # Update before deleting
        cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
        """, (location_id,))

        # History
        cursor.execute("""
        INSERT INTO ObjectHistory
        (id, name, label, objtype_id, asset_no, has_problems, comment, ctime, user_name)
        SELECT
            id, name, label, objtype_id, asset_no, has_problems, comment, CURRENT_TIMESTAMP(), %s
        FROM Object
        WHERE id = %s
        """, (user_name, location_id,))

        # Final delete of the object
        cursor.execute("DELETE FROM Object WHERE id = %s", (location_id,))

        # Final cleanup of links
        cursor.execute("""
        DELETE FROM EntityLink
        WHERE (parent_entity_type IN ('rack', 'row', 'location') AND parent_entity_id = %s)
           OR (child_entity_type IN ('rack', 'row', 'location') AND child_entity_id = %s)
        """, (location_id, location_id))

        database.commit()

        return {
            "status": "success",
            "message": "Location deletada com sucesso",
            "id": location_id,
            "name": location[1]
        }

    except Exception as e:
        database.rollback()
        raise e

    finally:
        cursor.close()
        database.close()


def list_locations():

    query = """
    SELECT id, name
    FROM Object
    WHERE objtype_id = %s
    ORDER BY name
    """

    objtype_id = 1562

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute(query, (objtype_id,))
        results = cursor.fetchall()

        locations = []

        for row in results:
            locations.append({
                "id": row[0],
                "name": row[1]
            })

        return locations

    finally:
        cursor.close()
        database.close()


def list_complete_location():

    location_objtype_id = 1562
    row_objtype_id = 1561

    database = connect()
    cursor = database.cursor()

    try:
        # Fetch all locations
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

            # Fetch rows linked to this location
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

    finally:
        cursor.close()
        database.close()