from fastapi import APIRouter
from app.service.objects.summary_service import (
    get_object_summary_service,
)

router = APIRouter(
    prefix="/summary",
    tags=["Objects summary"]
)

@router.get("/{object_id}")
def get_object_attributes_route(object_id: int):
    return get_object_summary_service(object_id)

