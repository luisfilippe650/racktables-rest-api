from fastapi import APIRouter
from app.core.databaseConnection import connect

status_router = APIRouter(prefix="/status", tags=["Health"])

@status_router.get("/")
def health():
    try:
        db = connect()
        db.close()
        return {"status": "ok", "database": "connected", "API" : "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}