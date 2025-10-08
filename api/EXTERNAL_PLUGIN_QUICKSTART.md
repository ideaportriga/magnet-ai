# Creating External Plugin Packages - Quick Start

## Step-by-Step Guide

### 1. Create Plugin Repository

```bash
# Create new repository
mkdir magnet-plugins-file
cd magnet-plugins-file
git init

# Create structure
mkdir -p magnet_plugins
touch magnet_plugins/__init__.py
touch setup.py
touch pyproject.toml
touch README.md
```

### 2. Copy Plugin Code

```bash
# Copy your plugin from the main repo
cp ../magnet-ai/api/src/plugins/external/knowledge_source/file.py magnet_plugins/
```

### 3. Create setup.py

```python
from setuptools import setup, find_packages

setup(
    name="magnet-plugins-file",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        # Core dependencies only if needed
        # Usually empty since magnet-ai is already installed
    ],
)
```

### 4. Create magnet_plugins/__init__.py

```python
"""Magnet AI External Plugins - File"""

from magnet_plugins.file import FileUrlPlugin

__version__ = "1.0.0"
__all__ = ["FileUrlPlugin"]
```

### 5. Commit and Push

```bash
git add .
git commit -m "Initial commit - File URL plugin"

# Push to GitHub (private repo)
git remote add origin https://github.com/your-org/magnet-plugins-file.git
git push -u origin main

# Tag version
git tag v1.0.0
git push origin v1.0.0
```

### 6. Install in Main Project

```bash
# In your main magnet-ai project
cd /path/to/magnet-ai/api

# Install from GitHub
pip install git+https://github.com/your-org/magnet-plugins-file.git

# Or install specific version
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
```

### 7. Configure Environment

```bash
# Add to .env
MAGNET_PLUGINS=magnet_plugins.file

# Or for multiple plugins
MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
```

### 8. Test

```python
# In Python shell or test script
from core.plugins.registry import PluginRegistry
from core.plugins.plugin_types import PluginType

# Load plugins
PluginRegistry.auto_load()

# Check if loaded
plugins = PluginRegistry.list_available(PluginType.KNOWLEDGE_SOURCE)
print(plugins)  # Should include 'File'

# Get plugin
plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, "File")
print(plugin.metadata)
```

## Quick Install Commands

### From GitHub (Recommended)

```bash
# Latest version
pip install git+https://github.com/your-org/magnet-plugins-file.git

# Specific tag
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0

# Specific branch
pip install git+https://github.com/your-org/magnet-plugins-file.git@develop

# With SSH (if configured)
pip install git+ssh://git@github.com/your-org/magnet-plugins-file.git
```

### From Private PyPI

```bash
# One-time
pip install magnet-plugins-file --index-url https://your-pypi.com/simple

# Or configure permanently in pip.conf
```

### In requirements.txt

```txt
# From GitHub
git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0

# Or from PyPI
magnet-plugins-file==1.0.0
magnet-plugins-fluidtopics==1.0.0
```

## Directory Structure Comparison

### Before (in main repo)

```
magnet-ai/
└── api/
    └── src/
        └── plugins/
            └── external/
                └── knowledge_source/
                    ├── file.py
                    └── fluidtopics.py
```

### After (separate repos)

```
magnet-plugins-file/          # Private repo 1
├── setup.py
├── pyproject.toml
└── magnet_plugins/
    ├── __init__.py
    └── file.py

magnet-plugins-fluidtopics/   # Private repo 2
├── setup.py
├── pyproject.toml
└── magnet_plugins/
    ├── __init__.py
    └── fluidtopics.py

magnet-ai/                     # Main repo (public)
└── api/
    └── src/
        └── plugins/
            ├── builtin/      # Public plugins
            └── external/     # Empty or removed
```

## Environment Variable Patterns

```bash
# Single plugin
MAGNET_PLUGINS=magnet_plugins.file

# Multiple plugins (comma-separated)
MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

# Mix of external packages and local plugins
MAGNET_PLUGINS=magnet_plugins.file,plugins.custom.local_plugin

# Empty = only builtin plugins
MAGNET_PLUGINS=
```

## Troubleshooting

### Plugin not loading

```bash
# Check if installed
pip list | grep magnet-plugins

# Check import path
python -c "import magnet_plugins.file; print(magnet_plugins.file.__file__)"

# Check registration
python -c "
from core.plugins.registry import PluginRegistry
PluginRegistry.auto_load()
print(PluginRegistry.list_available())
"
```

### Import errors

```bash
# Ensure main app is installed
pip install -e /path/to/magnet-ai/api

# Reinstall plugin
pip uninstall magnet-plugins-file
pip install git+https://github.com/your-org/magnet-plugins-file.git
```

## Best Practices

1. **Versioning**: Use semantic versioning (v1.0.0, v1.1.0, etc.)
2. **Tags**: Tag releases in git for reproducible installs
3. **Documentation**: Include README with usage examples
4. **Testing**: Test plugin independently before integrating
5. **Dependencies**: Keep external dependencies minimal
6. **Security**: Use private repositories for client-specific code

## See Also

- [EXTERNAL_PLUGIN_PACKAGING.md](./EXTERNAL_PLUGIN_PACKAGING.md) - Detailed packaging guide
- [PLUGIN_SYSTEM.md](./PLUGIN_SYSTEM.md) - Plugin system overview
- [EXTERNAL_PLUGIN_EXAMPLE.md](./EXTERNAL_PLUGIN_EXAMPLE.md) - Package structure example
