# Documentation Plugin - Complete Implementation Summary

This document provides a complete overview of the Documentation knowledge source plugin implementation for Magnet AI.

## Overview

The Documentation plugin enables Magnet AI to crawl and index VitePress documentation sites. It automatically discovers and processes documentation pages across multiple languages and sections.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI (Vue.js)                         │
│  - CreateNew.vue: Create new documentation source            │
│  - generalinfo.vue: Edit documentation source                │
│  - Header.vue: Save changes                                  │
│  - collections.js: Configuration schema                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP API
┌───────────────────────▼─────────────────────────────────────┐
│                   API Backend (Python)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Plugin Layer                                       │    │
│  │  - plugin.py: Plugin registration & metadata       │    │
│  │  - Validates configuration                         │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│  ┌──────────────▼─────────────────────────────────────┐    │
│  │  Data Source Layer                                  │    │
│  │  - source.py: VitePress crawler                    │    │
│  │  - Discovers & fetches documentation pages         │    │
│  │  - Extracts clean content from HTML                │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│  ┌──────────────▼─────────────────────────────────────┐    │
│  │  Data Processor Layer                               │    │
│  │  - documentation_data_processor.py                  │    │
│  │  - Creates document chunks                          │    │
│  │  - Adds metadata to each chunk                      │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
└─────────────────┼─────────────────────────────────────────┘
                  │
┌─────────────────▼─────────────────────────────────────────┐
│              Vector Database (Embeddings)                  │
│  - Stores document chunks                                  │
│  - Enables semantic search                                 │
└────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### Backend (Python)

#### New Files:
1. **`api/src/plugins/builtin/knowledge_source/documentation/`**
   - `__init__.py` - Plugin initialization and registration
   - `plugin.py` - Plugin class with metadata and configuration
   - `README.md` - Plugin documentation

2. **`api/src/data_sources/vitepress/`**
   - `source.py` - VitePress crawler implementation
   - `__init__.py` - Package initialization

3. **`api/src/data_sync/processors/documentation_data_processor.py`**
   - Document processing and chunking

4. **Documentation Files:**
   - `api/test_documentation_plugin.py` - Test script
   - `api/DOCUMENTATION_PLUGIN_QUICKSTART.md` - User guide

#### Modified Files:
1. **`api/src/plugins/builtin/knowledge_source/__init__.py`**
   - Added `documentation` import
   - Registered in `__all__`

2. **`api/PLUGIN_SYSTEM.md`**
   - Added Documentation to list of built-in plugins

### Frontend (Vue.js)

#### Modified Files:
1. **`web/apps/@ipr/magnet-admin/src/config/collections/collections.js`**
   - Added "Documentation" to source_type options
   - Added field configurations for Documentation

2. **`web/apps/@ipr/magnet-admin/src/components/Collections/CreateNew.vue`**
   - Added `transformSourceFields()` method
   - Transforms comma-separated strings to arrays

3. **`web/apps/@ipr/magnet-admin/src/components/Collections/Header.vue`**
   - Added `transformSourceFields()` method
   - Transforms data before saving

4. **`web/apps/@ipr/magnet-admin/src/components/Collections/generalinfo.vue`**
   - Modified `source_fields` getter
   - Transforms arrays to strings for display

5. **Documentation:**
   - `web/WEB_UI_DOCUMENTATION_PLUGIN.md` - UI changes documentation

## Configuration

### Plugin Configuration Schema

```json
{
  "type": "object",
  "properties": {
    "base_url": {
      "type": "string",
      "description": "Base URL of the VitePress documentation site"
    },
    "languages": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of language codes to crawl",
      "default": ["en"]
    },
    "sections": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of documentation sections to crawl",
      "default": ["quickstarts", "admin"]
    },
    "max_depth": {
      "type": "integer",
      "description": "Maximum depth for crawling",
      "default": 5
    }
  },
  "required": ["base_url"]
}
```

### Example Configuration

