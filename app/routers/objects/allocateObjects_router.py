from app.repository.objects.allocateObjects_repository import (
    allocate_server_to_rack,
    unallocate_server_from_rack
)
from app.schema.objects.allocateObjects_schema import AllocateServer
from fastapi import APIRouter

router = APIRouter(
    prefix="/allocations",
    tags=["process for allocate and unallocate"]
)

@router.post("/")
def create_allocation(data: AllocateServer):
    return allocate_server_to_rack(data)

@router.delete("/{object_id}")
def delete_allocation(object_id: int):
    return unallocate_server_from_rack(object_id)
