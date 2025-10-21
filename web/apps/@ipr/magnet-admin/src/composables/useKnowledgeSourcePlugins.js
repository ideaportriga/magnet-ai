import { ref, computed } from 'vue'
import { useChroma } from '@shared'

/**
 * Composable for loading and managing knowledge source plugins from backend
 * 
 * This composable fetches available plugins from the API and transforms them
 * into the format expected by the frontend forms.
 */
export function useKnowledgeSourcePlugins() {
  const plugins = ref([])
  const loading = ref(false)
  const error = ref(null)

  /**
   * Fetch plugins from backend
   */
  async function fetchPlugins() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/admin/knowledge_sources/plugins')
      if (!response.ok) {
        throw new Error(`Failed to fetch plugins: ${response.statusText}`)
      }
      const data = await response.json()
      plugins.value = data.plugins || []
      
      console.log('Fetched plugins from API:', plugins.value.length, 'plugins')
      console.log('Plugin source types:', plugins.value.map(p => p.source_type))
    } catch (err) {
      error.value = err.message
      console.error('Error fetching knowledge source plugins:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Get list of source type options for dropdown
   */
  const sourceTypeOptions = computed(() => {
    return plugins.value.map(plugin => plugin.source_type)
  })

  /**
   * Transform plugin field schema to frontend component config
   * Backend now returns fields in the correct format, so we just need to convert
   * readonly_after_sync to a function for collections
   * 
   * @param {Object} field - Field from plugin schema (already formatted by backend)
   * @returns {Object} Frontend component config
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

  /**
   * Get source type children configuration for all plugins
   * Format: { 'PluginName': [field configs], ... }
   * 
   * Backend now separates provider_fields from source_fields,
   * so we only use source_fields here (no filtering needed)
   */
  const sourceTypeChildren = computed(() => {
    const children = {
      '': [], // Empty source type
    }

    plugins.value.forEach(plugin => {
      // Backend already separates source_fields from provider_fields
      const fields = plugin.source_fields || []
      
      children[plugin.source_type] = fields.map(transformFieldToComponent)
    })

    return children
  })

  /**
   * Get provider fields configuration for a specific plugin type
   * These are the fields that should be configured at the provider level
   * 
   * @param {string} pluginType - Plugin source_type
   * @returns {Array} Provider field configurations
   */
  function getProviderFields(pluginType) {
    const plugin = plugins.value.find(p => p.source_type === pluginType)
    if (!plugin) return []

    return (plugin.provider_fields || []).map(field => ({
      ...transformFieldToComponent(field),
      // Provider fields should not be readonly based on last_synced
      readonly: false,
    }))
  }

  /**
   * Get plugin metadata by source type
   * 
   * @param {string} sourceType - Plugin source_type
   * @returns {Object|null} Plugin metadata
   */
  function getPluginMetadata(sourceType) {
    return plugins.value.find(p => p.source_type === sourceType) || null
  }

  return {
    plugins,
    loading,
    error,
    fetchPlugins,
    sourceTypeOptions,
    sourceTypeChildren,
    getProviderFields,
    getPluginMetadata,
  }
}
