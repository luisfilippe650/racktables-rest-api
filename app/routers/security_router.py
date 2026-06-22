from fastapi import APIRouter, Depends, HTTPException
from app.schema.security_schemas import UserModel
from app.service.security_service import create_access_token, authenticate_user

router = APIRouter(
    prefix="/login",
    tags=["login"],
)

@router.post("/")
def user_login( data: UserModel):
    return authenticate_user(data)
