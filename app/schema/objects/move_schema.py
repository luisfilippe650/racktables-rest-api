from pydantic import BaseModel, field_validator
from typing import Optional

class MoveServer(BaseModel):
    object_id: int
    destination_rack_id: int
    start_unit: int
    source_rack_id: Optional[int] = None
    height: Optional[int] = None

    @field_validator("object_id", "destination_rack_id", "start_unit")
    @classmethod
    def validate_positive_required_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be greater than zero")
        return value

    @field_validator("source_rack_id", "height")
    @classmethod
    def validate_positive_optional_ints(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("Value must be greater than zero")
        return value
