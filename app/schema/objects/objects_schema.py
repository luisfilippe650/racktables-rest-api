from pydantic import BaseModel, field_validator
from typing import Optional

class CreateObject(BaseModel):
    name : str
    label : Optional[str] = None
    asset_no : Optional[str] = None
    comment : Optional[str] = None
    objtype_id: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Object name cannot be empty")
        if len(cleaned) > 255:
            raise ValueError("Object name cannot exceed 255 characters")
        return cleaned

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) > 255:
            raise ValueError("Object label cannot exceed 255 characters")
        return cleaned or None

    @field_validator("asset_no")
    @classmethod
    def validate_asset_no(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) > 64:
            raise ValueError("Object asset number cannot exceed 64 characters")
        return cleaned or None

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("objtype_id")
    @classmethod
    def validate_objtype_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Object type ID must be greater than zero")
        return value

class UpdateObjectSchema(BaseModel):
    name: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Object name cannot be empty")
        if len(cleaned) > 255:
            raise ValueError("Object name cannot exceed 255 characters")
        return cleaned

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
