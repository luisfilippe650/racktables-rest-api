from fastapi import FastAPI
from app.routers.rackspace.manageLocations_router import router as locations_router
from app.routers.rackspace.rows_router import router as rows_router
from app.routers.rackspace.rack_router import router as racks_router
from app.routers.objects.objects_router import router as objects_router
from app.routers.objects.allocateObjects_router import router as allocate_router
app = FastAPI()

#describe version
API_PREFIX = "/v0.2"

app.include_router(locations_router, prefix=API_PREFIX)
app.include_router(rows_router, prefix=API_PREFIX)
app.include_router(racks_router, prefix=API_PREFIX)
app.include_router(objects_router, prefix=API_PREFIX)
app.include_router(allocate_router, prefix=API_PREFIX)
