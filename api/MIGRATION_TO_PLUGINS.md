# Migration Guide: Plugin System

## ✅ What Has Been Implemented

The Magnet AI codebase now in2. **Test an external plugin** (e.g., Salesforce):
   - Set environment: `export MAGNET_PLUGINS=plugins.external.knowledge_source.salesforce`
   - Create a collection with `source_type: "Salesforce"`des a universal plugin system that supports multiple plugin types, starting with Knowledge Source plugins.

### Created Files

#### Core Plugin Infrastructure
- `src/core/plugins/__init__.py` - Plugin system entry point
- `src/core/plugins/base.py` - Base plugin interface (`BasePlugin`, `PluginMetadata`)
- `src/core/plugins/plugin_types.py` - Plugin type enumeration (`PluginType`)
- `src/core/plugins/interfaces.py` - Specialized interfaces (`KnowledgeSourcePlugin`)
- `src/core/plugins/registry.py` - Universal plugin registry (`PluginRegistry`)

#### Built-in Plugins (Public Repository)
- `src/plugins/builtin/knowledge_source/sharepoint/` - SharePoint Documents
- `src/plugins/builtin/knowledge_source/sharepoint_pages/` - SharePoint Pages
- `src/plugins/builtin/knowledge_source/confluence/` - Confluence
- `src/plugins/builtin/knowledge_source/salesforce/` - Salesforce
- `src/plugins/builtin/knowledge_source/oracle_knowledge/` - Oracle Knowledge
- `src/plugins/builtin/knowledge_source/rightnow/` - RightNow
- `src/plugins/builtin/knowledge_source/hubspot/` - HubSpot
- `src/plugins/builtin/knowledge_source/file/` - File URL
- `src/plugins/builtin/knowledge_source/fluidtopics/` - Fluid Topics

**Note**: All knowledge source plugins are now built-in and organized in subdirectories with proper structure.

#### External Plugin Directory (For Future Client-Specific Plugins)
- `src/plugins/external/knowledge_source/` - Reserved for client-specific plugins

**Note**: External plugins directory is now empty but available for future client-specific implementations.

#### Updated Code
- `src/routes/admin/knowledge_sources.py` - Refactored to use plugin system

#### Documentation
- `PLUGIN_SYSTEM.md` - Complete plugin system documentation
- `EXTERNAL_PLUGIN_EXAMPLE.md` - Guide for creating external plugin packages
- `src/plugins/external/README.md` - Warning about external plugins
- `.gitignore.plugins` - Template for excluding external plugins
- `.env.example` - Updated with `MAGNET_PLUGINS` configuration

## 🔄 What Changed

### Before (Old System)
```python
async def sync_collection_standalone(collection_id: str, **kwargs) -> None:
    source_type = source.get("source_type")
    
    match source_type:
        case CollectionSource.SHAREPOINT:
            # 40+ lines of SharePoint-specific code
        case CollectionSource.CONFLUENCE:
            # 30+ lines of Confluence-specific code
        case CollectionSource.SALESFORCE:
            # 30+ lines of Salesforce-specific code
        # ... 6 more cases (200+ lines total)
        case _:
            raise ClientException("Sync is not supported")
```

### After (Plugin System)
```python
# Load plugins once at module import
PluginRegistry.auto_load()

async def sync_collection_standalone(collection_id: str, **kwargs) -> None:
    source_type = source.get("source_type")
    
    # Get plugin from registry
    plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, source_type)
    
    if not plugin:
        raise ClientException(f"Unknown source type: {source_type}")
    
    # Create processor and sync
    processor = await plugin.create_processor(source, collection_config, store)
    await Synchronizer(processor, store).sync(collection_id)
```

**Result**: 200+ lines of code → ~15 lines of code

## 📋 Next Steps: Preparing for GitHub

### Step 1: Test the Plugin System

1. **Run the application**:
   ```bash
   cd api
   python run.py
   ```

2. **Test a built-in plugin** (e.g., SharePoint):
   - Create a collection with `source_type: "Sharepoint"`
   - Trigger sync
   - Verify it works

3. **Test an external plugin** (e.g., Salesforce):
   - Set environment: `export MAGNET_PLUGINS=plugins.external.salesforce`
   - Create a collection with `source_type: "Salesforce"`
   - Trigger sync
   - Verify it works

### Step 2: Move External Plugins to Private Repository

#### Option A: Keep in Main Repo for Now (Development)
If you want to keep everything together during development:

1. **Update .gitignore**:
   ```bash
   # Add to api/.gitignore
   # External plugins (client-specific) - organized by type
   # Uncomment these lines before publishing to public GitHub
   # src/plugins/external/*/
   # !src/plugins/external/*/__init__.py
   # !src/plugins/external/README.md
   ```

2. **Continue development** with all plugins in one place

#### Option B: Separate Immediately (Production)
If you're ready to split now:

