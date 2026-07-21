from fastapi import APIRouter, Query
from app.schema.objects.objects_schema import CreateObject
from app.service.objects.objects_service import (
    create_object_service,
    delete_object_service,
    get_object_by_name_service,
    get_object_by_service_tag_service,
    list_object_types_service,
    list_all_objects_service,
    list_objects_service
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
def list_objects_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_objects_service(page, per_page)

@router.get("/all")
def list_all_objects_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=255)
):
    return list_all_objects_service(page, per_page, search)

@router.get("/by-name")
def get_object_by_name_route(
    name: str = Query(..., min_length=1, max_length=255)
):
    return get_object_by_name_service(name)

@router.get("/by-service-tag")
def get_object_by_service_tag_route(
    service_tag: str = Query(..., min_length=1, max_length=64)
):
    return get_object_by_service_tag_service(service_tag)

@router.get("/types")
def list_object_types_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_object_types_service(page, per_page)
