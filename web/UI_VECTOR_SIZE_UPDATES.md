# UI Updates for Vector Size Configuration

## Overview

The admin UI has been updated to support configuring vector dimensions for embedding models. This aligns with the backend changes that added the `configs` JSON field to the AI Models table.

## Changes Made

### 1. **NewModel.vue** (Model creation from Provider page)
- Added a new step (step 1) for embeddings models with vector configuration
- Added `vectorSize` computed property to handle `configs.vector_size`
- Added vector size input field with validation
- Updated `steps` computed property to show "Configuration" step for embeddings
- Updated `createModel()` method to include configs in payload

**UI Changes:**
- When creating an embeddings model, users now see a second step titled "Configuration"
- Vector Size input field with default value of 1536
- Helpful description showing common values: 1536, 1024, 3072

### 2. **CreateNew.vue** (Model creation from Models page)
- Added the same vector configuration step for embeddings models
- Added `vectorSize` computed property
- Updated `steps` logic to include configuration step for embeddings
- Updated `createModel()` method to handle configs properly

**UI Changes:**
- Similar to NewModel.vue
- Shows "Configuration" step instead of "Capabilities" for embeddings type

### 3. **ModelDrawer.vue** (Model editing drawer)
- **Replaced** the Features section with conditional rendering based on model type
- For `type === "prompts"`: Shows Features (JSON mode, Structured Outputs, Tool calling, Reasoning)
- For `type === "embeddings"`: Shows Vector Configuration with vector size input
- Added `vectorSize` computed property to read/write `configs.vector_size`
- Updated `save()` method to clean up empty configs objects

**UI Changes:**
- When editing a prompt model: Features section remains as before
- When editing an embeddings model: 
  - Features section is **replaced** with "Vector Configuration"
  - Shows Vector Size input field
  - Displays helpful description

## User Flow

### Creating an Embeddings Model

1. Navigate to Provider page or Models page
2. Click "Add Model" or "New Model"
3. Fill in basic settings (Step 0):
   - Provider model name (e.g., `text-embedding-3-small`)
   - System name (e.g., `OPENAI_EMBEDDING_3_SMALL`)
   - Display name (e.g., `OpenAI Embedding 3 Small`)
   - **Select Category: "Vector Embedding"**
4. Click "Next"
5. Configure vector settings (Step 1):
   - **Vector Size**: Enter dimension (e.g., 1024 for text-embedding-3-small)
   - See helpful hints about common values
6. Click "Create"

### Editing an Embeddings Model

1. Open an embeddings model in the drawer
2. Navigate to "Parameters" tab
3. Scroll to "Vector Configuration" section (replaces Features for embeddings)
4. Modify Vector Size as needed
5. Click "Save"

## Technical Details

### Data Structure

The `configs` field is stored as a JSON object:

```javascript
{
  "configs": {
    "vector_size": 1024
  }
}
```

### Computed Properties

All three components use a similar pattern:

```javascript
vectorSize: {
  get() {
    return this.newRow?.configs?.vector_size || 1536
  },
  set(val) {
    if (!this.newRow.configs) {
      this.newRow.configs = {}
    }
    this.newRow.configs.vector_size = parseInt(val) || 1536
  },
}
```

### Validation

- Vector size is expected to be a number
- Default value: 1536 (if not specified)
- The input uses `v-model.number` to ensure numeric type
- Empty configs objects are cleaned up before saving

## Common Vector Sizes

| Model | Vector Size | Notes |
|-------|-------------|-------|
| text-embedding-ada-002 | 1536 | Fixed size |
| text-embedding-3-small | 512-1536 | Configurable, default 1536 |
| text-embedding-3-large | 256-3072 | Configurable, default 3072 |
| Cohere embed-v3 | 1024 | Fixed size |

## Screenshots / UI Mockup

### Embeddings Model - Step 1 (Configuration)
```
┌─────────────────────────────────────────┐
│ Vector Configuration                     │
│                                          │
│ Vector Size                              │
│ ┌─────────────────────────────────────┐ │
│ │ 1024                                │ │
│ └─────────────────────────────────────┘ │
│ Dimension of the embedding vector        │
│ (default: 1536). Common values: 1536     │
│ (ada-002), 1024 (embed-3-small),        │
│ 3072 (embed-3-large)                    │
└─────────────────────────────────────────┘
```

### Model Drawer - Parameters Tab (Embeddings)
```
┌─────────────────────────────────────────┐
│ General settings                         │
│ ...                                      │
│ ─────────────────────────────────────── │
│                                          │
│ Vector Configuration                     │
│                                          │
│ Vector Size                              │
│ ┌─────────────────────────────────────┐ │
│ │ 1024                                │ │
│ └─────────────────────────────────────┘ │
│ Dimension of the embedding vector.       │
│ Common values: 1536 (ada-002), 1024     │
│ (embed-3-small), 3072 (embed-3-large)   │
└─────────────────────────────────────────┘
```

### Model Drawer - Parameters Tab (Prompts)
```
┌─────────────────────────────────────────┐
│ General settings                         │
│ ...                                      │
│ ─────────────────────────────────────── │
│                                          │
│ Features                                 │
│                                          │
│ ☑ JSON mode                             │
│ ☑ Structured Outputs                    │
│ ☑ Tool calling                          │
│ ☐ Reasoning                             │
└─────────────────────────────────────────┘
```

## Testing Checklist

- [ ] Create a new embeddings model with vector_size = 1024
- [ ] Verify configs field is saved correctly in database
- [ ] Edit an existing embeddings model and change vector_size
- [ ] Verify prompts models still show Features section
- [ ] Verify embeddings models show Vector Configuration instead of Features
- [ ] Create a collection with the new embeddings model
- [ ] Verify documents table is created with correct vector dimension
- [ ] Test with different vector sizes: 512, 1024, 1536, 3072

## Related Files

### Backend
- `api/src/core/db/models/ai_model/ai_model.py` - Database model
- `api/src/core/domain/ai_models/schemas.py` - Pydantic schemas
- `api/src/stores/pgvector_db/store.py` - Vector store implementation

### Frontend
- `web/apps/@ipr/magnet-admin/src/components/ModelProviders/NewModel.vue`
- `web/apps/@ipr/magnet-admin/src/components/ModelConfig/CreateNew.vue`
- `web/apps/@ipr/magnet-admin/src/components/ModelProviders/ModelDrawer.vue`

## Migration Notes

### For Existing Embeddings Models

Existing embeddings models without `configs.vector_size` will:
1. Default to 1536 dimensions in the UI
2. Continue to work with existing collections (tables already created with 1536)
3. Can be edited to set the correct vector_size for future collections

### For New Collections

When creating a new collection with an embeddings model:
1. The system checks the model's `configs.vector_size`
2. Creates the documents table with the specified dimension
3. Falls back to 1536 if not configured

## Future Enhancements

- Add validation to ensure vector_size is within reasonable bounds (e.g., 128-8192)
- Add presets for common models (e.g., "OpenAI ada-002 (1536)", "OpenAI 3-small (1024)")
- Show warning when changing vector_size on a model with existing collections
- Add bulk migration tool to convert collections from one vector size to another
