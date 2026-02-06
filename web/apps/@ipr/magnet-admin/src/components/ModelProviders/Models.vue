<template lang="pug">
.column(style='width: 100%; overflow: hidden')
  .row
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(flat, label='Import', icon='fas fa-download', @click='openImportDialog', :loading='loadingAvailableModels')
      km-btn.q-mr-12(label='New', @click='showNewDialog = true')
  .row.q-mt-md
    .col-auto.center-flex-y
      km-filter-bar(v-model:config='filterConfig', v-model:filterObject='filterObject', outputFormat='sql')
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(
        v-if='selected.length > 0',
        icon='delete',
        label='Delete',
        @click='showDeleteDialog = true',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='16px',
        hoverBg='primary-bg'
      )
  .row.q-mt-md(style='overflow-x: auto; width: 100%')
    km-table-new(
      @selectRow='openDetails',
      selection='multiple',
      row-key='id',
      :active-record-id='modelConfig?.id',
      v-model:selected='selected',
      :columns='columns',
      :visibleColumns='visibleColumns',
      :rows='filteredRows',
      :pagination='pagination',
      binary-state-sort
    )
model-providers-new-model(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Models
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected models. Are you sure?` }}

//- Import Models Dialog
q-dialog(v-model='showImportDialog', persistent)
  q-card(style='min-width: 700px; max-width: 900px; max-height: 85vh')
    q-card-section.row.items-center.q-pb-none
      .km-heading-7 Import Models from Provider
      q-space
      q-btn(icon='close', flat, round, dense, @click='showImportDialog = false')
    
    q-card-section
      //- Source indicator banner
      .row.items-center.q-gutter-sm.q-mb-md
        .km-description.text-secondary-text
          | Models from 
          strong {{ provider?.name }}
        km-chip(
          :label="availableModelsSource === 'api' ? 'Provider API' : 'LiteLLM Registry'",
          :color="availableModelsSource === 'api' ? 'positive' : 'primary-light'",
          :text-color="availableModelsSource === 'api' ? 'white' : 'primary'",
          round
        )
        km-chip(v-if='availableModelsProviderType', :label='availableModelsProviderType', color='light', text-color='grey-8', round)
      
      //- Info/Warning about source
      q-banner.q-mb-md(v-if="availableModelsSource === 'litellm'", rounded, dense, class='bg-amber-1')
        template(#avatar)
          q-icon(name='o_info', color='amber-8')
        .text-caption.text-grey-8
          | Model list from LiteLLM registry. Capabilities are estimated and may not reflect actual provider features.
      
      q-banner.q-mb-md(v-else-if="availableModelsSource === 'api' && availableModelsError", rounded, dense, class='bg-amber-1')
        template(#avatar)
          q-icon(name='o_warning', color='amber-8')
        .text-caption.text-grey-8 {{ availableModelsError }}
      
      //- Search filter
      km-input.q-mb-md(
        placeholder='Filter models...',
        iconBefore='search',
        v-model='importSearchString',
        @input='importSearchString = $event',
        clearable
      )
      
      //- Models list
      .q-mt-sm(style='max-height: 400px; overflow-y: auto')
        q-list(v-if='filteredAvailableModels.length > 0', separator)
          q-item(
            v-for='model in filteredAvailableModels',
            :key='model.id',
            clickable,
            @click='toggleModelSelection(model)',
            :class="{ 'bg-grey-2': isModelSelected(model) }"
          )
            q-item-section(side)
              q-checkbox(
                :model-value='isModelSelected(model)',
                @update:model-value='toggleModelSelection(model)',
                :disable='isModelAlreadyAdded(model)'
              )
            q-item-section
              q-item-label.row.items-center.q-gap-8
                span {{ model.id }}
                km-chip(
                  :label="model.model_type === 'embeddings' ? 'Embeddings' : 'Chat'",
                  :color="model.model_type === 'embeddings' ? 'in-progress' : 'primary-light'",
                  :text-color="model.model_type === 'embeddings' ? 'grey-7' : 'primary'",
                  round
                )
              q-item-label(caption)
                .row.items-center.q-gap-4
                  span(v-if='model.owned_by') {{ model.owned_by }}
                  template(v-if='model.max_tokens')
                    span.text-grey-5 •
                    span {{ formatTokens(model.max_tokens) }} tokens
            q-item-section(side)
              .row.items-center.q-gap-4
                template(v-if='isModelAlreadyAdded(model)')
                  km-chip(label='Already added', color='light', text-color='grey-7', round)
                template(v-else)
                  km-chip(v-if='model.supports_function_calling', label='Tools', color='primary-light', text-color='primary', round, tooltip='Function/Tool Calling')
                  km-chip(v-if='model.supports_json_mode', label='JSON', color='primary-light', text-color='primary', round, tooltip='JSON Mode')
                  km-chip(v-if='model.supports_vision', label='Vision', color='primary-light', text-color='primary', round, tooltip='Vision/Image Support')
        
        .text-center.q-pa-lg.text-secondary-text(v-else-if='!loadingAvailableModels')
          | No models found
          template(v-if='availableModelsError && !availableModels.length')
            .q-mt-sm.text-negative {{ availableModelsError }}
    
    q-card-actions.q-pa-md(align='right')
      .text-secondary-text.q-mr-md(v-if='selectedModelsToImport.length > 0')
        | {{ selectedModelsToImport.length }} model(s) selected
      km-btn(flat, label='Cancel', color='primary', @click='showImportDialog = false')
      km-btn(
        label='Import Selected',
        @click='importSelectedModels',
        :disable='selectedModelsToImport.length === 0',
        :loading='importingModels'
      )
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma, toUpperCaseWithUnderscores } from '@shared'
import { categoryOptions, featureOptions } from '../../config/model/model.js'

/**
 * Fuzzy match a query against a target string.
 * Returns a score > 0 if matched, 0 if not matched.
 * Higher score = better match.
 */
function fuzzyMatch(query, target) {
  if (!query || !target) return 0
  
  const q = query.toLowerCase()
  const t = target.toLowerCase()
  
  // Exact substring match gets highest score
  if (t.includes(q)) return 1000 + (q.length / t.length) * 100
  
  // Starts-with match gets very high score
  if (t.startsWith(q)) return 2000
  
  // Fuzzy subsequence matching
  let qi = 0
  let ti = 0
  let score = 0
  let consecutive = 0
  let lastMatchIndex = -2
  
  while (qi < q.length && ti < t.length) {
    if (q[qi] === t[ti]) {
      // Bonus for consecutive matches
      if (ti === lastMatchIndex + 1) {
        consecutive++
        score += consecutive * 3
      } else {
        consecutive = 1
        score += 1
      }
      
      // Bonus for matching at word boundaries (after -, _, ., space, or start)
      if (ti === 0 || '-_. '.includes(t[ti - 1])) {
        score += 5
      }
      
      // Bonus for matching uppercase letters (camelCase boundaries)
      if (ti > 0 && target[ti] === target[ti].toUpperCase() && target[ti] !== target[ti].toLowerCase()) {
        score += 3
      }
      
      lastMatchIndex = ti
      qi++
    }
    ti++
  }
  
  // All query characters must be found
  if (qi < q.length) return 0
  
  // Bonus for shorter targets (more precise match)
  score += Math.max(0, 10 - (t.length - q.length))
  
  return score
}

export default {
  setup() {
    const { searchString, pagination, columns, visibleColumns, visibleRows, selectedRow, delete: deleteItem, create } = useChroma('model')

    const filterObject = ref({})

    const filterConfig = {
      type: {
        key: 'type',
        label: 'Type',
        multiple: true,
        options: categoryOptions,
      },
      features: {
        key: 'features',
        label: 'Features',
        multiple: true,
        options: featureOptions,
        customLogic: (selected) => ({ $or: selected.map((feature) => ({ [feature]: true })) }),
      },
    }

    return {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
      selectedRow,
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      filterObject,
      filterConfig,
      deleteItem,
      create,
      // Import dialog state
      showImportDialog: ref(false),
      availableModels: ref([]),
      availableModelsSource: ref(''),
      availableModelsProviderType: ref(''),
      availableModelsError: ref(null),
      loadingAvailableModels: ref(false),
      selectedModelsToImport: ref([]),
      importSearchString: ref(''),
      importingModels: ref(false),
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    filteredRows() {
      let rows = this.visibleRows.filter((item) => item.provider_system_name === this.provider.system_name)

      // Apply type filter
      if (this.filterObject.typeIn && this.filterObject.typeIn.length > 0) {
        rows = rows.filter((item) => this.filterObject.typeIn.includes(item.type))
      }

      // Apply features filter
      if (this.filterObject.featuresIn && this.filterObject.featuresIn.length > 0) {
        rows = rows.filter((item) => {
          return this.filterObject.featuresIn.some((feature) => item[feature] === true)
        })
      }

      return rows
    },
    modelConfig() {
      return this.$store.getters['modelConfig/entity']
    },
    // Filter available models by fuzzy search
    filteredAvailableModels() {
      if (!this.importSearchString) {
        return this.availableModels
      }
      const query = this.importSearchString.trim()
      if (!query) return this.availableModels
      
      return this.availableModels
        .map(m => {
          const idScore = fuzzyMatch(query, m.id)
          const ownerScore = m.owned_by ? fuzzyMatch(query, m.owned_by) * 0.5 : 0
          return { model: m, score: Math.max(idScore, ownerScore) }
        })
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score)
        .map(item => item.model)
    },
    // Get list of already added model names
    existingModelNames() {
      return this.filteredRows.map(m => m.ai_model?.toLowerCase() || m.name?.toLowerCase())
    },
  },
  methods: {
    openDetails(row) {
      this.$store.commit('modelConfig/setEntity', row)
    },
    async deleteSelected() {
      try {
        for (const item of this.selected) {
          await this.deleteItem(item)
        }
        this.selected = []
        this.showDeleteDialog = false
        this.$q.notify({
          position: 'top',
          message: 'Models deleted successfully.',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } catch (error) {
        console.error('Error deleting models:', error)
        this.$q.notify({
          position: 'top',
          message: 'Error deleting models.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      }
    },
    // Import methods
    async openImportDialog() {
      this.loadingAvailableModels = true
      this.availableModels = []
      this.selectedModelsToImport = []
      this.importSearchString = ''
      this.availableModelsError = null
      this.availableModelsProviderType = ''
      
      try {
        const result = await this.$store.dispatch('chroma/availableModels', { 
          payload: this.provider?.id, 
          entity: 'provider' 
        })
        
        if (result) {
          this.availableModels = result.models || []
          this.availableModelsSource = result.source || ''
          this.availableModelsProviderType = result.provider_type || ''
          this.availableModelsError = result.error || null
        }
        
        this.showImportDialog = true
      } catch (error) {
        console.error('Error loading available models:', error)
        this.$q.notify({
          position: 'top',
          message: 'Failed to load available models.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      } finally {
        this.loadingAvailableModels = false
      }
    },
    isModelSelected(model) {
      return this.selectedModelsToImport.some(m => m.id === model.id)
    },
    isModelAlreadyAdded(model) {
      return this.existingModelNames.includes(model.id.toLowerCase())
    },
    toggleModelSelection(model) {
      if (this.isModelAlreadyAdded(model)) return
      
      const index = this.selectedModelsToImport.findIndex(m => m.id === model.id)
      if (index === -1) {
        this.selectedModelsToImport.push(model)
      } else {
        this.selectedModelsToImport.splice(index, 1)
      }
    },
    formatProviderName(name) {
      if (!name) return ''
      return name
        .replace(/_/g, ' ')
        .toLowerCase()
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },
    formatTokens(num) {
      if (!num) return '0'
      if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
      if (num >= 1000) return `${(num / 1000).toFixed(0)}K`
      return num.toString()
    },
    async importSelectedModels() {
      if (this.selectedModelsToImport.length === 0) return
      
      this.importingModels = true
      let successCount = 0
      let errorCount = 0
      
      try {
        for (const model of this.selectedModelsToImport) {
          // Use model capabilities from the available models data
          const modelType = model.model_type || 'prompts'
          const payload = {
            name: model.id,
            ai_model: model.id,
            system_name: toUpperCaseWithUnderscores(this.provider.system_name + '_' + model.id),
            display_name: `${this.formatProviderName(this.provider.name)}: ${model.id}`,
            provider_name: this.provider.system_name,
            provider_system_name: this.provider.system_name,
            type: modelType,
            // Set features based on capabilities from LiteLLM
            json_mode: model.supports_json_mode || false,
            json_schema: model.supports_response_schema || false,
            tool_calling: model.supports_function_calling || false,
            reasoning: false, // Not available from LiteLLM currently
            description: null,
          }
          
          try {
            await this.create(JSON.stringify(payload))
            successCount++
          } catch (error) {
            console.error(`Error creating model ${model.id}:`, error)
            errorCount++
          }
        }
        
        this.showImportDialog = false
        this.selectedModelsToImport = []
        
        if (successCount > 0) {
          this.$q.notify({
            position: 'top',
            message: `Successfully imported ${successCount} model(s).`,
            color: 'positive',
            textColor: 'black',
            timeout: 2000,
          })
        }
        
        if (errorCount > 0) {
          this.$q.notify({
            position: 'top',
            message: `Failed to import ${errorCount} model(s).`,
            color: 'warning',
            textColor: 'black',
            timeout: 2000,
          })
        }
      } catch (error) {
        console.error('Error importing models:', error)
        this.$q.notify({
          position: 'top',
          message: 'Error importing models.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      } finally {
        this.importingModels = false
      }
    },
  },
}
</script>
