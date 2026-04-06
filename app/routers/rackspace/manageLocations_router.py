from fastapi import APIRouter
from app.service.rackspace.manageLocations_service import (
    create_location_service,
    delete_location_service,
    list_locations_service,
    list_complete_location_service,
)
from app.schema.rackspace.manageLocations_schema import AddLocation

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.post("/")
def create_location_route(data: AddLocation):
    return create_location_service(data)

@router.delete("/{location_id}")
def delete_location_route(location_id: int):
    return delete_location_service(location_id)

@router.get("/")
def list_locations_route():
    return list_locations_service()

@router.get("/rows")
def list_locations_with_rows_route():
    return list_complete_location_service()