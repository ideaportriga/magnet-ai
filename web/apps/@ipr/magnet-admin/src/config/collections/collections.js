import { required, minLength, validJson, validSystemName } from '@shared/utils/validationRules'
import NameDescription from '@/config/rag-tools/component/NameDescription.vue'
import { markRaw, ref } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { ChipCopy } from '@ui'
import store from '@/store'

/**
 * Transform plugin field schema to frontend component config
 */
function transformFieldToComponent(field) {
  const config = { ...field }

  // Convert readonly_after_sync boolean to a function
  if (field.readonly_after_sync) {
    config.readonly = (collection) => !!collection?.last_synced
    delete config.readonly_after_sync
  } else if (typeof field.readonly === 'boolean') {
    // Keep boolean readonly as-is
    const readonlyValue = field.readonly
    config.readonly = () => readonlyValue
  }

  return config
}

// Static sourceTypeChildren as fallback (will be replaced by dynamic data)
const staticSourceTypeChildren = {
  '': [],
  Sharepoint: [
    // sharepoint_site_url is now in provider (not here)
    {
      name: 'sharepoint_library',
      label: 'Library',
      field: 'sharepoint_library',
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'sharepoint_folder',
      label: 'Folder',
      field: 'sharepoint_folder',
      component: 'km-input',
      readonly: (collection) => !!collection?.sharepoint_folder,
      type: 'String',
    },
    {
      name: 'sharepoint_recursive',
      label: 'Include subfolders',
      field: 'sharepoint_recursive',
      component: 'km-toggle',
      disable: (collection) => !!collection?.sharepoint_recursive,
      type: 'Boolean',
    },
  ],
  'Sharepoint Pages': [
    // sharepoint_site_url is now in provider (not here)
    {
      name: 'sharepoint_pages_page_name',
      label: 'Page name',
      field: 'sharepoint_pages_page_name',
      component: 'km-input',
      disable: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'sharepoint_pages_embed_title',
      label: 'Embed titles instead of content',
      field: 'sharepoint_pages_embed_title',
      component: 'km-toggle',
      disable: (collection) => !!collection?.last_synced,
      type: 'Boolean',
    },
  ],
  File: [
    {
      name: 'file_url',
      label: 'File URL(s)',
      field: 'file_url',
      description: 'Only links to PDF files are accepted',
      component: 'km-input-list-add',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
  ],
  Hubspot: [],
  Salesforce: [
    {
      name: 'object_api_name',
      label: 'Object API Name',
      field: 'object_api_name',
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'output_config',
      label: 'Output config',
      field: 'output_config',
      component: 'km-codemirror',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
  ],
  Confluence: [
    // confluence_url is now in provider (not here)
    {
      name: 'confluence_space',
      label: 'Confluence space key',
      field: 'confluence_space',
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
  ],
  RightNow: [
    // rightnow_url is now in provider (not here)
  ],
  'Manual Upload': [],
  'Oracle Knowledge': [
    // oracle_knowledge_url is now in provider (not here)
  ],
  'Fluid Topics': [
    {
      name: 'fluid_topics_search_filters',
      label: 'Search filters',
      field: 'fluid_topics_search_filters',
      component: 'km-codemirror',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
  ],
  Documentation: [
    // base_url is now in provider (not here)
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
  ],
}

// Static source type options as fallback (extracted from staticSourceTypeChildren keys)
const staticSourceTypeOptions = Object.keys(staticSourceTypeChildren).filter((key) => key !== '')

// Export reactive references that will be updated when plugins are loaded
export const sourceTypeChildren = ref(staticSourceTypeChildren)
export const sourceTypeOptions = ref(staticSourceTypeOptions)

/**
 * Initialize plugins data from store
 * Call this function after plugins have been loaded into the store
 */
export function initializePlugins() {
  const plugins = store.state?.chroma?.plugins?.items || []

  console.log('Initializing plugins from store:', plugins.length, 'plugins')

  if (plugins.length === 0) {
    console.warn('No plugins found in store. Using static configuration.')
    return
  }

  // Build sourceTypeChildren from plugins
  const children = {
    '': [], // Empty source type
  }

  plugins.forEach((plugin) => {
    const fields = plugin.source_fields || []
    children[plugin.source_type] = fields.map(transformFieldToComponent)
  })

  // Build sourceTypeOptions
  const options = plugins.map((plugin) => plugin.source_type)

  // Update reactive references with data from store
  sourceTypeChildren.value = children
  sourceTypeOptions.value = options

  console.log('Updated sourceTypeOptions to:', sourceTypeOptions.value)
  console.log('Updated sourceTypeChildren keys to:', Object.keys(sourceTypeChildren.value))
}

/**
 * Get provider fields configuration for a specific plugin type
 */
export function getProviderFields(pluginType) {
  const plugins = store.state?.chroma?.plugins?.items || []
  const plugin = plugins.find((p) => p.source_type === pluginType)

  if (!plugin) return []

  return (plugin.provider_fields || []).map((field) => ({
    ...transformFieldToComponent(field),
    // Provider fields should not be readonly based on last_synced
    readonly: false,
  }))
}

const controls = {
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
  },
  nameDescription: {
    name: 'nameDescription',
    label: 'Name',
    field: 'name',
    type: 'component',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
    columnNumber: 0,
    rules: [required(), minLength(3, 'Collection name must consist of more than 3 characters')],
  },

  category: {
    name: 'category',
    label: 'Category',
    field: 'category',
    options: ['Knowledge base', 'User Manual'],
    columnNumber: 3,
    validate: true,
    rules: [required()],
    display: false,
    fromMetadata: false,
  },
  description: {
    description: 'description',
    label: 'Description',
    field: 'description',
    name: 'description',
    validate: true,
    columnNumber: 0,
    display: false,
    fromMetadata: false,
  },
  system_name: {
    name: 'system_name',
    code: 'system_name',
    display: true,
    label: 'System name',
    field: 'system_name',
    type: 'component',
    component: markRaw(ChipCopy),
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(3, 'RAG Tools system name must consist of more than 3 characters'), validSystemName()],
    align: 'left',
    classes: 'km-button-xs-text',
  },
  created: {
    name: 'created',
    label: 'Created',
    field: 'created_at',
    type: 'Date',
    display: true,
    format: (val) => formatDateTime(val),
    ignorePatch: true,
    columnNumber: 5,
    fromMetadata: false,
    align: 'left',
    sortable: true,
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  last_synced: {
    name: 'last_synced',
    label: 'Last synced',
    field: 'last_synced',
    readonly: true,
    type: 'Date',
    format: (val) => formatDateTime(val),
    ignorePatch: true,
    columnNumber: 6,
    fromMetadata: false,
  },
  show_in_qa: {
    name: 'show_in_qa',
    label: 'Show in Q&A',
    field: 'show_in_qa',
    type: 'Boolean',
    format: (val) => (val ? 'Yes' : 'No'),
    columnNumber: 4,
    fromMetadata: false,
    display: false,
  },
  source_type: {
    name: 'source_type',
    label: 'Source',
    field: (row) => row?.source?.source_type,
    // Use dynamic options from plugins
    get options() {
      return sourceTypeOptions.value
    },
    // Use dynamic children from plugins
    get children() {
      return sourceTypeChildren.value
    },
    columnNumber: 1,
    validate: true,
    rules: [required()],
    fromMetadata: false,
  },
  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
    validate: true,
    rules: [required(), minLength(3, 'Collection name must consist of more than 3 characters')],
    columnNumber: 0,
    display: false,

    fromMetadata: false,
  },
  type: {
    name: 'type',
    label: 'Type',
    field: 'type',
    options: ['Public', 'Internal'],
    columnNumber: 2,
    validate: true,
    rules: [required()],
    fromMetadata: false,
    display: false,
  },
  chunking_strategy: {
    name: 'chunking_strategy',
    label: 'Chunking strategy',
    field: 'chunking_strategy',
    options: [
      { label: 'None', value: 'none' },
      { label: 'Recursive Character Text Splitting', value: 'recursive_character_text_splitting' },
      { label: 'HTML Header Splitting', value: 'html_header_splitting' },
    ],
    columnNumber: 2,
    validate: true,
    rules: [required()],
    fromMetadata: false,
    display: false,
  },
  chunk_size: {
    name: 'chunk_size',
    label: 'Chunk size',
    field: 'chunk_size',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_overlap: {
    name: 'chunk_overlap',
    label: 'Chunk overlap',
    field: 'chunk_overlap',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_transformation_method: {
    name: 'chunk_transformation_method',
    label: 'Chunk transformation method',
    field: 'chunk_transformation_method',
    options: [
      { label: 'Replace chunk content', value: 'replace' },
      { label: 'Prepend before chunk', value: 'prepend' },
      { label: 'Append after chunk', value: 'append' },
    ],
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_usage_method: {
    name: 'chunk_usage_method',
    label: 'Chunk usage method',
    field: 'chunk_usage_method',
    options: [
      { label: 'Use original chunk for both indexing and retrieval', value: 'original_both' },
      { label: 'Use transformed chunk for both indexing and retrieval', value: 'transformed_both' },
      { label: 'Use original chunk for indexing and transformed chunk for retrieval', value: 'original_indexing_transformed_retrieval' },
      { label: 'Use transformed chunk for indexing and original chunk for retrieval', value: 'transformed_indexing_original_retrieval' },
    ],
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  semantic_search_supported: {
    name: 'semantic_search_supported',
    label: 'Support semantic search',
    field: 'semantic_search_supported',
    type: 'Boolean',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  support_keyword_search: {
    name: 'support_keyword_search',
    label: 'Support keyword search',
    field: 'support_keyword_search',
    type: 'Boolean',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  metadata: {
    name: 'metadata',
    label: 'metadata',
    field: 'metadata',
    readonly: false,
    type: 'Object',
    display: false,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [validJson()],
  },
}

export default controls
