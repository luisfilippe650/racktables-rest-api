from fastapi import APIRouter
from fastapi.params import Depends
from app.core.security import get_current_user
from app.schema.objects.objects_schema import CreateObject, UpdateObjectSchema
from app.service.objects.objects_service import (
    create_object_service,
    delete_object_service,
    list_object_types_service,
    list_objects_service,
    update_object_service
)

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)

@router.post("/")
def create_object_route(data: CreateObject, user_id: str = Depends(get_current_user)):
    return create_object_service(data)

@router.delete("/{object_id}")
def delete_object_route(object_id: int, user_id: str = Depends(get_current_user)):
    return delete_object_service(object_id)

@router.patch("/{object_id}")
def update_object_route(object_id: int, data: UpdateObjectSchema, user_id: str = Depends(get_current_user)):
    return update_object_service(object_id, data.name , data.comment )

@router.get("/")
def list_objects_route(user_id: str = Depends(get_current_user)):
    return list_objects_service()

@router.get("/types")
def list_object_types_route(user_id: str = Depends(get_current_user)):
    return list_object_types_service()