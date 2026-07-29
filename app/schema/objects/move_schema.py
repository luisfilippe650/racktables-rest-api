from pydantic import field_validator

from app.schema.base_schema import StrictRequestModel


class MoveServer(StrictRequestModel):
    object_id: int
    destination_rack_id: int
    start_unit: int

    @field_validator("object_id", "destination_rack_id", "start_unit")
    @classmethod
    def validate_positive_required_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be greater than zero")
        return value
