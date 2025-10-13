# Documen## URL Pattern

The plugin expects your VitePress documentation to follow this URL pattern:

```
{base_url}/docs/{language}/{section}/{page-path}.html
```

For example:
- `http://localhost:5173/docs/en/quickstarts/introduction/what-is-magnet-ai.html`
- `http://localhost:5173/docs/en/admin/connect/models/overview.html`

Where:
- **base_url**: `http://localhost:5173`
- **language**: `en`, `ru`, etc.
- **section**: `quickstarts`, `admin`, etc.
- **page-path**: nested path to the page

**Note**: The crawler starts from the language root page (`{base_url}/docs/{language}/`) and automatically discovers all pages belonging to the specified sections.uick Start Guide

This guide will help you quickly set up the Documentation knowledge source plugin to crawl your VitePress documentation.

## Prerequisites

1. VitePress documentation running and accessible (e.g., http://localhost:5173)
2. Magnet AI API running with the Documentation plugin enabled

## Step 1: Understand Your Documentation Structure

The plugin expects your VitePress documentation to follow this URL pattern:

```
{base_url}/docs/{language}/{section}/{page-path}.html
```

For example:
- `http://localhost:5173/docs/en/quickstarts/introduction/what-is-magnet-ai.html`
- `http://localhost:5173/docs/ru/admin/user-management/roles.html`

Where:
- **base_url**: `http://localhost:5173`
- **language**: `en`, `ru`, etc.
- **section**: `quickstarts`, `admin`, etc.
- **page-path**: nested path to the page

## Step 2: Create a Collection with Documentation Source

### Using the API

```bash
curl -X POST "http://localhost:8000/collections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Magnet AI Documentation",
    "description": "Official Magnet AI documentation for users and administrators",
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
  }'
```

### Configuration Breakdown

#### Required
- `type`: Must be `"Documentation"`
- `base_url`: Base URL of your VitePress site

#### Optional
- `languages`: Array of language codes (default: `["en"]`)
- `sections`: Array of section names (default: `["quickstarts", "admin"]`)
- `max_depth`: Maximum crawl depth (default: `5`)

#### Chunking
- `chunk_size`: Size of text chunks (recommended: 500-2000)
- `chunk_overlap`: Overlap between chunks (recommended: 100-300)

## Step 3: Sync the Collection

After creating the collection, trigger a sync:

```bash
curl -X POST "http://localhost:8000/collections/{collection_id}/sync"
```

The plugin will:
1. Start from URLs like: `{base_url}/docs/{lang}/{section}/`
2. Crawl all linked pages within the same language and section
3. Extract content and metadata from each page
4. Create chunks according to your configuration
5. Store chunks in the vector database

## Step 4: Query Your Documentation

Once synced, you can query the documentation:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a new knowledge source?",
    "collection_ids": ["{collection_id}"]
  }'
```

## Common Use Cases

### 1. Single Language, All Sections

```json
{
  "type": "Documentation",
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["quickstarts", "admin", "api", "guides"]
}
```

### 2. Multiple Languages, Specific Section

```json
{
  "type": "Documentation",
  "base_url": "https://docs.yourcompany.com",
  "languages": ["en", "es", "fr", "de"],
  "sections": ["quickstarts"],
  "max_depth": 3
}
```

### 3. Development Environment

```json
{
  "type": "Documentation",
  "base_url": "http://localhost:5173",
  "languages": ["en"],
  "sections": ["quickstarts"],
  "max_depth": 2
}
```

### 4. Production with Multiple Sections

```json
{
  "type": "Documentation",
  "base_url": "https://docs.yourcompany.com",
  "languages": ["en", "ru"],
  "sections": ["quickstarts", "admin", "developer", "api"],
  "max_depth": 7
}
```

## Tips for Best Results

### 1. Start Small
Begin with a limited scope (one language, one section, low depth) to test:
```json
{
  "languages": ["en"],
  "sections": ["quickstarts"],
  "max_depth": 2
}
```

### 2. Adjust Crawl Depth
- **Low depth (2-3)**: Fast, limited coverage
- **Medium depth (4-5)**: Good balance
- **High depth (6+)**: Complete coverage, slower

### 3. Optimize Chunking
For documentation:
- **Technical docs**: smaller chunks (500-800)
- **General docs**: medium chunks (800-1200)
- **Detailed guides**: larger chunks (1200-2000)

### 4. Language Considerations
If you have multilingual documentation, you can:
- **Option A**: Create separate collections per language
  ```json
  // English collection
  {"languages": ["en"], "sections": ["quickstarts", "admin"]}
  
  // Russian collection  
  {"languages": ["ru"], "sections": ["quickstarts", "admin"]}
  ```
  
- **Option B**: Combine all languages in one collection
  ```json
  {"languages": ["en", "ru"], "sections": ["quickstarts", "admin"]}
  ```

### 5. Monitor Sync Progress
Watch the logs during sync to see:
- Pages being crawled
- Content being extracted
- Chunks being created

```bash
# If running via Docker
docker logs -f magnet-ai-api

# If running directly
tail -f api.log
```

## Troubleshooting

### Plugin Not Found
```
Error: Documentation plugin not found
```
**Solution**: Make sure the plugin is registered. Check that:
1. `src/plugins/builtin/knowledge_source/__init__.py` imports `documentation`
2. API server was restarted after adding the plugin

### Connection Refused
```
Error: Connection refused to http://localhost:5173
```
**Solution**: Ensure VitePress is running:
```bash
cd web
npm run dev
```

### No Pages Found
```
Crawl complete. Found 0 documentation pages.
```
**Solution**: Check that:
1. The base URL is correct
2. The language and section names match your documentation structure
3. VitePress is serving content at the expected URLs

### Max Depth Reached Too Soon
```
Max depth reached for http://...
```
**Solution**: Increase `max_depth` if you have deeply nested documentation

## Next Steps

1. **Test the Plugin**: Run `python test_documentation_plugin.py` in the `api` directory
2. **Create Collection**: Use the API to create a documentation collection
3. **Sync Content**: Trigger a sync to crawl your documentation
4. **Query**: Test queries against your documentation
5. **Refine**: Adjust languages, sections, and chunking as needed

## Support

For issues or questions:
1. Check the plugin README: `api/src/plugins/builtin/knowledge_source/documentation/README.md`
2. Review the logs during sync
3. Test with the provided test script
4. Ensure VitePress is accessible and serving content correctly
