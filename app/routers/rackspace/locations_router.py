from app.schema.rackspace.locations_schema import AddLocation
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.service.rackspace.locations_service import (
    create_location_service,
    delete_location_service,
    list_locations_service,
    list_complete_location_service,
)

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.post("/")
def create_location_route(data: AddLocation, user_id: str = Depends(get_current_user)):
    return create_location_service(data)

@router.delete("/{location_id}")
def delete_location_route(location_id: int, user_id: str = Depends(get_current_user)):
    return delete_location_service(location_id)

@router.get("/")
def list_locations_route():
    return list_locations_service()

@router.get("/rows")
def list_locations_with_rows_route():
    return list_complete_location_service()