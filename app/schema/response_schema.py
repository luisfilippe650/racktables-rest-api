from pydantic import BaseModel
from typing import Any, Optional, Dict

class GenericResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None
    count: Optional[int] = None
