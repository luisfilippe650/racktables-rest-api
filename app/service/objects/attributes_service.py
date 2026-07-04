import logging

from app.core.database import connect
from app.repository.common_repository import get_object_basic_info, insert_history_record
from app.repository.objects.attributes_repository import (
    get_available_attributes,
    upsert_attribute_value,
    get_dict_key_by_value,
    update_fixed_object_fields,
    delete_attribute_value,
    get_dictionary_options,
    count_object_name
)
from app.utils.responses import success_response, error_response
from app.utils.user_name import USER_NAME
from datetime import datetime
import re

FIXED_FIELDS = ['name', 'label', 'asset_no', 'has_problems', 'comment']
ALLOWED_UPDATE_TYPES = [1, 4, 1504]  # 1: BlackBox, 4: Server, 1504: VM
FORBIDDEN_FIELDS = ['id', 'object_id', 'objtype_id']
FORBIDDEN_ATTRIBUTES = ['Height, units']
REQUIRED_TEXT_FIELDS = ['name']

logger = logging.getLogger(__name__)

def update_object_attributes_service(object_id: int, updates: dict):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        if not updates:
            return error_response("No fields were provided for update", status_code=400)

        # 0. Check for forbidden fields (Security first)
        for field in FORBIDDEN_FIELDS:
            if field in updates:
                return error_response(
                    f"Forbidden update: Field '{field}' is immutable and cannot be changed.",
                    status_code=403
                )
        
        # Check for forbidden dynamic attributes
        for attr in FORBIDDEN_ATTRIBUTES:
            if attr in updates:
                return error_response(
                    f"Forbidden update: Attribute '{attr}' cannot be changed via this endpoint. Please use the allocation functions.",
                    status_code=403
                )

        cursor.execute("START TRANSACTION")

        # 1. Validate object existence
        obj_info = get_object_basic_info(cursor, object_id)
        if not obj_info:
            database.rollback()
            return error_response("Object not found", status_code=404)

        objtype_id = obj_info['objtype_id']

        # 2. Restrict to allowed object types
        if objtype_id not in ALLOWED_UPDATE_TYPES:
            database.rollback()
            return error_response(
                "Updates via this endpoint are restricted to specific object types (Server, VM, etc.)", 
                status_code=403,
                detail=f"Object type ID {objtype_id} is not allowed."
            )

        # 3. Get available dynamic attributes for this object type
        available_attrs = get_available_attributes(cursor, objtype_id)
        attr_map = {attr['attr_name']: attr for attr in available_attrs}

        fixed_updates = {}
        dynamic_updates_count = 0

        # Helper: normalize boolean-like inputs
        def _to_bool_like(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                low = v.strip().lower()
                if low in ('1', 'true', 'yes', 'y', 'on'):
                    return True
                if low in ('0', 'false', 'no', 'n', 'off'):
                    return False
            return None

        # Helper to process a single dynamic attribute update
        def _process_dynamic_attr(key, value):
            nonlocal dynamic_updates_count
            attr = attr_map[key]
            attr_id = attr['attr_id']
            attr_type = attr['attr_type']
            chapter_id = attr['chapter_id']

            # Validation C: Clear attribute only through an explicit command.
            if isinstance(value, dict) and value.get("clear") is True and len(value) == 1:
                delete_attribute_value(cursor, object_id, attr_id)
                dynamic_updates_count += 1
                return None

            if value is None or (isinstance(value, str) and value.strip() == ""):
                return error_response(
                    f"Attribute '{key}' cannot be empty. To clear it, send {{\"clear\": true}}.",
                    status_code=400
                )

            processed_value = value

            # Validation A: Character limits for string attributes
            if attr_type == 'string' and len(str(value)) > 255:
                return error_response(f"Attribute '{key}' is too long (max 255 chars)", status_code=400)
            if attr_type == 'string' and isinstance(value, str):
                processed_value = value.strip()

            # Validation B: Range validation for uint
            if attr_type == 'uint':
                # Accept boolean-like inputs and convert to 1/0 for uint fields
                b = _to_bool_like(value)
                if b is not None:
                    processed_value = 1 if b else 0
                else:
                    try:
                        val_int = int(value)
                        if val_int < 0 or val_int > 4294967295: # Max uint32
                            raise ValueError()
                        processed_value = val_int
                    except ValueError:
                        return error_response(f"Attribute '{key}' must be a positive integer between 0 and 4,294,967,295", status_code=400)

            # Validation D: Date format and conversion to Unix timestamp
            if attr_type == 'date':
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(value)):
                    return error_response(f"Attribute '{key}' must be in YYYY-MM-DD format", status_code=400)
                try:
                    processed_value = int(datetime.strptime(str(value), "%Y-%m-%d").timestamp())
                except ValueError:
                    return error_response(f"Attribute '{key}' is not a valid calendar date", status_code=400)

            # Validation E: Dictionary suggestions
            if attr_type == 'dict':
                dict_key = get_dict_key_by_value(cursor, chapter_id, str(value))
                if dict_key is None:
                    options = get_dictionary_options(cursor, chapter_id)
                    return error_response(
                        message=f"Invalid value for '{key}'.",
                        detail=f"Allowed values: {', '.join(options[:10])}{'...' if len(options) > 10 else ''}",
                        status_code=400
                    )
                processed_value = dict_key

            upsert_attribute_value(cursor, object_id, objtype_id, attr_id, processed_value, attr_type)
            dynamic_updates_count += 1
            return None

        # 3. Process each update item
        for key, value in updates.items():
            # Handle Fixed Fields (Object Table)
            if key in FIXED_FIELDS:
                if value is None:
                    if key in REQUIRED_TEXT_FIELDS:
                        database.rollback()
                        return error_response(f"Field '{key}' cannot be empty", status_code=400)
                    fixed_updates[key] = None
                    continue

                if isinstance(value, str):
                    value = value.strip()

                if isinstance(value, str) and value == "":
                    if key in REQUIRED_TEXT_FIELDS:
                        database.rollback()
                        return error_response(f"Field '{key}' cannot be empty", status_code=400)
                    fixed_updates[key] = None
                    continue

                # Validation A: Character limits for fixed fields
                if key == 'asset_no' and value and len(str(value)) > 64:
                    database.rollback()
                    return error_response(f"Field '{key}' is too long (max 64 chars)", status_code=400)
                if value and len(str(value)) > 255:
                    database.rollback()
                    return error_response(f"Field '{key}' is too long (max 255 chars)", status_code=400)

                # Special handling for boolean-like fixed fields (e.g., has_problems)
                if key == 'has_problems':
                    b = _to_bool_like(value)
                    if b is not None:
                        # RackTables stores 'yes'/'no' strings for has_problems
                        fixed_updates[key] = 'yes' if b else 'no'
                        continue
                    # allow explicit 'yes'/'no' strings to pass through
                    if isinstance(value, str) and value.strip().lower() in ('yes', 'no'):
                        fixed_updates[key] = value.strip().lower()
                        continue
                    database.rollback()
                    return error_response("Field 'has_problems' must be one of: yes, no, true, false, 1, 0", status_code=400)

                if key == 'name':
                    name_exists = count_object_name(cursor, value, object_id)
                    if name_exists > 0:
                        database.rollback()
                        return error_response(f"An object with the name '{value}' already exists", status_code=400)

                fixed_updates[key] = value
                continue

            # Handle Dynamic Attributes (AttributeValue Table)
            if key in attr_map:
                error = _process_dynamic_attr(key, value)
                if error:
                    database.rollback()
                    return error
            else:
                database.rollback()
                return error_response(f"Attribute '{key}' is not valid for this object type", status_code=400)

        # 4. Perform updates on the Object table
        if fixed_updates:
            update_fixed_object_fields(cursor, object_id, fixed_updates)

        # 5. Record History
        insert_history_record(cursor, USER_NAME, object_id)

        database.commit()

        return success_response(
            message="Object attributes updated successfully",
            data={
                "object_id": object_id,
                "fixed_fields_updated": list(fixed_updates.keys()),
                "dynamic_attributes_updated": dynamic_updates_count
            }
        )

    except Exception as e:
        database.rollback()
        logger.exception("Unexpected error during attribute update")
        return error_response("An unexpected error occurred during attribute update", status_code=500)

    finally:
        cursor.close()
        database.close()
