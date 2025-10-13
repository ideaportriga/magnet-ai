# Plugin System

Magnet AI now uses a flexible plugin architecture for knowledge sources and other extensible components.

## Architecture

### Core Components

- **`core/plugins/base.py`**: Base plugin interface
- **`core/plugins/plugin_types.py`**: Plugin type enumeration
- **`core/plugins/interfaces.py`**: Specialized plugin interfaces
- **`core/plugins/registry.py`**: Universal plugin registry

### Plugin Types

Currently supported:
- **Knowledge Source Plugins**: Data source integrations (SharePoint, Confluence, etc.)

Future support planned:
- LLM Provider Plugins
- Authentication Plugins
- Storage Backend Plugins
- Embedding Model Plugins
- Tool Plugins

## Built-in vs External Plugins

### Built-in Plugins (Public Repository)

Located in `src/plugins/builtin/knowledge_source/`:
- **SharePoint Documents** (`sharepoint/`)
- **SharePoint Pages** (`sharepoint_pages/`)
- **Confluence** (`confluence/`)
- **Salesforce** (`salesforce/`)
- **Oracle Knowledge** (`oracle_knowledge/`)
- **RightNow** (`rightnow/`)
- **HubSpot** (`hubspot/`)
- **File URL** (`file/`)
- **Fluid Topics** (`fluidtopics/`)

These plugins are included in the public GitHub repository.

### External Plugins (Private Repository)

Located in `src/plugins/external/knowledge_source/`:

This directory is reserved for client-specific and proprietary plugins that should NOT be included in the public repository.

**Note**: External plugins follow the same structure as built-in plugins, organized by type in subdirectories.

## Using External Plugins

### Option 1: Keep in Repository (Development)

For development, you can keep external plugins in `src/plugins/external/`. They will be auto-loaded.

### Option 2: Install as Package from GitHub (Production - Recommended)

1. **Create a separate repository** for the plugin (see [EXTERNAL_PLUGIN_QUICKSTART.md](./EXTERNAL_PLUGIN_QUICKSTART.md))

2. **Install the plugin**:
   ```bash
   # Install latest version
   pip install git+https://github.com/your-org/magnet-plugins-file.git
   
   # Install specific version
   pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
   ```

3. **Configure in environment**:
   ```bash
   export MAGNET_PLUGINS=magnet_plugins.file
   ```

### Option 3: Install from Private PyPI

1. **Publish to private PyPI** (Azure Artifacts, JFrog, etc.)

2. **Install**:
   ```bash
   pip install magnet-plugins-file --index-url https://your-private-pypi.com/simple
   ```

3. **Configure**:
   ```bash
   export MAGNET_PLUGINS=magnet_plugins.file
   ```

### Option 4: Install Multiple Plugins

```bash
# In requirements.txt
git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0

# In .env
MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
```

## Creating a New Plugin

### 1. Create Plugin Class

```python
# my_plugin.py
from typing import Any, Dict
from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from core.plugins.registry import PluginRegistry
from data_sync.data_processor import DataProcessor

class MyCustomPlugin(KnowledgeSourcePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="My Custom Source",
            version="1.0.0",
            author="Your Name",
            description="Description of your plugin",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=["required-package"],
            config_schema={
                "type": "object",
                "properties": {
                    "custom_url": {"type": "string"},
                },
                "required": ["custom_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "MyCustomSource"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        # Your implementation here
        pass

# Auto-register
PluginRegistry.register(MyCustomPlugin())
```

### 2. Register Plugin

Plugins are automatically registered when their module is imported. The registry will load:
- All modules in `src/plugins/builtin/<plugin_type>/`
- Modules specified in `MAGNET_PLUGINS` environment variable

## Configuration

### Environment Variables

```bash
# Load external plugins
export MAGNET_PLUGINS=magnet_plugins.salesforce,magnet_plugins.oracle_knowledge

# Or in .env file
MAGNET_PLUGINS=magnet_plugins.salesforce,magnet_plugins.oracle_knowledge
```

## .gitignore Configuration

To exclude client-specific plugins from the public repository:

```gitignore
# Exclude external plugins by type
src/plugins/external/*/
!src/plugins/external/*/__init__.py
!src/plugins/external/README.md
```

This pattern:
- Excludes all subdirectories in `external/` (knowledge_source/, llm_provider/, etc.)
- Keeps `__init__.py` files for proper Python package structure
- Keeps the README for documentation

## Migration from Old System

The old `sync_collection_standalone` function with `match/case` has been replaced with a plugin-based system.

**Before**:
```python
match source_type:
    case "Sharepoint":
        # 50 lines of code
    case "Confluence":
        # 30 lines of code
    # ... many more cases
```

**After**:
```python
plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, source_type)
processor = await plugin.create_processor(source, collection_config, store)
await Synchronizer(processor, store).sync(collection_id)
```

## Benefits

1. **Separation of Concerns**: Each plugin is self-contained
2. **Easy to Extend**: Add new sources without modifying core code
3. **Public/Private Split**: Keep client-specific code in private repos
4. **Dynamic Loading**: Load only needed plugins
5. **Better Testing**: Test each plugin independently
6. **Versioning**: Version plugins separately from core

## Future Extensions

The plugin system is designed to support additional plugin types:

- **LLM Providers**: OpenAI, Anthropic, Azure OpenAI
- **Authentication**: OAuth, SAML, LDAP
- **Storage Backends**: PostgreSQL, MongoDB, Pinecone
- **Embedding Models**: OpenAI, Cohere, local models
- **Notification**: Email, Slack, Teams
- **Tools**: Custom AI agent tools