```json
{
  "name": "Magnet AI Documentation",
  "system_name": "MAGNET_AI_DOCS",
  "source": {
    "source_type": "Documentation",
    "base_url": "http://localhost:5173",
    "languages": ["en", "ru"],
    "sections": ["quickstarts", "admin"],
    "max_depth": 5
  },
  "chunking": {
    "strategy": "recursive_character_text_splitting",
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "indexing": {
    "semantic_search_supported": true,
    "fulltext_search_supported": false
  }
}
```

## Features

### Backend Features

1. **Recursive Crawling**
   - Starts from base URLs constructed from languages and sections
   - Follows internal links within the same section
   - Respects max_depth to prevent infinite loops

2. **Content Extraction**
   - Finds VitePress content areas (`.vp-doc`, `<main>`, `<article>`)
   - Removes navigation, scripts, styles
   - Extracts clean text content
   - Preserves document structure

3. **Metadata Tracking**
   - URL as unique identifier
   - Page title extraction
   - Language and section information
   - Supports incremental updates (re-syncs all pages)

4. **Error Handling**
   - Handles HTTP errors gracefully
   - Logs warnings for failed pages
   - Continues crawling after errors

### Frontend Features

1. **User-Friendly Input**
   - Comma-separated strings for languages and sections
   - Automatic trimming and validation
   - Clear field descriptions

2. **Data Transformation**
   - Automatic conversion from strings to arrays on save
   - Automatic conversion from arrays to strings on load
   - Preserves data integrity

3. **Field Locking**
   - Critical fields disabled after first sync
   - Prevents configuration changes that could break sync

## How It Works

### 1. User Creates Documentation Source (Web UI)

```
User fills form:
├─ Name: "Magnet AI Docs"
├─ Source Type: "Documentation"
├─ Base URL: "http://localhost:5173"
├─ Languages: "en, ru"      ← User enters as comma-separated string
├─ Sections: "quickstarts, admin"  ← User enters as comma-separated string
└─ Max Depth: "5"
```

### 2. Web UI Transforms Data

```javascript
// CreateNew.vue transforms before sending to API
{
  "languages": ["en", "ru"],        // Array
  "sections": ["quickstarts", "admin"],  // Array
  "max_depth": 5                    // Integer
}
```

### 3. API Receives and Validates

```python
# plugin.py validates configuration
source_config = {
    "base_url": "http://localhost:5173",
    "languages": ["en", "ru"],
    "sections": ["quickstarts", "admin"],
    "max_depth": 5
}
```

### 4. Plugin Creates Processor

```python
# plugin.py creates data source and processor
data_source = VitePressDataSource(
    base_url="http://localhost:5173",
    languages=["en", "ru"],
    sections=["quickstarts", "admin"],
    max_depth=5
)

processor = DocumentationDataProcessor(data_source, collection_config)
```

### 5. Crawler Discovers Pages

```python
# source.py crawls documentation
Starting URLs (Language roots):
├─ http://localhost:5173/docs/en/
└─ http://localhost:5173/docs/ru/

For each language:
├─ Fetch language root page
├─ Find all links matching sections (e.g., /docs/en/quickstarts/*, /docs/en/admin/*)
└─ For each section link:
    ├─ Fetch HTML
    ├─ Extract title and content
    ├─ Find more internal links in same section
    └─ Recursively crawl (up to max_depth)
```

### 6. Processor Creates Chunks

```python
# documentation_data_processor.py processes pages
For each page:
├─ Create base metadata (URL, title, language, section)
├─ Split content into chunks (according to chunking config)
└─ Create DocumentData objects
```

### 7. Chunks Stored in Vector DB

```
Each chunk:
├─ Content: "What is Magnet AI? Magnet AI is..."
├─ Metadata:
│   ├─ sourceId: "http://localhost:5173/docs/en/quickstarts/intro.html"
│   ├─ title: "What is Magnet AI"
│   ├─ language: "en"
│   └─ section: "quickstarts"
└─ Embedding: [0.123, -0.456, ...]  ← Generated by embedding model
```

## Usage

### Create Documentation Source via Web UI

