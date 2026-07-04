from fastapi import APIRouter, Query
from app.schema.rackspace.racks_schema import CreateRack, UpdateRackName
from app.service.rackspace.racks_service import (
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
def list_racks_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_racks_service(page, per_page)

@router.patch("/{rack_id}")
def update_rack_name_route(rack_id: int, data: UpdateRackName):
    return update_rack_name_service(rack_id, data.name)

@router.get("/occupancy")
def list_racks_space(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_racks_with_space_service(page, per_page)

@router.get("/{rack_id}/occupancy")
def list_rack_space(rack_id: int):
    return get_rack_occupancy_service(rack_id)

@router.get("/{rack_id}")
def get_rack_details_route(rack_id: int):
    return get_rack_details_service(rack_id)

@router.delete("/{rack_id}")
def delete_rack_route(rack_id: int):
    return delete_rack_service(rack_id)
