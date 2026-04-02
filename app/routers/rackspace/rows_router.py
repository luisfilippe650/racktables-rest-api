from fastapi import APIRouter
from app.repository.rackspace.rows_repository import (
    create_row,
    delete_row,
    list_row,
    list_complete_rows
)
from app.schema.rackspace.rows_schema import AddManageRows

router = APIRouter(
    prefix="/rows",
    tags=["Rows"]
)

@router.post("/")
def create_row_route(data: AddManageRows):
    return create_row(data)

@router.delete("/{row_id}")
def delete_row_route(row_id: int):
    return delete_row(row_id)

@router.get("/")
def list_rows_route():
    return list_row()

@router.get("/with-racks")
def list_rows_with_racks_route():
    return list_complete_rows()