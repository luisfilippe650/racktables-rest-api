def get_object_attributes(cursor, object_id: int):
    # Returns all attributes (standard + custom) for a given object
    sql = """
    SELECT 
        RO.id AS object_id,
        RO.name AS common_name,
        RO.label AS visible_label,
        RO.asset_no AS asset_tag,
        RO.has_problems,
        A.name AS attribute_name,
        A.type AS attribute_type,
        COALESCE(
            D.dict_value,
            AV.string_value,
            CAST(AV.float_value AS CHAR),
            CAST(AV.uint_value  AS CHAR)
        ) AS attribute_value
    FROM RackObject AS RO
    LEFT JOIN AttributeMap   AS AM ON RO.objtype_id = AM.objtype_id
    LEFT JOIN Attribute      AS A  ON AM.attr_id     = A.id
    LEFT JOIN AttributeValue AS AV ON AV.attr_id     = AM.attr_id
                                   AND AV.object_id  = RO.id
    LEFT JOIN Dictionary     AS D  ON D.dict_key     = AV.uint_value
                                   AND AM.chapter_id = D.chapter_id
    WHERE RO.id = %s
    ORDER BY A.name
    """

    cursor.execute(sql, (object_id,))
    rows = cursor.fetchall()

    if not rows:
        return None

    # Assemble the object with fixed fields + dynamic attributes
    result = {
        'object_id': rows[0]['object_id'],
        'common_name': rows[0]['common_name'],
        'visible_label': rows[0]['visible_label'],
        'asset_tag': rows[0]['asset_tag'],
        'has_problems': rows[0]['has_problems'],
        'attributes': {}
    }

    # Here the custom attributes appear
    for row in rows:
        if isinstance(row, dict):
            attr_name = row['attribute_name']
            attr_value = row['attribute_value']
        else:
            attr_name = row[5]
            attr_value = row[7]

        if attr_name:
            result['attributes'][attr_name] = attr_value

    return result
