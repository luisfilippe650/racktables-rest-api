<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue" />
  <img src="https://img.shields.io/badge/MySQL-Database-orange" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue" />
  <img src="https://img.shields.io/badge/Status-Testing%20v0.1-yellow" />
</p>

# RackTables REST API

---

## Overview

This project is a REST API built with **FastAPI** to interact directly with the **RackTables** database.

The API provides structured operations for managing:
- Locations
- Rows
- Racks
- Objects (Servers, Network Devices)
- Server allocation and unallocation within racks

**Version Status:** `v0.1 (Testing Phase)`  
Current development focuses on data integrity, business rule validation, and safe interactions with the underlying RackTables database structure.

## Project Structure

```text
app/
├── routers/
├── repository/
├── schema/
├── core/
└── main.py

Technologies Used
Python 3.11

FastAPI

MySQL

Docker

Pydantic

Getting Started
1. Clone the Repository
Bash
git clone git@github.com:luisfilippe650/racktables-rest-api.git
cd racktables-rest-api
2. Environment Variables
Create a .env file in the root directory:

Snippet de código
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
3. Database Setup (Docker Recommended)
Spin up the MySQL container. This will automatically create the database and execute schema.sql and seed.sql.

Bash
docker run -d \
  --name racktables-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=racktables \
  -p 3307:3306 \
  -v $(pwd)/database:/docker-entrypoint-initdb.d \
  mysql:8
4. Running the API Locally
Bash
uvicorn app.main:app --reload
API Base URL: http://127.0.0.1:8000

Swagger UI (Docs): http://127.0.0.1:8000/docs

API Reference
Locations
POST /locations - Create a new location

JSON
{ "name": "Datacenter A" }
DELETE /locations/{location_id} - Delete a location

Rules: Removes all dependencies, cleans related data, and maintains history.

GET /locations - List all locations

GET /locations/with-rows - List locations including their rows

Rows
POST /rows - Create a new row

JSON
{ "name": "Row A" }
DELETE /rows/{row_id} - Delete a row

Rules: Cannot be deleted if it contains racks.

GET /rows - List all rows

GET /rows/with-racks - List rows including their racks

Racks
POST /racks - Create a new rack

Rules: Must be linked to a valid row.

JSON
{
  "name": "Rack 01",
  "row_id": 1,
  "rack_height": 42
}
DELETE /racks/{rack_id} - Delete a rack

Rules: Cannot be deleted if objects are currently allocated within it.

GET /racks - List all racks

GET /racks/space - List racks with available space metrics

JSON
{
  "rack_id": 1,
  "rack_name": "Rack 01",
  "total_units": 42,
  "occupied_units": [42, 41],
  "free_units": [40, 39, 38]
}
Objects
POST /objects - Create a new object

Rules: Validates object type, prevents duplicates, and creates default ports for servers.

JSON
{
  "name": "Server01",
  "label": "Production Server",
  "objtype_id": 4
}
DELETE /objects/{object_id} - Delete an object

Rules: Removes network configs, VLANs, ports, and mounts. Saves history before deletion.

GET /objects - List all objects

GET /objects/types - List supported object types

Allocations
POST /allocations - Allocate a server

Rules: Rack and object must exist, object must be a server (type 4), must not be already allocated, requested space must be free, and height must be valid.

JSON
{
  "rack_id": 1,
  "object_id": 10,
  "start_unit": 42,
  "height": 2
}
DELETE /allocations/{object_id} - Unallocate a server

Rules: Removes the object from RackSpace, updates history, and creates an unmount operation.

Business Rules & Database Integrity
Transactions: Uses explicit START TRANSACTION with rollback capabilities on failure.

Validation: Thoroughly validates all entities prior to execution.

Auditing: Maintains historical logs for all major operations.

State Management: Strict constraints prevent invalid states within the legacy RackTables database.

Roadmap & Status
Version 0.1 (Current)

Core API features implemented.

Primary focus on stability, data correctness, and reverse-engineering RackTables core logic.

Future Plans

MQTT integration.

Arduino hardware automation.

Real-time physical rack tracking.

Learning Goals
This project was built to explore and achieve the following:

Deepen understanding of complex, relational database schemas.

Reverse-engineer legacy RackTables behavior to build a modern REST abstraction layer.

Develop robust APIs strictly governed by real-world business rules.

Lay the groundwork for hardware and IoT integration.

Author
Luis Filippe - GitHub Profile
