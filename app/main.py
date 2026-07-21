from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.routers.rackspace.locations_router import router as locations_router
from app.routers.rackspace.rows_router import router as rows_router
from app.routers.rackspace.racks_router import router as racks_router
from app.routers.objects.objects_router import router as objects_router
from app.routers.objects.mount_unmount_router import router as allocate_router
from app.routers.objects.move_router import router as move_router
from app.utils.status_code import status_router
from app.routers.objects.summary_router import router as summary_router
from app.routers.objects.dictionary_router import router as dictionary_router
from app.utils.responses import error_response
from app.core.database import initialize_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    if initialize_pool() is None:
        raise RuntimeError("Database connection pool could not be initialized")
    yield

app = FastAPI(
    title="RackTables Integration API",
    description="""
The RackTables REST API is an integration layer built in Python with FastAPI, designed to expose read and write operations directly on the RackTables MySQL database — an open-source data center inventory and management system.

The API abstracts the underlying SQL queries by providing standardized RESTful endpoints for managing the core RackTables resources: Locations, Rows, Racks, Objects, and Allocations.

Developed by INPE — National Institute for Space Research (Brazil), this solution aims to simplify and standardize programmatic access to infrastructure inventory, enabling seamless integrations with other systems and automation tooling.
""",
    version="1.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

#describe version
API_PREFIX = "/v1/racktables"

app.include_router(locations_router, prefix=API_PREFIX)
app.include_router(rows_router, prefix=API_PREFIX)
app.include_router(racks_router, prefix=API_PREFIX)
app.include_router(objects_router, prefix=API_PREFIX)
app.include_router(summary_router, prefix=API_PREFIX)
app.include_router(dictionary_router, prefix=API_PREFIX)
app.include_router(allocate_router, prefix=API_PREFIX)
app.include_router(move_router, prefix=API_PREFIX)
app.include_router(status_router, prefix=API_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({key: value for key, value in error.items() if key != "ctx"})

    return error_response(
        "Request validation failed",
        status_code=422,
        detail={
            "reason": "validation_error",
            "action": "Fix the request fields and try again.",
            "errors": errors,
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(
        str(exc.detail),
        status_code=exc.status_code,
    )
