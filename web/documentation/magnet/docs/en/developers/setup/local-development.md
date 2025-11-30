# Local Development

Best practices and workflows for local development with Magnet AI.

## Development Environment

### Recommended Setup

- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: 3.12+ with virtual environment
- **Node.js**: 18+ with npm or yarn
- **IDE**: VS Code with recommended extensions
- **Database**: PostgreSQL for production-like environment

### Directory Structure

Keep your workspace organized:

```
magnet-ai/
├── api/                    # Backend (Litestar)
│   ├── .venv/             # Python virtual environment
│   ├── src/               # Source code
│   └── tests/             # Tests
├── web/                   # Frontend (Nx Monorepo)
│   ├── apps/              # Applications (admin, panel)
│   ├── packages/          # Shared libraries
│   └── documentation/     # This documentation
└── docker/                # Docker configuration
```

## Backend Development

### Virtual Environment

Always use a virtual environment:

```bash
cd api
poetry shell
```

### Installing Dependencies

#### Using Poetry (Recommended)

```bash
poetry install
```

### Running the Backend

#### Development Server

```bash
uvicorn app:app --reload --env-file="../.env"
```

The server runs with:

- Auto-reload enabled
- Debug mode (if configured in .env)
- CORS enabled for local frontend

#### Custom Port

```bash
uvicorn app:app --reload --env-file="../.env" --port 8001
```

### Environment Variables

Create `.env` in the root directory (or `api/.env` if running standalone):

```bash
# Required
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/magnet_ai

# Application
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# External Services
VECTOR_DB_TYPE=POSTGRES
```

### Database Workflow

#### Run Migrations

```bash
npm run db:migrate
```

#### Apply Migrations

```bash
npm run db:upgrade
```

#### Reset Database

```bash
npm run db:reset
```

### Code Style

#### Format Code

```bash
ruff format src/
```

#### Lint Code

```bash
ruff check src/
```

#### Type Checking

```bash
mypy src/
```

### Debugging

#### Using pdb

Add breakpoint:

```python
import pdb; pdb.set_trace()
```

#### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Litestar",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app:app", "--reload", "--port", "8000"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

## Frontend Development

### Installing Dependencies

```bash
cd web
yarn install
```

### Running the Frontend

#### Development Server

**User Panel:**

```bash
yarn nx dev magnet-panel
```

**Admin Console:**

```bash
yarn nx dev magnet-admin
```

Access at:

- Panel: `http://localhost:4200` (or similar)
- Admin: `http://localhost:4201` (or similar)

### Hot Reload

Changes to TypeScript/Vue files automatically reload the browser.

### Code Style

#### Format & Lint

```bash
yarn lint
```

#### Type Checking

```bash
yarn type-check
```

### Browser DevTools

Use Vue.js devtools extension for debugging Vue components.

## Full Stack Development

### Running Both Services (Recommended)

Use the root script to run everything:

```bash
npm run dev
```

This starts:

- API: `http://localhost:8000`
- Web Apps: `http://localhost:3000` & `http://localhost:3001`

### API Testing

#### Using curl

```bash
# List agents
curl http://localhost:8000/api/agents
```

#### Using Postman

1. Import API collection
2. Set base URL: `http://localhost:8000`
3. Create requests for endpoints

### Database Management

#### Using DBeaver

Universal database tool:

```bash
brew install --cask dbeaver-community
```

Connect to `localhost:5432` (User: `postgres`, Pass: `postgres` or as defined in `.env`).

## Plugin Development

### Creating a Plugin

Plugins in Magnet AI are typically Python modules integrated via the `PluginRegistry`.

1. Create plugin directory in `api/src/plugins/`.
2. Implement your plugin logic.
3. Register it in `api/src/core/server/plugin_registry.py` or via the dynamic loader.

### Plugin Testing

Create `tests/test_my_plugin.py` and run:

```bash
pytest tests/test_my_plugin.py
```

## Performance Monitoring

### Backend Performance

Litestar provides built-in instrumentation hooks. You can also use standard Python profiling tools.

### Frontend Performance

#### Vue DevTools

1. Install Vue.js devtools extension
2. Use Performance tab
3. Record interactions
4. Analyze render performance

## Logging

### Backend Logging

Configure in `api/src/core/config/logging.py`.
Magnet AI uses `structlog` for structured logging.

Use in code:

```python
import structlog

logger = structlog.get_logger()

logger.info("event_name", key="value")
logger.error("error_event", error=str(e))
```

### Frontend Logging

Use console methods:

```typescript
console.log('Debug info')
console.warn('Warning')
console.error('Error')
```

## Common Workflows

### Adding a New Feature

1. Create feature branch
2. Implement backend API (Litestar Controller)
3. Write backend tests
4. Implement frontend UI (Vue Components)
5. Write frontend tests
6. Test integration
7. Create pull request

### Fixing a Bug

1. Reproduce the bug
2. Write a failing test
3. Fix the bug
4. Verify test passes
5. Commit and PR

### Code Review Checklist

- [ ] Tests pass
- [ ] Code formatted (Ruff/Prettier)
- [ ] No lint errors
- [ ] Documentation updated
- [ ] Changes reviewed

## Next Steps

- [Testing](/docs/en/developers/setup/testing) - Testing guide
- [Deployment](/docs/en/developers/setup/deployment) - Deployment strategies
- [Plugin Development](/docs/en/developers/plugins/creating-plugins) - Create plugins
