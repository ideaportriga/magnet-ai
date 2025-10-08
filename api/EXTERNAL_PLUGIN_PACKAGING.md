# External Plugin Package Example: File URL Plugin

This example shows how to package the File URL plugin as a standalone installable package.

## Project Structure

```
magnet-plugins-file/
├── README.md
├── setup.py
├── pyproject.toml
├── LICENSE
└── magnet_plugins/
    ├── __init__.py
    └── file.py
```

## Files

### setup.py

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="magnet-plugins-file",
    version="1.0.0",
    author="Your Company",
    author_email="your.email@company.com",
    description="File URL plugin for Magnet AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/magnet-plugins-file",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        # Core dependency - adjust version as needed
        # If installing from PyPI:
        # "magnet-ai>=1.0.0",
        # Or if installing from git:
        # Leave empty and install magnet-ai separately
    ],
)
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "magnet-plugins-file"
version = "1.0.0"
description = "File URL plugin for Magnet AI"
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [
    {name = "Your Company", email = "your.email@company.com"}
]
keywords = ["magnet-ai", "plugin", "knowledge-source"]

dependencies = []

[project.urls]
Homepage = "https://github.com/your-org/magnet-plugins-file"
Repository = "https://github.com/your-org/magnet-plugins-file"
```

### magnet_plugins/__init__.py

```python
"""Magnet AI External Plugins - File URL

This package provides File URL knowledge source plugin for Magnet AI.
"""

from magnet_plugins.file import FileUrlPlugin

__version__ = "1.0.0"
__all__ = ["FileUrlPlugin"]
```

### magnet_plugins/file.py

```python
"""File URL Knowledge Source Plugin

Synchronizes content from file URLs.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from core.plugins.registry import PluginRegistry
from data_sources.file.source import UrlDataSource
from data_sync.data_processor import DataProcessor
from data_sync.processors.file_data_processor import UrlDataProcessor


class FileUrlPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing files from URLs"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="File URL",
            version="1.0.0",
            author="Your Company",
            description="Synchronizes content from file URLs",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "file_url": {
                        "type": "string",
                        "description": "URL of the file to sync",
                    },
                },
                "required": ["file_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "File"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create File URL processor

        Args:
            source_config: Source configuration containing file URL
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            UrlDataProcessor instance

        Raises:
            ClientException: If file_url is missing
        """
        file_url = source_config.get("file_url")

        if not file_url:
            raise ClientException("Missing `file_url` in metadata")

        # Create data source
        data_source = UrlDataSource(file_url)

        # Return processor
        return UrlDataProcessor(data_source, collection_config)


# Auto-register plugin when module is imported
PluginRegistry.register(FileUrlPlugin())
```

### README.md

```markdown
# Magnet AI - File URL Plugin

File URL knowledge source plugin for Magnet AI.

## Installation

### From GitHub (Private Repository)

```bash
pip install git+https://github.com/your-org/magnet-plugins-file.git
```

### From Private PyPI

```bash
pip install magnet-plugins-file --index-url https://your-private-pypi.com/simple
```

### Development Mode

```bash
git clone https://github.com/your-org/magnet-plugins-file.git
cd magnet-plugins-file
pip install -e .
```

## Usage

### Option 1: Auto-load (if installed in site-packages)

The plugin will be automatically discovered if installed properly.

### Option 2: Explicit Load via Environment Variable

```bash
export MAGNET_PLUGINS=magnet_plugins.file
```

### Option 3: Multiple Plugins

```bash
export MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics
```

## Configuration

In your collection configuration, use:

```json
{
  "source": {
    "source_type": "File",
    "file_url": "https://example.com/document.pdf"
  }
}
```

## Requirements

- Python >= 3.12
- magnet-ai (core application)

## License

Proprietary - Your Company
```

## Installation Methods

### 1. Install from Private GitHub Repository

```bash
# Install latest from main branch
pip install git+https://github.com/your-org/magnet-plugins-file.git

# Install specific version/tag
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0

# Install specific branch
pip install git+https://github.com/your-org/magnet-plugins-file.git@develop
```

### 2. Install from Private PyPI (e.g., Azure Artifacts, JFrog Artifactory)

```bash
# Configure private index
pip install magnet-plugins-file --index-url https://your-private-pypi.com/simple

# Or add to pip.conf
# [global]
# extra-index-url = https://your-private-pypi.com/simple
```

### 3. Install from Local Directory (Development)

```bash
# Editable install for development
cd magnet-plugins-file
pip install -e .

# Regular install
pip install .
```

### 4. Install via requirements.txt

```txt
# requirements.txt

# Core application
magnet-ai>=1.0.0

# External plugins from GitHub
git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
git+https://github.com/your-org/magnet-plugins-fluidtopics.git@v1.0.0

# Or from private PyPI
# magnet-plugins-file==1.0.0
# magnet-plugins-fluidtopics==1.0.0
```

### 5. Install via Poetry

```toml
# pyproject.toml

[tool.poetry.dependencies]
python = "^3.12"
magnet-ai = "^1.0.0"

# From GitHub
magnet-plugins-file = {git = "https://github.com/your-org/magnet-plugins-file.git", tag = "v1.0.0"}

# Or from private PyPI
# magnet-plugins-file = "^1.0.0"
```

## Docker Integration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install core application
COPY api/ /app/api/
RUN pip install -e /app/api

# Install external plugins
ARG INSTALL_FILE_PLUGIN=false
ARG INSTALL_FLUIDTOPICS_PLUGIN=false

# Install from GitHub
RUN if [ "$INSTALL_FILE_PLUGIN" = "true" ]; then \
    pip install git+https://github.com/your-org/magnet-plugins-file.git; \
    fi

RUN if [ "$INSTALL_FLUIDTOPICS_PLUGIN" = "true" ]; then \
    pip install git+https://github.com/your-org/magnet-plugins-fluidtopics.git; \
    fi

# Set environment for plugin loading
ENV MAGNET_PLUGINS=magnet_plugins.file,magnet_plugins.fluidtopics

CMD ["python", "/app/api/run.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      args:
        INSTALL_FILE_PLUGIN: "true"
        INSTALL_FLUIDTOPICS_PLUGIN: "true"
    environment:
      MAGNET_PLUGINS: "magnet_plugins.file,magnet_plugins.fluidtopics"
      # Other environment variables...
    volumes:
      - ./api:/app/api
    ports:
      - "5000:5000"
```

## GitHub Actions for Publishing

### .github/workflows/publish.yml

```yaml
name: Publish Package

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to Private PyPI
        env:
          TWINE_USERNAME: ${{ secrets.PYPI_USERNAME }}
          TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
        run: |
          twine upload --repository-url https://your-private-pypi.com dist/*
```

## Version Management

### Using Git Tags

```bash
# Tag a release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Install specific version
pip install git+https://github.com/your-org/magnet-plugins-file.git@v1.0.0
```

### Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

## See Also

- [PLUGIN_SYSTEM.md](../../PLUGIN_SYSTEM.md) - Main plugin system documentation
- [EXTERNAL_PLUGIN_EXAMPLE.md](../../EXTERNAL_PLUGIN_EXAMPLE.md) - General external plugin guide
