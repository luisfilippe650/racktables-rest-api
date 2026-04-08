<div align="center">

# 🗄️ RackTables REST API

**Uma API REST moderna para integração direta com o banco de dados do RackTables**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.3-orange?style=flat-square)]()

<br/>

> Gerencie Locations, Rows, Racks, Objects e Allocations do RackTables  
> via endpoints REST padronizados — sem tocar em SQL.

</div>

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a API](#-executando-a-api)
- [Endpoints](#-endpoints)
  - [Racks](#racks)
  - [Locations](#locations)
  - [Rows](#rows)
  - [Objects](#objects)
  - [Allocations](#allocations)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Códigos de Status HTTP](#-códigos-de-status-http)
- [Contribuindo](#-contribuindo)

---

## 🔍 Sobre o Projeto

A **RackTables REST API** é uma camada de abstração desenvolvida em **Python + FastAPI** que expõe os recursos do [RackTables](https://racktables.org/) — sistema open-source de inventário e gerenciamento de data center — via endpoints HTTP padronizados.

A API realiza operações **diretamente no banco de dados MySQL** do RackTables, eliminando a necessidade de interagir manualmente com SQL ou com a interface web legada.

### ✨ Funcionalidades

- 📍 **Locations** — Crie e gerencie locais físicos do data center
- 🗂️ **Rows** — Organize fileiras de racks por location
- 🖥️ **Racks** — Gerencie racks, altura e ocupação por unidade (U)
- 📦 **Objects** — Cadastre equipamentos (servidores, switches, UPS, etc.)
- 🔌 **Allocations** — Aloque e desaloque equipamentos em posições específicas do rack

---

## 🛠️ Stack Tecnológica

| Tecnologia | Função |
|---|---|
| **Python 3** | Linguagem principal |
| **FastAPI** | Framework web de alta performance |
| **Pydantic** | Validação e serialização de dados |
| **mysql-connector** | Conector com o banco de dados MySQL |
| **Uvicorn** | Servidor ASGI para rodar a aplicação |
| **Docker** | Containerização do ambiente |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

---

## 📁 Estrutura do Projeto

```
racktables-rest-api/
│
├── app/
│   ├── main.py                          # Ponto de entrada FastAPI
│   │
│   ├── core/
│   │   └── databaseConnection.py        # Gerenciamento de conexão MySQL
│   │
│   ├── routers/                         # Camada de roteamento HTTP
│   │   ├── objects/
│   │   │   ├── objects_router.py
│   │   │   └── allocateObjects_router.py
│   │   └── rackspace/
│   │       ├── manageLocations_router.py
│   │       ├── rack_router.py
│   │       └── rows_router.py
│   │
│   ├── service/                         # Regras de negócio
│   │   ├── objects/
│   │   │   ├── objects_service.py
│   │   │   └── allocateObjects_service.py
│   │   └── rackspace/
│   │       ├── manageLocations_service.py
│   │       ├── rack_service.py
│   │       └── rows_service.py
│   │
│   ├── repository/                      # Acesso a dados (queries SQL)
│   │   ├── objects/
│   │   │   ├── objects_repository.py
│   │   │   └── allocateObjects_repository.py
│   │   └── rackspace/
│   │       ├── manageLocations_repository.py
│   │       ├── rack_repository.py
│   │       └── rows_repository.py
│   │
│   └── schema/                          # Schemas Pydantic
│       ├── objects/
│       │   ├── objects_schema.py
│       │   └── allocateObjects_schema.py
│       └── rackspace/
│           ├── manageLocations_schema.py
│           ├── rack_schema.py
│           └── rows_schema.py
```

### Fluxo de Requisição

```
Cliente HTTP
    │
    ▼
[Router]  ──→  Valida rota e método HTTP
    │
    ▼
[Service]  ──→  Aplica regras de negócio
    │
    ▼
[Repository]  ──→  Executa queries no MySQL
    │
    ▼
[MySQL — RackTables DB]
```

---

## 📦 Pré-requisitos

- Python 3.8+
- MySQL com o banco de dados do RackTables configurado
- Docker *(opcional)*

---

## ⚙️ Instalação e Configuração

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/racktables-rest-api.git
cd racktables-rest-api
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente**

Crie um arquivo `.env` na raiz do projeto:

```env
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=racktables
```

---

## 🚀 Executando a API

**Modo desenvolvimento (com hot reload):**

```bash
uvicorn app.main:app --reload
```

**Especificando host e porta:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Com Docker:**

```bash
docker build -t racktables-api .
docker run -p 8000:8000 --env-file .env racktables-api
```

A API estará disponível em `http://localhost:8000`

> 📄 **Documentação interativa Swagger:** `http://localhost:8000/docs`  
> 📄 **Documentação ReDoc:** `http://localhost:8000/redoc`

---

## 📡 Endpoints

### Racks

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/racks` | Lista todos os racks |
| `GET` | `/racks/{rack_id}` | Busca um rack pelo ID |
| `GET` | `/racks/occupancy` | Ocupação de todos os racks |
| `GET` | `/racks/{rack_id}/occupancy` | Ocupação de um rack específico |
| `POST` | `/racks` | Cria um novo rack |
| `DELETE` | `/racks/{rack_id}` | Remove um rack |

### Locations

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/locations` | Lista todas as locations |
| `GET` | `/locations/rows` | Lista locations com suas rows |
| `POST` | `/locations` | Cria uma nova location |
| `DELETE` | `/locations/{location_id}` | Remove uma location |

### Rows

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/rows` | Lista todas as rows |
| `GET` | `/rows/racks` | Lista rows com seus racks |
| `POST` | `/rows` | Cria uma nova row |
| `DELETE` | `/rows/{row_id}` | Remove uma row |

### Objects

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/objects` | Lista todos os objetos |
| `GET` | `/object/types` | Lista tipos de objetos disponíveis |
| `POST` | `/objects` | Cria um novo objeto |
| `DELETE` | `/object/{object_id}` | Remove um objeto |

### Allocations

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/allocations` | Aloca um objeto em um rack |
| `DELETE` | `/allocations/{object_id}` | Desaloca um objeto |

---

## 💡 Exemplos de Uso

### Criar um Rack

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
  "message": "Rack criado com sucesso",
  "rack_id": 27
}
```

---

### Verificar Ocupação de um Rack

```bash
curl http://localhost:8000/racks/26/occupancy
```

```json
{
  "rack_id": 26,
  "rack_name": "Rack A1",
  "total_units": 42,
  "occupied_units": [1, 2, 3],
  "free_units": [4, 5, 6, 7, ...]
}
```

---

### Criar um Object (Servidor)

```bash
curl -X POST http://localhost:8000/objects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Servidor de Produção",
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

### Alocar um Servidor em um Rack

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
  "message": "Servidor alocado com sucesso",
  "rack_id": 26,
  "object_id": 31,
  "start_unit": 10,
  "end_unit": 9,
  "height": 2,
  "molecule_id": 7
}
```

---

### Desalocar um Servidor

```bash
curl -X DELETE http://localhost:8000/allocations/31
```

```json
{
  "message": "Servidor desalocado com sucesso",
  "object_id": 31,
  "rack_id": 26,
  "units_removed": [9, 10],
  "molecule_id": 8
}
```

---

## 📊 Códigos de Status HTTP

| Código | Status | Descrição |
|---|---|---|
| `200` | OK | Requisição processada com sucesso |
| `201` | Created | Recurso criado com sucesso |
| `400` | Bad Request | Dados inválidos no body da requisição |
| `404` | Not Found | Recurso não encontrado |
| `422` | Unprocessable Entity | Estrutura JSON inválida ou ausente |
| `500` | Internal Server Error | Erro no servidor ou falha no banco de dados |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

1. Faça um fork do projeto
2. Crie sua branch (`git checkout -b feature/minha-feature`)
3. Commit suas alterações (`git commit -m 'feat: adiciona minha feature'`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

<div align="center">

Feito para o gerenciamento do data center do INPE ( Instituto Nacional De Pesquisas Espaciais ) 

</div>
