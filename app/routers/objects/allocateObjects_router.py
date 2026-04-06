from app.service.objects.allocateObjects_service import allocate_server_to_rack_service, unallocate_server_from_rack_service
from app.schema.objects.allocateObjects_schema import AllocateServer
from fastapi import APIRouter

router = APIRouter(
    prefix="/allocations",
    tags=["process for allocate and unallocate"]
)

@router.post("/")
def allocation(data: AllocateServer):
    return allocate_server_to_rack_service(data)

@router.delete("/{object_id}")
def unallocate(object_id: int):
    return unallocate_server_from_rack_service(object_id)
