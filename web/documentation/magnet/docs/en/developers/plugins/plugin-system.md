# Plugin System

Magnet AI features a flexible plugin architecture that allows you to extend the platform with custom functionality.

## Overview

The plugin system enables developers to:
- Add custom knowledge source connectors
- Integrate with external APIs and services
- Create custom AI tools
- Extend platform capabilities without modifying core code

## Plugin Types

### Knowledge Source Plugins

Connect to various data sources:
- **File-based**: PDF, TXT, Markdown documents
- **Web services**: SharePoint, Confluence, Salesforce
- **Databases**: SQL, NoSQL databases
- **Custom APIs**: Any REST or GraphQL API

### Tool Plugins

Extend agent capabilities:
- **RAG Tools**: Document retrieval and Q&A
- **API Tools**: External service integrations
- **Custom Tools**: Domain-specific functionality

### Model Plugins (Planned)

Support for additional LLM providers:
- Custom OpenAI-compatible APIs
- Proprietary models
- Self-hosted models

## Plugin Architecture

### Core Components

```
api/src/
├── core/
│   └── plugins/
│       ├── base.py              # Base plugin interface
│       ├── plugin_types.py      # Plugin type definitions
│       ├── interfaces.py        # Specialized interfaces
│       └── registry.py          # Plugin registry
└── plugins/
    ├── builtin/                 # Built-in plugins (public)
    │   └── knowledge_source/
    │       ├── sharepoint/
    │       ├── confluence/
    │       ├── file/
    │       └── ...
    └── external/                # External plugins (private)
        └── knowledge_source/
            └── custom/
```

### Plugin Lifecycle

1. **Discovery**: Plugins are discovered at startup
2. **Registration**: Plugins register with the plugin registry
3. **Initialization**: Plugin instances are created as needed
4. **Execution**: Plugins execute their functionality
5. **Cleanup**: Resources are released when done

## Built-in vs External Plugins

### Built-in Plugins

Included with Magnet AI:
- SharePoint Documents & Pages
- Confluence
- Salesforce
- File URL
- Documentation crawler (VitePress)

Located in: `api/src/plugins/builtin/`

### External Plugins

Custom, client-specific, or proprietary plugins:
- Installed as separate packages
- Not included in public repository
- Maintained independently

Located in: `api/src/plugins/external/`

## Plugin Interface

### Base Plugin Class

All plugins inherit from `BasePlugin`:

```python
from core.plugins.base import BasePlugin
from core.plugins.plugin_types import PluginType

class MyPlugin(BasePlugin):
    """My custom plugin."""
    
    @property
    def plugin_type(self) -> PluginType:
        """Return the plugin type."""
        return PluginType.KNOWLEDGE_SOURCE
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "my_plugin"
    
    @property
    def version(self) -> str:
        """Return the plugin version."""
        return "1.0.0"
    
    def initialize(self):
        """Initialize the plugin."""
        pass
    
    def cleanup(self):
        """Clean up plugin resources."""
        pass
```

### Knowledge Source Plugin Interface

For data source connectors:

```python
from core.plugins.interfaces import KnowledgeSourcePlugin

class MyKnowledgeSource(KnowledgeSourcePlugin):
    """Custom knowledge source."""
    
    def fetch_documents(self, config: dict) -> list:
        """Fetch documents from the source."""
        # Implementation
        pass
    
    def validate_config(self, config: dict) -> bool:
        """Validate configuration."""
        # Implementation
        pass
    
    def test_connection(self, config: dict) -> bool:
        """Test connection to the source."""
        # Implementation
        pass
```

## Configuration

### Plugin Configuration

Plugins receive configuration through the knowledge source or tool configuration:

```python
{
    "plugin_name": "my_plugin",
    "settings": {
        "api_key": "secret",
        "endpoint": "https://api.example.com",
        "custom_param": "value"
    }
}
```

### Environment Variables

Plugins can access environment variables for sensitive data:

```python
import os

class MyPlugin(BasePlugin):
    def initialize(self):
        self.api_key = os.getenv('MY_PLUGIN_API_KEY')
```

## Plugin Registry

### Registering Plugins

Plugins are automatically discovered and registered:

```python
from core.plugins.registry import PluginRegistry

# Get plugin instance
plugin = PluginRegistry.get_plugin('my_plugin')

# List all plugins of a type
plugins = PluginRegistry.get_plugins_by_type(PluginType.KNOWLEDGE_SOURCE)
```

### Plugin Metadata

Each plugin provides metadata:

```python
{
    "name": "my_plugin",
    "version": "1.0.0",
    "type": "knowledge_source",
    "description": "My custom plugin",
    "author": "Your Name",
    "capabilities": ["fetch", "search"]
}
```

## Error Handling

Plugins should handle errors gracefully:

```python
from core.plugins.base import PluginError

class MyPlugin(BasePlugin):
    def fetch_documents(self, config):
        try:
            # Plugin logic
            pass
        except Exception as e:
            raise PluginError(f"Failed to fetch documents: {e}")
```

## Testing Plugins

### Unit Tests

Create tests in `tests/plugins/`:

```python
import unittest
from plugins.builtin.knowledge_source.my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
    
    def test_fetch_documents(self):
        config = {"api_key": "test"}
        docs = self.plugin.fetch_documents(config)
        self.assertIsInstance(docs, list)
```

### Integration Tests

Test plugin integration with the platform:

```python
def test_plugin_registration():
    plugin = PluginRegistry.get_plugin('my_plugin')
    assert plugin is not None
    assert plugin.plugin_type == PluginType.KNOWLEDGE_SOURCE
```

## Best Practices

1. **Follow the Interface**: Implement all required methods
2. **Validate Configuration**: Check config before use
3. **Handle Errors**: Provide meaningful error messages
4. **Document Your Plugin**: Include docstrings and README
5. **Test Thoroughly**: Write comprehensive tests
6. **Version Properly**: Use semantic versioning
7. **Minimize Dependencies**: Keep plugin lightweight

## Next Steps

- [Creating Plugins](/docs/en/developers/plugins/creating-plugins) - Step-by-step guide
- [Plugin API](/docs/en/developers/plugins/plugin-api) - Complete API reference
- [Plugin Examples](/docs/en/developers/plugins/examples) - Example implementations
