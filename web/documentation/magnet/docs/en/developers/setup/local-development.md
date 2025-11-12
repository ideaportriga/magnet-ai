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
├── api/                    # Backend
│   ├── .venv/             # Python virtual environment
│   ├── src/               # Source code
│   └── tests/             # Tests
├── web/                   # Frontend
│   ├── node_modules/      # Dependencies
│   ├── apps/              # Applications
│   └── packages/          # Shared packages
└── docker/                # Docker configuration
```

## Backend Development

### Virtual Environment

Always use a virtual environment:

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

### Installing Dependencies

#### Using Poetry (Recommended)

```bash
poetry install
```

#### Using pip

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Running the Backend

#### Development Server

```bash
python run.py
```

The server runs with:
- Auto-reload enabled
- Debug mode on
- CORS enabled for local frontend

#### Custom Port

```bash
FLASK_RUN_PORT=5001 python run.py
```

### Environment Variables

Create `api/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
DATABASE_URL=sqlite:///db.sqlite3
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG

# External Services
VECTOR_DB_URL=...
REDIS_URL=...

# CORS
CORS_ORIGINS=http://localhost:4200,http://localhost:3000
```

### Database Workflow

#### Initialize Database

```bash
python scripts/ensure_database.py
```

#### Reset Database

```bash
rm db.sqlite3
python scripts/ensure_database.py
```

#### Load Fixtures

```bash
python manage_fixtures.py load
```

#### Save Fixtures

```bash
python manage_fixtures.py save
```

### Code Style

#### Format Code

```bash
black src/
isort src/
```

#### Lint Code

```bash
pylint src/
flake8 src/
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
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "src/app.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true
    }
  ]
}
```

## Frontend Development

### Installing Dependencies

```bash
cd web
npm install
```

### Running the Frontend

#### Development Server

```bash
npm run serve:knowledge-magnet
```

Or with Nx:

```bash
nx serve knowledge-magnet
```

Access at `http://localhost:4200`

#### Custom Port

```bash
nx serve knowledge-magnet --port=3000
```

### Hot Reload

Changes to TypeScript/React files automatically reload the browser.

### Environment Configuration

Create `web/apps/knowledge-magnet/.env.local`:

```bash
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=Magnet AI Dev
VITE_ENABLE_DEBUG=true
```

### Code Style

#### Format Code

```bash
npm run format
```

#### Lint Code

```bash
npm run lint
```

#### Type Checking

```bash
npm run type-check
```

### Browser DevTools

Use React DevTools extension for debugging React components.

## Full Stack Development

### Running Both Services

#### Option 1: tmux/screen

Create a tmux session:

```bash
tmux new -s magnet

# Window 1: Backend
cd api && python run.py

# Window 2 (Ctrl+B, C): Frontend
cd web && npm run serve:knowledge-magnet

# Window 3 (Ctrl+B, C): Logs/testing
```

#### Option 2: Docker Compose

```bash
docker-compose -f docker-compose.yml up
```

Services:
- API: `http://localhost:5000`
- Web: `http://localhost:4200`
- PostgreSQL: `localhost:5432`

#### Option 3: Shell Script

Create `dev.sh`:

```bash
#!/bin/bash
trap 'kill 0' EXIT

cd api && python run.py &
cd web && npm run serve:knowledge-magnet &

wait
```

Run:

```bash
chmod +x dev.sh
./dev.sh
```

### API Testing

#### Using curl

```bash
# List agents
curl http://localhost:5000/api/agents

# Create agent
curl -X POST http://localhost:5000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Agent","model_id":"gpt-4"}'
```

#### Using httpie

```bash
# Install httpie
brew install httpie

# List agents
http localhost:5000/api/agents

# Create agent
http POST localhost:5000/api/agents \
  name="Test Agent" \
  model_id="gpt-4"
```

#### Using Postman

1. Import API collection
2. Set base URL: `http://localhost:5000`
3. Create requests for endpoints

### Database Management

#### Using SQLite Browser

For SQLite databases:

```bash
brew install --cask db-browser-for-sqlite
open db.sqlite3
```

#### Using pgAdmin (PostgreSQL)

1. Install pgAdmin
2. Add server: `localhost:5432`
3. Connect with credentials

#### Using DBeaver

Universal database tool:

```bash
brew install --cask dbeaver-community
```

## Plugin Development

### Creating a Plugin

1. Create plugin directory:

```bash
cd api/src/plugins/builtin/knowledge_source
mkdir my_plugin
touch my_plugin/__init__.py
touch my_plugin/plugin.py
```

2. Implement plugin (see [Creating Plugins](/docs/en/developers/plugins/creating-plugins))

3. Test plugin:

```bash
python -c "
from core.plugins.registry import PluginRegistry
plugin = PluginRegistry.get_plugin('my_plugin')
print(plugin.name, plugin.version)
"
```

### Plugin Testing

Create `tests/test_my_plugin.py`:

```python
import unittest
from plugins.builtin.knowledge_source.my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def test_plugin_loads(self):
        plugin = MyPlugin()
        self.assertEqual(plugin.name, 'my_plugin')
```

Run:

```bash
pytest tests/test_my_plugin.py
```

## Performance Monitoring

### Backend Performance

#### Flask-DebugToolbar

Add to development:

```bash
pip install flask-debugtoolbar
```

#### Profiling

```python
from werkzeug.middleware.profiler import ProfilerMiddleware

app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
```

### Frontend Performance

#### React DevTools Profiler

1. Install React DevTools extension
2. Use Profiler tab
3. Record interactions
4. Analyze render performance

## Hot Reload Configuration

### Backend Hot Reload

Flask automatically reloads on code changes in development mode.

Disable if needed:

```bash
FLASK_RUN_NO_RELOAD=1 python run.py
```

### Frontend Hot Reload

Vite provides instant hot module replacement (HMR).

Configure in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    hmr: {
      overlay: true
    }
  }
});
```

## Logging

### Backend Logging

Configure in `api/src/config/logging.py`:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Use in code:

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Frontend Logging

Use console methods:

```typescript
console.log('Debug info');
console.warn('Warning');
console.error('Error');
```

## Common Workflows

### Adding a New Feature

1. Create feature branch
2. Implement backend API
3. Write backend tests
4. Implement frontend UI
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
- [ ] Code formatted
- [ ] No lint errors
- [ ] Documentation updated
- [ ] Changes reviewed

## Next Steps

- [Testing](/docs/en/developers/setup/testing) - Testing guide
- [Deployment](/docs/en/developers/setup/deployment) - Deployment strategies
- [Plugin Development](/docs/en/developers/plugins/creating-plugins) - Create plugins
