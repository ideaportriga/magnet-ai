# Plugin API Reference

Complete API reference for developing Magnet AI plugins.

## Base Plugin Class

### BasePlugin

All plugins must inherit from `BasePlugin`.

**Location**: `core/plugins/base.py`

#### Properties

##### plugin_type

```python
@property
def plugin_type(self) -> PluginType:
    """Return the plugin type."""
```

Returns the type of plugin (KNOWLEDGE_SOURCE, TOOL, MODEL, etc.)

##### name

```python
@property
def name(self) -> str:
    """Return the plugin name."""
```

Returns the unique identifier for the plugin.

##### version

```python
@property
def version(self) -> str:
    """Return the plugin version."""
```

Returns the semantic version string (e.g., "1.0.0").

##### description

```python
@property
def description(self) -> str:
    """Return the plugin description."""
```

Returns a human-readable description of the plugin.

#### Methods

##### initialize

```python
def initialize(self) -> None:
    """Initialize the plugin."""
```

Called when the plugin is loaded. Use for:

- Setting up connections
- Loading configuration
- Initializing resources

##### cleanup

```python
def cleanup(self) -> None:
    """Clean up plugin resources."""
```

Called when the plugin is unloaded. Use for:

- Closing connections
- Releasing resources
- Cleanup operations

## Knowledge Source Plugin Interface

### KnowledgeSourcePlugin

**Location**: `core/plugins/interfaces.py`

Inherits from `BasePlugin` with additional methods for data source integration.

#### Methods

##### validate_config

```python
def validate_config(self, config: dict) -> bool:
    """
    Validate the plugin configuration.

    Args:
        config: Plugin configuration dictionary

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
```

Validate configuration before use. Should check:

- Required fields present
- Field types correct
- Values within valid ranges

**Example:**

```python
def validate_config(self, config: dict) -> bool:
    required = ['api_key', 'endpoint']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    return True
```

##### test_connection

```python
def test_connection(self, config: dict) -> bool:
    """
    Test connection to the data source.

    Args:
        config: Plugin configuration dictionary

    Returns:
        True if connection successful

    Raises:
        ConnectionError: If connection fails
    """
```

Test connectivity to the data source.

**Example:**

```python
def test_connection(self, config: dict) -> bool:
    try:
        response = requests.get(config['endpoint'])
        return response.status_code == 200
    except Exception as e:
        raise ConnectionError(f"Connection failed: {e}")
```

##### fetch_documents

```python
def fetch_documents(self, config: dict) -> list[dict]:
    """
    Fetch documents from the data source.

    Args:
        config: Plugin configuration dictionary

    Returns:
        List of document dictionaries

    Raises:
        Exception: If fetch operation fails
    """
```

Fetch documents from the data source. Each document should include:

- `id`: Unique identifier
- `title`: Document title
- `content`: Document content
- `metadata`: Additional metadata (dict)

**Example:**

```python
def fetch_documents(self, config: dict) -> list[dict]:
    documents = []
    response = self._api_call(config)

    for item in response.json():
        documents.append({
            'id': item['id'],
            'title': item['title'],
            'content': item['body'],
            'metadata': {
                'url': item['url'],
                'author': item['author'],
                'created_at': item['created_at']
            }
        })

    return documents
```

##### sync_incremental (Optional)

```python
def sync_incremental(self, config: dict, last_sync: datetime) -> list[dict]:
    """
    Fetch only documents modified since last sync.

    Args:
        config: Plugin configuration
        last_sync: Timestamp of last synchronization

    Returns:
        List of modified/new documents
    """
```

Optional method for incremental synchronization.

##### search_documents (Optional)

```python
def search_documents(self, config: dict, query: str) -> list[dict]:
    """
    Search for documents matching a query.

    Args:
        config: Plugin configuration
        query: Search query string

    Returns:
        List of matching documents
    """
```

Optional method for searching within the data source.

## Plugin Types

### PluginType Enum

**Location**: `core/plugins/plugin_types.py`

```python
from enum import Enum

class PluginType(Enum):
    KNOWLEDGE_SOURCE = "knowledge_source"
    TOOL = "tool"
    MODEL = "model"
    AUTH = "auth"
    STORAGE = "storage"
```

## Plugin Registry

### PluginRegistry

**Location**: `core/plugins/registry.py`

Central registry for managing plugins.

