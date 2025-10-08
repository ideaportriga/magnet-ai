# Plugin Directory Structure

## Complete Structure

```
api/src/
├── core/
│   └── plugins/                    # Core plugin infrastructure
│       ├── __init__.py
│       ├── base.py                 # BasePlugin, PluginMetadata
│       ├── plugin_types.py         # PluginType enum
│       ├── interfaces.py           # Type-specific interfaces
│       └── registry.py             # PluginRegistry
│
└── plugins/
    ├── builtin/                    # PUBLIC - Shipped with core
    │   ├── knowledge_source/       # Knowledge source plugins
    │   │   ├── __init__.py
    │   │   ├── sharepoint.py
    │   │   ├── sharepoint_pages.py
    │   │   ├── confluence.py
    │   │   ├── file.py
    │   │   └── fluidtopics.py
    │   │
    │   ├── llm_provider/           # Future: LLM providers
    │   │   └── __init__.py
    │   │
    │   ├── authentication/         # Future: Auth methods
    │   │   └── __init__.py
    │   │
    │   └── storage_backend/        # Future: Storage backends
    │       └── __init__.py
    │
    └── external/                   # PRIVATE - Client-specific
        ├── __init__.py
        ├── README.md               # Warning about client code
        │
        ├── knowledge_source/       # Client knowledge sources
        │   ├── __init__.py
        │   ├── salesforce.py       # CLIENT-SPECIFIC
        │   ├── oracle_knowledge.py # CLIENT-SPECIFIC
        │   ├── rightnow.py         # CLIENT-SPECIFIC
        │   └── hubspot.py          # CLIENT-SPECIFIC
        │
        ├── llm_provider/           # Future: Client LLM providers
        │   └── __init__.py
        │
        ├── authentication/         # Future: Client auth methods
        │   └── __init__.py
        │
        └── storage_backend/        # Future: Client storage
            └── __init__.py
```

## Design Principles

### 1. Consistent Structure
Both `builtin/` and `external/` follow the same organization:
- Organized by plugin type (knowledge_source, llm_provider, etc.)
- Each type has its own subdirectory
- Each subdirectory has an `__init__.py`

### 2. Clear Separation
- **builtin/** = Public, shipped with Magnet AI
- **external/** = Private, client-specific code

### 3. Scalability
Ready to add new plugin types:
- Just create a new subdirectory under both builtin/ and external/
- Add interface to `core/plugins/interfaces.py`
- Plugins auto-load from the new directory

### 4. Git-Friendly
Simple `.gitignore` pattern excludes all external plugins:
```gitignore
src/plugins/external/*/
!src/plugins/external/*/__init__.py
!src/plugins/external/README.md
```

## Loading Behavior

### Built-in Plugins
Automatically loaded from `src/plugins/builtin/<type>/`:
```python
PluginRegistry.load_builtin_plugins()  # Loads all types
# or
PluginRegistry.load_builtin_plugins(PluginType.KNOWLEDGE_SOURCE)  # Specific type
```

### External Plugins
Loaded via environment variable `MAGNET_PLUGINS`:
```bash
# Load specific modules
export MAGNET_PLUGINS=plugins.external.knowledge_source.salesforce

# Load multiple
export MAGNET_PLUGINS=plugins.external.knowledge_source.salesforce,plugins.external.knowledge_source.oracle_knowledge
```

Or installed as separate packages:
```bash
pip install magnet-plugins-salesforce
export MAGNET_PLUGINS=magnet_plugins.salesforce
```

## Benefits

✅ **Consistent**: Same structure for builtin and external  
✅ **Organized**: Grouped by plugin type  
✅ **Scalable**: Easy to add new plugin types  
✅ **Maintainable**: Clear separation of concerns  
✅ **Git-friendly**: Simple exclude patterns  
✅ **Future-proof**: Ready for expansion  

## Migration from Old Structure

If you have plugins in the old flat structure (`external/*.py`), move them:

```bash
cd src/plugins/external
mkdir -p knowledge_source
mv salesforce.py oracle_knowledge.py rightnow.py hubspot.py knowledge_source/
```

Update environment variable:
```bash
# Old
export MAGNET_PLUGINS=plugins.external.salesforce

# New
export MAGNET_PLUGINS=plugins.external.knowledge_source.salesforce
```
