from fastapi import APIRouter
from app.repository.rackspace.manageLocations_repository import (
    create_location,
    delete_location,
    list_locations,
    list_complete_location
)
from app.schema.rackspace.manageLocations_schema import AddLocation

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.post("/")
def create_location_route(data: AddLocation):
    return create_location(data)

@router.delete("/{location_id}")
def delete_location_route(location_id: int):
    return delete_location(location_id)

@router.get("/")
def list_locations_route():
    return list_locations()

@router.get("/with-rows")
def list_locations_with_rows_route():
    return list_complete_location()