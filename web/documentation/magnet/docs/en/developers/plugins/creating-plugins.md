# Creating Plugins

This guide walks you through creating a custom plugin for Magnet AI.

## Quick Start

### 1. Choose Plugin Type

Decide what type of plugin you're creating:
- **Knowledge Source**: Connect to a data source
- **Tool**: Add custom functionality
- **Model**: Integrate an LLM provider (planned)

### 2. Set Up Plugin Structure

For a built-in plugin:

```bash
cd api/src/plugins/builtin/knowledge_source
mkdir my_plugin
cd my_plugin
touch __init__.py
touch plugin.py
touch README.md
```

For an external plugin package:

```bash
mkdir magnet-plugins-myplugin
cd magnet-plugins-myplugin
mkdir -p magnet_plugins
touch magnet_plugins/__init__.py
touch setup.py
touch pyproject.toml
touch README.md
```

## Creating a Knowledge Source Plugin

### Step 1: Define the Plugin Class

Create `plugin.py`:

```python
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType

class MyKnowledgeSourcePlugin(KnowledgeSourcePlugin):
    """Custom knowledge source plugin."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.KNOWLEDGE_SOURCE
    
    @property
    def name(self) -> str:
        return "my_knowledge_source"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Connects to my custom data source"
    
    def initialize(self):
        """Initialize the plugin."""
        # Set up connections, load config, etc.
        pass
    
    def cleanup(self):
        """Clean up resources."""
        # Close connections, release resources
        pass
```

### Step 2: Implement Required Methods

```python
def validate_config(self, config: dict) -> bool:
    """Validate the configuration."""
    required_fields = ['api_key', 'endpoint']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    return True

def test_connection(self, config: dict) -> bool:
    """Test connection to the data source."""
    try:
        # Test the connection
        response = self._make_request(config['endpoint'], config['api_key'])
        return response.status_code == 200
    except Exception as e:
        raise ConnectionError(f"Connection test failed: {e}")

def fetch_documents(self, config: dict) -> list:
    """Fetch documents from the data source."""
    self.validate_config(config)
    
    documents = []
    
    try:
        # Fetch documents from your source
        response = self._make_request(
            f"{config['endpoint']}/documents",
            config['api_key']
        )
        
        for item in response.json():
            documents.append({
                'id': item['id'],
                'title': item['title'],
                'content': item['content'],
                'metadata': {
                    'source': 'my_knowledge_source',
                    'author': item.get('author'),
                    'created_at': item.get('created_at')
                }
            })
    
    except Exception as e:
        raise Exception(f"Failed to fetch documents: {e}")
    
    return documents
```

### Step 3: Add Helper Methods

```python
import requests

def _make_request(self, url: str, api_key: str):
    """Make HTTP request to the API."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response

def _parse_document(self, raw_doc: dict) -> dict:
    """Parse raw document into standard format."""
    return {
        'id': raw_doc['id'],
        'title': raw_doc.get('title', 'Untitled'),
        'content': raw_doc.get('body', ''),
        'metadata': {
            'url': raw_doc.get('url'),
            'last_modified': raw_doc.get('updated_at')
        }
    }
```

### Step 4: Create __init__.py

```python
"""My Knowledge Source Plugin."""

from .plugin import MyKnowledgeSourcePlugin

__all__ = ['MyKnowledgeSourcePlugin']
```

### Step 5: Add Documentation

Create `README.md`:

```markdown
# My Knowledge Source Plugin

Connects Magnet AI to My Custom Data Source.

## Configuration

Required fields:
- `api_key`: API key for authentication
- `endpoint`: API endpoint URL

Optional fields:
- `page_size`: Number of items per page (default: 100)
- `filters`: Additional filters to apply

## Example Configuration

\```json
{
  "plugin_name": "my_knowledge_source",
  "settings": {
    "api_key": "your-api-key",
    "endpoint": "https://api.example.com/v1",
    "page_size": 50
  }
}
\```

## Features

- Automatic document fetching
- Incremental sync support
- Metadata extraction

## Requirements

- Python 3.12+
- `requests` library
```

## Creating an External Plugin Package

For distributable plugins, create a standalone package.

### Step 1: Create setup.py

```python
from setuptools import setup, find_packages

setup(
    name="magnet-plugins-myplugin",
    version="1.0.0",
    description="My custom Magnet AI plugin",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "requests>=2.31.0",
        # Add other dependencies
    ],
    entry_points={
        'magnet.plugins': [
            'my_plugin = magnet_plugins.my_plugin:MyKnowledgeSourcePlugin',
        ],
    },
)
```

### Step 2: Create pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "magnet-plugins-myplugin"
version = "1.0.0"
description = "My custom Magnet AI plugin"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

### Step 3: Install Your Plugin

```bash
# Development installation
pip install -e .

# Or install from repository
pip install git+https://github.com/yourusername/magnet-plugins-myplugin.git
```

## Testing Your Plugin

### Unit Tests

Create `tests/test_my_plugin.py`:

```python
import unittest
from magnet_plugins.my_plugin import MyKnowledgeSourcePlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyKnowledgeSourcePlugin()
        self.config = {
            'api_key': 'test-key',
            'endpoint': 'https://api.test.com'
        }
    
    def test_validate_config_valid(self):
        result = self.plugin.validate_config(self.config)
        self.assertTrue(result)
    
    def test_validate_config_missing_field(self):
        invalid_config = {'api_key': 'test'}
        with self.assertRaises(ValueError):
            self.plugin.validate_config(invalid_config)
    
    def test_fetch_documents(self):
        # Mock the API response
        docs = self.plugin.fetch_documents(self.config)
        self.assertIsInstance(docs, list)
```

### Integration Tests

```python
from core.plugins.registry import PluginRegistry

def test_plugin_registration():
    # Ensure plugin is registered
    plugin = PluginRegistry.get_plugin('my_knowledge_source')
    assert plugin is not None
    assert plugin.name == 'my_knowledge_source'

def test_plugin_in_magnet():
    # Test using the plugin in Magnet AI
    # Create a knowledge source with your plugin
    # Verify it works end-to-end
    pass
```

## Deployment

### For Built-in Plugins

Built-in plugins are deployed with Magnet AI automatically.

### For External Plugins

1. **Package the plugin**:
   ```bash
   python -m build
   ```

2. **Publish to PyPI** (optional):
   ```bash
   twine upload dist/*
   ```

3. **Install in Magnet AI**:
   ```bash
   pip install magnet-plugins-myplugin
   ```

4. **Configure in environment**:
   ```bash
   MAGNET_EXTERNAL_PLUGINS=magnet_plugins.my_plugin
   ```

## Best Practices

1. **Configuration Validation**: Always validate configuration before use
2. **Error Handling**: Provide clear error messages
3. **Logging**: Use Python logging for debugging
4. **Documentation**: Document all configuration options
5. **Testing**: Write comprehensive tests
6. **Dependencies**: Minimize external dependencies
7. **Security**: Never hardcode credentials
8. **Versioning**: Follow semantic versioning

## Next Steps

- [Plugin API](/docs/en/developers/plugins/plugin-api) - Complete API reference
- [Plugin Examples](/docs/en/developers/plugins/examples) - Example implementations
- [Plugin System](/docs/en/developers/plugins/plugin-system) - Architecture overview
