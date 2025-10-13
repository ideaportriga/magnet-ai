# Documentation Plugin - Final Summary

## Problem Solved

VitePress uses dynamic JavaScript navigation, making links invisible to BeautifulSoup's static HTML parsing. This prevented the crawler from discovering section pages.

## Complete Solution

### 3-Tier Fallback Strategy

1. **Automatic Discovery** (tries first)
   - Parses language root page for section links
   - Works if VitePress renders links in static HTML

2. **User-Specified Start URLs** (recommended)
   - Allows specifying exact entry points for each section
   - Most reliable for dynamic navigation

3. **Common Entry Points** (last resort)
   - Tries standard paths like `overview.html`, `index.html`
   - Fallback when discovery fails and no URLs specified

## Configuration

### Basic (Auto-discovery)
```json
{
  "source_type": "Documentation",
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["admin", "quickstarts"]
}
```

### Recommended (Explicit Start URLs)
```json
{
  "source_type": "Documentation",
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["admin", "quickstarts"],
  "section_start_urls": {
    "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html",
    "quickstarts": "http://localhost:5173/docs/en/quickstarts/introduction.html"
  }
}
```

## Web UI Changes

### New Field: Section Start URLs

**Field**: `section_start_urls` (optional)
**Component**: `km-codemirror` (JSON editor)
**Format**: JSON object mapping section names to URLs

**Example**:
```json
{
  "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html",
  "quickstarts": "http://localhost:5173/docs/en/quickstarts/intro.html"
}
```

### Data Transformation

#### On Save (UI → API):
- `section_start_urls`: JSON string → Parsed object
- Validation with try/catch
- Invalid JSON is removed

#### On Load (API → UI):
- `section_start_urls`: Object → Pretty-printed JSON string
- 2-space indentation for readability

## Files Modified

### Backend
- ✅ `api/src/data_sources/vitepress/source.py`
  - Added `section_start_urls` parameter
  - Added `_try_common_entry_points()` method
  - Enhanced logging in `_find_section_links()`
  - Modified `_crawl_section()` to use start URLs

- ✅ `api/src/plugins/builtin/knowledge_source/documentation/plugin.py`
  - Added `section_start_urls` to config schema
  - Pass to VitePressDataSource

- ✅ `api/test_documentation_plugin.py`
  - Updated with section_start_urls example

### Frontend
- ✅ `web/apps/@ipr/magnet-admin/src/config/collections/collections.js`
  - Added `section_start_urls` field with km-codemirror component

- ✅ `web/apps/@ipr/magnet-admin/src/components/Collections/CreateNew.vue`
  - Parse JSON string to object on save
  - Error handling for invalid JSON

- ✅ `web/apps/@ipr/magnet-admin/src/components/Collections/Header.vue`
  - Parse JSON string to object on save
  - Error handling for invalid JSON

- ✅ `web/apps/@ipr/magnet-admin/src/components/Collections/generalinfo.vue`
  - Convert object to pretty JSON string on load
  - Display in code editor

### Documentation
- ✅ `api/VITEPRESS_DYNAMIC_NAV_FIX.md` - Technical details
- ✅ `api/VITEPRESS_URL_STRUCTURE_FIX.md` - URL structure changes
- ✅ Multiple README updates

## Usage Guide

### Step 1: Open VitePress in Browser

Navigate to each section's first page:
- Admin: `http://localhost:5173/docs/en/admin/connect/models/overview.html`
- Quickstarts: `http://localhost:5173/docs/en/quickstarts/introduction.html`

### Step 2: Copy URLs

Copy the full URL from the browser address bar for each section.

### Step 3: Create Knowledge Source

In Magnet AI Admin UI:

1. Click "New" in Knowledge Sources
2. Fill basic info
3. Select "Documentation" as source type
4. Fill fields:
   - **Base URL**: `http://localhost:5173`
   - **Languages**: `en`
   - **Sections**: `admin, quickstarts`
   - **Section Start URLs**:
     ```json
     {
       "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html",
       "quickstarts": "http://localhost:5173/docs/en/quickstarts/introduction.html"
     }
     ```
   - **Max Crawl Depth**: `5`

5. Configure chunking/indexing as usual
6. Click "Save & Sync"

### Step 4: Monitor Sync

Check logs for:
```
INFO: Using configured start URL for section 'admin': ...
INFO: Fetching: http://localhost:5173/docs/en/admin/connect/models/overview.html
INFO: Added page: Models Overview
INFO: Found 5 links matching section pattern
```

## Behavior

### With section_start_urls
1. Start from specified URL
2. Extract content
3. Find internal links in same section
4. Recursively crawl (up to max_depth)

### Without section_start_urls
1. Try to discover from `/docs/{lang}/`
2. If no links found, try common entry points:
   - `/docs/{lang}/{section}/`
   - `/docs/{lang}/{section}/index.html`
   - `/docs/{lang}/{section}/overview.html`
   - etc.
3. Use first successful response
4. Recursively crawl from there

## Testing

```bash
cd api
python test_documentation_plugin.py
```

Expected output:
```
Testing Documentation Plugin
============================================================
Plugin found: Documentation v1.0.0
Using configured start URL for section 'admin': http://localhost:5173/docs/en/admin/connect/models/overview.html
Found 12 documentation pages

First 5 pages:
  1. Models Overview
     URL: http://localhost:5173/docs/en/admin/connect/models/overview.html
  ...

Created 5 chunks for page: Models Overview
Test completed successfully!
```

## Benefits

1. ✅ **Reliable**: Explicit URLs bypass dynamic navigation
2. ✅ **Flexible**: Falls back to auto-discovery if needed
3. ✅ **User-friendly**: JSON editor in UI
4. ✅ **Robust**: Multiple fallback strategies
5. ✅ **Well-documented**: Clear error messages and logs

## Recommendation

**Always use `section_start_urls` for VitePress sites** to ensure reliable crawling, especially when navigation is generated dynamically.
