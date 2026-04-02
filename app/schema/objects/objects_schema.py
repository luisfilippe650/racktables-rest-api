from pydantic import BaseModel

class CreateObject(BaseModel):
    name : str
    label : str
    asset_no : str
    objtype_id: int


