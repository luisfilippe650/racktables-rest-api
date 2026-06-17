from fastapi.responses import JSONResponse
from typing import Any, Optional
import re

def translate_mysql_error(error_msg: str) -> str:
    """
    Translates cryptic MySQL error messages into something more human-readable.
    """
    # Type mismatch (Incorrect integer value)
    if "1366" in error_msg:
        column_match = re.search(r"for column `([^`]+)`", error_msg)
        column = column_match.group(1) if column_match else "unknown"

        if "uint_value" in error_msg:
            return f"Validation error: The attribute value must be a number (integer), but text was received."
        if "float_value" in error_msg:
            return f"Validation error: The attribute value must be a decimal number, but an invalid format was received."
        return f"Type mismatch error on field '{column}'."

    # Duplicate entry
    if "1062" in error_msg:
        value_match = re.search(r"Duplicate entry '([^']+)'", error_msg)
        value = value_match.group(1) if value_match else "this value"
        return f"Already exists: '{value}' is already in use and must be unique."

    # Foreign key constraint (cannot delete)
    if "1451" in error_msg:
        return "Cannot delete: This item is still linked to other resources (e.g., a rack with objects, or a row with racks)."

    # Default to original if no mapping found
    return error_msg

def success_response(data: Any = None, message: str = "Operation successful", status_code: int = 200, count: Optional[int] = None):
    content = {
        "status": "success",
        "message": message,
    }
    if data is not None:
        content["data"] = data
    if count is not None:
        content["count"] = count
        
    return JSONResponse(content=content, status_code=status_code)

def error_response(message: str = "An error occurred", status_code: int = 400, detail: Optional[str] = None):
    friendly_detail = translate_mysql_error(detail) if detail else None
    
    content = {
        "status": "error",
        "message": message,
    }
    if friendly_detail:
        content["detail"] = friendly_detail
        
    return JSONResponse(content=content, status_code=status_code)
