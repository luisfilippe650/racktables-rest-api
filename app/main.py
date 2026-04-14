from fastapi import FastAPI
from app.routers.rackspace.manageLocations_router import router as locations_router
from app.routers.rackspace.rows_router import router as rows_router
from app.routers.rackspace.rack_router import router as racks_router
from app.routers.objects.objects_router import router as objects_router
from app.routers.objects.allocateObjects_router import router as allocate_router
from app.routers.objects.moveObject_router import router as move_router
from app.utils.status_code import status_router

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
    openapi_url="/openapi.json"
)

#describe version
API_PREFIX = "/v1"

app.include_router(locations_router, prefix=API_PREFIX)
app.include_router(rows_router, prefix=API_PREFIX)
app.include_router(racks_router, prefix=API_PREFIX)
app.include_router(objects_router, prefix=API_PREFIX)
app.include_router(allocate_router, prefix=API_PREFIX)
app.include_router(move_router, prefix=API_PREFIX)
app.include_router(status_router, prefix=API_PREFIX)