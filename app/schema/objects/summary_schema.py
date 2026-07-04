from pydantic import RootModel
from typing import Dict, Any

class UpdateAttributes(RootModel[Dict[str, Any]]):
    pass