1. **Create private repository** for each client plugin:
   ```bash
   # Example: Salesforce plugin
   mkdir magnet-plugins-salesforce
   cd magnet-plugins-salesforce
   
   # Copy plugin file
   cp ../magnet-ai/api/src/plugins/external/knowledge_source/salesforce.py .
   
   # Create package structure (see EXTERNAL_PLUGIN_EXAMPLE.md)
   ```

2. **Update .gitignore** in main repo:
   ```bash
   # Add to api/.gitignore
   src/plugins/external/*/
   !src/plugins/external/*/__init__.py
   !src/plugins/external/README.md
   ```

3. **Install external plugins**:
   ```bash
   pip install git+https://github.com/your-org/magnet-plugins-salesforce.git
   ```

4. **Configure environment**:
   ```bash
   export MAGNET_PLUGINS=magnet_plugins.salesforce,magnet_plugins.oracle_knowledge
   ```

### Step 3: Update Documentation

1. **Main README.md** - Add section about plugin system
2. **CONTRIBUTING.md** - Guidelines for creating plugins
3. **Release notes** - Document the migration

### Step 4: Publish to GitHub

1. **Review files to exclude**:
   ```bash
   # Check what will be committed
   git status
   
   # Ensure external plugins are excluded
   git check-ignore src/plugins/external/salesforce.py
   ```

2. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: Implement universal plugin system for knowledge sources"
   git push origin main
   ```

## 🎯 Benefits of This Architecture

### 1. **Separation of Public and Private Code**
- ✅ Built-in plugins in public GitHub repository
- ✅ Client-specific plugins in private repositories
- ✅ No sensitive client code in public repo

### 2. **Extensibility**
- ✅ Add new plugin types easily (LLM, Auth, Storage, etc.)
- ✅ Each plugin is self-contained and independent
- ✅ No need to modify core code for new sources

### 3. **Maintainability**
- ✅ 200+ lines of match/case → 15 lines
- ✅ Each plugin has clear responsibility
- ✅ Easier to test and debug

### 4. **Flexibility**
- ✅ Load only needed plugins
- ✅ Version plugins independently
- ✅ Hot-swap implementations

### 5. **Developer Experience**
- ✅ Clear plugin interface to implement
- ✅ Auto-registration (no manual wiring)
- ✅ Helpful error messages

## 📚 Documentation References

- **[PLUGIN_SYSTEM.md](./PLUGIN_SYSTEM.md)** - Complete guide to the plugin system
- **[EXTERNAL_PLUGIN_EXAMPLE.md](./EXTERNAL_PLUGIN_EXAMPLE.md)** - How to create external packages
- **[src/plugins/external/README.md](./src/plugins/external/README.md)** - Important warnings about external plugins

## 🔧 Troubleshooting

### Plugin Not Found
**Error**: `Unknown knowledge source type: 'Salesforce'`

**Solution**:
1. Check if plugin is installed: `pip list | grep magnet-plugins`
2. Check environment: `echo $MAGNET_PLUGINS`
3. Verify plugin registration in logs

### Import Errors
**Error**: `ImportError: cannot import name 'PluginRegistry'`

**Solution**:
1. Ensure you're in the correct directory
2. Reinstall: `pip install -e .`
3. Check Python path

### Plugin Not Loading
**Error**: Plugin installed but not appearing

**Solution**:
1. Check plugin auto-registration: Look for `PluginRegistry.register()` at end of file
2. Verify module is imported: Add to `MAGNET_PLUGINS`
3. Check logs for import errors

## 🚀 Future Enhancements

The plugin system is ready to support:
- **LLM Provider Plugins** (OpenAI, Anthropic, Azure OpenAI)
- **Authentication Plugins** (OAuth, SAML, LDAP)
- **Storage Backend Plugins** (PostgreSQL, MongoDB, Pinecone)
- **Embedding Model Plugins** (OpenAI, Cohere, local models)
- **Notification Plugins** (Email, Slack, Teams)
- **Tool Plugins** (for AI agents)

Just add the interface to `core/plugins/interfaces.py` and start creating plugins!

## ✅ Checklist for Going Live

- [ ] Test all built-in plugins
- [ ] Test external plugin loading
- [ ] Move client-specific plugins to private repos (or exclude from git)
- [ ] Update .gitignore
- [ ] Update main README.md
- [ ] Create CHANGELOG entry
- [ ] Review all documentation
- [ ] Run full test suite
- [ ] Deploy to staging
- [ ] Verify in production

## 🤝 Need Help?

Refer to:
1. **[PLUGIN_SYSTEM.md](./PLUGIN_SYSTEM.md)** for architecture details
2. **[EXTERNAL_PLUGIN_EXAMPLE.md](./EXTERNAL_PLUGIN_EXAMPLE.md)** for packaging guide
3. Existing plugin implementations in `src/plugins/builtin/knowledge_source/`
