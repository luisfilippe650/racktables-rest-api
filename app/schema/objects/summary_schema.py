from pydantic import BaseModel
from typing import Dict, Any

class UpdateAttributes(BaseModel):
    __root__: Dict[str, Any]

    class Config:
        # Allow arbitrary keys (dynamic attributes), but ensure valid JSON types
        extra = 'forbid'
