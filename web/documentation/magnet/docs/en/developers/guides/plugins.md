# External Plugins Directory

This directory is for **client-specific** and **proprietary** plugins that should NOT be included in the public repository.

## 🎯 Purpose

External plugins are:

- ✅ Client-specific implementations (File, FluidTopics, etc.)
- ✅ Proprietary integrations with custom systems
- ✅ Customer-specific features or data sources
- ✅ Plugins that require special credentials or licenses

## 📁 Current Directory Structure

```
external/
├── __init__.py                    # ✅ In git (required)
├── README.md                      # ✅ In git (this file)
│
└── knowledge_source/              # Plugin type directory
    └── __init__.py                # ✅ In git (required)
    # Custom client-specific plugins can be added here
    # Example: custom_plugin/      # ❌ NOT in git (client-specific)
```

## 🔄 How External Plugins are Loaded

External plugins are **automatically loaded** from this directory - no configuration needed!

```python
# In core/plugins/registry.py
def load_external_plugins(cls):
    # 1. Auto-scan plugins/external/ directory (local files)
    # 2. Load from MAGNET_PLUGINS env var (installed packages)
```

### Two Loading Methods

#### 1️⃣ Local Directory (Development & Private Deployments)

```bash
# Just place plugin directory here - it loads automatically!
api/src/plugins/external/knowledge_source/custom_plugin/
```

✅ No environment variables needed  
✅ Perfect for development  
✅ Works with .gitignore to keep private

#### 2️⃣ Installed Packages (Production with Separate Repos)

```bash
# Install from private GitHub repo
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0

# Configure environment
export MAGNET_PLUGINS=magnet_plugins.file
```

✅ Complete isolation from main repo  
✅ Version management via git tags  
✅ CI/CD friendly

## 🚀 For Production Deployment

**Recommended:** Use separate private repositories for client-specific plugins.

## 📝 Quick Example

```python
# external/knowledge_source/custom_source.py

from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.base import PluginMetadata
from core.plugins.registry import PluginRegistry
from core.plugins.plugin_types import PluginType

class CustomSourcePlugin(KnowledgeSourcePlugin):
    def __init__(self):
        super().__init__(
            metadata=PluginMetadata(
                name="Custom Source",
                version="1.0.0",
                author="Your Company",
                description="Client-specific custom data source"
            )
        )

    @property
    def source_type(self) -> str:
        return "CustomSource"

    async def create_processor(self, source, collection_config, store):
        # Your implementation
        pass

# Auto-register
PluginRegistry.register(PluginType.KNOWLEDGE_SOURCE, CustomSourcePlugin())
```

## 🔒 Before Publishing to GitHub

Make sure your `.gitignore` excludes external plugins:

```bash
# Check what will be committed
git status
git ls-files src/plugins/external/

# Should only show __init__.py files!
```

## 💡 Development Workflow

```bash
# 1. Develop locally
echo "# plugin code" > external/knowledge_source/my_plugin.py

# 2. Test locally (auto-loaded, no env vars needed)
python run.py

# 3. When ready to deploy:
#    Option A: Keep in external/ with .gitignore
#    Option B: Move to separate private repo

# 4. For production, use separate repos (recommended)
```
