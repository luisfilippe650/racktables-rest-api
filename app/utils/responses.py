from fastapi.responses import JSONResponse
from typing import Any, Optional

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
    content = {
        "status": "error",
        "message": message,
    }
    if detail:
        content["detail"] = detail
        
    return JSONResponse(content=content, status_code=status_code)
