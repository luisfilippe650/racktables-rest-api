from pydantic import BaseModel

class CreateObject(BaseModel):
    name : str
    label : str
    asset_no : str | None
    objtype_id: int


