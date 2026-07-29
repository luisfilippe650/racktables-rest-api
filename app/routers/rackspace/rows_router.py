from fastapi import APIRouter, Path, Query
from app.service.rackspace.rows_service import (
    create_row_service,
    delete_row_service,
    list_row_service,
    list_complete_rows_service,
    get_row_by_name_service,
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


@router.get("/by-name")
def get_row_by_name_route(
    name: str = Query(..., min_length=1, max_length=255)
):
    return get_row_by_name_service(name)


@router.delete("/{row_id}")
def delete_row_route(row_id: int = Path(..., ge=1)):
    return delete_row_service(row_id)


@router.patch("/{row_id}")
def update_row_name_route(data: UpdateRowName, row_id: int = Path(..., ge=1)):
    return update_row_name_service(row_id, data.name)


@router.put("/{row_id}/{location_id}")
def add_location_to_row_route(
    row_id: int = Path(..., ge=1),
    location_id: int = Path(..., ge=1)
):
    return add_location_to_row_service(row_id, location_id)


@router.delete("/{row_id}/{location_id}")
def remove_location_from_row_route(
    row_id: int = Path(..., ge=1),
    location_id: int = Path(..., ge=1)
):
    return remove_location_from_row_service(row_id, location_id)
