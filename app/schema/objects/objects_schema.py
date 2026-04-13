from pydantic import BaseModel
from typing import Optional

class CreateObject(BaseModel):
    name : str
    label : str
    asset_no : str | None
    objtype_id: int

class UpdateObjectSchema(BaseModel):
    name: Optional[str] = None
    comment: Optional[str] = None