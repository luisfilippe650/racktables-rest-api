<div align="center">

# 🗄️ RackTables REST API

**A modern REST API for direct integration with the RackTables database**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.3-orange?style=flat-square)]()

<br/>

> Manage Locations, Rows, Racks, Objects and Allocations in RackTables  
> through standardized REST endpoints — no SQL required.

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the API](#-running-the-api)
- [Endpoints](#-endpoints)
  - [Racks](#racks)
  - [Locations](#locations)
  - [Rows](#rows)
  - [Objects](#objects)
  - [Allocations](#allocations)
- [Usage Examples](#-usage-examples)
- [HTTP Status Codes](#-http-status-codes)
- [Contributing](#-contributing)

---

## 🔍 About

The **RackTables REST API** is an abstraction layer built with **Python + FastAPI** that exposes [RackTables](https://racktables.org/) resources — an open-source data center inventory and management system — through standardized HTTP endpoints.

The API operates **directly on the RackTables MySQL database**, eliminating the need to interact manually with SQL queries or the legacy web interface.

### ✨ Features

- 📍 **Locations** — Create and manage physical data center locations
- 🗂️ **Rows** — Organize rack rows within locations
- 🖥️ **Racks** — Manage racks, rack height and per-unit occupancy
- 📦 **Objects** — Register equipment (servers, switches, UPS, etc.)
- 🔌 **Allocations** — Allocate and deallocate equipment at specific rack positions

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

> 📄 **Interactive Swagger docs:** `http://localhost:8000/docs`  
> 📄 **ReDoc documentation:** `http://localhost:8000/redoc`

---

## 📡 Endpoints

### Racks

| Method | Route | Description |
|---|---|---|
| `GET` | `/racks` | List all racks |
| `GET` | `/racks/{rack_id}` | Get a rack by ID |
| `GET` | `/racks/occupancy` | Get occupancy for all racks |
| `GET` | `/racks/{rack_id}/occupancy` | Get occupancy for a specific rack |
| `POST` | `/racks` | Create a new rack |
| `DELETE` | `/racks/{rack_id}` | Delete a rack |

### Locations

| Method | Route | Description |
|---|---|---|
| `GET` | `/locations` | List all locations |
| `GET` | `/locations/rows` | List locations with their rows |
| `POST` | `/locations` | Create a new location |
| `DELETE` | `/locations/{location_id}` | Delete a location |

### Rows

| Method | Route | Description |
|---|---|---|
| `GET` | `/rows` | List all rows |
| `GET` | `/rows/racks` | List rows with their racks |
| `POST` | `/rows` | Create a new row |
| `DELETE` | `/rows/{row_id}` | Delete a row |

### Objects

| Method | Route | Description |
|---|---|---|
| `GET` | `/objects` | List all objects |
| `GET` | `/object/types` | List all available object types |
| `POST` | `/objects` | Create a new object |
| `DELETE` | `/object/{object_id}` | Delete an object |

### Allocations

| Method | Route | Description |
|---|---|---|
| `POST` | `/allocations` | Allocate an object into a rack |
| `DELETE` | `/allocations/{object_id}` | Deallocate an object from a rack |

---

## 💡 Usage Examples

### Create a Rack

```bash
curl -X POST http://localhost:8000/racks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rack A1",
    "rack-height": 42,
    "row_id": 13,
    "assent_no": ""
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
curl http://localhost:8000/racks/26/occupancy
```

```json
{
  "rack_id": 26,
  "rack_name": "Rack A1",
  "total_units": 42,
  "occupied_units": [1, 2, 3],
  "free_units": [4, 5, 6, 7, "..."]
}
```

---

### Create an Object (Server)

```bash
curl -X POST http://localhost:8000/objects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Production Server",
    "asset_no": "PAT-0042",
    "objtype_id": 4
  }'
```

```json
{
  "message": "Object created successfully",
  "object_id": 31,
  "name": "srv-prod-01",
  "objtype_id": 4,
  "ports_created": 3
}
```

---

### Allocate a Server to a Rack

```bash
curl -X POST http://localhost:8000/allocations \
  -H "Content-Type: application/json" \
  -d '{
    "rack_id": 26,
    "object_id": 31,
    "start_unit": 10,
    "height": 2
  }'
```

```json
{
  "message": "Server allocated successfully",
  "rack_id": 26,
  "object_id": 31,
  "start_unit": 10,
  "end_unit": 9,
  "height": 2,
  "molecule_id": 7
}
```

---

### Deallocate a Server

```bash
curl -X DELETE http://localhost:8000/allocations/31
```

```json
{
  "message": "Server deallocated successfully",
  "object_id": 31,
  "rack_id": 26,
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

Made with ❤️ for data center management

</div>
