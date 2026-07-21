import logging

from fastapi import APIRouter
from app.core.database import connect
from app.utils.responses import error_response, success_response
from app.utils.database_resources import close_database_resources

status_router = APIRouter(prefix="/status", tags=["Health"])
logger = logging.getLogger(__name__)

@status_router.get("/")
def health():
    db = None
    try:
        db = connect()
        if not db:
            return error_response(
                message="Database unavailable",
                status_code=503,
                detail={
                    "reason": "service_unavailable",
                    "action": "Check database connectivity and try again.",
                    "services": {"api": "ok", "database": "unavailable"},
                },
            )
        return success_response(
            message="API is healthy",
            data={"services": {"api": "ok", "database": "connected"}},
        )
    except Exception as e:
        logger.exception("Healthcheck failed")
        return error_response(
            message="Health check failed",
            status_code=503,
            detail={
                "reason": "service_unavailable",
                "action": "Check database connectivity and try again.",
                "services": {"api": "ok", "database": "unavailable"},
            },
        )
    finally:
        close_database_resources(database=db, logger=logger)
