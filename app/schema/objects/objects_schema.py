from pydantic import BaseModel
from typing import Optional

class CreateObject(BaseModel):
    name : str
    label : Optional[str] = None
    asset_no : Optional[str] = None
    objtype_id: int

class UpdateObjectSchema(BaseModel):
    name: Optional[str] = None
    comment: Optional[str] = None