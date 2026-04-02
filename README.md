<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue" />
  <img src="https://img.shields.io/badge/MySQL-Database-orange" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue" />
  <img src="https://img.shields.io/badge/Status-Testing%20v0.1-yellow" />
</p>

# 🚀 RackTables REST API

---

## 📌 Overview

This project is a REST API built with **FastAPI** to interact directly with the **RackTables database**.

The API provides structured operations for:

- Locations
- Rows
- Racks
- Objects (Servers, Network Devices)
- Allocation and unallocation of servers in racks

⚠️ **Version:** `0.1 (Testing Phase)`

This version focuses on:
- Data integrity
- Business rule validation
- Safe interaction with RackTables database

---

## 🧱 Project Structure
app/
├── routers/
├── repository/
├── schema/
├── core/
└── main.py

---

## ⚙️ Technologies Used

- Python
- FastAPI
- MySQL
- Docker
- Pydantic

---

## ⚙️ Installation

```bash
git clone git@github.com:luisfilippe650/racktables-rest-api.git
cd racktables-rest-api

▶️ Running the API
uvicorn app.main:app --reload

API disponível em:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

🐳 Docker (Recommended)
docker run -d \
  --name racktables-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=racktables \
  -p 3307:3306 \
  -v $(pwd)/database:/docker-entrypoint-initdb.d \
  mysql:8
✔ This will:
Create database automatically
Execute schema.sql and seed.sql
Expose MySQL on port 3307
🔐 Environment Variables (.env)

Create a .env file in root:

DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
📡 API ENDPOINTS
📍 Locations
➕ Create Location

POST /locations

Body:
{
  "name": "Datacenter A"
}
Response:
{
  "id": 1,
  "name": "Datacenter A",
  "message": "Location criada com sucesso"
}
❌ Delete Location

DELETE /locations/{location_id}

Rules:
Removes all dependencies
Cleans related data
Maintains history
📄 List Locations

GET /locations

📄 List Locations with Rows

GET /locations/with-rows

📍 Rows
➕ Create Row

POST /rows

{
  "name": "Row A"
}
❌ Delete Row

DELETE /rows/{row_id}

Rules:
Cannot delete if it has racks
📄 List Rows

GET /rows

📄 List Rows with Racks

GET /rows/with-racks

📍 Racks
➕ Create Rack

POST /racks

{
  "name": "Rack 01",
  "row_id": 1,
  "rack_height": 42
}
Rules:
Must be linked to a valid row
❌ Delete Rack

DELETE /racks/{rack_id}

Rules:
Cannot delete if there are objects allocated
📄 List Racks

GET /racks

📄 List Racks with Space

GET /racks/space

Example Response:
{
  "rack_id": 1,
  "rack_name": "Rack 01",
  "total_units": 42,
  "occupied_units": [42, 41],
  "free_units": [40, 39, 38]
}
📦 Objects
➕ Create Object

POST /objects

{
  "name": "Server01",
  "label": "Production Server",
  "objtype_id": 4
}
Behavior:
Validates object type
Prevents duplicates
Creates default ports for servers
❌ Delete Object

DELETE /objects/{object_id}

Behavior:
Removes:
Network configs
VLANs
Ports
Mounts
Saves history before deletion
📄 List Objects

GET /objects

📄 List Object Types

GET /objects/types

🔗 Allocation
➕ Allocate Server

POST /allocations

{
  "rack_id": 1,
  "object_id": 10,
  "start_unit": 42,
  "height": 2
}
Validations:
Rack exists
Object exists
Must be server (type 4)
Must not already be allocated
Space must be free
Height must be valid
Success Response:
{
  "message": "Servidor alocado com sucesso",
  "rack_id": 1,
  "object_id": 10,
  "start_unit": 42,
  "end_unit": 41,
  "height": 2
}
❌ Unallocate Server

DELETE /allocations/{object_id}

Behavior:
Removes from RackSpace
Updates history
Creates unmount operation
🧠 Business Rules
Uses transactions (START TRANSACTION)
Rollback on failure
Validates all entities before operations
Maintains historical logs
Prevents invalid states in database
🧪 Status

🚧 Version: 0.1

Core features implemented
Focus on stability and correctness
Future plans:
MQTT integration
Arduino automation
Real-time rack tracking
🎯 Learning Goals

This project was designed to:

Understand complex relational databases
Reverse engineer RackTables behavior
Build APIs with real business rules
Prepare for hardware integration (IoT)
👨‍💻 Author

Luis Filippe
