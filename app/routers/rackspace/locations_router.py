from fastapi import APIRouter, Path, Query
from app.service.rackspace.locations_service import (
    create_location_service,
    delete_location_service,
    get_location_by_name_service,
    list_locations_service,
    list_complete_location_service,
)
from app.schema.rackspace.locations_schema import AddLocation

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.post("/")
def create_location_route(data: AddLocation):
    return create_location_service(data)

@router.delete("/{location_id}")
def delete_location_route(location_id: int = Path(..., ge=1)):
    return delete_location_service(location_id)

@router.get("/")
def list_locations_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_locations_service(page, per_page)

@router.get("/by-name")
def get_location_by_name_route(
    name: str = Query(..., min_length=1, max_length=255)
):
    return get_location_by_name_service(name)

@router.get("/rows")
def list_locations_with_rows_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_complete_location_service(page, per_page)
