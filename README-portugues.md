<div align="center">

# 🗄️ RackTables REST API

**Uma API REST moderna para integração direta com o banco de dados do RackTables**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/Licença-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Versão-1.1-orange?style=flat-square)]()

<br/>

> Gerencie Localizações, Fileiras, Racks, Objetos, Alocações e Movimentação de Equipamentos no RackTables  
> através de endpoints REST padronizados — sem necessidade de SQL.

<br/>

> 💡 **Dica:** Com a API em execução, acesse a documentação interativa completa em  
> **`http://localhost:8000/docs`** (Swagger UI) ou **`http://localhost:8000/redoc`** (ReDoc)  
> para explorar e testar todos os endpoints diretamente pelo navegador.

</div>

---

## 📋 Índice

- [Sobre](#-sobre)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a API](#-executando-a-api)
- [Documentação Interativa (Swagger)](#-documentação-interativa-swagger)
- [Endpoints](#-endpoints)
  - [Health Check](#health-check)
  - [Localizações](#localizações)
  - [Fileiras](#fileiras)
  - [Racks](#racks)
  - [Objetos](#objetos)
  - [Alocações](#alocações)
  - [Mover Objetos](#mover-objetos)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Códigos HTTP](#-códigos-http)
- [Contribuindo](#-contribuindo)

---

## 🔍 Sobre

A **RackTables REST API** é uma camada de integração construída com **Python + FastAPI** pelo **INPE — Instituto Nacional de Pesquisas Espaciais (Brasil)**, que expõe os recursos do [RackTables](https://racktables.org/) — um sistema open-source de inventário e gerenciamento de data centers — através de endpoints HTTP padronizados.

A API opera **diretamente no banco de dados MySQL do RackTables**, eliminando a necessidade de interagir manualmente com queries SQL ou com a interface web legada.

### ✨ Funcionalidades

- 🏥 **Health Check** — Monitore o status da API em tempo real
- 📍 **Localizações** — Crie e gerencie localizações físicas do data center
- 🗂️ **Fileiras** — Organize fileiras de racks, vincule-as a localizações e renomeie-as
- 🖥️ **Racks** — Gerencie racks, altura e ocupação por unidade, renomeie-os
- 📦 **Objetos** — Cadastre e atualize equipamentos (servidores, switches, nobreaks, etc.)
- 🔌 **Alocações** — Aloque e desaloque equipamentos em posições específicas dos racks
- 🚚 **Mover Objetos** — Mova servidores entre racks em uma única operação

---

## 🛠️ Tecnologias

| Tecnologia | Finalidade |
|---|---|
| **Python 3** | Linguagem principal |
| **FastAPI** | Framework web de alta performance |
| **Pydantic** | Validação e serialização de dados |
| **mysql-connector** | Conector para banco de dados MySQL |
| **Uvicorn** | Servidor ASGI para execução da aplicação |
| **Docker** | Containerização do ambiente |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

---

## 📁 Estrutura do Projeto

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
[Repository]  ──→  Executa queries MySQL
    │
    ▼
[MySQL — Banco RackTables]
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

A API estará disponível em `http://localhost:8000`

---

## 📖 Documentação Interativa (Swagger)

Uma das grandes vantagens do FastAPI é a **geração automática de documentação interativa**. Com a API em execução, você tem acesso a duas interfaces:

### Swagger UI — `http://localhost:8000/docs`

A interface mais completa para explorar e testar a API:

- ✅ Visualize todos os endpoints organizados por grupo (Localizações, Fileiras, Racks, etc.)
- ✅ Veja os **schemas de requisição e resposta** de cada endpoint
- ✅ **Execute requisições reais** diretamente pelo navegador — sem Postman ou curl
- ✅ Inspecione os códigos de resposta possíveis e exemplos de payload

### ReDoc — `http://localhost:8000/redoc`

Interface alternativa focada na legibilidade da documentação, ideal para compartilhar com equipes ou clientes.

> **Recomendamos fortemente o uso do Swagger UI (`/docs`) para explorar a API durante o desenvolvimento e os testes.**

---

## 📡 Endpoints

> Todos os endpoints utilizam o prefixo `/v1/`. Para detalhes completos dos schemas de requisição e resposta, acesse **`http://localhost:8000/docs`**.

---

### Health Check

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/status/` | Verifica se a API está online e operacional |

---

### Localizações

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/locations/` | Lista todas as localizações |
| `POST` | `/v1/locations/` | Cria uma nova localização |
| `DELETE` | `/v1/locations/{location_id}` | Remove uma localização pelo ID |
| `GET` | `/v1/locations/rows` | Lista localizações com suas fileiras associadas |

**Schema — Criar Localização (`POST /v1/locations/`):**

```json
{
  "name": "string"
}
```

---

### Fileiras

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/rows/` | Lista todas as fileiras |
| `POST` | `/v1/rows/` | Cria uma nova fileira |
| `DELETE` | `/v1/rows/{row_id}` | Remove uma fileira pelo ID |
| `PATCH` | `/v1/rows/{row_id}` | Atualiza o nome de uma fileira |
| `GET` | `/v1/rows/racks` | Lista fileiras com seus racks associados |
| `PUT` | `/v1/rows/{row_id}/{location_id}` | Vincula uma fileira a uma localização |
| `DELETE` | `/v1/rows/{row_id}/{location_id}` | Remove o vínculo entre uma fileira e uma localização |

**Schema — Criar Fileira (`POST /v1/rows/`):**

```json
{
  "name": "string"
}
```

**Schema — Atualizar Nome da Fileira (`PATCH /v1/rows/{row_id}`):**

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
| `GET` | `/v1/racks/{rack_id}` | Retorna os detalhes de um rack específico |
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
  "asset_no": "string"
}
```

> `rack_height` é opcional (padrão: `42`). `row_id` é obrigatório.

**Schema — Atualizar Nome do Rack (`PATCH /v1/racks/{rack_id}`):**

```json
{
  "name": "string"
}
```

---

### Objetos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/v1/objects/` | Lista todos os objetos cadastrados |
| `POST` | `/v1/objects/` | Cria um novo objeto |
| `DELETE` | `/v1/objects/{object_id}` | Remove um objeto pelo ID |
| `PATCH` | `/v1/objects/{object_id}` | Atualiza o nome ou comentário de um objeto |
| `GET` | `/v1/objects/types` | Lista todos os tipos de objeto disponíveis |

**Schema — Criar Objeto (`POST /v1/objects/`):**

```json
{
  "name": "string",
  "label": "string",
  "asset_no": "string",
  "objtype_id": 0
}
```

**Schema — Atualizar Objeto (`PATCH /v1/objects/{object_id}`):**

```json
{
  "name": "string",
  "comment": "string"
}
```

> Ambos os campos são opcionais no `PATCH`. Envie apenas o que deseja atualizar.

---

### Alocações

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/v1/allocations/` | Aloca um objeto em uma posição do rack |
| `DELETE` | `/v1/allocations/{object_id}` | Desaloca um objeto do rack |

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

### Mover Objetos

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/v1/move/` | Move um servidor de um rack para outro |

**Schema — Mover Servidor (`POST /v1/move/`):**

```json
{
  "object_id": 0,
  "source_rack_id": 0,
  "destination_rack_id": 0,
  "start_unit": 0,
  "height": 0
}
```

> Todos os campos são obrigatórios. `start_unit` e `height` referem-se à posição no rack de **destino**.

---

## 💡 Exemplos de Uso

### Verificar Status da API

```bash
curl http://localhost:8000/v1/status/
```

---

### Criar uma Localização

```bash
curl -X POST http://localhost:8000/v1/locations/ \
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

---

### Criar uma Fileira e Vinculá-la a uma Localização

```bash
# 1. Criar a fileira
curl -X POST http://localhost:8000/v1/rows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Fileira 01"}'

# 2. Vincular fileira (id: 10) à localização (id: 29)
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

### Consultar Ocupação de um Rack

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

### Criar um Servidor e Alocá-lo em um Rack

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

# 2. Alocar o objeto (id: 31) no rack (id: 27), a partir da unidade 10, altura 2U
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

### Mover um Servidor para Outro Rack

```bash
# Mover objeto (id: 31) do rack (id: 27) para o rack (id: 35), posicionando na unidade 5, altura 2U
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

### Desalocar um Servidor

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

## 📊 Códigos HTTP

| Código | Status | Descrição |
|---|---|---|
| `200` | OK | Requisição processada com sucesso |
| `201` | Created | Recurso criado com sucesso |
| `400` | Bad Request | Dados inválidos no corpo da requisição |
| `404` | Not Found | Recurso não encontrado |
| `422` | Unprocessable Entity | Corpo JSON ausente ou malformado |
| `500` | Internal Server Error | Erro no servidor ou falha na conexão com o banco |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/minha-feature`)
3. Faça o commit das suas alterações (`git commit -m 'feat: adiciona minha feature'`)
4. Envie para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

<div align="center">

Desenvolvido para o gerenciamento do data center do INPE (Instituto Nacional de Pesquisas Espaciais)

</div>
