# System Architecture

Magnet AI follows a modern, modular architecture with a clear separation between frontend and backend components, managed within a monorepo.

## High-Level Overview

```mermaid
graph TD
    Client[Frontend (Web)<br>Vue 3 + TypeScript + Nx] -->|REST API| API[Backend (API)<br>Python + Litestar + SQLAlchemy]
    API --> DB[(PostgreSQL<br>Metadata)]
    API --> VectorDB[(pgvector<br>Vector Database)]

    style Client fill:#f9f,stroke:#333,stroke-width:2px
    style API fill:#bbf,stroke:#333,stroke-width:2px
    style DB fill:#dfd,stroke:#333,stroke-width:2px
    style VectorDB fill:#dfd,stroke:#333,stroke-width:2px
```

## Core Components

### Frontend Layer

- **Technology**: Vue 3, TypeScript, Nx monorepo
- **Location**: `/web` directory
- **Applications**:
  - **Magnet Admin**: For system configuration and management.
  - **Magnet Panel**: For end-user interaction with AI agents.
- **Key Features**:
  - Agent configuration UI
  - Prompt template management
  - Knowledge source integration
  - Usage dashboards and analytics

### Backend Layer

- **Technology**: Python 3.12+, Litestar, SQLAlchemy (Async)
- **Location**: `/api` directory
- **Purpose**: Business logic, API endpoints, and AI orchestration
- **Key Features**:
  - High-performance Async REST API
  - Plugin system for extensibility
  - OpenAI and LLM integration
  - RAG (Retrieval Augmented Generation) tools
  - Agent execution engine

### Data Layer

- **PostgreSQL**: Primary database for application metadata and configurations.
- **pgvector**: Vector extension for PostgreSQL to store embeddings for semantic search.

## Architecture Principles

### 1. Plugin-Based Architecture

Magnet AI uses a plugin system that allows developers to extend functionality without modifying core code:

- Data source plugins
- Tool plugins
- Custom AI model integrations

### 2. API-First Design

All functionality is exposed through REST APIs, enabling:

- Third-party integrations
- Custom UI implementations
- Automation and scripting

### 3. Separation of Concerns

- Frontend handles presentation and user interaction
- Backend manages business logic and data processing
- Plugins provide modular functionality

### 4. Scalability

- Stateless API design
- Async I/O for high concurrency
- Horizontal scaling support

## Technology Stack

### Backend

- **Framework**: Litestar (High-performance ASGI framework)
- **ORM**: SQLAlchemy (Async)
- **Database**: PostgreSQL + pgvector

### Frontend

- **Framework**: Vue 3
- **Language**: TypeScript
- **Build Tool**: Nx, Vite
- **UI Library**: PrimeVue / Custom components
- **State Management**: Pinia / Vuex

### DevOps

- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Grafana / Prometheus / OpenTelemetry

## Data Flow

1. **User Request**: User interacts with the web UI (Admin or Panel).
2. **API Call**: Frontend sends REST API request to backend.
3. **Business Logic**: Backend processes request, may invoke plugins.
4. **AI Processing**: If needed, calls OpenAI or other LLM services.
5. **Data Retrieval**: Queries databases (SQL, vector) as needed.
6. **Response**: Returns data to frontend.
7. **UI Update**: Frontend updates the interface.

## Security Architecture

- **Authentication**: Token-based authentication (JWT/OAuth).
- **Authorization**: Role-based access control (RBAC).
- **API Security**: CORS configuration, input validation (Pydantic).
- **Data Protection**: Encrypted connections, secure credential storage.

## Next Steps

- [Backend Architecture](/docs/en/developers/architecture/backend) - Deep dive into backend design
- [Frontend Architecture](/docs/en/developers/architecture/frontend) - Frontend structure details
- [Database Schema](/docs/en/developers/architecture/database) - Data models and relationships
