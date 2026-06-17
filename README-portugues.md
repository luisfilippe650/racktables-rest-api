<div align="center">

# RackTables REST API

**Integration layer for programmatic access to the RackTables MySQL database**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Version](https://img.shields.io/badge/Versão-1.1-orange?style=flat-square)]()

</div>

> API REST construída com Python + FastAPI que expõe operações de leitura e escrita diretamente no banco de dados MySQL do [RackTables](https://racktables.org/), eliminando a necessidade de interagir manualmente com queries SQL ou com a interface web legada.
>
> Com a API em execução, a documentação interativa está disponível em `http://localhost:8000/docs` (Swagger UI) e `http://localhost:8000/redoc` (ReDoc).

---

## Índice

- [Sobre](#sobre)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Executando a API](#executando-a-api)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Localizações](#localizações)
  - [Fileiras](#fileiras)
  - [Racks](#racks)
  - [Objetos](#objetos)
  - [Resumo de Objetos](#resumo-de-objetos)
  - [Alocações](#alocações)
  - [Mover Objetos](#mover-objetos)
- [Exemplos de Uso](#exemplos-de-uso)
- [Códigos HTTP](#códigos-http)

---

## Sobre

A **RackTables REST API** é uma camada de integração desenvolvida pelo **INPE — Instituto Nacional de Pesquisas Espaciais (Brasil)**. Abstrai as queries SQL do RackTables em endpoints RESTful padronizados para gerenciamento dos recursos de inventário de data center: Localizações, Fileiras, Racks, Objetos e Alocações.
> Esta é uma API gratuita e de uso aberto.

**Recursos cobertos:**

- Health Check — monitoramento do status da API
- Localizações — gerenciamento de localizações físicas do data center
- Fileiras — organização e vínculo de fileiras de racks com localizações
- Racks — criação, renomeação e consulta de ocupação por unidade
- Objetos — cadastro e atualização de equipamentos (servidores, switches etc...)
- Resumo de Objetos — leitura e escrita de atributos fixos e dinâmicos por equipamento
- Alocações — montagem e desmontagem de equipamentos em posições específicas de racks
- Movimentação — transferência de servidores entre racks em operação atômica


---

## Tecnologias

| Tecnologia | Finalidade |
|---|---|
| Python 3 | Linguagem principal |
| FastAPI | Framework web |
| Pydantic | Validação e serialização de dados |
| mysql-connector | Conector MySQL |
| Uvicorn | Servidor ASGI |
| Docker | Containerização |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## Estrutura do Projeto

```
racktables-rest-api/
│
├── app/
│   ├── main.py                          # Ponto de entrada do FastAPI
│   │
│   ├── core/
│   │   └── databaseConnection.py        # Gerenciamento da conexão MySQL
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
│   ├── service/                         # Camada de regras de negócio
│   │   ├── objects/
│   │   │   ├── objects_service.py
│   │   │   └── allocateObjects_service.py
│   │   └── rackspace/
│   │       ├── manageLocations_service.py
│   │       ├── rack_service.py
│   │       └── rows_service.py
│   │
│   ├── repository/                      # Camada de acesso a dados (queries SQL)
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

**Fluxo de requisição:**

```
Cliente HTTP
    │
    ▼
[Router]      →  valida rota e método HTTP
    │
    ▼
[Service]     →  aplica regras de negócio
    │
    ▼
[Repository]  →  executa queries MySQL
    │
    ▼
[MySQL — Banco RackTables]
```

---

## Pré-requisitos

- Python 3.8+
- MySQL com o banco de dados do RackTables configurado
- Docker *(opcional)*

---

## Instalação e Configuração

**1. Clone o repositório**

```bash
git clone https://github.com/luisfilippe650/racktables-rest-api.git
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

## Executando a API

**Modo de desenvolvimento (com hot reload):**

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

A API estará disponível em `http://localhost:8000`.

---

## Endpoints

Todos os endpoints utilizam o prefixo `/v1/racktables/`. Para detalhes completos dos schemas de requisição e resposta, acesse `http://localhost:8000/docs`.

---

### Health Check

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/status/` | Verifica se a API está online e operacional |

---

### Localizações

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/locations/` | Lista todas as localizações |
| `POST` | `/v1/racktables/locations/` | Cria uma nova localização |
| `DELETE` | `/v1/racktables/locations/{location_id}` | Remove uma localização pelo ID |
| `GET` | `/v1/racktables/locations/rows` | Lista localizações com suas fileiras associadas |

**Schema — Criar Localização:**

```json
{
  "name": "string"
}
```

---

### Fileiras

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/rows/` | Lista todas as fileiras |
| `POST` | `/v1/racktables/rows/` | Cria uma nova fileira |
| `DELETE` | `/v1/racktables/rows/{row_id}` | Remove uma fileira pelo ID |
| `PATCH` | `/v1/racktables/rows/{row_id}` | Atualiza o nome de uma fileira |
| `GET` | `/v1/racktables/rows/racks` | Lista fileiras com seus racks associados |
| `PUT` | `/v1/racktables/rows/{row_id}/{location_id}` | Vincula uma fileira a uma localização |
| `DELETE` | `/v1/racktables/rows/{row_id}/{location_id}` | Remove o vínculo entre uma fileira e uma localização |

**Schema — Criar / Renomear Fileira:**

```json
{
  "name": "string"
}
```

---

### Racks

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/racks/` | Lista todos os racks |
| `POST` | `/v1/racktables/racks/` | Cria um novo rack |
| `GET` | `/v1/racktables/racks/{rack_id}` | Retorna os detalhes de um rack específico |
| `PATCH` | `/v1/racktables/racks/{rack_id}` | Atualiza o nome de um rack |
| `DELETE` | `/v1/racktables/racks/{rack_id}` | Remove um rack pelo ID |
| `GET` | `/v1/racktables/racks/occupancy` | Retorna a ocupação de todos os racks |
| `GET` | `/v1/racktables/racks/{rack_id}/occupancy` | Retorna a ocupação de um rack específico |

**Schema — Criar Rack:**

```json
{
  "name": "string",
  "rack_height": 42,
  "row_id": 0,
  "asset_no": "string"
}
```

> `rack_height` é opcional (padrão: `42`). `row_id` é obrigatório.

---

### Objetos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/objects/` | Lista todos os objetos cadastrados |
| `POST` | `/v1/racktables/objects/` | Cria um novo objeto |
| `DELETE` | `/v1/racktables/objects/{object_id}` | Remove um objeto pelo ID |
| `PATCH` | `/v1/racktables/objects/{object_id}` | Atualiza o nome ou comentário de um objeto |
| `GET` | `/v1/racktables/objects/types` | Lista todos os tipos de objeto disponíveis |

**Schema — Criar Objeto:**

```json
{
  "name": "string",
  "label": "string",
  "asset_no": "string",
  "objtype_id": 0
}
```

**Schema — Atualizar Objeto (`PATCH`):**

```json
{
  "name": "string",
  "comment": "string"
}
```

> Ambos os campos são opcionais. Envie apenas o que deseja atualizar.

---

### Resumo de Objetos

Permite consultar e atualizar atributos detalhados de um equipamento, incluindo campos fixos (`name`, `label`, `asset_no`) e atributos dinâmicos do RackTables (Serial, Height, etc.).

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racktables/summary/{object_id}` | Retorna todos os atributos de um objeto |
| `PATCH` | `/v1/racktables/summary/{object_id}/attributes` | Atualiza atributos fixos e/ou dinâmicos de um objeto |

**Schema — Atualizar Atributos (`PATCH`):**

O corpo aceita um objeto JSON livre com qualquer combinação de campos fixos e atributos dinâmicos:

```json
{
  "name": "srv-prod-01",
  "asset_no": "PAT-0042",
  "Serial": "SN123456",
  "Height": 2
}
```

---

### Alocações

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/v1/racktables/mount/` | Aloca um objeto em uma posição do rack |
| `DELETE` | `/v1/racktables/mount/{object_id}` | Desaloca um objeto do rack |

**Schema — Alocar Objeto:**

```json
{
  "rack_id": 0,
  "object_id": 0,
  "start_unit": 0,
  "height": 0
}
```

> Todos os campos são obrigatórios.

---

### Mover Objetos

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/v1/racktables/move/` | Move um servidor de um rack para outro |

**Schema — Mover Servidor:**

```json
{
  "object_id": 0,
  "destination_rack_id": 0,
  "start_unit": 0,
  "source_rack_id": 0,
  "height": 0
}
```

> `start_unit` e `height` referem-se à posição no rack de **destino**. `source_rack_id` e `height` são opcionais.

---

## Exemplos de Uso

### Verificar status da API

```bash
curl http://localhost:8000/v1/racktables/status/
```

### Criar uma localização

```bash
curl -X POST http://localhost:8000/v1/racktables/locations/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Sala de Servidores A"}'
```

```json
{
  "id": 29,
  "name": "Sala de Servidores A",
  "message": "Location created successfully"
}
```

### Criar uma fileira e vinculá-la a uma localização

```bash
# Criar a fileira
curl -X POST http://localhost:8000/v1/racktables/rows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Fileira 01"}'

# Vincular fileira (id: 10) à localização (id: 29)
curl -X PUT http://localhost:8000/v1/racktables/rows/10/29
```

### Criar um rack

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
  "message": "Rack created successfully",
  "rack_id": 27
}
```

### Consultar ocupação de um rack

```bash
curl http://localhost:8000/v1/racktables/racks/27/occupancy
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

### Criar um servidor e alocá-lo em um rack

```bash
# Criar o objeto
curl -X POST http://localhost:8000/v1/racktables/objects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Servidor de Produção",
    "asset_no": "PAT-0042",
    "objtype_id": 4
  }'

# Alocar o objeto (id: 31) no rack (id: 27), unidade 10, altura 2U
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
  "message": "Server allocated successfully",
  "rack_id": 27,
  "object_id": 31,
  "start_unit": 10,
  "end_unit": 9,
  "height": 2
}
```

### Atualizar atributos de um objeto

```bash
curl -X PATCH http://localhost:8000/v1/racktables/summary/31/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01-renamed",
    "Serial": "SN987654",
    "Height": 2
  }'
```

### Mover um servidor para outro rack

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

### Desalocar um servidor

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

## Códigos HTTP

| Código | Status | Descrição |
|---|---|---|
| `200` | OK | Requisição processada com sucesso |
| `201` | Created | Recurso criado com sucesso |
| `400` | Bad Request | Dados inválidos no corpo da requisição |
| `404` | Not Found | Recurso não encontrado |
| `422` | Unprocessable Entity | Corpo JSON ausente ou malformado |
| `500` | Internal Server Error | Erro no servidor ou falha na conexão com o banco |

---

<div align="center">
Desenvolvido para o gerenciamento do data center do <strong>INPE — Instituto Nacional de Pesquisas Espaciais</strong>
</div>