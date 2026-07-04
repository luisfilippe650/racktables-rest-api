from pydantic import BaseModel, field_validator

class AddLocation(BaseModel):
    name : str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Location name cannot be empty")
        if len(cleaned) > 255:
            raise ValueError("Location name cannot exceed 255 characters")
        return cleaned
