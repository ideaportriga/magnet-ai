# VitePress URL Structure Update

## Issue

The initial implementation assumed VitePress documentation URLs follow this pattern:
```
http://localhost:5173/docs/{lang}/{section}/
```

However, the actual structure is:
- Language root: `http://localhost:5173/docs/{lang}/`
- Section pages: `http://localhost:5173/docs/{lang}/{section}/path/to/page.html`

For example:
- Language root: `http://localhost:5173/docs/en/`
- Section page: `http://localhost:5173/docs/en/admin/connect/models/overview.html`

## Solution

Modified the crawler to:

1. **Start from language root pages** instead of section URLs
2. **Discover section links** by scanning the language root page
3. **Crawl each section** separately

## Changes Made

### `api/src/data_sources/vitepress/source.py`

#### Modified `get_data()` method:
- Changed to start from language root URLs (`/docs/{lang}/`)
- Added loop to crawl each section separately

#### Added `_crawl_section()` method:
- New method to crawl a specific section
- Fetches language root page first
- Finds all links belonging to the section
- Initiates recursive crawling for each link

#### Added `_find_section_links()` method:
- Extracts links from language root page
- Filters by section pattern (`/docs/{lang}/{section}/...`)
- Returns list of starting URLs for the section

## How It Works Now

```
1. Start with language roots:
   - http://localhost:5173/docs/en/
   - http://localhost:5173/docs/ru/

2. For each language:
   a. Fetch language root page
   b. For each section (e.g., "quickstarts", "admin"):
      - Find all links matching /docs/{lang}/{section}/*
      - Crawl each link recursively
      - Follow internal links within same section

3. Result:
   - All pages in specified sections are discovered and indexed
   - Pages in other sections are ignored
```

## Example

Configuration:
```json
{
  "base_url": "http://localhost:5173",
  "languages": ["en", "ru"],
  "sections": ["quickstarts", "admin"]
}
```

Crawl process:
```
1. Fetch http://localhost:5173/docs/en/
   - Find links: /docs/en/quickstarts/intro.html, /docs/en/admin/connect/models/overview.html, etc.
   
2. Crawl section "quickstarts":
   - Start from: /docs/en/quickstarts/intro.html
   - Follow links in /docs/en/quickstarts/*
   
3. Crawl section "admin":
   - Start from: /docs/en/admin/connect/models/overview.html
   - Follow links in /docs/en/admin/*
   
4. Repeat for Russian (/docs/ru/)
```

## Benefits

1. **More flexible**: Works with actual VitePress structure
2. **Better discovery**: Finds all section pages from language root
3. **Maintains section filtering**: Still only crawls specified sections
4. **Recursive crawling**: Follows internal links within sections

## Testing

Test with the actual VitePress structure:
```bash
cd api
python test_documentation_plugin.py
```

Expected result:
- Successfully discovers pages from http://localhost:5173/docs/en/
- Filters by specified sections
- Crawls all pages within those sections

## Updated Documentation

- ✅ `api/src/plugins/builtin/knowledge_source/documentation/README.md`
- ✅ `api/DOCUMENTATION_PLUGIN_QUICKSTART.md`
- ✅ `DOCUMENTATION_PLUGIN_COMPLETE_SUMMARY.md`

All documentation now reflects the correct URL structure and crawling approach.
