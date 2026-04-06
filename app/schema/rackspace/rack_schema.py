from pydantic import BaseModel

class CreateRack(BaseModel):
    name : str
    rack_height : int = 42
    row_id : int
    assent_no : str | None


