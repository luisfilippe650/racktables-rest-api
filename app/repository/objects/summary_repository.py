from app.repository.common_repository import get_object_basic_info


def dictionary_chapter_exists(cursor, chapter_id: int) -> bool:
    sql = """
    SELECT 1
    FROM Dictionary
    WHERE chapter_id = %s
    LIMIT 1
    """
    cursor.execute(sql, (chapter_id,))
    return cursor.fetchone() is not None


def count_dictionary_options_for_chapter(cursor, chapter_id: int) -> int:
    sql = """
    SELECT COUNT(*) as count
    FROM Dictionary
    WHERE chapter_id = %s
    """
    cursor.execute(sql, (chapter_id,))
    result = cursor.fetchone()
    if isinstance(result, dict):
        return result['count']
    return result[0] if result else 0


def get_dictionary_options_for_chapter(cursor, chapter_id: int, limit: int = None, offset: int = None) -> list:
    """
    Fetches all valid options for a given Dictionary chapter.
    Returns a list of dicts: {"id": dict_key, "name": cleaned_label}.
    The cleaned_label replaces the RackTables '%GPASS%' separator with a space.
    """
    sql = """
    SELECT dict_key, dict_value
    FROM Dictionary
    WHERE chapter_id = %s
    ORDER BY dict_value
    """
    params = [chapter_id]
    if limit is not None and offset is not None:
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()

    options = []
    for row in rows:
        # Support both dict-row and tuple-row fetch results
        dict_key = row.get('dict_key') if isinstance(row, dict) else row[0]
        raw = row.get('dict_value', '') if isinstance(row, dict) else row[1]
        if raw is None:
            continue
        name = raw.replace('%GPASS%', ' ')
        options.append({
            'id': dict_key,
            'name': name
        })
    return options


def get_object_attributes(cursor, object_id: int):
    """
    Returns all attributes (standard + custom) for a given object.

    Returns None if the object does not exist.
    Returns a dict with 'attributes': {} if the object exists but has no mapped attributes.

    For attributes of type 'dict', the returned structure is:
      attributes[attr_name] = {
          'value': <dict_key or None>,
          'available_options': [{id,name}, ...]
      }
    This lets clients populate dropdowns with id+name and send id on PATCH.
    """

    # Step 1: validate object existence independently from attribute mapping.
    # A valid object with no mapped attributes would return zero rows from the
    # attribute JOIN, which must not be confused with "object not found".
    obj = get_object_basic_info(cursor, object_id)
    if not obj:
        return None

    sql = """
    SELECT
        o.id                                         AS object_id,
        o.name                                       AS common_name,
        o.label                                      AS visible_label,
        o.asset_no                                   AS asset_tag,
        o.has_problems,
        o.comment,
        a.id                                         AS attr_id,
        a.name                                       AS attr_name,
        a.type                                       AS attr_type,
        am.chapter_id,
        av.string_value,
        av.uint_value,
        av.float_value,
        d.dict_value,
        FROM_UNIXTIME(av.uint_value, '%Y-%m-%d')     AS date_value
    FROM Object AS o
    LEFT JOIN AttributeMap   AS am ON am.objtype_id  = o.objtype_id
    LEFT JOIN Attribute      AS a  ON a.id           = am.attr_id
    LEFT JOIN AttributeValue AS av ON av.object_id   = o.id
                                   AND av.attr_id    = am.attr_id
    -- Filter dict JOIN by type to avoid resolving uint values against Dictionary
    LEFT JOIN Dictionary     AS d  ON a.type         = 'dict'
                                   AND d.dict_key    = av.uint_value
                                   AND d.chapter_id  = am.chapter_id
    WHERE o.id = %s
    ORDER BY a.name
    """

    cursor.execute(sql, (object_id,))
    rows = cursor.fetchall()

    # Build the fixed-field block from the first row (same for all attribute rows).
    first = rows[0] if rows else {}
    result = {
        'object_id':     first.get('object_id', object_id),
        'common_name':   first.get('common_name'),
        'visible_label': first.get('visible_label'),
        'asset_tag':     first.get('asset_tag'),
        'has_problems':  first.get('has_problems'),
        'comment':       first.get('comment'),
        'attributes': {}
    }

    # Prefetch dictionary options for all chapter_ids found to avoid N+1 queries
    chapter_ids = set()
    for row in rows:
        if row.get('attr_type') == 'dict' and row.get('chapter_id'):
            chapter_ids.add(row.get('chapter_id'))

    dict_options_map = {}
    if chapter_ids:
        # Batch fetch all options for these chapter_ids
        in_clause = ','.join(['%s'] * len(chapter_ids))
        fetch_sql = f"SELECT chapter_id, dict_key, dict_value FROM Dictionary WHERE chapter_id IN ({in_clause}) ORDER BY chapter_id, dict_value"
        cursor.execute(fetch_sql, tuple(chapter_ids))
        dict_rows = cursor.fetchall()
        for drow in dict_rows:
            ch = drow.get('chapter_id') if isinstance(drow, dict) else drow[0]
            key = drow.get('dict_key') if isinstance(drow, dict) else drow[1]
            raw = drow.get('dict_value') if isinstance(drow, dict) else drow[2]
            name = raw.replace('%GPASS%', ' ') if raw else raw
            dict_options_map.setdefault(ch, []).append({'id': key, 'name': name})

    for row in rows:
        attr_name = row.get('attr_name')
        if not attr_name:
            # Row produced by LEFT JOIN when no attributes are mapped — skip.
            continue

        attr_type = row.get('attr_type')
        chapter_id = row.get('chapter_id')

        # Choose the correct column based on the declared attribute type.
        # This is explicit and safe: no COALESCE guessing across type boundaries.
        if attr_type == 'string':
            value = row.get('string_value')
        elif attr_type == 'float':
            value = row.get('float_value')
        elif attr_type == 'date':
            # date_value is already formatted as 'YYYY-MM-DD' by FROM_UNIXTIME.
            value = row.get('date_value')
        else:
            # 'uint' and any future types fall back to uint_value.
            value = row.get('uint_value')

        # For dict-type attributes, return the dict_key as the value and include
        # available options as [{id,name}] so the client can display labels and
        # send the stable id (dict_key) back on PATCH.
        if attr_type == 'dict' and chapter_id:
            dict_value_id = row.get('uint_value')
            available_options = dict_options_map.get(chapter_id, [])
            result['attributes'][attr_name] = {
                'value': dict_value_id,
                'available_options': available_options
            }
        else:
            result['attributes'][attr_name] = value

    return result
