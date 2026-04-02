from fastapi import APIRouter
from app.repository.rackspace.rack_repository import (
    create_rack,
    list_racks,
    delete_rack,
    list_racks_with_space
)
from app.schema.rackspace.rack_schema import CreateRack

router = APIRouter(
    prefix="/racks",
    tags=["Racks"]
)

@router.post("/")
def create_rack_route(data: CreateRack):
    return create_rack(data)

@router.delete("/{rack_id}")
def delete_rack_route(rack_id: int):
    return delete_rack(rack_id)

@router.get("/")
def list_racks_route():
    return list_racks()

@router.get("/space")
def list_racks_space():
    return list_racks_with_space()