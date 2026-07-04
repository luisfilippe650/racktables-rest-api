from fastapi import APIRouter, Query
from app.service.rackspace.rows_service import (
    create_row_service,
    delete_row_service,
    list_row_service,
    list_complete_rows_service,
    add_location_to_row_service,
    remove_location_from_row_service,
    update_row_name_service
)
from app.schema.rackspace.rows_schema import AddRows, UpdateRowName

router = APIRouter(
    prefix="/rows",
    tags=["Rows"]
)


@router.post("/")
def create_row_route(data: AddRows):
    return create_row_service(data)


@router.get("/")
def list_rows_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_row_service(page, per_page)


@router.get("/racks")
def list_rows_with_racks_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    return list_complete_rows_service(page, per_page)


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
