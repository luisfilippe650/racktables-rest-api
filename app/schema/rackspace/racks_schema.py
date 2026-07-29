from pydantic import field_validator
from typing import Optional

from app.schema.base_schema import StrictRequestModel


class CreateRack(StrictRequestModel):
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

    @field_validator("asset_no")
    @classmethod
    def validate_asset_no(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) > 64:
            raise ValueError("Rack asset number cannot exceed 64 characters")
        return cleaned or None

class UpdateRackName(StrictRequestModel):
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
