from app.core.security import get_current_user
from app.service.objects.mount_unmount_service import mount_server_service, unmount_server_service
from app.schema.objects.mount_unmount_schema import MountServer
from fastapi import APIRouter , Depends

router = APIRouter(
    prefix="/mount",
    tags=["Process for mount and unmount"]
)

@router.post("/")
def mount(data: MountServer , user_id: str = Depends(get_current_user)):
    return mount_server_service(data)

@router.delete("/{object_id}")
def unmount(object_id: int , user_id: str = Depends(get_current_user)):
    return unmount_server_service(object_id)
