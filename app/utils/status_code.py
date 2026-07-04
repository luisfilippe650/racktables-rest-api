import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.database import connect

status_router = APIRouter(prefix="/status", tags=["Health"])
logger = logging.getLogger(__name__)

@status_router.get("/")
def health():
    db = None
    try:
        db = connect()
        if not db:
            return JSONResponse(
                content={"status": "error", "database": "unavailable", "API": "ok"},
                status_code=503
            )
        return {"status": "ok", "database": "connected", "API" : "ok"}
    except Exception as e:
        logger.exception("Healthcheck failed")
        return JSONResponse(
            content={"status": "error", "database": "unavailable", "API": "ok"},
            status_code=503
        )
    finally:
        if db and db.is_connected():
            db.close()
