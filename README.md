<div align="center">

# RackTables REST API

**Integration layer for programmatic access to the RackTables MySQL database**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Version](https://img.shields.io/badge/Version-1.1-orange?style=flat-square)]()

</div>

> REST API built with Python + FastAPI that exposes read and write operations directly on the [RackTables](https://racktables.org/) MySQL database, eliminating the need to interact manually with raw SQL queries or the legacy web interface.
>
> Once running, interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

---

## Table of Contents

- [About](#about)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation and Configuration](#installation-and-configuration)
- [Running the API](#running-the-api)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Locations](#locations)
  - [Rows](#rows)
  - [Racks](#racks)
  - [Objects](#objects)
  - [Object Summary](#object-summary)
  - [Allocations](#allocations)
  - [Move Objects](#move-objects)
- [Usage Examples](#usage-examples)
- [HTTP Status Codes](#http-status-codes)

---

## About

The **RackTables REST API** is an integration layer developed by **INPE — National Institute for Space Research (Brazil)**. It abstracts RackTables SQL queries into standardized RESTful endpoints for managing data center inventory resources: Locations, Rows, Racks, Objects, and Allocations.

> This is a free and open-use API.

**Covered resources:**

- Health Check — API status monitoring
- Locations — physical data center location management
- Rows — rack row organization and location binding
- Racks — creation, renaming, and per-unit occupancy queries
- Objects — registration and update of equipment (servers, switches, UPS, etc.)
- Object Summary — read and write of fixed and dynamic attributes per equipment
- Allocations — mounting and unmounting equipment at specific rack units
- Move — atomic server transfer between racks

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3 | Primary language |
| FastAPI | Web framework |
| Pydantic | Data validation and serialization |
| mysql-connector | MySQL connector |
| Uvicorn | ASGI server |
| Docker | Containerization |
| python-dotenv | Environment variable management |

---

## Project Structure

```
racktables-rest-api/
│
├── app/
│   ├── main.py                          # FastAPI entry point
│   │
│   ├── core/
│   │   └── databaseConnection.py        # MySQL connection management
│   │
│   ├── routers/                         # HTTP routing layer
│   │   ├── objects/
│   │   │   ├── objects_router.py
│   │   │   └── allocateObjects_router.py
│   │   └── rackspace/
│   │       ├── manageLocations_router.py
│   │       ├── rack_router.py
│   │       └── rows_router.py
│   │
│   ├── service/                         # Business logic layer
│   │   ├── objects/
│   │   │   ├── objects_service.py
│   │   │   └── allocateObjects_service.py
│   │   └── rackspace/
│   │       ├── manageLocations_service.py
│   │       ├── rack_service.py
│   │       └── rows_service.py
│   │
│   ├── repository/                      # Data access layer (SQL queries)
│   │   ├── objects/
│   │   │   ├── objects_repository.py
│   │   │   └── allocateObjects_repository.py
│   │   └── rackspace/
│   │       ├── manageLocations_repository.py
│   │       ├── rack_repository.py
│   │       └── rows_repository.py
│   │
│   └── schema/                          # Pydantic schemas
│       ├── objects/
│       │   ├── objects_schema.py
│       │   └── allocateObjects_schema.py
│       └── rackspace/
│           ├── manageLocations_schema.py
│           ├── rack_schema.py
│           └── rows_schema.py
```

**Request flow:**

```
HTTP Client
    │
    ▼
[Router]      →  validates route and HTTP method
    │
    ▼
[Service]     →  applies business rules
    │
    ▼
[Repository]  →  executes MySQL queries
    │
    ▼
[MySQL — RackTables Database]
```

---

## Prerequisites

- Python 3.8+
- MySQL with the RackTables database configured
- Docker *(optional)*

---

## Installation and Configuration

**1. Clone the repository**

```bash
git clone https://github.com/luisfilippe650/racktables-rest-api.git
cd racktables-rest-api
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file at the project root:

```env
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
DB_POOL_SIZE=10
DB_CONNECTION_TIMEOUT=5
DB_READ_TIMEOUT=15
DB_WRITE_TIMEOUT=15
```

---

## Running the API

**Development mode (with hot reload):**

```bash
uvicorn app.main:app --reload
```

**Specifying host and port:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**With Docker:**

```bash
docker build -t racktables-api .
docker run -p 8000:8000 --env-file .env racktables-api
```

The API will be available at `http://localhost:8000`.

---

## Endpoints

All endpoints use the prefix `/v1/racktables/`. For full request and response schemas, see `http://localhost:8000/docs`.

Request bodies with a fixed schema are strict: unknown fields are rejected with `422 Unprocessable Entity`. The object summary update is the exception because it accepts dynamic RackTables attributes.

Paginated listings return items and metadata separately:

```json
{
  "status": "success",
  "message": "Operation successful",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "page_count": 0,
      "total": 0
    }
  }
}
```

---

### Health Check

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/status/` | Checks whether the API is online and operational |

---

### Locations

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/locations/` | Lists all locations |
| `GET` | `/v1/racktables/locations/by-name?name={name}` | Returns a location by name |
| `POST` | `/v1/racktables/locations/` | Creates a new location |
| `DELETE` | `/v1/racktables/locations/{location_id}` | Removes a location by ID |
| `GET` | `/v1/racktables/locations/rows` | Lists locations with their associated rows |

**Schema — Create Location:**

```json
{
  "name": "string"
}
```

---

### Rows

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/rows/` | Lists all rows |
| `GET` | `/v1/racktables/rows/by-name?name={name}` | Returns a row by name |
| `POST` | `/v1/racktables/rows/` | Creates a new row |
| `DELETE` | `/v1/racktables/rows/{row_id}` | Removes a row by ID |
| `PATCH` | `/v1/racktables/rows/{row_id}` | Updates a row name |
| `GET` | `/v1/racktables/rows/racks` | Lists rows with their associated racks |
| `PUT` | `/v1/racktables/rows/{row_id}/{location_id}` | Binds a row to a location |
| `DELETE` | `/v1/racktables/rows/{row_id}/{location_id}` | Removes the binding between a row and a location |

**Schema — Create / Rename Row:**

```json
{
  "name": "string"
}
```

---

### Racks

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/racks/` | Lists all racks |
| `GET` | `/v1/racktables/racks/by-name?name={name}` | Returns a rack by name |
| `POST` | `/v1/racktables/racks/` | Creates a new rack |
| `GET` | `/v1/racktables/racks/{rack_id}` | Returns details of a specific rack |
| `PATCH` | `/v1/racktables/racks/{rack_id}` | Updates a rack name |
| `DELETE` | `/v1/racktables/racks/{rack_id}` | Removes a rack by ID |
| `GET` | `/v1/racktables/racks/occupancy` | Returns occupancy for all racks |
| `GET` | `/v1/racktables/racks/{rack_id}/occupancy` | Returns occupancy for a specific rack |

**Schema — Create Rack:**

```json
{
  "name": "string",
  "rack_height": 42,
  "row_id": 10,
  "asset_no": "string"
}
```

> `rack_height` is optional (default: `42`). `row_id` is required.

---

### Objects

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/objects/` | Lists registered inventory objects |
| `GET` | `/v1/racktables/objects/all` | Lists all objects, including locations, rows, and racks |
| `POST` | `/v1/racktables/objects/` | Creates a new object |
| `DELETE` | `/v1/racktables/objects/{object_id}` | Removes an object by ID |
| `GET` | `/v1/racktables/objects/types` | Lists all available object types |

**Schema — Create Object:**

```json
{
  "name": "string",
  "label": "string",
  "asset_no": "string",
  "comment": "string",
  "objtype_id": 4
}
```

---

### Object Summary

Allows querying and updating detailed attributes of an equipment item, including fixed fields (`name`, `label`, `asset_no`) and dynamic RackTables attributes (Serial, Height, etc.).
The `GET` response also includes `is_allocated`, indicating whether the object is allocated in a rack.

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racktables/summary/{object_id}` | Returns all attributes of an object |
| `PATCH` | `/v1/racktables/summary/{object_id}` | Updates fixed and/or dynamic attributes of an object; send only the fields to change |

**Schema — Update Attributes (`PATCH`):**

The body accepts a free-form JSON object with any combination of fixed fields and dynamic attributes:

```json
{
  "name": "srv-prod-01",
  "label": "Production Server",
  "asset_no": "PAT-0042",
  "has_problems": false,
  "comment": "Server updated through the API",
  "Serial": "SN123456",
  "OEM S/N 1": "ABC123"
}
```

To clear a dynamic attribute, send the `clear` command:

```json
{
  "Serial": { "clear": true }
}
```

---

### Allocations

| Method | Route | Description |
|---|---|---|
| `POST` | `/v1/racktables/mount/` | Mounts an object at a rack position |
| `DELETE` | `/v1/racktables/mount/{object_id}` | Unmounts an object from the rack |

**Schema — Mount Object:**

```json
{
  "rack_id": 33,
  "object_id": 815,
  "start_unit": 10,
  "height": 2
}
```

> All fields are required.

---

### Move Objects

| Method | Route | Description |
|---|---|---|
| `POST` | `/v1/racktables/move/` | Moves a server from one rack to another |

**Schema — Move Server:**

```json
{
  "object_id": 815,
  "destination_rack_id": 34,
  "start_unit": 20,
  "source_rack_id": 33,
  "height": 2
}
```

> `start_unit` and `height` refer to the position in the **destination** rack. `source_rack_id` and `height` are optional.

---

## Usage Examples

### Check API status

```bash
curl http://localhost:8000/v1/racktables/status/
```

### Create a location

```bash
curl -X POST http://localhost:8000/v1/racktables/locations/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Server Room A"}'
```

```json
{
  "status": "success",
  "message": "Location successfully created",
  "data": {
    "id": 29,
    "name": "Server Room A"
  }
}
```

### Create a row and bind it to a location

```bash
# Create the row
curl -X POST http://localhost:8000/v1/racktables/rows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Row 01"}'

# Bind row (id: 10) to location (id: 29)
curl -X PUT http://localhost:8000/v1/racktables/rows/10/29
```

### Create a rack

```bash
curl -X POST http://localhost:8000/v1/racktables/racks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rack A1",
    "rack_height": 42,
    "row_id": 10,
    "asset_no": "PAT-001"
  }'
```

```json
{
  "status": "success",
  "message": "Rack created successfully",
  "data": {
    "rack_id": 27,
    "name": "Rack A1"
  }
}
```

### Query rack occupancy

```bash
curl http://localhost:8000/v1/racktables/racks/27/occupancy
```

```json
{
  "status": "success",
  "message": "Operation successful",
  "data": {
    "rack_id": 27,
    "rack_name": "Rack A1",
    "total_units": 42,
    "occupied_units": [1, 2],
    "free_units": [3, 4, 5, "..."]
  }
}
```

### Create a server and allocate it to a rack

```bash
# Create the object
curl -X POST http://localhost:8000/v1/racktables/objects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Production Server",
    "asset_no": "PAT-0042",
    "objtype_id": 4
  }'

# Mount object (id: 31) in rack (id: 27), starting at unit 10, height 2U
curl -X POST http://localhost:8000/v1/racktables/mount/ \
  -H "Content-Type: application/json" \
  -d '{
    "rack_id": 27,
    "object_id": 31,
    "start_unit": 10,
    "height": 2
  }'
```

```json
{
  "status": "success",
  "message": "Server allocated successfully",
  "data": {
    "rack_id": 27,
    "object_id": 31,
    "start_unit": 10,
    "end_unit": 9,
    "height": 2,
    "molecule_id": 123
  }
}
```

### Update object attributes

Update fixed object fields:

```bash
curl -X PATCH http://localhost:8000/v1/racktables/summary/31 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01-renamed",
    "label": "Production Server",
    "asset_no": "PAT-0042",
    "has_problems": false,
    "comment": "Updated through the API"
  }'
```

Update dynamic RackTables attributes:

```bash
curl -X PATCH http://localhost:8000/v1/racktables/summary/31 \
  -H "Content-Type: application/json" \
  -d '{
    "Serial": "SN987654",
    "OEM S/N 1": "ABC123"
  }'
```

Clear a dynamic attribute:

```bash
curl -X PATCH http://localhost:8000/v1/racktables/summary/31 \
  -H "Content-Type: application/json" \
  -d '{
    "Serial": { "clear": true }
  }'
```

### Move a server to another rack

```bash
curl -X POST http://localhost:8000/v1/racktables/move/ \
  -H "Content-Type: application/json" \
  -d '{
    "object_id": 31,
    "source_rack_id": 27,
    "destination_rack_id": 35,
    "start_unit": 5,
    "height": 2
  }'
```

### Unmount a server

```bash
curl -X DELETE http://localhost:8000/v1/racktables/mount/31
```

```json
{
  "message": "Server deallocated successfully",
  "object_id": 31,
  "rack_id": 27,
  "units_removed": [9, 10]
}
```

---

## HTTP Status Codes

| Code | Status | Description |
|---|---|---|
| `200` | OK | Request processed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid data in the request body |
| `404` | Not Found | Resource not found |
| `422` | Unprocessable Entity | Missing or malformed JSON body |
| `500` | Internal Server Error | Server error or database connection failure |

---

<div align="center">
Developed for data center management at <strong>INPE — National Institute for Space Research</strong>
</div>
