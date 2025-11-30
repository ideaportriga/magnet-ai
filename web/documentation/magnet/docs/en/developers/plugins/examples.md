# Plugin Examples

Real-world examples of Magnet AI plugins to help you get started.

## Simple File Plugin

A basic knowledge source plugin that reads from local files.

```python
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
import os
import mimetypes

class FilePlugin(KnowledgeSourcePlugin):
    """Simple file-based knowledge source."""

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.KNOWLEDGE_SOURCE

    @property
    def name(self) -> str:
        return "file"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Read documents from local file system"

    def validate_config(self, config: dict) -> bool:
        if 'directory' not in config:
            raise ValueError("Missing required field: directory")

        if not os.path.exists(config['directory']):
            raise ValueError(f"Directory not found: {config['directory']}")

        return True

    def test_connection(self, config: dict) -> bool:
        return os.path.isdir(config['directory'])

    def fetch_documents(self, config: dict) -> list:
        self.validate_config(config)

        documents = []
        directory = config['directory']
        allowed_extensions = config.get('extensions', ['.txt', '.md', '.pdf'])

        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, file)
                    doc = self._read_file(file_path)
                    if doc:
                        documents.append(doc)

        return documents

    def _read_file(self, file_path: str) -> dict:
        """Read a single file and return as document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'id': file_path,
                'title': os.path.basename(file_path),
                'content': content,
                'metadata': {
                    'source': 'file',
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'modified': os.path.getmtime(file_path)
                }
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
```

## REST API Plugin

A plugin that fetches data from a REST API.

```python
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
import requests
from datetime import datetime

class RestApiPlugin(KnowledgeSourcePlugin):
    """Fetch documents from a REST API."""

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.KNOWLEDGE_SOURCE

    @property
    def name(self) -> str:
        return "rest_api"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Fetch documents from REST API endpoints"

    def initialize(self):
        self.session = requests.Session()

    def cleanup(self):
        self.session.close()

    def validate_config(self, config: dict) -> bool:
        required = ['endpoint', 'api_key']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        return True

    def test_connection(self, config: dict) -> bool:
        try:
            headers = self._get_headers(config)
            response = self.session.get(
                f"{config['endpoint']}/health",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {e}")

    def fetch_documents(self, config: dict) -> list:
        self.validate_config(config)

        documents = []
        page = 1
        page_size = config.get('page_size', 100)

        while True:
            batch = self._fetch_page(config, page, page_size)
            if not batch:
                break

            documents.extend(batch)
            page += 1

            # Stop if we've fetched all pages
            if len(batch) < page_size:
                break

        return documents

    def _fetch_page(self, config: dict, page: int, page_size: int) -> list:
        """Fetch a single page of documents."""
        headers = self._get_headers(config)

        try:
            response = self.session.get(
                f"{config['endpoint']}/documents",
                headers=headers,
                params={'page': page, 'size': page_size},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return [self._parse_document(item) for item in data]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch page {page}: {e}")

    def _get_headers(self, config: dict) -> dict:
        """Build request headers."""
        return {
            'Authorization': f"Bearer {config['api_key']}",
            'Content-Type': 'application/json',
            'User-Agent': 'MagnetAI/1.0'
        }

    def _parse_document(self, item: dict) -> dict:
        """Parse API response item into document format."""
        return {
            'id': item['id'],
            'title': item.get('title', 'Untitled'),
            'content': item.get('content', item.get('body', '')),
            'metadata': {
                'source': 'rest_api',
                'url': item.get('url'),
                'author': item.get('author'),
                'created_at': item.get('created_at'),
                'tags': item.get('tags', [])
            }
        }

    def sync_incremental(self, config: dict, last_sync: datetime) -> list:
        """Fetch only documents modified since last sync."""
        self.validate_config(config)

        headers = self._get_headers(config)

        try:
            response = self.session.get(
                f"{config['endpoint']}/documents/modified",
                headers=headers,
                params={'since': last_sync.isoformat()},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return [self._parse_document(item) for item in data]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Incremental sync failed: {e}")
```

## Database Plugin

A plugin that queries a SQL database.

