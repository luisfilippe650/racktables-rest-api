from pydantic import BaseModel

class MountServer(BaseModel):
    rack_id : int
    object_id : int
    start_unit : int
    height : int