from app.service.objects.mount_unmount_service import allocate_server_to_rack_service, \
    unallocate_server_from_rack_service, mount_server_service
from app.schema.objects.mount_unmount_schema import MountServer
from fastapi import APIRouter

router = APIRouter(
    prefix="/mount",
    tags=["process for mount and unmount"]
)

@router.post("/")
def mount(data: MountServer):
    return mount_server_service(data)

@router.delete("/{object_id}")
def unmount(object_id: int):
    return unmount_server_service(object_id)
