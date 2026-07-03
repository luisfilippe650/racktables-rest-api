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
    Finds the dict_key in the Dictionary table for a given value and chapter.
    Uses case-insensitive search for better usability.
    """
    sql = """
    SELECT dict_key 
    FROM Dictionary 
    WHERE chapter_id = %s AND LOWER(dict_value) = LOWER(%s)
    LIMIT 1
    """
    cursor.execute(sql, (chapter_id, value))
    result = cursor.fetchone()
    if result:
        return result['dict_key'] if isinstance(result, dict) else result[0]
    return None


def update_fixed_object_fields(cursor, object_id: int, fields: dict):
    """
    Updates fields in the Object table (name, label, asset_no, has_problems).
    """
    if not fields:
        return

    set_clause = ", ".join([f"{k} = %s" for k in fields.keys()])
    values = list(fields.values())
    values.append(object_id)

    sql = f"UPDATE Object SET {set_clause} WHERE id = %s"
    cursor.execute(sql, tuple(values))


def delete_attribute_value(cursor, object_id: int, attr_id: int):
    """
    Removes a specific attribute value for an object.
    """
    sql = "DELETE FROM AttributeValue WHERE object_id = %s AND attr_id = %s"
    cursor.execute(sql, (object_id, attr_id))


def get_dictionary_options(cursor, chapter_id: int):
    """
    Returns a list of all valid dict_values for a specific chapter.
    """
    sql = "SELECT dict_value FROM Dictionary WHERE chapter_id = %s ORDER BY dict_value"
    cursor.execute(sql, (chapter_id,))
    rows = cursor.fetchall()
    return [r['dict_value'] if isinstance(r, dict) else r[0] for r in rows]
