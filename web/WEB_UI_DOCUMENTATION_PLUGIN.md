# Web UI Changes for Documentation Plugin

This document describes the changes made to the web interface to support the new Documentation knowledge source plugin.

## Files Modified

### 1. `/web/apps/@ipr/magnet-admin/src/config/collections/collections.js`

Added "Documentation" source type configuration:

#### Changes:
- **Added to `source_type.options` array**: `'Documentation'`
- **Added to `sourceTypeChildren` object**: Configuration for Documentation fields

```javascript
Documentation: [
  {
    name: 'base_url',
    label: 'Base URL',
    field: 'base_url',
    description: 'Base URL of the VitePress documentation site (e.g., http://localhost:5173)',
    component: 'km-input',
    readonly: (collection) => !!collection?.last_synced,
    type: 'String',
  },
  {
    name: 'languages',
    label: 'Languages',
    field: 'languages',
    description: 'Comma-separated list of language codes (e.g., en,ru)',
    component: 'km-input',
    readonly: (collection) => !!collection?.last_synced,
    type: 'String',
  },
  {
    name: 'sections',
    label: 'Sections',
    field: 'sections',
    description: 'Comma-separated list of documentation sections (e.g., quickstarts,admin)',
    component: 'km-input',
    readonly: (collection) => !!collection?.last_synced,
    type: 'String',
  },
  {
    name: 'max_depth',
    label: 'Max Crawl Depth',
    field: 'max_depth',
    description: 'Maximum depth for crawling documentation pages (default: 5)',
    component: 'km-input',
    readonly: (collection) => !!collection?.last_synced,
    type: 'Number',
  },
]
```

### 2. `/web/apps/@ipr/magnet-admin/src/components/Collections/CreateNew.vue`

Added data transformation for Documentation source when creating a new collection.

#### Changes:
- **Added `transformSourceFields()` method**: Converts comma-separated strings to arrays for languages and sections
- **Modified `createNew()` method**: Calls `transformSourceFields()` before saving

```javascript
transformSourceFields(source) {
  if (source?.source_type === 'Documentation') {
    const transformed = { ...source }
    
    // Convert languages from comma-separated string to array
    if (transformed.languages && typeof transformed.languages === 'string') {
      transformed.languages = transformed.languages
        .split(',')
        .map(lang => lang.trim())
        .filter(lang => lang.length > 0)
    }
    
    // Convert sections from comma-separated string to array
    if (transformed.sections && typeof transformed.sections === 'string') {
      transformed.sections = transformed.sections
        .split(',')
        .map(section => section.trim())
        .filter(section => section.length > 0)
    }
    
    // Convert max_depth to integer
    if (transformed.max_depth) {
      transformed.max_depth = parseInt(transformed.max_depth) || 5
    }
    
    return transformed
  }
  
  return source
}
```

### 3. `/web/apps/@ipr/magnet-admin/src/components/Collections/Header.vue`

Added data transformation for Documentation source when saving changes.

#### Changes:
- **Added `transformSourceFields()` method**: Same as in CreateNew.vue
- **Modified `save()` method**: Transforms source fields before updating

### 4. `/web/apps/@ipr/magnet-admin/src/components/Collections/generalinfo.vue`

Added bidirectional transformation for Documentation source fields in the edit view.

#### Changes:
- **Modified `source_fields` getter**: Transforms arrays to comma-separated strings for display

```javascript
source_fields: {
  get() {
    const source = this.$store.getters.knowledge?.source || {}
    
    // Transform Documentation arrays to comma-separated strings for display
    if (source.source_type === 'Documentation') {
      const transformed = { ...source }
      
      if (Array.isArray(transformed.languages)) {
        transformed.languages = transformed.languages.join(', ')
      }
      
      if (Array.isArray(transformed.sections)) {
        transformed.sections = transformed.sections.join(', ')
      }
      
      return transformed
    }
    
    return source
  },
  set(value) {
    this.$store.dispatch('updateKnowledge', { source: value })
  },
}
```

## How It Works

### Data Flow

1. **User Input**: User enters comma-separated values in the UI
   - Example: "en, ru" for languages
   - Example: "quickstarts, admin" for sections

2. **Save/Create**: When saving, the data is transformed
   - Strings are split by comma
   - Each value is trimmed
   - Empty values are filtered out
   - Arrays are created: `["en", "ru"]` and `["quickstarts", "admin"]`
   - `max_depth` is converted to integer

3. **API Call**: Transformed data is sent to the backend
   ```json
   {
     "source": {
       "source_type": "Documentation",
       "base_url": "http://localhost:5173",
       "languages": ["en", "ru"],
       "sections": ["quickstarts", "admin"],
       "max_depth": 5
     }
   }
   ```

4. **Load/Edit**: When loading existing data for editing
   - Arrays are converted back to comma-separated strings
   - Display: "en, ru" and "quickstarts, admin"

## User Interface

### Creating a New Documentation Source

1. Click "New" button in Knowledge Sources
2. Fill in "Basic configuration":
   - Name: e.g., "Magnet AI Documentation"
   - System name: e.g., "MAGNET_AI_DOCS"
   - Source type: Select "Documentation"
   - Base URL: e.g., "http://localhost:5173"
   - Languages: e.g., "en, ru"
   - Sections: e.g., "quickstarts, admin"
   - Max Crawl Depth: e.g., "5"
3. Configure chunking and indexing as usual
4. Click "Save" or "Save & Sync"

### Editing an Existing Documentation Source

1. Open the Documentation knowledge source
2. Go to "Settings" tab
3. Modify fields as needed
   - Note: Some fields are disabled after first sync
4. Click "Save" in the header

## Field Descriptions in UI

- **Base URL**: Base URL of the VitePress documentation site (e.g., http://localhost:5173)
- **Languages**: Comma-separated list of language codes (e.g., en,ru)
- **Sections**: Comma-separated list of documentation sections (e.g., quickstarts,admin)
- **Max Crawl Depth**: Maximum depth for crawling documentation pages (default: 5)

## Testing

To test the new Documentation source:

1. Ensure VitePress is running at http://localhost:5173
2. Create a new knowledge source with type "Documentation"
3. Fill in the configuration
4. Save and sync
5. Check that the data is correctly transformed and sent to the API
6. Verify that crawling works by checking the job logs
7. Edit the source and verify that fields display correctly

## Notes

- Fields are disabled after the first sync to prevent configuration changes
- The UI uses comma-separated strings for user-friendly input
- Data is automatically transformed to arrays when communicating with the backend
- When editing, arrays from the backend are converted back to comma-separated strings
