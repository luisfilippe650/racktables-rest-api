from app.repository.common_repository import (
    delete_file_links,
    delete_tags,
    delete_network_data,
    delete_entity_links,
    delete_mount_data,
    delete_port_data,
    insert_history_record,
    get_object_basic_info,
    update_object_name,
    delete_attribute_values
)
from app.utils.objtype import RACK, ROW
from app.utils.attribute_ids import HEIGHT

def get_row_by_id(cursor, row_id: int):
    sql = "SELECT id FROM Object WHERE id = %s AND objtype_id = %s LIMIT 1"
    cursor.execute(sql, (row_id, ROW))
    return cursor.fetchone()


def insert_rack(cursor, name: str, objtype_id: int, asset_no):
    sql = """
    INSERT INTO Object
    (name, label, objtype_id, asset_no)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, None, objtype_id, asset_no))
    return cursor.lastrowid


def insert_attribute(cursor, value: int, object_id: int, object_tid: int, attr_id: int):
    sql = """
    INSERT INTO AttributeValue
    (uint_value, object_id, object_tid, attr_id)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, (value, object_id, object_tid, attr_id))


def link_rack_to_row(cursor, row_id: int, rack_id: int):
    sql = """
    INSERT INTO EntityLink
    (parent_entity_type, parent_entity_id, child_entity_type, child_entity_id)
    VALUES
    (%s, %s, %s, %s)
    """
    cursor.execute(sql, ("row", row_id, "rack", rack_id))


def get_rack_by_id(cursor, rack_id: int):
    sql = "SELECT id FROM Object WHERE id = %s AND objtype_id = %s LIMIT 1"
    cursor.execute(sql, (rack_id, RACK))
    return cursor.fetchone()


def check_rack_has_objects(cursor, rack_id: int):
    sql = """
    SELECT 1
    FROM RackSpace
    WHERE rack_id = %s
      AND object_id IS NOT NULL
    LIMIT 1
    """
    cursor.execute(sql, (rack_id,))
    return cursor.fetchone()


def delete_rack_thumbnail(cursor, rack_id: int):
    cursor.execute("DELETE FROM RackThumbnail WHERE rack_id = %s", (rack_id,))


def delete_rackspace_by_rack(cursor, rack_id: int):
    cursor.execute("DELETE FROM RackSpace WHERE rack_id = %s", (rack_id,))


def anonymize_rack(cursor, rack_id: int):
    cursor.execute("""
        UPDATE Object
        SET name = NULL,
            label = ''
        WHERE id = %s
          AND objtype_id = %s
    """, (rack_id, RACK))


def delete_rack_object(cursor, rack_id: int):
    cursor.execute("DELETE FROM Object WHERE id = %s AND objtype_id = %s", (rack_id, RACK))


def list_racks_basic_info_query(cursor):
    sql = f"""
    SELECT
        rack.id AS rack_id,
        rack.name AS rack_name,
        av.uint_value AS rack_height,
        row_obj.id AS row_id,
        row_obj.name AS row_name
    FROM Object AS rack

    LEFT JOIN AttributeValue av
        ON av.object_id = rack.id
       AND av.attr_id = {HEIGHT}
       AND av.object_tid = {RACK}

    LEFT JOIN EntityLink el
        ON el.child_entity_type = 'rack'
       AND el.child_entity_id = rack.id
       AND el.parent_entity_type = 'row'

    LEFT JOIN Object AS row_obj
        ON row_obj.id = el.parent_entity_id

    WHERE rack.objtype_id = {RACK}
    ORDER BY rack.name
    """
    cursor.execute(sql)
    return cursor.fetchall()


def list_racks_with_height(cursor):
    sql = f"""
    SELECT
        r.id AS rack_id,
        r.name AS rack_name,
        av.uint_value AS total_units
    FROM Object r
    LEFT JOIN AttributeValue av
        ON av.object_id = r.id
       AND av.object_tid = {RACK}
       AND av.attr_id = {HEIGHT}
    WHERE r.objtype_id = {RACK}
    ORDER BY r.name
    """
    cursor.execute(sql)
    return cursor.fetchall()


def get_occupied_units_by_rack(cursor, rack_id: int):
    sql = "SELECT DISTINCT unit_no FROM RackSpace WHERE rack_id = %s AND object_id IS NOT NULL"
    cursor.execute(sql, (rack_id,))
    return cursor.fetchall()


def get_rack_details_query(cursor, rack_id: int):
    query = f"""
    SELECT
        rack.id AS rack_id,
        rack.name AS rack_name,
        rack.asset_no AS rack_asset_no,
        av.uint_value AS rack_height,

        row_obj.id AS row_id,
        row_obj.name AS row_name,

        COUNT(DISTINCT CASE
            WHEN rs.object_id IS NOT NULL THEN rs.unit_no
        END) AS allocated_units,

        (
            COALESCE(av.uint_value, 0) -
            COUNT(DISTINCT CASE
                WHEN rs.object_id IS NOT NULL THEN rs.unit_no
            END)
        ) AS free_units

    FROM Object AS rack

    LEFT JOIN AttributeValue AS av
        ON av.object_id = rack.id
       AND av.object_tid = {RACK}
       AND av.attr_id = {HEIGHT}

    LEFT JOIN EntityLink AS el
        ON el.child_entity_type = 'rack'
       AND el.child_entity_id = rack.id
       AND el.parent_entity_type = 'row'

    LEFT JOIN Object AS row_obj
        ON row_obj.id = el.parent_entity_id

    LEFT JOIN RackSpace AS rs
        ON rs.rack_id = rack.id

    WHERE rack.objtype_id = {RACK}
      AND rack.id = %s

    GROUP BY
        rack.id,
        rack.name,
        rack.asset_no,
        av.uint_value,
        row_obj.id,
        row_obj.name
    """
    cursor.execute(query, (rack_id,))
    return cursor.fetchone()


def get_rack_with_height(cursor, rack_id: int):
    sql = f"""
    SELECT
        r.id AS rack_id,
        r.name AS rack_name,
        av.uint_value AS total_units
    FROM Object r
    LEFT JOIN AttributeValue av
        ON av.object_id = r.id
       AND av.object_tid = {RACK}
       AND av.attr_id = {HEIGHT}
    WHERE r.objtype_id = {RACK}
      AND r.id = %s
    LIMIT 1
    """
    cursor.execute(sql, (rack_id,))
    return cursor.fetchone()


def count_rack_name(cursor, rack_name: str, rack_id: int):
    sql = f"SELECT COUNT(*) as count FROM Object WHERE name = %s AND id != %s AND objtype_id = {RACK}"
    cursor.execute(sql, (rack_name, rack_id))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0]


def update_rack_name_query(cursor, rack_id: int, rack_name: str):
    sql = f"UPDATE Object SET name = %s WHERE id = %s AND objtype_id = {RACK}"
    cursor.execute(sql, (rack_name, rack_id))
