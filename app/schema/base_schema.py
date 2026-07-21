from pydantic import BaseModel, ConfigDict


class StrictRequestModel(BaseModel):
    """Base model for request bodies with a fixed public contract."""

    model_config = ConfigDict(extra="forbid")
