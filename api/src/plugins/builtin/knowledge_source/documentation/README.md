# Documentation Knowledge Source Plugin

This plugin enables Magnet AI to crawl and synchronize content from VitePress documentation sites.

## Features

- **Automatic Crawling**: Recursively crawls documentation pages following internal links
- **Multi-language Support**: Can crawl documentation in multiple languages
- **Section Filtering**: Target specific documentation sections (e.g., quickstarts, admin)
- **Depth Control**: Configurable crawl depth to prevent infinite loops
- **VitePress Optimized**: Designed specifically for VitePress sites but works with other static documentation

## Configuration

### Required Parameters

- `base_url` (string): Base URL of the VitePress documentation site
  - Example: `http://localhost:5173` or `https://docs.yoursite.com`

### Optional Parameters

- `languages` (array of strings): List of language codes to crawl
  - Default: `["en"]`
  - Example: `["en", "ru", "es"]`
  - The crawler will visit `{base_url}/docs/{language}/` for each language

- `sections` (array of strings): List of documentation sections to crawl
  - Default: `["quickstarts", "admin"]`
  - Example: `["quickstarts", "admin", "api", "guides"]`
  - Only pages matching `/docs/{language}/{section}/*` will be crawled

- `max_depth` (integer): Maximum crawl depth
  - Default: `5`
  - Prevents infinite loops and limits crawl scope
  - Depth is calculated from each section's starting page

## Usage Example

### Collection Configuration

```json
{
  "name": "Magnet AI Documentation",
  "description": "Internal documentation for Magnet AI",
  "source": {
    "type": "Documentation",
    "base_url": "http://localhost:5173",
    "languages": ["en", "ru"],
    "sections": ["quickstarts", "admin"],
    "max_depth": 5
  },
  "chunking": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

## URL Pattern

The plugin expects VitePress documentation URLs to follow this pattern:

```
{base_url}/docs/{language}/{section}/{page-path}.html
```

Example:
```
http://localhost:5173/docs/en/admin/connect/models/overview.html
```

The crawler starts from the language root page (`{base_url}/docs/{language}/`) and discovers all links that belong to the specified sections.

## How It Works

1. **Starting Points**: The plugin starts from language root pages (e.g., `http://localhost:5173/docs/en/`)
2. **Section Discovery**: For each language, it finds all links belonging to specified sections
3. **Crawling**: It fetches each page and extracts:
   - Page title (from `<h1>` or `<title>` tag)
   - Main content (from VitePress content area)
   - Links to other documentation pages
4. **Following Links**: Only follows links within the same language and section
5. **Content Extraction**: Extracts clean text from HTML, removing navigation, scripts, and styles
6. **Chunking**: Splits content into chunks according to collection configuration

## Metadata

Each document chunk includes the following metadata:

- `sourceId`: URL of the documentation page
- `name`: Page title
- `title`: Page title
- `path`: URL of the page
- `source`: URL of the page
- `language`: Language code (e.g., "en", "ru")
- `section`: Section name (e.g., "quickstarts", "admin")
- `createdTime`: Empty (not available for static docs)
- `modifiedTime`: Empty (not available for static docs)

## Testing

Run the test script to verify the plugin works:

```bash
cd api
python test_documentation_plugin.py
```

Make sure your VitePress documentation is running before testing.

## Dependencies

- `httpx`: HTTP client for fetching pages
- `beautifulsoup4`: HTML parsing and content extraction

These are already included in the main project dependencies.

## Limitations

- **No Change Detection**: Since static documentation doesn't provide modification dates, pages will be re-synced every time
- **Same-Section Only**: The crawler only follows links within the same section to avoid crawling unrelated content
- **Static Content**: Best suited for static documentation sites, not dynamic web applications

## Future Improvements

- Support for sitemap.xml to discover all pages
- Better change detection using ETag or content hashing
- Support for authentication (private documentation)
- PDF export support for documentation pages
- Custom CSS selectors for content extraction
