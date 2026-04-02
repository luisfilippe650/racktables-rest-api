<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-v0.1%20Testing-F59E0B?style=for-the-badge" />
</p>

<h1 align="center">🗄️ RackTables REST API</h1>

<p align="center">
  A modern REST API layer built on top of the <strong>RackTables</strong> database — bringing structured, validated, and auditable operations to your datacenter infrastructure.
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-business-rules">Business Rules</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 📌 Overview

This project exposes a **FastAPI-based REST API** to interact directly with the **RackTables** relational database — the open-source solution widely used for physical datacenter asset management.

The API abstracts and enforces the complex internal logic of RackTables, providing clean and predictable endpoints for:

- 📍 **Locations** — Datacenter sites
- 🧱 **Rows** — Physical row groupings inside locations
- 🗄️ **Racks** — Individual rack units with capacity tracking
- 🖥️ **Objects** — Servers, network devices, and other assets
- 📦 **Allocations** — Server placement and removal within racks

> **Version:** `v0.1 — Testing Phase`
> Current development focuses on data integrity, business rule enforcement, and safe interactions with the underlying legacy RackTables schema.

---

## 🗂️ Project Structure

```text
racktables-rest-api/
│
├── app/
│   ├── routers/           # Route definitions per resource (locations, racks, objects...)
│   ├── repository/        # Database query logic (raw SQL with MySQL connector)
│   ├── schema/            # Pydantic models for request/response validation
│   ├── core/              # Database connection, config, shared utilities
│   └── main.py            # Application entry point, router registration
│
├── database/
│   ├── schema.sql         # RackTables database schema
│   └── seed.sql           # Initial seed data
│
├── .env                   # Environment variables (not committed)
├── docker-compose.yml     # (optional) Compose setup
└── README.md
```

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python 3.11** | Core language |
| **FastAPI** | REST framework with automatic OpenAPI docs |
| **MySQL 8** | Primary database (RackTables-compatible) |
| **Docker** | Containerized database setup |
| **Pydantic v2** | Request validation and schema enforcement |
| **MySQL Connector** | Raw SQL execution with dictionary cursors |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone git@github.com:luisfilippe650/racktables-rest-api.git
cd racktables-rest-api
```

### 2. Configure Environment Variables

Create a `.env` file at the project root:

```env
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
```

### 3. Start the Database (Docker)

This command spins up MySQL 8, creates the database, and runs `schema.sql` + `seed.sql` automatically:

```bash
docker run -d \
  --name racktables-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=racktables \
  -p 3307:3306 \
  -v $(pwd)/database:/docker-entrypoint-initdb.d \
  mysql:8
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

| Interface | URL |
|---|---|
| **API Base URL** | `http://127.0.0.1:8000` |
| **Swagger UI** | `http://127.0.0.1:8000/docs` |
| **ReDoc** | `http://127.0.0.1:8000/redoc` |

---

## 📡 API Reference

### 📍 Locations

> Base path: `/locations`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/locations` | Create a new location |
| `DELETE` | `/locations/{location_id}` | Delete a location and its dependencies |
| `GET` | `/locations` | List all locations |
| `GET` | `/locations/with-rows` | List locations including their rows |

#### `POST /locations`

```json
{
  "name": "Datacenter A"
}
```

#### `DELETE /locations/{location_id}`

> ⚠️ **Rule:** Removes all dependencies, cleans related data, and maintains audit history before deletion.

---

### 🧱 Rows

> Base path: `/rows`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/rows` | Create a new row |
| `DELETE` | `/rows/{row_id}` | Delete a row |
| `GET` | `/rows` | List all rows |
| `GET` | `/rows/with-racks` | List rows including their racks |

#### `POST /rows`

```json
{
  "name": "Row A"
}
```

#### `DELETE /rows/{row_id}`

> ⚠️ **Rule:** A row **cannot be deleted** if it contains racks. Remove all racks first.

---

### 🗄️ Racks

