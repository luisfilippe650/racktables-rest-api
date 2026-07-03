from app.repository.common_repository import get_object_basic_info


def get_dictionary_options_for_chapter(cursor, chapter_id: int) -> list:
    """
    Fetches all valid options (dict_values) for a given Dictionary chapter.
    Returns a sorted list of strings — exactly what the RackTables website
    shows in its drop-down boxes (HW type, SW type, etc.).
    The query hits the live Database so results are always up-to-date.
    """
    sql = """
    SELECT dict_value
    FROM Dictionary
    WHERE chapter_id = %s
    ORDER BY dict_value
    """
    cursor.execute(sql, (chapter_id,))
    rows = cursor.fetchall()
    # Strip the %GPASS% hierarchy separator so callers see clean labels.
    options = []
    for row in rows:
        raw = row.get('dict_value', '') if isinstance(row, dict) else row[0]
        if raw:
            options.append(raw.replace('%GPASS%', ' '))
    return options


def get_object_attributes(cursor, object_id: int):
    """
    Returns all attributes (standard + custom) for a given object.

    Returns None if the object does not exist.
    Returns a dict with 'attributes': {} if the object exists but has no mapped attributes.

    Each attribute column (string_value, uint_value, float_value, dict_value, date_value)
    is returned separately so the caller can select the correct one based on attr_type,
    avoiding the ambiguity of COALESCE across different types.
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
        elif attr_type == 'dict':
            # dict_value is already resolved by the Dictionary JOIN above.
            # Strip the %GPASS% separator used by RackTables for hierarchy.
            raw = row.get('dict_value')
            value = raw.replace('%GPASS%', ' ') if raw else None
        elif attr_type == 'date':
            # date_value is already formatted as 'YYYY-MM-DD' by FROM_UNIXTIME.
            value = row.get('date_value')
        else:
            # 'uint' and any future types fall back to uint_value.
            value = row.get('uint_value')

        # For dict-type attributes, also include all available options so the
        # caller knows every valid choice (mirrors the website drop-down box).
        # The options are fetched live from the Database — always up-to-date.
        if attr_type == 'dict' and chapter_id:
            available_options = get_dictionary_options_for_chapter(cursor, chapter_id)
            result['attributes'][attr_name] = {
                'value': value,
                'available_options': available_options
            }
        else:
            result['attributes'][attr_name] = value

    return result
