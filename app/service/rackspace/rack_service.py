from app.core.databaseConnection import connect
from app.repository.rackspace.rack_repository import (
    get_row_by_id,
    insert_rack,
    insert_history,
    insert_attribute,
    link_rack_to_row,
    get_rack_by_id,
    check_rack_has_objects,
    list_racks_with_height,
    get_occupied_units_by_rack,
)
from app.schema.rackspace.rack_schema import CreateRack


OBJTYPE_RACK = 1560
USER_NAME = "API - user"

def create_rack_service(data: CreateRack):

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        # regra de negócio (service)
        row_exists = get_row_by_id(cursor, data.row_id)

        if not row_exists:
            database.rollback()
            return {"error": "Row não encontrado"}

        rack_id = insert_rack(
            cursor,
            data.name,
            OBJTYPE_RACK,
            data.assent_no
        )

        insert_history(cursor, USER_NAME, rack_id)

        # altura do rack (attr_id = 27)
        insert_attribute(cursor, data.rack_height, rack_id, OBJTYPE_RACK, 27)

        # orientação (attr_id = 29)
        insert_attribute(cursor, 1, rack_id, OBJTYPE_RACK, 29)

        link_rack_to_row(cursor, data.row_id, rack_id)

        database.commit()

        return {
            "message": "Rack criado com sucesso",
            "rack_id": rack_id
        }

    except Exception as e:
        database.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        database.close()

def delete_rack_service(rack_id: int):

    database = connect()
    cursor = database.cursor()

    try:
        cursor.execute("START TRANSACTION")

        rack = get_rack_by_id(cursor, rack_id)

        if not rack:
            database.rollback()
            return {"error": "Rack não encontrado"}

        has_objects = check_rack_has_objects(cursor, rack_id)

        if has_objects:
            database.rollback()
            return {"error": "Rack possui objetos alocados"}

        # aqui você mantém seu cleanup pesado (pode extrair depois)
        cursor.execute("DELETE FROM RackThumbnail WHERE rack_id = %s", (rack_id,))
        cursor.execute("DELETE FROM RackSpace WHERE rack_id = %s", (rack_id,))

        insert_history(cursor, USER_NAME, rack_id)

        cursor.execute("DELETE FROM Object WHERE id = %s", (rack_id,))

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

def list_racks_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        cursor.execute("""
        SELECT
            rack.id AS rack_id,
            rack.name AS rack_name,
            av.uint_value AS rack_height,
            row_obj.id AS row_id,
            row_obj.name AS row_name
        FROM Object AS rack

        LEFT JOIN AttributeValue av
            ON av.object_id = rack.id
           AND av.attr_id = 27
           AND av.object_tid = 1560

        LEFT JOIN EntityLink el
            ON el.child_entity_type = 'rack'
           AND el.child_entity_id = rack.id
           AND el.parent_entity_type = 'row'

        LEFT JOIN Object AS row_obj
            ON row_obj.id = el.parent_entity_id

        WHERE rack.objtype_id = 1560
        ORDER BY rack.name
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        database.close()

def list_racks_with_space_service():
    database = connect()
    cursor = database.cursor(dictionary=True)

    try:
        racks = list_racks_with_height(cursor)

        result = []

        for rack in racks:
            rack_id = rack["rack_id"]
            total_units = rack["total_units"] or 0

            occupied_rows = get_occupied_units_by_rack(cursor, rack_id)
            occupied_units = sorted(
                [row["unit_no"] for row in occupied_rows],
                reverse=True
            )

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