> Base path: `/racks`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/racks` | Create a new rack |
| `DELETE` | `/racks/{rack_id}` | Delete a rack |
| `GET` | `/racks` | List all racks |
| `GET` | `/racks/space` | List racks with available space metrics |

#### `POST /racks`

```json
{
  "name": "Rack 01",
  "row_id": 1,
  "rack_height": 42
}
```

> ⚠️ **Rule:** Must be linked to a valid, existing row.

#### `DELETE /racks/{rack_id}`

> ⚠️ **Rule:** A rack **cannot be deleted** if objects are currently allocated within it.

#### `GET /racks/space` — Response Example

```json
[
  {
    "rack_id": 1,
    "rack_name": "Rack 01",
    "total_units": 42,
    "occupied_units": [42, 41, 40, 39],
    "free_units": [38, 37, 36, 35, 34]
  }
]
```

---

### 🖥️ Objects

> Base path: `/objects`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/objects` | Create a new object (server, device, etc.) |
| `DELETE` | `/objects/{object_id}` | Delete an object and all its dependencies |
| `GET` | `/objects` | List all objects |
| `GET` | `/objects/types` | List all supported object types |

#### `POST /objects`

```json
{
  "name": "Server01",
  "label": "Production Server",
  "objtype_id": 4
}
```

> ⚠️ **Rules:**
> - Validates object type against supported types
> - Prevents duplicate names
> - Automatically creates default ports for server-type objects (`objtype_id: 4`)

#### `DELETE /objects/{object_id}`

> ⚠️ **Rule:** Removes network configurations, VLANs, ports, mounts, and rack allocations. Saves full audit history before deletion.

#### `GET /objects` — Response Example

```json
[
  {
    "object_id": 38,
    "object_name": "SERVER-01",
    "object_label": "Servidor de teste",
    "asset_no": "PAT-001",
    "objtype_id": 4,
    "object_type": "Server",
    "rack_id": 37,
    "rack_name": "RACK-01"
  }
]
```

---

### 📦 Allocations

> Base path: `/allocations`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/allocations` | Allocate a server to a rack position |
| `DELETE` | `/allocations/{object_id}` | Unallocate a server from its rack |
| `GET` | `/allocations` | List all racks with space metrics |

#### `POST /allocations`

```json
{
  "rack_id": 1,
  "object_id": 10,
  "start_unit": 42,
  "height": 2
}
```

> ⚠️ **Rules enforced before allocation:**
> - Rack and object must both exist
> - Object must be of server type (`objtype_id: 4`)
> - Object must not already be allocated elsewhere
> - Requested rack units must all be free
> - Height must be a valid positive integer

#### `DELETE /allocations/{object_id}`

> ⚠️ **Rule:** Removes the object from RackSpace, updates the history log, and registers an unmount operation.

---

## 🔐 Business Rules & Data Integrity

| Concern | Approach |
|---|---|
| **Transactions** | All write operations use explicit `START TRANSACTION` with full rollback on failure |
| **Validation** | All entities and constraints are validated before execution |
| **Auditing** | Historical logs are maintained for all create, delete, and allocation operations |
| **State Management** | Strict constraints prevent invalid database states in the legacy RackTables schema |
| **Cascade Safety** | Deletions are safe — dependencies are resolved in the correct order before removal |

---

## 🗺️ Roadmap

### ✅ Version 0.1 (Current)
- [x] Core CRUD for Locations, Rows, Racks, Objects
- [x] Allocation and unallocation with full business rule validation
- [x] Transaction safety and audit logging
- [x] Rack space calculation endpoint
- [x] Swagger/OpenAPI documentation

### 🔮 Future Plans
- [ ] **MQTT integration** — Real-time event publishing on rack changes
- [ ] **Arduino hardware automation** — Physical indicator lights on rack actions
- [ ] **Real-time rack tracking** — Live sync between API state and physical hardware
- [ ] **Authentication layer** — JWT-based access control
- [ ] **Bulk operations** — Import/export racks and objects via CSV

---

## 🎯 Learning Goals

This project was built to explore:

- 🔍 Deep understanding of complex, relational legacy database schemas
- 🔧 Reverse-engineering RackTables internal behavior to build a modern REST abstraction
- 📐 Developing APIs strictly governed by real-world datacenter business rules
- 🤖 Laying groundwork for hardware and IoT integration with physical infrastructure

---

## 👤 Author

**Luis Filippe**
- GitHub: [@luisfilippe650](https://github.com/luisfilippe650)

---
