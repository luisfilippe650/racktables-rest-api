from fastapi import APIRouter
from app.service.rackspace.rows_service import (
    create_row_service,
    delete_row_service,
    list_row_service,
    list_complete_rows_service,
    add_location_to_row_service,
    remove_location_from_row_service,
    update_row_name_service
)
from app.schema.rackspace.rows_schema import AddManageRows, UpdateRowName

router = APIRouter(
    prefix="/rows",
    tags=["Rows"]
)


@router.post("/")
def create_row_route(data: AddManageRows):
    return create_row_service(data)


@router.get("/")
def list_rows_route():
    return list_row_service()


@router.get("/racks")
def list_rows_with_racks_route():
    return list_complete_rows_service()


@router.delete("/{row_id}")
def delete_row_route(row_id: int):
    return delete_row_service(row_id)


@router.patch("/{row_id}")
def update_row_name_route(row_id: int, data: UpdateRowName):
    return update_row_name_service(row_id, data.name)


@router.put("/{row_id}/{location_id}")
def add_location_to_row_route(row_id: int, location_id: int):
    return add_location_to_row_service(row_id, location_id)


@router.delete("/{row_id}/{location_id}")
def remove_location_from_row_route(row_id: int, location_id: int):
    return remove_location_from_row_service(row_id, location_id)