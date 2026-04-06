from fastapi import APIRouter
from app.service.rackspace.rows_service import (
    create_row_service,
    delete_row_service,
    list_row_service,
    list_complete_rows_service
)
from app.schema.rackspace.rows_schema import AddManageRows

router = APIRouter(
    prefix="/rows",
    tags=["Rows"]
)

@router.post("/")
def create_row_route(data: AddManageRows):
    return create_row_service(data)

@router.delete("/{row_id}")
def delete_row_route(row_id: int):
    return delete_row_service(row_id)

@router.get("/")
def list_rows_route():
    return list_row_service()

@router.get("/racks")
def list_rows_with_racks_route():
    return list_complete_rows_service()