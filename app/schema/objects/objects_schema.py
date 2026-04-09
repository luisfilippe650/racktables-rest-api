from pydantic import BaseModel

class CreateObject(BaseModel):
    name : str
    label : str
    asset_no : str | None
    objtype_id: int

class UpdateObjectName(BaseModel):
    name : str

class UpdateObjectComment(BaseModel):
    comment : str