from fastapi import APIRouter
from app.service.objects.summary_service import (
    get_object_summary_service,
)
from app.service.objects.attributes_service import update_object_attributes_service

router = APIRouter(
    prefix="/summary",
    tags=["Objects summary"]
)

@router.get("/{object_id}")
def get_object_attributes_route(object_id: int):
    return get_object_summary_service(object_id)

@router.patch("/{object_id}")
def update_attributes_route(object_id: int, updates: dict):
    """
      Update both fixed fields (name, label, asset_no) and
      dynamic RackTables attributes (Serial, Height, etc...)
      """
    return update_object_attributes_service(object_id, updates)

