from pydantic import BaseModel
from typing import Optional


class CreateRack(BaseModel):
    name : str
    rack_height : int = 42
    row_id : int
    asset_no : Optional[str] = None

class UpdateRackName (BaseModel):
    name : str