1. Navigate to Knowledge Sources
2. Click "New"
3. Fill in configuration:
   - Name: "My Documentation"
   - System Name: "MY_DOCS"
   - Source Type: "Documentation"
   - Base URL: "http://localhost:5173"
   - Languages: "en, ru"
   - Sections: "quickstarts, admin"
   - Max Crawl Depth: "5"
4. Configure chunking and indexing
5. Click "Save & Sync"

### Create Documentation Source via API

```bash
curl -X POST "http://localhost:8000/collections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Magnet AI Documentation",
    "system_name": "MAGNET_AI_DOCS",
    "source": {
      "source_type": "Documentation",
      "base_url": "http://localhost:5173",
      "languages": ["en", "ru"],
      "sections": ["quickstarts", "admin"],
      "max_depth": 5
    },
    "chunking": {
      "strategy": "recursive_character_text_splitting",
      "chunk_size": 1000,
      "chunk_overlap": 200
    },
    "indexing": {
      "semantic_search_supported": true,
      "fulltext_search_supported": false
    }
  }'
```

### Query Documentation

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a knowledge source?",
    "collection_ids": ["<collection_id>"]
  }'
```

## Testing

### Backend Test

```bash
cd api
python test_documentation_plugin.py
```

Expected output:
```
Testing Documentation Plugin
============================================================
Plugin found: Documentation v1.0.0
Description: Synchronizes content from VitePress documentation sites
Found 25 documentation pages

First 5 pages:
  1. What is Magnet AI
     URL: http://localhost:5173/docs/en/quickstarts/introduction/what-is-magnet-ai.html
  ...
  
Test completed successfully!
```

### Frontend Test

1. Start VitePress: `cd web && npm run dev`
2. Start API: `cd api && python run.py`
3. Open Admin UI: http://localhost:8080
4. Create new Documentation source
5. Sync and verify pages are indexed

## Troubleshooting

### Issue: Plugin not found

**Error**: `Documentation plugin not found`

**Solution**: Restart API server to register the plugin

### Issue: No pages found

**Error**: `Found 0 documentation pages`

**Solutions**:
- Check VitePress is running at base_url
- Verify language and section names match URL structure
- Check VitePress URL pattern: `{base_url}/docs/{lang}/{section}/`

### Issue: Max depth reached too quickly

**Error**: `Max depth reached for http://...`

**Solution**: Increase `max_depth` parameter

### Issue: Array/String conversion errors

**Error**: Data not saving correctly

**Solution**: Check that transformSourceFields() is being called in both CreateNew.vue and Header.vue

## Best Practices

1. **Start Small**: Test with one language and section first
2. **Monitor Logs**: Watch API logs during first sync
3. **Adjust Depth**: Start with low depth (2-3), increase if needed
4. **Chunk Size**: Use 800-1200 for technical documentation
5. **Regular Syncs**: Schedule periodic syncs to keep docs updated

## Performance Considerations

- **Crawl Time**: Depends on number of pages and network speed
- **Memory**: Crawler stores all pages in memory during sync
- **API Calls**: Each page = 1 HTTP request to VitePress
- **Embeddings**: Generated during indexing (can be slow for many chunks)

## Future Enhancements

- [ ] Support for sitemap.xml discovery
- [ ] Better change detection using ETags or content hashing
- [ ] Authentication support for private documentation
- [ ] PDF export of documentation pages
- [ ] Custom CSS selectors for content extraction
- [ ] Incremental updates (only sync changed pages)

## Support

For issues or questions:
1. Check plugin README: `api/src/plugins/builtin/knowledge_source/documentation/README.md`
2. Review quick start guide: `api/DOCUMENTATION_PLUGIN_QUICKSTART.md`
3. Run test script: `python api/test_documentation_plugin.py`
4. Check API logs for detailed error messages

## Summary

The Documentation plugin is a complete solution for indexing VitePress documentation in Magnet AI. It includes:

✅ Backend plugin with crawler and processor  
✅ Frontend UI with data transformation  
✅ Comprehensive documentation  
✅ Test scripts  
✅ Error handling  
✅ Multi-language support  
✅ Section filtering  
✅ Depth control  

The plugin is production-ready and follows Magnet AI's plugin architecture standards.
