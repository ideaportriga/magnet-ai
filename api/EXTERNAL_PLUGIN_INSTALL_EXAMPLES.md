# External Plugin Installation Examples

## Quick Examples

### Install File Plugin from GitHub

```bash
# Latest version
pip install git+https://github.com/your-org/magnet-plugins-file.git

# Specific version
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0

# Configure
export MAGNET_PLUGINS=magnet_plugins.file
```

### Install Multiple Plugins

```bash
# Install both plugins
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
pip install git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0

# Configure
export MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
```

### Using requirements.txt

```txt
# requirements.txt

# Core application
-e ./api

# External plugins from GitHub
git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0
```

```bash
pip install -r requirements.txt
```

### Docker Example

```dockerfile
FROM python:3.12

WORKDIR /app

# Copy and install core
COPY api/ /app/api/
RUN pip install -e /app/api

# Install external plugins
RUN pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
RUN pip install git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0

# Set environment
ENV MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

CMD ["python", "api/run.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
      - DATABASE_URL=postgresql://...
    ports:
      - "5000:5000"
```

### With Build Arguments (Conditional Install)

```dockerfile
FROM python:3.12

WORKDIR /app

COPY api/ /app/api/
RUN pip install -e /app/api

# Conditional plugin installation
ARG INSTALL_FILE_PLUGIN=false
ARG INSTALL_FLUIDTOPICS_PLUGIN=false

RUN if [ "$INSTALL_FILE_PLUGIN" = "true" ]; then \
    pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0; \
    fi

RUN if [ "$INSTALL_FLUIDTOPICS_PLUGIN" = "true" ]; then \
    pip install git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0; \
    fi

ENV MAGNET_PLUGINS=${MAGNET_PLUGINS}

CMD ["python", "api/run.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      args:
        INSTALL_FILE_PLUGIN: "true"
        INSTALL_FLUIDTOPICS_PLUGIN: "true"
    environment:
      - MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
```

## Verification

### Check Installed Plugins

```bash
# List installed packages
pip list | grep magnet-plugins

# Check plugin registration
python -c "
from core.plugins.registry import PluginRegistry
from core.plugins.plugin_types import PluginType

PluginRegistry.auto_load()
available = PluginRegistry.list_available(PluginType.KNOWLEDGE_SOURCE)
print('Available plugins:', available)
"
```

### Test Plugin

```python
from core.plugins.registry import PluginRegistry
from core.plugins.plugin_types import PluginType

# Load all plugins
PluginRegistry.auto_load()

# Get specific plugin
plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, "File")

if plugin:
    print(f"✅ Plugin loaded: {plugin.metadata.name}")
    print(f"   Version: {plugin.metadata.version}")
    print(f"   Author: {plugin.metadata.author}")
else:
    print("❌ Plugin not found")
```

## Environment Variables

### Basic Configuration

```bash
# Single plugin
export MAGNET_PLUGINS=magnet_plugins.file

# Multiple plugins
export MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

# No external plugins (builtin only)
export MAGNET_PLUGINS=
```

### In .env File

```bash
# .env

# External plugins to load
MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

# Other config...
DATABASE_URL=postgresql://...
```

## Common Patterns

### Development Setup

```bash
# Clone main repo
git clone https://github.com/your-org/magnet-ai.git
cd magnet-ai/api

# Install core in editable mode
pip install -e .

# Install external plugins from GitHub
pip install git+https://github.com/your-org/magnet-plugins-file.git
pip install git+https://github.com/your-org/magnet-plugins-fluidtopics.git

# Configure
export MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

# Run
python run.py
```

### Production Setup

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Set environment
export MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e ./api
          pip install git+https://${{ secrets.GH_TOKEN }}@github.com/your-org/magnet-plugins-file.git@v1.0.0
          pip install git+https://${{ secrets.GH_TOKEN }}@github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0
      
      - name: Deploy
        env:
          MAGNET_PLUGINS: magnet_plugins.file,magnet_plugins.fluidtopics
        run: |
          # Your deployment script
```

## Troubleshooting

### Plugin not loading

```bash
# Check environment variable
echo $MAGNET_PLUGINS

# Verify package installed
pip show magnet-plugins-file

# Check import
python -c "import magnet_plugins.file"

# Check registration
python -c "
from core.plugins.registry import PluginRegistry
PluginRegistry.load_external_plugins()
print(PluginRegistry.list_available())
"
```

### Version conflicts

```bash
# Uninstall and reinstall
pip uninstall magnet-plugins-file
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.1.0

# Check version
pip show magnet-plugins-file
```

## Documentation Links

- **[EXTERNAL_PLUGIN_QUICKSTART.md](./EXTERNAL_PLUGIN_QUICKSTART.md)** - Quick start guide
- **[EXTERNAL_PLUGIN_PACKAGING.md](./EXTERNAL_PLUGIN_PACKAGING.md)** - Detailed packaging guide
- **[PLUGIN_SYSTEM.md](./PLUGIN_SYSTEM.md)** - Plugin system overview
