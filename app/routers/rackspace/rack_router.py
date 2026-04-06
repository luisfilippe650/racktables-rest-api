from fastapi import APIRouter
from app.service.rackspace.rack_service import (
    create_rack_service,
    list_racks_service,
    delete_rack_service,
    list_racks_with_space_service
)
from app.schema.rackspace.rack_schema import CreateRack

router = APIRouter(
    prefix="/racks",
    tags=["Racks"]
)

@router.post("/")
def create_rack_route(data: CreateRack):
    return create_rack_service(data)

@router.delete("/{rack_id}")
def delete_rack_route(rack_id: int):
    return delete_rack_service(rack_id)

@router.get("/")
def list_racks_route():
    return list_racks_service()

@router.get("/space")
def list_racks_space():
    return list_racks_with_space_service()