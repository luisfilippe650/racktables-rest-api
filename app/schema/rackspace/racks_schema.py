from pydantic import BaseModel, field_validator
from typing import Optional


class CreateRack(BaseModel):
    name : str
    rack_height : int = 42
    row_id : int
    asset_no : Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Rack name cannot be empty")
        if len(cleaned) > 255:
            raise ValueError("Rack name cannot exceed 255 characters")
        return cleaned

    @field_validator("rack_height")
    @classmethod
    def validate_rack_height(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Rack height must be greater than zero")
        return value

    @field_validator("row_id")
    @classmethod
    def validate_row_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Row ID must be greater than zero")
        return value

class UpdateRackName (BaseModel):
    name : str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Rack name cannot be empty")
        if len(cleaned) > 255:
            raise ValueError("Rack name cannot exceed 255 characters")
        return cleaned
