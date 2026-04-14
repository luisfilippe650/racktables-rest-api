<div align="center">

# 🗄️ RackTables REST API

**A modern REST API for direct integration with the RackTables database**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1-orange?style=flat-square)]()

<br/>

> Manage Locations, Rows, Racks, Objects, Allocations and Object Movement in RackTables  
> through standardized REST endpoints — no SQL required.

<br/>

> 💡 **Tip:** Once the API is running, access the full interactive documentation at  
> **`http://localhost:8000/docs`** (Swagger UI) or **`http://localhost:8000/redoc`** (ReDoc)  
> to explore and test all endpoints directly from your browser.

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the API](#-running-the-api)
- [Interactive Documentation (Swagger)](#-interactive-documentation-swagger)
- [Endpoints](#-endpoints)
  - [Health Check](#health-check)
  - [Locations](#locations)
  - [Rows](#rows)
  - [Racks](#racks)
  - [Objects](#objects)
  - [Allocations](#allocations)
  - [Move Objects](#move-objects)
- [Usage Examples](#-usage-examples)
- [HTTP Status Codes](#-http-status-codes)
- [Contributing](#-contributing)

---

## 🔍 About

The **RackTables REST API** is an integration layer built with **Python + FastAPI** by **INPE — National Institute for Space Research (Brazil)**, that exposes [RackTables](https://racktables.org/) resources — an open-source data center inventory and management system — through standardized HTTP endpoints.

The API operates **directly on the RackTables MySQL database**, eliminating the need to interact manually with SQL queries or the legacy web interface.

### ✨ Features

- 🏥 **Health Check** — Monitor the API status in real time
- 📍 **Locations** — Create and manage physical data center locations
- 🗂️ **Rows** — Organize rack rows, link them to locations and rename them
- 🖥️ **Racks** — Manage racks, rack height and per-unit occupancy, rename them
- 📦 **Objects** — Register and update equipment (servers, switches, UPS, etc.)
- 🔌 **Allocations** — Allocate and deallocate equipment at specific rack positions
- 🚚 **Move Objects** — Move servers between racks in a single operation

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3** | Core language |
| **FastAPI** | High-performance web framework |
| **Pydantic** | Data validation and serialization |
| **mysql-connector** | MySQL database connector |
| **Uvicorn** | ASGI server to run the application |
| **Docker** | Environment containerization |
| **python-dotenv** | Environment variable management |

---

## 📁 Project Structure

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

### Request Flow

```
HTTP Client
    │
    ▼
[Router]  ──→  Validates route and HTTP method
    │
    ▼
[Service]  ──→  Applies business rules
    │
    ▼
[Repository]  ──→  Executes MySQL queries
    │
    ▼
[MySQL — RackTables DB]
```

---

## 📦 Prerequisites

- Python 3.8+
- MySQL with the RackTables database configured
- Docker *(optional)*

---

## ⚙️ Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/your-username/racktables-rest-api.git
cd racktables-rest-api
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
```

---

## 🚀 Running the API

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

The API will be available at `http://localhost:8000`

---

## 📖 Interactive Documentation (Swagger)

One of the biggest advantages of FastAPI is **automatic interactive documentation generation**. Once the API is running, you have access to two interfaces:

### Swagger UI — `http://localhost:8000/docs`

The most complete interface to explore and test the API:

- ✅ View all endpoints organized by group (Locations, Rows, Racks, etc.)
- ✅ See the **request and response schemas** for every endpoint
- ✅ **Execute real requests** directly from the browser — no Postman or curl needed
- ✅ Inspect possible response codes and example payloads

### ReDoc — `http://localhost:8000/redoc`

An alternative interface focused on documentation readability, ideal for sharing with teams or clients.

> **We strongly recommend using the Swagger UI (`/docs`) to explore the API during development and testing.**

---

## 📡 Endpoints

> All endpoints use the `/v1/` prefix. For full request/response schema details, visit **`http://localhost:8000/docs`**.

---

### Health Check

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/status/` | Check if the API is online and operational |

---

### Locations

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/locations/` | List all locations |
| `POST` | `/v1/locations/` | Create a new location |
| `DELETE` | `/v1/locations/{location_id}` | Delete a location by ID |
| `GET` | `/v1/locations/rows` | List locations with their associated rows |

**Schema — Create Location (`POST /v1/locations/`):**

```json
{
  "name": "string"
}
```

---

### Rows

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/rows/` | List all rows |
| `POST` | `/v1/rows/` | Create a new row |
| `DELETE` | `/v1/rows/{row_id}` | Delete a row by ID |
| `PATCH` | `/v1/rows/{row_id}` | Update a row's name |
| `GET` | `/v1/rows/racks` | List rows with their associated racks |
| `PUT` | `/v1/rows/{row_id}/{location_id}` | Link a row to a location |
| `DELETE` | `/v1/rows/{row_id}/{location_id}` | Remove the link between a row and a location |

**Schema — Create Row (`POST /v1/rows/`):**

```json
{
  "name": "string"
}
```

**Schema — Update Row Name (`PATCH /v1/rows/{row_id}`):**

```json
{
  "name": "string"
}
```

---

### Racks

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/racks/` | List all racks |
| `POST` | `/v1/racks/` | Create a new rack |
| `GET` | `/v1/racks/{rack_id}` | Get details of a specific rack |
| `PATCH` | `/v1/racks/{rack_id}` | Update a rack's name |
| `DELETE` | `/v1/racks/{rack_id}` | Delete a rack by ID |
| `GET` | `/v1/racks/occupancy` | Get occupancy for all racks |
| `GET` | `/v1/racks/{rack_id}/occupancy` | Get occupancy for a specific rack |

**Schema — Create Rack (`POST /v1/racks/`):**

```json
{
  "name": "string",
  "rack_height": 42,
  "row_id": 0,
  "asset_no": "string"
}
```

> `rack_height` is optional (default: `42`). `row_id` is required.

**Schema — Update Rack Name (`PATCH /v1/racks/{rack_id}`):**

```json
{
  "name": "string"
}
```

---

### Objects

| Method | Route | Description |
|---|---|---|
| `GET` | `/v1/objects/` | List all registered objects |
| `POST` | `/v1/objects/` | Create a new object |
| `DELETE` | `/v1/objects/{object_id}` | Delete an object by ID |
| `PATCH` | `/v1/objects/{object_id}` | Update an object's name or comment |
| `GET` | `/v1/objects/types` | List all available object types |

**Schema — Create Object (`POST /v1/objects/`):**

```json
{
  "name": "string",
  "label": "string",
  "asset_no": "string",
  "objtype_id": 0
}
```

**Schema — Update Object (`PATCH /v1/objects/{object_id}`):**

```json
{
  "name": "string",
  "comment": "string"
}
```

> Both fields are optional in `PATCH`. Send only what you want to update.

---

### Allocations

| Method | Route | Description |
|---|---|---|
| `POST` | `/v1/allocations/` | Allocate an object into a rack position |
| `DELETE` | `/v1/allocations/{object_id}` | Deallocate an object from a rack |

**Schema — Allocate (`POST /v1/allocations/`):**

```json
{
  "rack_id": 0,
  "object_id": 0,
  "start_unit": 0,
  "height": 0
}
```

> All fields are required.

---

### Move Objects

| Method | Route | Description |
|---|---|---|
| `POST` | `/v1/move/` | Move a server from one rack to another |

**Schema — Move Server (`POST /v1/move/`):**

```json
{
  "object_id": 0,
  "source_rack_id": 0,
  "destination_rack_id": 0,
  "start_unit": 0,
  "height": 0
}
```

> All fields are required. `start_unit` and `height` refer to the position in the **destination** rack.

---

## 💡 Usage Examples

### Check API Status

```bash
curl http://localhost:8000/v1/status/
```

---

### Create a Location

```bash
curl -X POST http://localhost:8000/v1/locations/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Server Room A"}'
```

```json
{
  "id": 29,
  "name": "Server Room A",
  "message": "Location created successfully"
}
```

---

### Create a Row and Link it to a Location

```bash
# 1. Create the row
curl -X POST http://localhost:8000/v1/rows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Row 01"}'

# 2. Link row (id: 10) to location (id: 29)
curl -X PUT http://localhost:8000/v1/rows/10/29
```

---

### Create a Rack

```bash
curl -X POST http://localhost:8000/v1/racks/ \
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
  "message": "Rack created successfully",
  "rack_id": 27
}
```

---

### Check Rack Occupancy

```bash
curl http://localhost:8000/v1/racks/27/occupancy
```

```json
{
  "rack_id": 27,
  "rack_name": "Rack A1",
  "total_units": 42,
  "occupied_units": [1, 2],
  "free_units": [3, 4, 5, "..."]
}
```

---

### Create a Server Object and Allocate it to a Rack

```bash
# 1. Create the object
curl -X POST http://localhost:8000/v1/objects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Production Server",
    "asset_no": "PAT-0042",
    "objtype_id": 4
  }'

# 2. Allocate object (id: 31) to rack (id: 27), starting at unit 10, height 2U
curl -X POST http://localhost:8000/v1/allocations/ \
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
  "message": "Server allocated successfully",
  "rack_id": 27,
  "object_id": 31,
  "start_unit": 10,
  "end_unit": 9,
  "height": 2,
  "molecule_id": 7
}
```

---

### Move a Server to Another Rack

```bash
# Move object (id: 31) from rack (id: 27) to rack (id: 35), placing it at unit 5, height 2U
curl -X POST http://localhost:8000/v1/move/ \
  -H "Content-Type: application/json" \
  -d '{
    "object_id": 31,
    "source_rack_id": 27,
    "destination_rack_id": 35,
    "start_unit": 5,
    "height": 2
  }'
```

---

### Deallocate a Server

```bash
curl -X DELETE http://localhost:8000/v1/allocations/31
```

```json
{
  "message": "Server deallocated successfully",
  "object_id": 31,
  "rack_id": 27,
  "units_removed": [9, 10],
  "molecule_id": 8
}
```

---

## 📊 HTTP Status Codes

| Code | Status | Description |
|---|---|---|
| `200` | OK | Request processed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid data in request body |
| `404` | Not Found | Resource not found |
| `422` | Unprocessable Entity | Missing or malformed JSON body |
| `500` | Internal Server Error | Server error or database connection failure |

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

<div align="center">

Made for INPE (National Institute for Space Research) data center management

</div>