#### Methods

##### register_plugin

```python
@classmethod
def register_plugin(cls, plugin: BasePlugin) -> None:
    """Register a plugin with the registry."""
```

Register a plugin instance.

##### get_plugin

```python
@classmethod
def get_plugin(cls, name: str) -> BasePlugin:
    """
    Get a plugin by name.

    Args:
        name: Plugin name

    Returns:
        Plugin instance or None
    """
```

Retrieve a registered plugin.

##### get_plugins_by_type

```python
@classmethod
def get_plugins_by_type(cls, plugin_type: PluginType) -> list[BasePlugin]:
    """
    Get all plugins of a specific type.

    Args:
        plugin_type: The plugin type to filter by

    Returns:
        List of matching plugins
    """
```

Get all plugins of a specific type.

##### list_plugins

```python
@classmethod
def list_plugins(cls) -> list[dict]:
    """
    List all registered plugins with metadata.

    Returns:
        List of plugin metadata dictionaries
    """
```

Get metadata for all registered plugins.

## Exceptions

### PluginError

Base exception for plugin errors.

```python
from core.plugins.base import PluginError

raise PluginError("Plugin operation failed")
```

### ConfigurationError

For configuration-related errors.

```python
from core.plugins.base import ConfigurationError

raise ConfigurationError("Invalid configuration")
```

## Document Format

### Standard Document Structure

```python
{
    'id': str,              # Unique identifier
    'title': str,           # Document title
    'content': str,         # Main content
    'metadata': {           # Additional metadata
        'url': str,         # Optional: Document URL
        'author': str,      # Optional: Author
        'created_at': str,  # Optional: ISO datetime
        'updated_at': str,  # Optional: ISO datetime
        'tags': list,       # Optional: Tags
        'source': str,      # Plugin name
        # ... custom fields
    }
}
```

## Configuration Format

### Plugin Configuration Structure

```python
{
    'plugin_name': str,     # Plugin identifier
    'settings': {           # Plugin-specific settings
        'api_key': str,
        'endpoint': str,
        # ... custom settings
    },
    'sync_schedule': str,   # Optional: Cron expression
    'enabled': bool,        # Optional: Enable/disable
}
```

## Logging

### Using Python Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyPlugin(BasePlugin):
    def fetch_documents(self, config):
        logger.info("Fetching documents from %s", config['endpoint'])
        try:
            # ... fetch logic
            logger.debug("Fetched %d documents", len(documents))
        except Exception as e:
            logger.error("Failed to fetch documents: %s", e)
            raise
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Environment Variables

### Accessing Environment Variables

```python
import os

class MyPlugin(BasePlugin):
    def initialize(self):
        self.api_key = os.getenv('MY_PLUGIN_API_KEY')
        self.endpoint = os.getenv('MY_PLUGIN_ENDPOINT', 'https://default.api.com')
```

### Recommended Environment Variables

- `{PLUGIN_NAME}_API_KEY`: API credentials
- `{PLUGIN_NAME}_ENDPOINT`: API endpoint URL
- `{PLUGIN_NAME}_TIMEOUT`: Request timeout (seconds)
- `{PLUGIN_NAME}_RETRY_COUNT`: Number of retries

## Utility Functions

### Common Utilities

```python
# HTTP requests with retry
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_request(url, headers=None):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session.get(url, headers=headers)

# Pagination helper
def paginate_api(endpoint, page_size=100):
    page = 1
    while True:
        response = make_request(f"{endpoint}?page={page}&size={page_size}")
        data = response.json()

        if not data:
            break

        yield from data
        page += 1
```

## Testing Utilities

### Mock Plugin for Testing

```python
from core.plugins.interfaces import KnowledgeSourcePlugin

class MockKnowledgeSource(KnowledgeSourcePlugin):
    def __init__(self, documents=None):
        self._documents = documents or []

    def fetch_documents(self, config):
        return self._documents

# Use in tests
plugin = MockKnowledgeSource(documents=[
    {'id': '1', 'title': 'Test', 'content': 'Content'}
])
```

## Next Steps

- [Plugin System](/docs/en/developers/plugins/plugin-system) - Architecture overview
- [Creating Plugins](/docs/en/developers/plugins/creating-plugins) - Step-by-step guide
- [Plugin Examples](/docs/en/developers/plugins/examples) - Example implementations
