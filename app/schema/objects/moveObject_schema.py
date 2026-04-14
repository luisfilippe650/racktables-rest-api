from pydantic import BaseModel

class MoveServer(BaseModel):
    object_id: int
    source_rack_id: int
    destination_rack_id: int
    start_unit: int
    height: int