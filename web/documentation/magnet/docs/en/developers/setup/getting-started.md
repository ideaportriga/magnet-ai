# Getting Started

This guide will help you set up your development environment for Magnet AI.

## Prerequisites

### Required Software

- **Node.js 18+**: Frontend development and project orchestration
- **Python 3.12+**: Backend development
- **Docker** & **Docker Compose**: For containerized database (PostgreSQL + pgvector)
- **Poetry**: Python dependency management
- **Git**: Version control

### Recommended Tools

- **VS Code**: With Python, Vue, and ESLint extensions
- **Postman** or **Insomnia**: For API testing
- **DBeaver** or **pgAdmin**: Database management

## Quick Start

The easiest way to get started is using the root automation scripts.

### 1. Clone the Repository

```bash
git clone https://github.com/ideaportriga/magnet-ai.git
cd magnet-ai
```

### 2. Setup Dependencies

Run the setup script to install all dependencies (Root, API, and Web):

```bash
npm install
npm run setup
```

### 3. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

The default settings in `.env` are configured for local development with Docker.

### 4. Start Development Environment

#### Option A: Local Development with Docker (Recommended)

This runs the API and Web frontend locally, and automatically starts the database in Docker.

```bash
npm run dev:docker
```

This starts:
- **Database** (Postgres + pgvector)
- **API** at `http://localhost:8000`
- **Web Panel** at `http://localhost:7000`
- **Web Admin** at `http://localhost:7002`

#### Option B: Local Development with External Database

If you have your own PostgreSQL database running (locally or remote).

1. **Configure `.env`**: Update `DB_HOST`, `DB_PORT`, etc.
2. **Run the App**:

   ```bash
   npm run dev
   ```

## Manual Setup

If you prefer to run services individually or need more control.

### Backend Setup (`api/`)

1. **Navigate to API directory**:

   ```bash
   cd api
   ```

2. **Install Dependencies**:

   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**:

   ```bash
   poetry shell
   ```

4. **Run Server**:
   ```bash
   uvicorn app:app --reload --env-file="../.env"
   ```

### Frontend Setup (`web/`)

1. **Navigate to Web directory**:

   ```bash
   cd web
   ```

2. **Install Dependencies**:

   ```bash
   yarn install
   ```

3. **Run Applications**:

   Magnet AI consists of multiple applications managed by Nx.

   **Run User Panel:**

   ```bash
   yarn nx dev magnet-panel
   ```

   **Run Admin Console:**

   ```bash
   yarn nx dev magnet-admin
   ```

## Project Structure

### Root Directory

```
magnet-ai/
├── api/                 # Python backend (Litestar)
├── web/                 # Frontend monorepo (Nx + Vue)
├── docker/              # Docker configuration
├── .github/             # CI/CD workflows
└── package.json         # Root scripts
```

### Backend (`api/`)

```
api/
├── src/
│   ├── app.py              # Application entry point
│   ├── core/               # Core domain, DB, config
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   └── plugins/            # Plugin system
├── tests/                  # Pytest tests
└── pyproject.toml          # Poetry dependencies
```

### Frontend (`web/`)

```
web/
├── apps/
│   ├── magnet-admin/       # Admin Console (Vue)
│   ├── magnet-panel/       # User Interface (Vue)
│   └── magnet-docs/        # Documentation (VitePress)
├── packages/
│   ├── shared/             # Shared logic
│   ├── themes/             # UI Themes
│   └── ui-comp/            # Shared UI Components
└── nx.json                 # Nx configuration
```

## Troubleshooting

### Database Connection Failed

Ensure Docker is running and you've executed `npm run docker:up`. Check `.env` matches Docker settings.

### Port Conflicts

- **8000**: API
- **5432**: PostgreSQL
- **7000**: Magnet Panel
- **7002**: Magnet Admin

If ports are in use, stop conflicting services or update `.env` and startup commands.

### Python Version Issues

Ensure you are using Python 3.12+. You can check with `python --version`. If using `pyenv`, ensure the local version is set correctly.
