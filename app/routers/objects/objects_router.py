from fastapi import APIRouter
from app.schema.objects.objects_schema import CreateObject
from app.repository.objects.objects_repository import (
    create_object,
    delete_object,
    list_objects,
    list_object_types
)

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)

@router.post("/")
def create_object_route(data: CreateObject):
    return create_object(data)

@router.delete("/{object_id}")
def delete_object_route(object_id: int):
    return delete_object(object_id)

@router.get("/")
def list_objects_route():
    return list_objects()

@router.get("/types")
def list_object_types_route():
    return list_object_types()