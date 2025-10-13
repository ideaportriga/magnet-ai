# VitePress Dynamic Navigation Fix

## Problem

VitePress часто использует JavaScript для генерации навигации, что означает, что ссылки на страницы не видны в статическом HTML, который парсит BeautifulSoup.

При попытке найти ссылки на странице `/docs/en/`, BeautifulSoup не находит ссылки на секции, хотя они видны в браузере:
```html
<a href="/docs/en/admin/connect/models/overview.html">Admin Guide</a>
```

## Solutions Implemented

### 1. Enhanced Logging

Добавлено детальное логирование для отладки:
- Количество найденных ссылок
- Каждая обрабатываемая ссылка
- Причина, по которой ссылка не подходит

### 2. Fallback to Common Entry Points

Если на корневой странице языка не найдены ссылки на секцию, crawler автоматически пробует распространенные пути:
- `/docs/{lang}/{section}/`
- `/docs/{lang}/{section}/index.html`
- `/docs/{lang}/{section}/overview.html`
- `/docs/{lang}/{section}/introduction.html`
- `/docs/{lang}/{section}/getting-started.html`

### 3. User-Specified Start URLs (Recommended)

Добавлена возможность указать конкретные стартовые URL для каждой секции.

#### Configuration:

```json
{
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["admin", "quickstarts"],
  "section_start_urls": {
    "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html",
    "quickstarts": "http://localhost:5173/docs/en/quickstarts/introduction.html"
  },
  "max_depth": 5
}
```

## Usage

### Option 1: Let crawler discover (may not work with dynamic navigation)

```json
{
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["admin"]
}
```

### Option 2: Specify start URLs (recommended for VitePress)

```json
{
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["admin"],
  "section_start_urls": {
    "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html"
  }
}
```

## Web UI Configuration

In `collections.js`, the `section_start_urls` field is optional and can be configured as JSON:

```javascript
{
  name: 'section_start_urls',
  label: 'Section Start URLs (optional)',
  field: 'section_start_urls',
  description: 'JSON object mapping section names to specific start URLs. Example: {"admin": "http://localhost:5173/docs/en/admin/overview.html"}',
  component: 'km-codemirror', // or 'km-input' for simple JSON
  readonly: (collection) => !!collection?.last_synced,
  type: 'Object',
}
```

## How It Works

1. **Try to discover from root page** (`/docs/{lang}/`)
   - Parse HTML with BeautifulSoup
   - Look for links matching `/docs/{lang}/{section}/*`

2. **If no links found and section_start_urls configured**:
   - Use the user-specified URL for that section
   - Start crawling from there

3. **If no links found and no section_start_urls**:
   - Try common entry points
   - Use first successful response

4. **Recursive crawling**:
   - From any starting point, follow internal links
   - Stay within the same section
   - Respect max_depth

## Files Modified

- `api/src/data_sources/vitepress/source.py`
  - Added `section_start_urls` parameter
  - Added `_try_common_entry_points()` method
  - Enhanced logging in `_find_section_links()`
  - Modified `_crawl_section()` to use start URLs

- `api/src/plugins/builtin/knowledge_source/documentation/plugin.py`
  - Added `section_start_urls` to config schema
  - Pass to VitePressDataSource

- `api/test_documentation_plugin.py`
  - Updated test to use section_start_urls

## Testing

```bash
cd api
python test_documentation_plugin.py
```

With logging, you'll see:
```
INFO: Using configured start URL for section 'admin': http://localhost:5173/docs/en/admin/connect/models/overview.html
INFO: Fetching: http://localhost:5173/docs/en/admin/connect/models/overview.html
INFO: Added page: Models Overview (http://localhost:5173/docs/en/admin/connect/models/overview.html)
```

## Recommendation

For VitePress sites with dynamic navigation, always specify `section_start_urls` to ensure reliable crawling.

Example workflow:
1. Open your VitePress site in a browser
2. Navigate to the first page of each section
3. Copy the URLs
4. Add them to `section_start_urls` configuration

This bypasses the need to discover links on dynamically generated pages.
