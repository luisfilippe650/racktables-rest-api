from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
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

def success_response(data: Any = None, message: str = "Operation successful", status_code: int = 200):
    content = {
        "status": "success",
        "message": message,
    }
    if data is not None:
        content["data"] = data
    return JSONResponse(content=jsonable_encoder(content), status_code=status_code)


def paginated_response(items: list, page: int, per_page: int, total: int, message: str = "Operation successful"):
    return success_response(
        message=message,
        data={
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "page_count": len(items),
                "total": total,
            },
        },
    )

def _default_error_reason(status_code: int) -> str:
    if status_code == 400:
        return "bad_request"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "conflict"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "internal_error"
    return "request_error"


def _default_error_action(status_code: int) -> str:
    if status_code == 404:
        return "Check the identifier and try again."
    if status_code == 409:
        return "Resolve the conflicting resource state and try again."
    if status_code == 422:
        return "Fix the request fields and try again."
    if status_code >= 500:
        return "Try again later or contact support if the problem persists."
    return "Review the request data and try again."


def _normalize_error_detail(status_code: int, detail: Optional[Any] = None) -> dict[str, Any]:
    normalized = {
        "reason": _default_error_reason(status_code),
        "action": _default_error_action(status_code),
    }

    if detail is None:
        return normalized

    if isinstance(detail, str):
        normalized["context"] = translate_mysql_error(detail)
        return normalized

    if isinstance(detail, dict):
        normalized.update(detail)
        normalized.setdefault("reason", _default_error_reason(status_code))
        normalized.setdefault("action", _default_error_action(status_code))
        return normalized

    normalized["context"] = detail
    return normalized


def error_response(message: str = "An error occurred", status_code: int = 400, detail: Optional[Any] = None):
    friendly_detail = _normalize_error_detail(status_code, detail)
    
    content = {
        "status": "error",
        "message": message,
        "detail": friendly_detail,
    }
        
    return JSONResponse(content=jsonable_encoder(content), status_code=status_code)
