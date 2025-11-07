# Getting Started

This guide will help you set up your development environment for Magnet AI.

## Prerequisites

### Required Software

- **Python 3.12+**: Backend development
- **Node.js 18+**: Frontend development
- **Docker**: For containerized development
- **Git**: Version control

### Recommended Tools

- **VS Code**: With Python and TypeScript extensions
- **Postman**: For API testing
- **pgAdmin** or **DBeaver**: Database management

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/magnet-ai.git
cd magnet-ai
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd api
poetry install
```

Or using pip:

```bash
pip install -r requirements.txt
```

#### Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Application
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

#### Initialize Database

```bash
python scripts/ensure_database.py
```

#### Run Backend

```bash
python run.py
```

Backend will start at `http://localhost:5000`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd web
npm install
```

#### Run Frontend

```bash
npm run serve:knowledge-magnet
```

Or with Nx:

```bash
nx serve knowledge-magnet
```

Frontend will start at `http://localhost:4200`

## Development Workflow

### Running Both Services

#### Option 1: Separate Terminals

Terminal 1 (Backend):
```bash
cd api
python run.py
```

Terminal 2 (Frontend):
```bash
cd web
npm run serve:knowledge-magnet
```

#### Option 2: Docker Compose

```bash
docker-compose up
```

This starts:
- Backend at `http://localhost:5000`
- Frontend at `http://localhost:4200`
- PostgreSQL database
- Vector database (if configured)

### Making Changes

#### Backend Changes

1. Edit Python files in `api/src/`
2. Flask auto-reloads in development mode
3. Test your changes via API or UI

#### Frontend Changes

1. Edit TypeScript/React files in `web/apps/knowledge-magnet/`
2. Vite auto-reloads in development
3. View changes in browser

## Project Structure

### Backend (`api/`)

```
api/
├── src/
│   ├── app.py              # Flask application
│   ├── models.py           # Database models
│   ├── routes/             # API routes
│   ├── services/           # Business logic
│   ├── plugins/            # Plugin system
│   └── utils/              # Utilities
├── scripts/                # Setup scripts
├── tests/                  # Tests
├── pyproject.toml          # Dependencies
└── run.py                  # Development server
```

### Frontend (`web/`)

```
web/
├── apps/
│   └── knowledge-magnet/   # Main app
│       ├── src/
│       │   ├── app/        # React components
│       │   ├── pages/      # Page components
│       │   └── services/   # API services
│       └── project.json    # Nx configuration
├── packages/               # Shared packages
└── nx.json                 # Nx workspace config
```

## Environment Configuration

### Backend Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Database
DATABASE_URL=postgresql://user:pass@localhost/magnet
VECTOR_DB_URL=...

# Application
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key

# CORS (for local development)
CORS_ORIGINS=http://localhost:4200

# Logging
LOG_LEVEL=INFO
```

### Frontend Environment Variables

Create `web/apps/knowledge-magnet/.env`:

```bash
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=Magnet AI
```

## Database Setup

### SQLite (Development)

Default configuration uses SQLite:

```bash
DATABASE_URL=sqlite:///db.sqlite3
```

No additional setup required.

### PostgreSQL (Production-like)

#### Install PostgreSQL

macOS:
```bash
brew install postgresql
brew services start postgresql
```

Linux:
```bash
sudo apt-get install postgresql
sudo systemctl start postgresql
```

#### Create Database

```bash
createdb magnet_dev
```

#### Update Configuration

```bash
DATABASE_URL=postgresql://localhost/magnet_dev
```

#### Run Migrations

```bash
cd api
python manage_migrations.py
```

## Common Tasks

### Add a New API Endpoint

1. Create route in `api/src/routes/`:

```python
# api/src/routes/my_route.py
from flask import Blueprint, jsonify

bp = Blueprint('my_route', __name__)

@bp.route('/my-endpoint', methods=['GET'])
def my_endpoint():
    return jsonify({'message': 'Hello!'})
```

2. Register in `api/src/app.py`:

```python
from routes.my_route import bp as my_route_bp

app.register_blueprint(my_route_bp, url_prefix='/api')
```

### Add a New Frontend Page

1. Create component in `web/apps/knowledge-magnet/src/pages/`:

```typescript
// MyPage.tsx
export function MyPage() {
  return <div>My New Page</div>;
}
```

2. Add route (if using React Router):

```typescript
import { MyPage } from './pages/MyPage';

<Route path="/my-page" element={<MyPage />} />
```

### Run Tests

#### Backend Tests

```bash
cd api
pytest
```

#### Frontend Tests

```bash
cd web
npm test
```

Or with Nx:

```bash
nx test knowledge-magnet
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- TypeScript
- ESLint
- Prettier

#### Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/api/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "typescript.tsdk": "web/node_modules/typescript/lib"
}
```

## Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError`
- Solution: Ensure dependencies are installed: `poetry install`

**Error**: `Database connection failed`
- Solution: Check DATABASE_URL in `.env`

**Error**: `OpenAI API error`
- Solution: Verify OPENAI_API_KEY is set

### Frontend Won't Start

**Error**: `Cannot find module`
- Solution: Run `npm install`

**Error**: `Port 4200 already in use`
- Solution: Kill existing process or change port

### Database Issues

**Error**: `Table doesn't exist`
- Solution: Run migrations: `python scripts/ensure_database.py`

**Error**: `Database locked`
- Solution: Close other connections to SQLite

## Next Steps

- [Local Development](/docs/en/developers/setup/local-development) - Detailed development guide
- [Testing](/docs/en/developers/setup/testing) - Testing strategies
- [System Architecture](/docs/en/developers/architecture/system-architecture) - Architecture overview
- [REST API](/docs/en/developers/api/rest-api) - API documentation
