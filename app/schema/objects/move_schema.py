from pydantic import BaseModel
from typing import Optional

class MoveServer(BaseModel):
    object_id: int
    destination_rack_id: int
    start_unit: int
    source_rack_id: Optional[int] = None
    height: Optional[int] = None