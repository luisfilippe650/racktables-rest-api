from pydantic import BaseModel

class AllocateServer(BaseModel):
    rack_id : int
    object_id : int
    start_unit : int
    height : int