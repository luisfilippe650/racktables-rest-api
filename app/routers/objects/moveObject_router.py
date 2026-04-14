from fastapi import APIRouter
from app.schema.objects.moveObject_schema import MoveServer
from app.service.objects.moveObjects_service import move_server_to_another_rack_service

router = APIRouter(
    prefix="/move",
    tags=["Move Objects"]
)

@router.post("/")
def move_server_route(data: MoveServer):
    return move_server_to_another_rack_service(data)