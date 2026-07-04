from fastapi import APIRouter, Query
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
def create_object_route(data: CreateObject):
    return create_object_service(data)

@router.delete("/{object_id}")
def delete_object_route(object_id: int):
    return delete_object_service(object_id)

@router.patch("/{object_id}")
def update_object_route(object_id: int, data: UpdateObjectSchema):
    return update_object_service(
        object_id,
        data.name,
        data.comment,
        data.model_fields_set
    )

@router.get("/")
def list_objects_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_objects_service(page, per_page)

@router.get("/types")
def list_object_types_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_object_types_service(page, per_page)
