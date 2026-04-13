from fastapi import APIRouter
from app.schema.rackspace.rack_schema import CreateRack, UpdateRackName
from app.service.rackspace.rack_service import (
    create_rack_service,
    list_racks_service,
    delete_rack_service,
    list_racks_with_space_service,
    get_rack_details_service,
    get_rack_occupancy_service, update_rack_name_service
)


router = APIRouter(
    prefix="/racks",
    tags=["Racks"]
)

@router.post("/")
def create_rack_route(data: CreateRack):
    return create_rack_service(data)

@router.get("/")
def list_racks_route():
    return list_racks_service()

@router.patch("/{rack_id}")
def update_rack_name_route(rack_id: int, data: UpdateRackName):
    return update_rack_name_service(rack_id, data.name)

@router.get("/occupancy")
def list_racks_space():
    return list_racks_with_space_service()

@router.get("/{rack_id}/occupancy")
def list_rack_space(rack_id: int):
    return get_rack_occupancy_service(rack_id)

@router.get("/{rack_id}")
def get_rack_details_route(rack_id: int):
    return get_rack_details_service(rack_id)

@router.delete("/{rack_id}")
def delete_rack_route(rack_id: int):
    return delete_rack_service(rack_id)