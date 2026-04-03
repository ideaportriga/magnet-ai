<template lang="pug">
.column.full-height(style='width: 100%; min-height: 0').no-wrap
  .row
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
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
        v-if='selectedRows.length > 0',
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
  .col.q-mt-md(style='min-height: 0; overflow-x: auto')
    km-data-table(
      fill-height,
      :table='table',
      row-key='id',
      :activeRowId='modelConfig?.id',
      @row-click='openDetails'
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
  .row.text-center.justify-center {{ `You are going to delete ${selectedRows?.length} selected models. Are you sure?` }}

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
                  :label="model.model_type === 'embeddings' ? 'Embeddings' : (model.model_type === 'stt' ? 'STT' : 'Chat')",
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
import { ref, computed, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { getEntityApis } from '@/api'
import { categoryOptions, featureOptions } from '../../config/model/model.js'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TypeChip from '@/config/model/component/TypeChip.vue'
import Features from '@/config/model/component/Features.vue'
import Check from '@/config/model/component/Check.vue'

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
      if (ti === lastMatchIndex + 1) {
        consecutive++
        score += consecutive * 3
      } else {
        consecutive = 1
        score += 1
      }

      if (ti === 0 || '-_. '.includes(t[ti - 1])) {
        score += 5
      }

      if (ti > 0 && target[ti] === target[ti].toUpperCase() && target[ti] !== target[ti].toLowerCase()) {
        score += 3
      }

      lastMatchIndex = ti
      qi++
    }
    ti++
  }

  if (qi < q.length) return 0

  score += Math.max(0, 10 - (t.length - q.length))

  return score
}

export default {
  props: {
    selectedModel: {
      type: Object,
      default: null,
    },
  },
  emits: ['select-model'],
  setup() {
    const queries = useEntityQueries()
    const { draft: providerDraft } = useEntityDetail('provider')
    const { data: listData } = queries.model.useList()
    const { mutateAsync: deleteItem } = queries.model.useRemove()
    const { mutateAsync: createEntity } = queries.model.useCreate()

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

    const columns = [
      selectionColumn(),
      textColumn('display_name', 'Display name'),
      textColumn('ai_model', 'Name'),
      componentColumn('type', 'Type', markRaw(TypeChip), {
        accessorKey: 'type',
        sortable: true,
      }),
      componentColumn('features', 'Features', markRaw(Features), {
        props: (row) => ({ name: 'features' }),
      }),
      componentColumn('is_default', 'Default', markRaw(Check), {
        accessorKey: 'is_default',
        sortable: true,
        align: 'center',
        props: (row) => ({ name: 'is_default' }),
      }),
      componentColumn('is_active', 'Active', markRaw(Check), {
        accessorKey: 'is_active',
        sortable: true,
        align: 'center',
        props: (row) => ({ name: 'is_active' }),
      }),
    ]

    // Filtered data based on provider and filter bar
    const filteredData = computed(() => {
      const items = listData.value?.items ?? []
      let rows = items.filter((item) => item.provider_system_name === providerDraft.value?.system_name)

      // Apply type filter
      if (filterObject.value.typeIn && filterObject.value.typeIn.length > 0) {
        rows = rows.filter((item) => filterObject.value.typeIn.includes(item.type))
      }

      // Apply features filter
      if (filterObject.value.featuresIn && filterObject.value.featuresIn.length > 0) {
        rows = rows.filter((item) => {
          return filterObject.value.featuresIn.some((feature) => item[feature] === true)
        })
      }

      return rows
    })

    const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(filteredData, columns, {
      enableRowSelection: true,
    })

    return {
      providerDraft,
      table,
      globalFilter,
      selectedRows,
      clearSelection,
      filterObject,
      filterConfig,
      deleteItem,
      createEntity,
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
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
      return this.providerDraft
    },
    modelConfig() {
      return this.selectedModel
    },
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
    existingModelNames() {
      return (this.table.getRowModel().rows ?? []).map(r => {
        const m = r.original
        return m.ai_model?.toLowerCase() || m.name?.toLowerCase()
      })
    },
  },
  methods: {
    openDetails(row) {
      this.$emit('select-model', row)
    },
    async deleteSelected() {
      try {
        for (const item of this.selectedRows) {
          await this.deleteItem(item)
        }
        this.clearSelection()
        this.showDeleteDialog = false
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Models deleted successfully.', timeout: 1000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Error deleting models.', timeout: 2000 })
      }
    },
    async openImportDialog() {
      this.loadingAvailableModels = true
      this.availableModels = []
      this.selectedModelsToImport = []
      this.importSearchString = ''
      this.availableModelsError = null
      this.availableModelsProviderType = ''

      try {
        const apis = getEntityApis()
        const result = await apis.provider.availableModels(this.provider?.id)

        if (result) {
          this.availableModels = result.models || []
          this.availableModelsSource = result.source || ''
          this.availableModelsProviderType = result.provider_type || ''
          this.availableModelsError = result.error || null
        }

        this.showImportDialog = true
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Failed to load available models.', timeout: 2000 })
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
          const modelType = model.model_type || 'prompts'
          const payload = {
            name: model.id,
            ai_model: model.id,
            system_name: toUpperCaseWithUnderscores(this.provider.system_name + '_' + model.id),
            display_name: `${this.formatProviderName(this.provider.name)}: ${model.id}`,
            provider_name: this.provider.system_name,
            provider_system_name: this.provider.system_name,
            type: modelType,
            json_mode: model.supports_json_mode || false,
            json_schema: model.supports_response_schema || false,
            tool_calling: model.supports_function_calling || false,
            reasoning: false,
            description: null,
          }

          try {
            await this.createEntity(payload)
            successCount++
          } catch (error) {
            errorCount++
          }
        }

        this.showImportDialog = false
        this.selectedModelsToImport = []

        if (successCount > 0) {
          this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: `Successfully imported ${successCount} model(s).`, timeout: 2000 })
        }

        if (errorCount > 0) {
          this.$q.notify({ color: 'orange-9', textColor: 'white', icon: 'warning', group: 'warning', message: `Failed to import ${errorCount} model(s).`, timeout: 2000 })
        }
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Error importing models.', timeout: 2000 })
      } finally {
        this.importingModels = false
      }
    },
  },
}
</script>
