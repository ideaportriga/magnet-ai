# Knowledge Source Plugin Consolidation

## Summary

All knowledge source plugins have been consolidated into the `builtin` directory. The `external` directory is now reserved for future client-specific plugins.

## Changes Made

### 1. Plugin Migration

**Moved from external to builtin:**
- `src/plugins/external/knowledge_source/file/` → `src/plugins/builtin/knowledge_source/file/`
- `src/plugins/external/knowledge_source/fluidtopics/` → `src/plugins/builtin/knowledge_source/fluidtopics/`

**Result:** All 9 knowledge source plugins are now in `builtin`:
1. Confluence
2. File (moved)
3. Fluid Topics (moved)
4. HubSpot
5. Oracle Knowledge
6. RightNow
7. Salesforce
8. SharePoint Documents
9. SharePoint Pages

### 2. Updated Plugin Registry

Updated `src/plugins/builtin/knowledge_source/__init__.py` to include the new plugins:
- Added `file` import
- Added `fluidtopics` import
- Updated `__all__` list

### 3. Documentation Updates

Updated the following documentation files:
- `PLUGIN_SYSTEM.md` - Updated plugin listings
- `MIGRATION_TO_PLUGINS.md` - Updated plugin organization
- `PLUGIN_SYSTEM_SUMMARY.md` - Updated metrics and examples
- `src/plugins/external/README.md` - Updated examples to show empty directory

## Plugin System Architecture

### How Plugins Work

1. **Auto-Registration**: Each plugin directory contains an `__init__.py` that registers the plugin:
   ```python
   from core.plugins.registry import PluginRegistry
   from .plugin import PluginClass
   
   PluginRegistry.register(PluginClass())
   ```

2. **Auto-Loading**: The system loads plugins via `PluginRegistry.auto_load()` in `routes/admin/knowledge_sources.py`:
   - Scans `src/plugins/builtin/knowledge_source/` directory
   - Scans `src/plugins/external/knowledge_source/` directory
   - Imports each plugin module, triggering registration

3. **Plugin Usage**: Plugins are retrieved by source_type:
   ```python
   plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, source_type)
   processor = await plugin.create_processor(source, collection_config, store)
   ```

### Plugin Structure

Each plugin follows this structure:
```
plugin_name/
├── __init__.py          # Auto-registration
├── plugin.py            # Plugin definition with metadata
└── processor.py         # Data processor (optional, some use shared processors)
```

### Source Types

Each plugin defines a unique `source_type` that matches the collection metadata:
- **Confluence**: `"Confluence"`
- **File**: `"File"`
- **Fluid Topics**: `"Fluid Topics"`
- **HubSpot**: `"Hubspot"`
- **Oracle Knowledge**: `"Oracle Knowledge"`
- **RightNow**: `"RightNow"`
- **Salesforce**: `"Salesforce"`
- **SharePoint**: `"Sharepoint"`
- **SharePoint Pages**: `"Sharepoint Pages"`

## External Directory

The `external` directory is now empty but available for future use:
- Reserved for client-specific plugins
- Plugins placed here will be auto-loaded
- Should be excluded from git via `.gitignore`

## Verification

All plugins follow the same pattern and are properly integrated:
- ✅ All plugins have `__init__.py` with auto-registration
- ✅ All plugins have `plugin.py` with metadata and `create_processor()`
- ✅ All plugins define unique `source_type`
- ✅ All plugins are imported in `builtin/knowledge_source/__init__.py`
- ✅ System uses `PluginRegistry.auto_load()` in routes
- ✅ Documentation updated to reflect new structure

## Benefits of Consolidation

1. **Simpler Structure**: All standard plugins in one place
2. **Consistent Pattern**: All plugins follow the same structure
3. **Clear Separation**: Built-in vs client-specific is now explicit
4. **Easier Maintenance**: All standard plugins together
5. **Better Documentation**: Clear examples of plugin structure

## Next Steps

When client-specific plugins are needed:
1. Create plugin directory in `src/plugins/external/knowledge_source/`
2. Follow the same structure as builtin plugins
3. Plugin will be auto-loaded without configuration
4. Ensure `.gitignore` excludes the plugin from commits
