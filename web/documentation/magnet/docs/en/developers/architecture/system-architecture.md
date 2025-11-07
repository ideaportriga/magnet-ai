# System Architecture

Magnet AI follows a modern microservices architecture with a clear separation between frontend and backend components.

## High-Level Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Web)                     │
│              React + TypeScript + Nx                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ REST API
                  │
┌─────────────────▼───────────────────────────────────┐
│                  Backend (API)                       │
│              Python + Flask + SQLAlchemy             │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴─────────┬─────────────┐
        │                   │             │
┌───────▼────────┐  ┌──────▼─────┐  ┌────▼──────┐
│   PostgreSQL   │  │   Vector   │  │  Storage  │
│   (Metadata)   │  │  Database  │  │  (Files)  │
└────────────────┘  └────────────┘  └───────────┘
```

## Core Components

### Frontend Layer
- **Technology**: React, TypeScript, Nx monorepo
- **Location**: `/web` directory
- **Purpose**: User interface for configuring and using AI tools
- **Key Features**:
  - Agent configuration UI
  - Prompt template management
  - Knowledge source integration
  - Usage dashboards and analytics

### Backend Layer
- **Technology**: Python, Flask, SQLAlchemy
- **Location**: `/api` directory
- **Purpose**: Business logic, API endpoints, and AI orchestration
- **Key Features**:
  - REST API for all operations
  - Plugin system for extensibility
  - OpenAI and LLM integration
  - RAG (Retrieval Augmented Generation) tools
  - Agent execution engine

### Data Layer
- **SQLite/PostgreSQL**: Application metadata, configurations
- **Vector Database**: Embeddings for semantic search
- **File Storage**: Static files and documents

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
- Horizontal scaling support
- Async task processing with schedulers

## Technology Stack

### Backend
- **Framework**: Flask
- **ORM**: SQLAlchemy
- **AI/ML**: OpenAI API, LangChain
- **Task Queue**: APScheduler
- **Database**: SQLite (development), PostgreSQL (production)

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Nx, Vite
- **UI Library**: Custom components
- **State Management**: React Context/Hooks

### DevOps
- **Containerization**: Docker, Docker Compose
- **Orchestration**: OpenShift (optional)
- **Monitoring**: Grafana (logging configuration available)

## Data Flow

1. **User Request**: User interacts with the web UI
2. **API Call**: Frontend sends REST API request to backend
3. **Business Logic**: Backend processes request, may invoke plugins
4. **AI Processing**: If needed, calls OpenAI or other LLM services
5. **Data Retrieval**: Queries databases (SQL, vector) as needed
6. **Response**: Returns data to frontend
7. **UI Update**: Frontend updates the interface

## Security Architecture

- **Authentication**: Token-based authentication
- **Authorization**: Role-based access control
- **API Security**: CORS configuration, rate limiting
- **Data Protection**: Encrypted connections, secure credential storage

## Next Steps

- [Backend Architecture](/docs/en/developers/architecture/backend) - Deep dive into backend design
- [Frontend Architecture](/docs/en/developers/architecture/frontend) - Frontend structure details
- [Database Schema](/docs/en/developers/architecture/database) - Data models and relationships
