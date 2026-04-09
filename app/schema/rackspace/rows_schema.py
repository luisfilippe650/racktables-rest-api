from pydantic import BaseModel

class AddManageRows(BaseModel):
    name : str

class  UpdateRowName(BaseModel):
    name : str