```python
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
import sqlalchemy
from sqlalchemy import create_engine, text

class DatabasePlugin(KnowledgeSourcePlugin):
    """Fetch documents from a SQL database."""

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.KNOWLEDGE_SOURCE

    @property
    def name(self) -> str:
        return "database"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Fetch documents from SQL databases"

    def initialize(self):
        self.engine = None

    def cleanup(self):
        if self.engine:
            self.engine.dispose()

    def validate_config(self, config: dict) -> bool:
        required = ['connection_string', 'table', 'columns']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(config['columns'], dict):
            raise ValueError("columns must be a dictionary")

        required_cols = ['id', 'title', 'content']
        for col in required_cols:
            if col not in config['columns']:
                raise ValueError(f"Missing required column mapping: {col}")

        return True

    def test_connection(self, config: dict) -> bool:
        try:
            engine = create_engine(config['connection_string'])
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return True
        except Exception as e:
            raise ConnectionError(f"Database connection failed: {e}")

    def fetch_documents(self, config: dict) -> list:
        self.validate_config(config)

        if not self.engine:
            self.engine = create_engine(config['connection_string'])

        documents = []
        table = config['table']
        cols = config['columns']

        # Build SELECT query
        select_cols = [
            f"{cols['id']} as id",
            f"{cols['title']} as title",
            f"{cols['content']} as content"
        ]

        # Add optional columns
        if 'author' in cols:
            select_cols.append(f"{cols['author']} as author")
        if 'created_at' in cols:
            select_cols.append(f"{cols['created_at']} as created_at")

        query = f"SELECT {', '.join(select_cols)} FROM {table}"

        # Add WHERE clause if specified
        if 'where' in config:
            query += f" WHERE {config['where']}"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))

                for row in result:
                    doc = {
                        'id': str(row.id),
                        'title': row.title,
                        'content': row.content,
                        'metadata': {
                            'source': 'database',
                            'table': table
                        }
                    }

                    # Add optional metadata
                    if hasattr(row, 'author'):
                        doc['metadata']['author'] = row.author
                    if hasattr(row, 'created_at'):
                        doc['metadata']['created_at'] = str(row.created_at)

                    documents.append(doc)

        except Exception as e:
            raise Exception(f"Failed to fetch documents: {e}")

        return documents
```

## Configuration Examples

### File Plugin Configuration

```json
{
  "plugin_name": "file",
  "settings": {
    "directory": "/path/to/documents",
    "extensions": [".txt", ".md", ".pdf"],
    "recursive": true
  }
}
```

### REST API Plugin Configuration

```json
{
  "plugin_name": "rest_api",
  "settings": {
    "endpoint": "https://api.example.com/v1",
    "api_key": "your-api-key-here",
    "page_size": 50
  },
  "sync_schedule": "0 */6 * * *"
}
```

### Database Plugin Configuration

```json
{
  "plugin_name": "database",
  "settings": {
    "connection_string": "postgresql://user:pass@localhost/dbname",
    "table": "articles",
    "columns": {
      "id": "article_id",
      "title": "article_title",
      "content": "article_body",
      "author": "author_name",
      "created_at": "publish_date"
    },
    "where": "status = 'published'"
  }
}
```

## Testing Examples

### Unit Test Example

```python
import unittest
from unittest.mock import Mock, patch
from plugins.rest_api import RestApiPlugin

class TestRestApiPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = RestApiPlugin()
        self.config = {
            'endpoint': 'https://api.test.com',
            'api_key': 'test-key'
        }

    def test_validate_config_valid(self):
        result = self.plugin.validate_config(self.config)
        self.assertTrue(result)

    def test_validate_config_missing_endpoint(self):
        config = {'api_key': 'test'}
        with self.assertRaises(ValueError):
            self.plugin.validate_config(config)

    @patch('requests.Session.get')
    def test_fetch_documents(self, mock_get):
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'id': '1',
                'title': 'Test Doc',
                'content': 'Test content'
            }
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        docs = self.plugin.fetch_documents(self.config)

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['title'], 'Test Doc')
```

## Next Steps

- [Plugin System](/docs/en/developers/plugins/plugin-system) - Architecture overview
- [Creating Plugins](/docs/en/developers/plugins/creating-plugins) - Detailed guide
- [Plugin API](/docs/en/developers/plugins/plugin-api) - Complete API reference
