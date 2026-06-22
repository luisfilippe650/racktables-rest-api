from fastapi import APIRouter, Depends
from app.schema.rackspace.racks_schema import CreateRack, UpdateRackName
from app.core.security import get_current_user
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
def create_rack_route(data: CreateRack , user_id: str = Depends(get_current_user)):
    return create_rack_service(data)

@router.get("/")
def list_racks_route(user_id: str = Depends(get_current_user)):
    return list_racks_service()

@router.patch("/{rack_id}")
def update_rack_name_route(rack_id: int, data: UpdateRackName, user_id: str = Depends(get_current_user)):
    return update_rack_name_service(rack_id, data.name)

@router.get("/occupancy")
def list_racks_space(user_id: str = Depends(get_current_user)):
    return list_racks_with_space_service()

@router.get("/{rack_id}/occupancy")
def list_rack_space(rack_id: int, user_id: str = Depends(get_current_user)):
    return get_rack_occupancy_service(rack_id)

@router.get("/{rack_id}")
def get_rack_details_route(rack_id: int, user_id: str = Depends(get_current_user)):
    return get_rack_details_service(rack_id)

@router.delete("/{rack_id}")
def delete_rack_route(rack_id: int, user_id: str = Depends(get_current_user)):
    return delete_rack_service(rack_id)