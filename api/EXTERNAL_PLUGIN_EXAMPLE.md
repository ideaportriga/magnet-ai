# Example: External Plugin Package

This example shows how to create an external plugin package for client-specific knowledge sources.

## Directory Structure

```
magnet-plugins-salesforce/
├── README.md
├── setup.py
├── pyproject.toml
└── magnet_plugins/
    ├── __init__.py
    └── salesforce.py
```

## Files

### setup.py
```python
from setuptools import setup, find_packages

setup(
    name="magnet-plugins-salesforce",
    version="1.0.0",
    description="Salesforce plugin for Magnet AI",
    author="Your Company",
    packages=find_packages(),
    install_requires=[
        "magnet-ai>=1.0.0",
        "simple-salesforce>=1.12.0",
    ],
    python_requires=">=3.12",
)
```

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "magnet-plugins-salesforce"
version = "1.0.0"
description = "Salesforce plugin for Magnet AI"
requires-python = ">=3.12"
dependencies = [
    "magnet-ai>=1.0.0",
    "simple-salesforce>=1.12.0",
]
```

### magnet_plugins/__init__.py
```python
"""Magnet AI External Plugins"""

from magnet_plugins.salesforce import SalesforcePlugin

__all__ = ["SalesforcePlugin"]
```

### magnet_plugins/salesforce.py
Copy from `api/src/plugins/external/salesforce.py` and ensure the auto-registration line is active.

## Installation

### Development Mode
```bash
cd magnet-plugins-salesforce
pip install -e .
```

### Production
```bash
pip install git+https://github.com/your-org/magnet-plugins-salesforce.git
```

### From PyPI (if published privately)
```bash
pip install magnet-plugins-salesforce --index-url https://your-private-pypi.com/simple
```

## Configuration

### Option 1: Auto-load (if installed)
The plugin will auto-load if it's in a standard location.

### Option 2: Explicit Load
```bash
export MAGNET_PLUGINS=magnet_plugins.salesforce
```

### Option 3: Multiple Plugins
```bash
export MAGNET_PLUGINS=magnet_plugins.salesforce,magnet_plugins.oracle_knowledge,magnet_plugins.rightnow
```

## Docker Integration

### Dockerfile
```dockerfile
FROM python:3.12

WORKDIR /app

# Install core application
COPY api/ /app/api/
RUN pip install -e /app/api

# Install client-specific plugins
ARG INSTALL_CLIENT_PLUGINS=true
RUN if [ "$INSTALL_CLIENT_PLUGINS" = "true" ]; then \
    pip install git+https://github.com/your-org/magnet-plugins-salesforce.git; \
    pip install git+https://github.com/your-org/magnet-plugins-oracle.git; \
    fi
```

### docker-compose.yml
```yaml
services:
  api:
    build:
      context: .
      args:
        INSTALL_CLIENT_PLUGINS: "true"
    environment:
      MAGNET_PLUGINS: "magnet_plugins.salesforce,magnet_plugins.oracle_knowledge"
```

## Repository Structure

### Public Repository (GitHub)
```
magnet-ai/
├── api/
│   └── src/
│       ├── core/plugins/
│       └── plugins/builtin/
└── README.md
```

### Private Repositories
```
magnet-plugins-salesforce/      # Private repo 1
magnet-plugins-oracle/          # Private repo 2
magnet-plugins-rightnow/        # Private repo 3
magnet-plugins-client-custom/   # Private repo 4
```

## Benefits

- ✅ Public repository stays clean
- ✅ Client-specific code in private repos
- ✅ Independent versioning
- ✅ Easy to install/uninstall
- ✅ Can be shared across projects
- ✅ Better access control
