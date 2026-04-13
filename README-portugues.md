<div align="center">

# 🗄️ RackTables REST API

**Uma API REST moderna para integração direta com o banco de dados do RackTables**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0-orange?style=flat-square)]()

<br/>

> Gerencie Locations, Rows, Racks, Objects e Allocations do RackTables  
> via endpoints REST padronizados — sem tocar em SQL.

<br/>

> 💡 **Dica:** Após subir a API, acesse a documentação interativa completa em  
> **`http://localhost:8000/docs`** (Swagger UI) ou **`http://localhost:8000/redoc`** (ReDoc)  
> para explorar e testar todos os endpoints diretamente pelo navegador.

</div>

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a API](#-executando-a-api)
- [Documentação Interativa (Swagger)](#-documentação-interativa-swagger)
- [Endpoints](#-endpoints)
  - [Health Check](#health-check)
  - [Locations](#locations)
  - [Rows](#rows)
  - [Racks](#racks)
  - [Objects](#objects)
  - [Allocations](#allocations)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Códigos de Status HTTP](#-códigos-de-status-http)
- [Contribuindo](#-contribuindo)

---

## 🔍 Sobre o Projeto

A **RackTables REST API** é uma camada de integração desenvolvida em **Python + FastAPI** pelo **INPE — Instituto Nacional de Pesquisas Espaciais (Brasil)**, que expõe os recursos do [RackTables](https://racktables.org/) — sistema open-source de inventário e gerenciamento de data center — através de endpoints HTTP padronizados.

A API realiza operações **diretamente no banco de dados MySQL** do RackTables, eliminando a necessidade de interagir manualmente com SQL ou com a interface web legada.

### ✨ Funcionalidades

- 🏥 **Health Check** — Monitore o status da API em tempo real
- 📍 **Locations** — Crie e gerencie locais físicos do data center
- 🗂️ **Rows** — Organize fileiras de racks, associe a locations e renomeie
- 🖥️ **Racks** — Gerencie racks, altura e ocupação por unidade (U), renomeie
- 📦 **Objects** — Cadastre e atualize equipamentos (servidores, switches, UPS, etc.)
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

---

## 📖 Documentação Interativa (Swagger)

Uma das maiores vantagens do FastAPI é a **geração automática de documentação interativa**. Após subir a API, você tem acesso a duas interfaces:

### Swagger UI — `http://localhost:8000/docs`

A interface mais completa para explorar e testar a API:

- ✅ Visualize todos os endpoints organizados por grupo (Locations, Rows, Racks, etc.)
- ✅ Veja os **schemas de entrada e saída** de cada endpoint
- ✅ **Execute requisições reais** diretamente pelo navegador, sem precisar de Postman ou curl
- ✅ Veja os exemplos de resposta e os códigos de status possíveis

### ReDoc — `http://localhost:8000/redoc`

Interface alternativa com foco em legibilidade da documentação, ideal para compartilhar com times ou clientes.

> **Recomendamos fortemente o uso do Swagger UI (`/docs`) para explorar a API durante o desenvolvimento e testes.**

---

## 📡 Endpoints

> Todos os endpoints utilizam o prefixo `/v1/`. Para detalhes completos de cada rota, incluindo schemas de request/response, acesse **`http://localhost:8000/docs`**.

---

### Health Check

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/status/` | Verifica se a API está online e operacional |

---

### Locations

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/locations/` | Lista todas as locations |
| `POST` | `/v1/locations/` | Cria uma nova location |
| `DELETE` | `/v1/locations/{location_id}` | Remove uma location pelo ID |
| `GET` | `/v1/locations/rows` | Lista locations com suas rows associadas |

**Schema — Criar Location (`POST /v1/locations/`):**

```json
{
  "name": "string"
}
```

---

### Rows

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/rows/` | Lista todas as rows |
| `POST` | `/v1/rows/` | Cria uma nova row |
| `DELETE` | `/v1/rows/{row_id}` | Remove uma row pelo ID |
| `PATCH` | `/v1/rows/{row_id}` | Atualiza o nome de uma row |
| `GET` | `/v1/rows/racks` | Lista rows com seus racks associados |
| `PUT` | `/v1/rows/{row_id}/{location_id}` | Associa uma row a uma location |
| `DELETE` | `/v1/rows/{row_id}/{location_id}` | Remove a associação entre row e location |

**Schema — Criar Row (`POST /v1/rows/`):**

```json
{
  "name": "string"
}
```

**Schema — Atualizar nome (`PATCH /v1/rows/{row_id}`):**

```json
{
  "name": "string"
}
```

---

### Racks

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/racks/` | Lista todos os racks |
| `POST` | `/v1/racks/` | Cria um novo rack |
| `GET` | `/v1/racks/{rack_id}` | Retorna detalhes de um rack específico |
| `PATCH` | `/v1/racks/{rack_id}` | Atualiza o nome de um rack |
| `DELETE` | `/v1/racks/{rack_id}` | Remove um rack pelo ID |
| `GET` | `/v1/racks/occupancy` | Retorna a ocupação de todos os racks |
| `GET` | `/v1/racks/{rack_id}/occupancy` | Retorna a ocupação de um rack específico |

**Schema — Criar Rack (`POST /v1/racks/`):**

```json
{
  "name": "string",
  "rack_height": 42,
  "row_id": 0,
  "assent_no": "string"
}
```

> `rack_height` é opcional (padrão: `42`). `row_id` é obrigatório.

**Schema — Atualizar nome (`PATCH /v1/racks/{rack_id}`):**

```json
{
  "name": "string"
}
```

---

### Objects

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/objects/` | Lista todos os objetos cadastrados |
| `POST` | `/v1/objects/` | Cria um novo objeto |
| `DELETE` | `/v1/objects/{object_id}` | Remove um objeto pelo ID |
| `PATCH` | `/v1/objects/{object_id}` | Atualiza nome ou comentário de um objeto |
| `GET` | `/v1/objects/types` | Lista todos os tipos de objetos disponíveis |

**Schema — Criar Object (`POST /v1/objects/`):**

```json
{
  "name": "string",
  "label": "string",
  "asset_no": "string",
  "objtype_id": 0
}
```

**Schema — Atualizar Object (`PATCH /v1/objects/{object_id}`):**

```json
{
  "name": "string",
  "comment": "string"
}
```

> Ambos os campos são opcionais no `PATCH`. Envie apenas o que deseja atualizar.

---

### Allocations

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/v1/allocations/` | Aloca um objeto em uma posição de um rack |
| `DELETE` | `/v1/allocations/{object_id}` | Desaloca um objeto de um rack |

**Schema — Alocar (`POST /v1/allocations/`):**

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

## 💡 Exemplos de Uso

### Verificar status da API

```bash
curl http://localhost:8000/v1/status/
```

---

### Criar uma Location

```bash
curl -X POST http://localhost:8000/v1/locations/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Sala de Servidores A"}'
```

```json
{
  "id": 29,
  "name": "Sala de Servidores A",
  "message": "Location criada com sucesso"
}
```

---

### Criar uma Row e associar a uma Location

```bash
# 1. Criar a row
curl -X POST http://localhost:8000/v1/rows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Fileira 01"}'

# 2. Associar a row (id: 10) à location (id: 29)
curl -X PUT http://localhost:8000/v1/rows/10/29
```

---

### Criar um Rack

```bash
curl -X POST http://localhost:8000/v1/racks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rack A1",
    "rack_height": 42,
    "row_id": 10,
    "assent_no": "PAT-001"
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

### Criar um Object (Servidor) e Alocar em um Rack

```bash
# 1. Criar o objeto
curl -X POST http://localhost:8000/v1/objects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-prod-01",
    "label": "Servidor de Produção",
    "asset_no": "PAT-0042",
    "objtype_id": 4
  }'

# 2. Alocar o objeto (id: 31) no rack (id: 27), unidade 10, altura 2U
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
  "message": "Servidor alocado com sucesso",
  "rack_id": 27,
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
curl -X DELETE http://localhost:8000/v1/allocations/31
```

```json
{
  "message": "Servidor desalocado com sucesso",
  "object_id": 31,
  "rack_id": 27,
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