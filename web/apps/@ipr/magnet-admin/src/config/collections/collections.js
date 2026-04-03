import { required, minLength, validJson, validSystemName } from '@shared/utils/validationRules'
import NameDescription from '@/config/rag-tools/component/NameDescription.vue'
import { markRaw, ref } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { ChipCopy } from '@ui'
import { getCachedItems } from '@/queries/getCachedItems'
import { m } from '@/paraglide/messages'

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
      label: m.collections_library(),
      field: 'sharepoint_library',
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'sharepoint_folder',
      label: m.collections_folder(),
      field: 'sharepoint_folder',
      component: 'km-input',
      readonly: (collection) => !!collection?.sharepoint_folder,
      type: 'String',
    },
    {
      name: 'sharepoint_recursive',
      label: m.collections_includeSubfolders(),
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
      label: m.collections_pageName(),
      field: 'sharepoint_pages_page_name',
      component: 'km-input',
      disable: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'sharepoint_pages_embed_title',
      label: m.collections_embedTitlesInsteadOfContent(),
      field: 'sharepoint_pages_embed_title',
      component: 'km-toggle',
      disable: (collection) => !!collection?.last_synced,
      type: 'Boolean',
    },
  ],
  File: [
    {
      name: 'file_url',
      label: m.collections_fileUrls(),
      field: 'file_url',
      description: m.collections_supportedFileLinks(),
      component: 'file-url-upload',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
  ],
  Hubspot: [],
  Salesforce: [
    {
      name: 'object_api_name',
      label: m.collections_objectApiName(),
      field: 'object_api_name',
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'output_config',
      label: m.collections_outputConfig(),
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
      label: m.collections_confluenceSpaceKey(),
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
      label: m.collections_searchFilters(),
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
      label: m.collections_languages(),
      field: 'languages',
      description: m.collections_languagesHint(),
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'sections',
      label: m.collections_sections(),
      field: 'sections',
      description: m.collections_sectionsHint(),
      component: 'km-input',
      readonly: (collection) => !!collection?.last_synced,
      type: 'String',
    },
    {
      name: 'max_depth',
      label: m.collections_maxCrawlDepth(),
      field: 'max_depth',
      description: m.collections_maxCrawlDepthHint(),
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
  const plugins = getCachedItems('plugins') || []

  if (plugins.length === 0) {
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

}

/**
 * Get provider fields configuration for a specific plugin type
 */
export function getProviderFields(pluginType) {
  const plugins = getCachedItems('plugins') || []
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
    label: m.common_nameDescription(),
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
    label: m.common_category(),
    field: 'category',
    options: [m.collections_knowledgeBase(), m.collections_userManual()],
    columnNumber: 3,
    validate: true,
    rules: [required()],
    display: false,
    fromMetadata: false,
  },
  description: {
    description: 'description',
    label: m.common_description(),
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
    label: m.common_systemName(),
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
    label: m.common_created(),
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
    label: m.collections_lastSynced(),
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
    label: m.collections_showInQa(),
    field: 'show_in_qa',
    type: 'Boolean',
    format: (val) => (val ? m.common_yes() : m.common_no()),
    columnNumber: 4,
    fromMetadata: false,
    display: false,
  },
  source_type: {
    name: 'source_type',
    label: m.collections_source(),
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
    label: m.common_name(),
    field: 'name',
    validate: true,
    rules: [required(), minLength(3, 'Collection name must consist of more than 3 characters')],
    columnNumber: 0,
    display: false,

    fromMetadata: false,
  },
  type: {
    name: 'type',
    label: m.common_type(),
    field: 'type',
    options: [m.collections_public(), m.collections_internal()],
    columnNumber: 2,
    validate: true,
    rules: [required()],
    fromMetadata: false,
    display: false,
  },
  chunking_strategy: {
    name: 'chunking_strategy',
    label: m.collections_chunkingStrategy(),
    field: 'chunking_strategy',
    options: [
      { label: m.collections_none(), value: 'none' },
      { label: m.collections_recursiveCharacterTextSplitting(), value: 'recursive_character_text_splitting' },
      { label: m.collections_htmlHeaderSplitting(), value: 'html_header_splitting' },
    ],
    columnNumber: 2,
    validate: true,
    rules: [required()],
    fromMetadata: false,
    display: false,
  },
  chunk_size: {
    name: 'chunk_size',
    label: m.collections_chunkSize(),
    field: 'chunk_size',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_overlap: {
    name: 'chunk_overlap',
    label: m.collections_chunkOverlap(),
    field: 'chunk_overlap',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_transformation_method: {
    name: 'chunk_transformation_method',
    label: m.collections_chunkTransformationMethod(),
    field: 'chunk_transformation_method',
    options: [
      { label: m.collections_replaceChunkContent(), value: 'replace' },
      { label: m.collections_prependBeforeChunk(), value: 'prepend' },
      { label: m.collections_appendAfterChunk(), value: 'append' },
    ],
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  chunk_usage_method: {
    name: 'chunk_usage_method',
    label: m.collections_chunkUsageMethod(),
    field: 'chunk_usage_method',
    options: [
      { label: m.collections_useOriginalChunkBoth(), value: 'original_both' },
      { label: m.collections_useTransformedChunkBoth(), value: 'transformed_both' },
      { label: m.collections_useOriginalIndexingTransformedRetrieval(), value: 'original_indexing_transformed_retrieval' },
      { label: m.collections_useTransformedIndexingOriginalRetrieval(), value: 'transformed_indexing_original_retrieval' },
    ],
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  semantic_search_supported: {
    name: 'semantic_search_supported',
    label: m.collections_supportSemanticSearch(),
    field: 'semantic_search_supported',
    type: 'Boolean',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  support_keyword_search: {
    name: 'support_keyword_search',
    label: m.collections_supportKeywordSearch(),
    field: 'support_keyword_search',
    type: 'Boolean',
    columnNumber: 2,
    validate: true,
    fromMetadata: false,
    display: false,
  },
  metadata: {
    name: 'metadata',
    label: m.common_metadata(),
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
