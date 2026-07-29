from app.utils.objtype import RACK, ROW, LOCATION

ALLOWED_FIXED_OBJECT_COLUMNS = {'name', 'label', 'asset_no', 'has_problems', 'comment'}


def validate_attribute_value_upsert_key(cursor):
    """
    Ensures AttributeValue has the unique key required by ON DUPLICATE KEY UPDATE.
    """
    sql = """
    SELECT
        INDEX_NAME,
        GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns_in_index
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'AttributeValue'
      AND NON_UNIQUE = 0
    GROUP BY INDEX_NAME
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        columns = row['columns_in_index'] if isinstance(row, dict) else row[1]
        if set(columns.split(',')) == {'object_id', 'attr_id'}:
            return

    raise RuntimeError(
        "AttributeValue must have a unique key on object_id and attr_id "
        "for safe attribute upserts"
    )


def get_available_attributes(cursor, objtype_id: int):
    """
    Returns all attributes allowed for a specific object type,
    including their types and IDs.
    """
    sql = """
    SELECT 
        A.id AS attr_id,
        A.name AS attr_name,
        A.type AS attr_type,
        AM.chapter_id
    FROM AttributeMap AM
    JOIN Attribute A ON AM.attr_id = A.id
    WHERE AM.objtype_id = %s
    """
    cursor.execute(sql, (objtype_id,))
    return cursor.fetchall()


def upsert_attribute_value(cursor, object_id: int, object_tid: int, attr_id: int, value, attr_type: str):
    """
    Inserts or updates a value in the AttributeValue table.
    """
    col = "string_value"
    if attr_type in ['uint', 'dict', 'date']:
        col = "uint_value"
    elif attr_type == 'float':
        col = "float_value"

    sql = f"""
    INSERT INTO AttributeValue (object_id, object_tid, attr_id, {col})
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        string_value = NULL,
        uint_value   = NULL,
        float_value  = NULL,
        {col}        = VALUES({col})
    """
    cursor.execute(sql, (object_id, object_tid, attr_id, value))


def get_dict_key_by_value(cursor, chapter_id: int, value: str):
    """
    Resolves a dictionary key for a given chapter using either:
      - numeric dict_key (preferred), or
      - exact dict_value (case-insensitive), or
      - cleaned dict_value where '%GPASS%' has been replaced by a space.
    This makes the PATCH accept the numeric id (dict_key) as the client
    UI/website does, while remaining compatible with label-based inputs.
    """
    if value is None:
        return None

    # 1) If caller provided a numeric id, validate it exists and return it.
    try:
        key = int(value)
        sql = "SELECT dict_key FROM Dictionary WHERE chapter_id = %s AND dict_key = %s LIMIT 1"
        cursor.execute(sql, (chapter_id, key))
        row = cursor.fetchone()
        if row:
            return row['dict_key'] if isinstance(row, dict) else row[0]
    except (ValueError, TypeError):
        # not an integer, continue to match by value
        pass

    # 2) Match by exact dict_value (case-insensitive)
    sql = "SELECT dict_key FROM Dictionary WHERE chapter_id = %s AND LOWER(dict_value) = LOWER(%s) LIMIT 1"
    cursor.execute(sql, (chapter_id, value))
    row = cursor.fetchone()
    if row:
        return row['dict_key'] if isinstance(row, dict) else row[0]

    # 3) Match by cleaned dict_value where %GPASS% is shown as a space in the UI
    sql = "SELECT dict_key FROM Dictionary WHERE chapter_id = %s AND LOWER(REPLACE(dict_value, '%GPASS%', ' ')) = LOWER(%s) LIMIT 1"
    cursor.execute(sql, (chapter_id, value))
    row = cursor.fetchone()
    if row:
        return row['dict_key'] if isinstance(row, dict) else row[0]

    return None


def update_fixed_object_fields(cursor, object_id: int, fields: dict):
    """
    Updates fields in the Object table (name, label, asset_no, has_problems).
    """
    if not fields:
        return

    invalid_columns = set(fields) - ALLOWED_FIXED_OBJECT_COLUMNS
    if invalid_columns:
        raise ValueError(f"Invalid fixed object fields: {', '.join(sorted(invalid_columns))}")

    set_clause = ", ".join([f"{k} = %s" for k in fields.keys()])
    values = list(fields.values())
    values.append(object_id)

    sql = f"UPDATE Object SET {set_clause} WHERE id = %s"
    cursor.execute(sql, tuple(values))


def count_object_name(cursor, name: str, object_id: int):
    sql = """
    SELECT COUNT(*) as count
    FROM Object
    WHERE name = %s
      AND id != %s
    """
    cursor.execute(sql, (name, object_id))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def count_object_service_tag(cursor, service_tag: str, object_id: int):
    sql = f"""
    SELECT COUNT(*) as count
    FROM Object
    WHERE asset_no = %s
      AND id != %s
      AND objtype_id NOT IN ({RACK}, {ROW}, {LOCATION})
    """
    cursor.execute(sql, (service_tag, object_id))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def delete_attribute_value(cursor, object_id: int, attr_id: int):
    """
    Removes a specific attribute value for an object.
    """
    sql = "DELETE FROM AttributeValue WHERE object_id = %s AND attr_id = %s"
    cursor.execute(sql, (object_id, attr_id))


def get_dictionary_options(cursor, chapter_id: int, limit: int = 11):
    """
    Returns a limited list of valid dict_values for a specific chapter.
    """
    sql = "SELECT dict_value FROM Dictionary WHERE chapter_id = %s ORDER BY dict_value LIMIT %s"
    cursor.execute(sql, (chapter_id, limit))
    rows = cursor.fetchall()
    return [r['dict_value'] if isinstance(r, dict) else r[0] for r in rows]
