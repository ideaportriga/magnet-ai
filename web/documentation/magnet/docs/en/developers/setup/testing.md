# Testing

Comprehensive testing guide for Magnet AI development.

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\        End-to-End (Few)
      /------\
     /  Integ \     Integration (Some)
    /----------\
   /   Unit     \   Unit Tests (Many)
  /--------------\
```

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows

## Backend Testing

### Test Structure

```
api/tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_models.py        # Model tests
├── test_services.py      # Service tests
├── test_routes.py        # API endpoint tests
└── plugins/
    └── test_plugins.py   # Plugin tests
```

### Running Tests

#### All Tests

```bash
cd api
pytest
```

#### Specific Test File

```bash
pytest tests/test_models.py
```

#### Specific Test

```bash
pytest tests/test_models.py::TestAgent::test_create_agent
```

#### With Coverage

```bash
pytest --cov=src --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

### Unit Tests

#### Testing Models

```python
import unittest
from src.models import Agent

class TestAgent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.agent_data = {
            'name': 'Test Agent',
            'model_id': 'gpt-4',
            'temperature': 0.7
        }
    
    def test_create_agent(self):
        """Test agent creation."""
        agent = Agent(**self.agent_data)
        
        self.assertEqual(agent.name, 'Test Agent')
        self.assertEqual(agent.model_id, 'gpt-4')
        self.assertEqual(agent.temperature, 0.7)
    
    def test_agent_validation(self):
        """Test agent validation."""
        invalid_data = {'name': ''}
        
        with self.assertRaises(ValueError):
            Agent(**invalid_data)
```

#### Testing Services

```python
import unittest
from unittest.mock import Mock, patch
from src.services.agent_service import AgentService

class TestAgentService(unittest.TestCase):
    def setUp(self):
        self.service = AgentService()
    
    @patch('src.services.agent_service.AgentStore')
    def test_get_agent(self, mock_store):
        """Test getting an agent."""
        # Arrange
        mock_agent = Mock()
        mock_agent.id = '123'
        mock_agent.name = 'Test Agent'
        mock_store.find_by_id.return_value = mock_agent
        
        # Act
        agent = self.service.get_agent('123')
        
        # Assert
        self.assertEqual(agent.id, '123')
        self.assertEqual(agent.name, 'Test Agent')
        mock_store.find_by_id.assert_called_once_with('123')
```

### Integration Tests

#### Testing API Endpoints

```python
import unittest
import json
from src.app import create_app

class TestAgentAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_list_agents(self):
        """Test listing agents."""
        response = self.client.get('/api/agents')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
    
    def test_create_agent(self):
        """Test creating an agent."""
        agent_data = {
            'name': 'Test Agent',
            'model_id': 'gpt-4',
            'temperature': 0.7
        }
        
        response = self.client.post(
            '/api/agents',
            data=json.dumps(agent_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'Test Agent')
    
    def test_create_agent_invalid_data(self):
        """Test creating agent with invalid data."""
        response = self.client.post(
            '/api/agents',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
```

### Testing Plugins

```python
import unittest
from plugins.builtin.knowledge_source.file import FilePlugin

class TestFilePlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = FilePlugin()
        self.config = {
            'directory': '/tmp/test_docs',
            'extensions': ['.txt', '.md']
        }
    
    def test_plugin_metadata(self):
        """Test plugin metadata."""
        self.assertEqual(self.plugin.name, 'file')
        self.assertEqual(self.plugin.plugin_type.value, 'knowledge_source')
    
    def test_validate_config(self):
        """Test config validation."""
        # Valid config
        self.assertTrue(self.plugin.validate_config(self.config))
        
        # Missing directory
        with self.assertRaises(ValueError):
            self.plugin.validate_config({})
    
    @patch('os.path.exists')
    @patch('os.walk')
    def test_fetch_documents(self, mock_walk, mock_exists):
        """Test fetching documents."""
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/tmp/test_docs', [], ['test.txt', 'readme.md'])
        ]
        
        with patch('builtins.open', unittest.mock.mock_open(read_data='test content')):
            docs = self.plugin.fetch_documents(self.config)
        
        self.assertEqual(len(docs), 2)
```

### Test Fixtures

Create reusable test data in `conftest.py`:

```python
import pytest
from src.app import create_app
from src.models import db, Agent

@pytest.fixture
def app():
    """Create test app."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_agent(app):
    """Create sample agent."""
    agent = Agent(
        name='Test Agent',
        model_id='gpt-4',
        temperature=0.7
    )
    db.session.add(agent)
    db.session.commit()
    return agent
```

Use in tests:

```python
def test_get_agent(client, sample_agent):
    """Test getting an agent."""
    response = client.get(f'/api/agents/{sample_agent.id}')
    assert response.status_code == 200
```

## Frontend Testing

### Test Structure

