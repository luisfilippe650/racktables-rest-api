from fastapi import APIRouter, Query
from app.service.objects.summary_service import (
    get_object_summary_service,
)
from app.service.objects.attributes_service import update_object_attributes_service
from app.schema.objects.summary_schema import UpdateAttributes

router = APIRouter(
    prefix="/summary",
    tags=["Objects summary"]
)

@router.get("/{object_id}")
def get_object_attributes_route(
    object_id: int,
    include_options: bool = Query(False, description="Include dictionary options for select attributes"),
):
    return get_object_summary_service(object_id, include_options=include_options)

@router.patch("/{object_id}")
def update_attributes_route(object_id: int, updates: UpdateAttributes):
    """
      Update both fixed fields (name, label, asset_no) and
      dynamic RackTables attributes (Serial, Height, etc...)
      """
    return update_object_attributes_service(object_id, updates.root)
