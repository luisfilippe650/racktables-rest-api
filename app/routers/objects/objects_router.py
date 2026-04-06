from fastapi import APIRouter
from app.schema.objects.objects_schema import CreateObject
from app.service.objects.objects_service import (
    create_object_service,
    delete_object_service,
    list_object_types_service, list_objects_service
)

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)

@router.post("/")
def create_object_route(data: CreateObject):
    return create_object_service(data)

@router.delete("/{object_id}")
def delete_object_route(object_id: int):
    return delete_object_service(object_id)

@router.get("/")
def list_objects_route():
    return list_objects_service()

@router.get("/types")
def list_object_types_route():
    return list_object_types_service()