```
web/apps/knowledge-magnet/src/
├── app/
│   ├── components/
│   │   ├── Component.tsx
│   │   └── Component.test.tsx
└── pages/
    ├── Page.tsx
    └── Page.test.tsx
```

### Running Tests

#### All Tests

```bash
cd web
npm test
```

Or with Nx:

```bash
nx test knowledge-magnet
```

#### Watch Mode

```bash
npm test -- --watch
```

#### Coverage

```bash
npm test -- --coverage
```

### Component Testing

#### Testing React Components

```typescript
import { render, screen } from '@testing-library/react';
import { AgentCard } from './AgentCard';

describe('AgentCard', () => {
  it('renders agent name', () => {
    const agent = {
      id: '1',
      name: 'Test Agent',
      model_id: 'gpt-4'
    };
    
    render(<AgentCard agent={agent} />);
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
  
  it('displays model information', () => {
    const agent = {
      id: '1',
      name: 'Test Agent',
      model_id: 'gpt-4'
    };
    
    render(<AgentCard agent={agent} />);
    
    expect(screen.getByText(/gpt-4/i)).toBeInTheDocument();
  });
});
```

#### Testing User Interactions

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { CreateAgentForm } from './CreateAgentForm';

describe('CreateAgentForm', () => {
  it('calls onSubmit when form is submitted', () => {
    const handleSubmit = jest.fn();
    
    render(<CreateAgentForm onSubmit={handleSubmit} />);
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: 'New Agent' }
    });
    
    fireEvent.change(screen.getByLabelText(/model/i), {
      target: { value: 'gpt-4' }
    });
    
    // Submit
    fireEvent.click(screen.getByText(/create/i));
    
    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'New Agent',
      model_id: 'gpt-4'
    });
  });
});
```

#### Testing Async Operations

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { AgentList } from './AgentList';

describe('AgentList', () => {
  it('loads and displays agents', async () => {
    // Mock API
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          success: true,
          data: [
            { id: '1', name: 'Agent 1' },
            { id: '2', name: 'Agent 2' }
          ]
        })
      })
    ) as jest.Mock;
    
    render(<AgentList />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument();
      expect(screen.getByText('Agent 2')).toBeInTheDocument();
    });
  });
});
```

### Testing Hooks

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useAgents } from './useAgents';

describe('useAgents', () => {
  it('fetches agents', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          success: true,
          data: [{ id: '1', name: 'Agent 1' }]
        })
      })
    ) as jest.Mock;
    
    const { result } = renderHook(() => useAgents());
    
    await waitFor(() => {
      expect(result.current.agents).toHaveLength(1);
      expect(result.current.loading).toBe(false);
    });
  });
});
```

## E2E Testing

### Playwright (Recommended)

#### Setup

```bash
cd web
npm install -D @playwright/test
npx playwright install
```

#### Example Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('Agent Management', () => {
  test('create new agent', async ({ page }) => {
    // Navigate to agents page
    await page.goto('http://localhost:4200/agents');
    
    // Click create button
    await page.click('text=Create Agent');
    
    // Fill in form
    await page.fill('[name="name"]', 'E2E Test Agent');
    await page.selectOption('[name="model_id"]', 'gpt-4');
    
    // Submit
    await page.click('text=Create');
    
    // Verify agent created
    await expect(page.locator('text=E2E Test Agent')).toBeVisible();
  });
});
```

#### Run E2E Tests

```bash
npx playwright test
```

## Test Best Practices

### 1. AAA Pattern

```python
def test_example():
    # Arrange
    data = {'name': 'Test'}
    
    # Act
    result = function(data)
    
    # Assert
    assert result == expected
```

### 2. Descriptive Names

```python
# Good
def test_agent_creation_with_valid_data_succeeds():
    pass

# Bad
def test1():
    pass
```

### 3. One Assertion Per Test

```python
# Good
def test_agent_has_name():
    agent = Agent(name='Test')
    assert agent.name == 'Test'

def test_agent_has_model():
    agent = Agent(model_id='gpt-4')
    assert agent.model_id == 'gpt-4'
```

### 4. Use Fixtures

```python
@pytest.fixture
def sample_agent():
    return Agent(name='Test', model_id='gpt-4')

def test_agent(sample_agent):
    assert sample_agent.name == 'Test'
```

### 5. Mock External Dependencies

```python
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {'data': 'test'}
    result = fetch_data()
    assert result == {'data': 'test'}
```

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r api/requirements.txt
      - run: cd api && pytest --cov
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd web && npm install
      - run: cd web && npm test
```

## Next Steps

- [Local Development](/docs/en/developers/setup/local-development) - Development workflow
- [Deployment](/docs/en/developers/setup/deployment) - Deployment guide
- [Backend Architecture](/docs/en/developers/architecture/backend) - Backend details
