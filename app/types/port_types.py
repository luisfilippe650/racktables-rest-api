from typing import TypedDict, Optional

class PortDict(TypedDict):
    name: str
    label: Optional[str]
    iif_id: int
    type: int
    l2address: Optional[str]