from pydantic import BaseModel, field_validator

class MountServer(BaseModel):
    rack_id : int
    object_id : int
    start_unit : int
    height : int

    @field_validator("rack_id", "object_id", "start_unit", "height")
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be greater than zero")
        return value
