<template>
  <div class="stack full-height km-flex-min-0" data-gap="0" style="inline-size: 100%">
    <div class="cluster" data-justify="between">
      <div class="flex-none">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="cluster flex-none" data-gap="md">
        <km-btn flat :label="m.common_import()" icon="download" :loading="loadingAvailableModels" @click="openImportDialog" />
        <km-btn :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </div>
    <div class="cluster mt-md" data-justify="between">
      <div class="flex-none">
        <km-filter-bar v-model:config="filterConfig" v-model:filter-object="filterObject" output-format="sql" />
      </div>
      <div class="km-space" />
      <div class="cluster flex-none" data-gap="md">
        <km-btn v-if="selectedRows.length &gt; 0" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
      </div>
    </div>
    <div class="flex-1 mt-md km-flex-min-0">
      <km-data-table fill-height :table="table" row-key="id" :page-size-options="[20, 50, 100, 200]" :active-row-id="modelConfig?.id" @row-click="openDetails" />
    </div>
  </div>
  <model-providers-new-model v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="cluster km-heading-7" data-justify="center">Delete Models</div>
    <div class="cluster text-center" data-justify="center">{{ `You are going to delete ${selectedRows?.length} selected models. Are you sure?` }}</div>
  </km-popup-confirm>
  <km-dialog v-model="showImportDialog" size="lg" persistent>
    <template #title>Import Models from Provider</template>

    <div class="stack p-lg" data-gap="md">
      <div class="cluster" data-gap="sm">
        <km-chip :label="availableModelsSource === 'api' ? 'Provider API' : 'LiteLLM Registry'" :tone="availableModelsSource === 'api' ? 'success' : 'brand'" round />
        <km-chip v-if="availableModelsProviderType" :label="availableModelsProviderType" tone="neutral" round />
      </div>

      <km-banner v-if="availableModelsSource === 'litellm'" rounded dense>
        <template #avatar>
          <km-glyph name="info" tone="warning" />
        </template>
        <div class="text-caption text-grey-8">Model list from LiteLLM registry. Capabilities are estimated and may not reflect actual provider features.</div>
      </km-banner>
      <km-banner v-else-if="availableModelsSource === 'api' &amp;&amp; availableModelsError" rounded dense>
        <template #avatar>
          <km-glyph name="warning" tone="warning" />
        </template>
        <div class="text-caption text-grey-8">{{ availableModelsError }}</div>
      </km-banner>

      <km-input v-model="importSearchString" :placeholder="m.modelProviders_filterModels()" icon-before="search" clearable @input="importSearchString = $event" />

      <div class="km-import-list">
        <ul v-if="filteredAvailableModels.length &gt; 0" class="km-import-list__items">
          <li
            v-for="model in filteredAvailableModels"
            :key="model.id"
            class="km-import-list__item"
            :class="{ 'km-import-list__item--selected': isModelSelected(model), 'km-import-list__item--disabled': isModelAlreadyAdded(model) }"
            @click="!isModelAlreadyAdded(model) &amp;&amp; toggleModelSelection(model)"
          >
            <km-checkbox :model-value="isModelSelected(model)" :disable="isModelAlreadyAdded(model)" @click.stop @update:model-value="toggleModelSelection(model)" />
            <div class="km-import-list__main">
              <div class="cluster" data-gap="sm">
                <span class="km-import-list__title">{{ model.id }}</span>
                <km-chip :label="model.model_type === 'embeddings' ? 'Embeddings' : (model.model_type === 'stt' ? 'STT' : 'Chat')" :tone="model.model_type === 'embeddings' ? 'neutral' : 'brand'" round />
              </div>
              <div class="cluster km-import-list__meta" data-gap="xs">
                <span v-if="model.owned_by">{{ model.owned_by }}</span>
                <template v-if="model.max_tokens">
                  <span class="text-grey-5">•</span>
                  <span>{{ formatTokens(model.max_tokens) }} tokens</span>
                </template>
              </div>
            </div>
            <div class="cluster flex-none" data-gap="xs">
              <template v-if="isModelAlreadyAdded(model)">
                <km-chip :label="m.common_alreadyAdded()" tone="neutral" round />
              </template>
              <template v-else>
                <km-chip v-if="model.supports_function_calling" tone="brand" :label="m.common_tools()" round tooltip="Function/Tool Calling" />
                <km-chip v-if="model.supports_json_mode" tone="brand" :label="m.common_json()" round tooltip="JSON Mode" />
                <km-chip v-if="model.supports_vision" tone="brand" :label="m.common_vision()" round tooltip="Vision/Image Support" />
              </template>
            </div>
          </li>
        </ul>
        <div v-else-if="!loadingAvailableModels" class="km-import-list__empty">
          No models found
          <div v-if="availableModelsError &amp;&amp; !availableModels.length" class="mt-sm text-negative">{{ availableModelsError }}</div>
        </div>
      </div>
    </div>

    <template #footer>
      <span v-if="selectedModelsToImport.length &gt; 0" class="text-secondary-text mr-md">{{ selectedModelsToImport.length }} model(s) selected</span>
      <km-btn flat :label="m.common_cancel()" tone="brand" @click="showImportDialog = false" />
      <km-btn :label="m.common_importSelected()" :disable="selectedModelsToImport.length === 0" :loading="importingModels" @click="importSelectedModels" />
    </template>
  </km-dialog>
</template>

<script>
import { ref, computed, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { getEntityApis } from '@/api'
import { categoryOptions, featureOptions } from '../../config/model/model.js'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useDataTable } from '@/composables/useDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TypeChip from '@/config/model/component/TypeChip.vue'
import Features from '@/config/model/component/Features.vue'
import Check from '@/config/model/component/Check.vue'
import { notify } from '@shared/utils/notify'

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
    const { mutateAsync: deleteItem } = queries.model.useRemove()
    const { mutateAsync: createEntity } = queries.model.useCreate()
    const filterObject = ref({})
    const filterConfig = {
      type: {
        key: 'type',
        label: m.common_type(),
        multiple: true,
        options: categoryOptions,
      },
      features: {
        key: 'features',
        label: m.common_features(),
        multiple: true,
        options: featureOptions,
        customLogic: (selected) => ({ $or: selected.map((feature) => ({ [feature]: true })) }),
      },
    }

    const columns = [
      selectionColumn(),
      textColumn('display_name', m.common_displayName()),
      textColumn('ai_model', m.common_name()),
      componentColumn('type', m.common_type(), markRaw(TypeChip), {
        accessorKey: 'type',
        sortable: true,
        // TypeChip needs `name` (required prop) to know which field on the
        // row holds the type value. Without it Vue warns every time the
        // list renders.
        props: () => ({ name: 'type' }),
      }),
      componentColumn('features', m.common_features(), markRaw(Features), {
        props: (row) => ({ name: 'features' }),
        wrap: true,
      }),
      componentColumn('is_default', m.common_default(), markRaw(Check), {
        accessorKey: 'is_default',
        sortable: true,
        align: 'center',
        props: (row) => ({ name: 'is_default' }),
      }),
      componentColumn('is_active', m.common_active(), markRaw(Check), {
        accessorKey: 'is_active',
        sortable: true,
        align: 'center',
        props: (row) => ({ name: 'is_active' }),
      }),
    ]

    // Server-side paging, sorting and search filtered by provider
    const providerExtraParams = computed(() => ({
      provider: providerDraft.value?.system_name ?? '',
    }))

    /**
     * Filter-bar values are applied on the client because the backend `/models`
     * endpoint only accepts a single `type` value and no per-feature flags.
     * Per-provider model lists are bounded (typically <100), so a high page
     * size + local filtering is the pragmatic correct behaviour here.
     *
     * Note: <km-filter-bar> embeds <km-select> without `emit-value`, so each
     * selection is the full `{ label, value }` option — unwrap it before
     * comparing against the row's primitive `type` / feature flags.
     */
    function unwrapValues(input) {
      const list = Array.isArray(input) ? input : (input != null ? [input] : [])
      return list.map((entry) =>
        entry && typeof entry === 'object' && 'value' in entry ? entry.value : entry,
      )
    }

    function filterRows(items) {
      const fo = filterObject.value ?? {}
      let result = items

      const types = unwrapValues(fo.type)
      if (types.length > 0) {
        result = result.filter((m) => types.includes(m.type))
      }

      const features = unwrapValues(fo.features)
      if (features.length > 0) {
        // OR semantics — model matches if it advertises any of the selected features.
        result = result.filter((m) => features.some((feat) => m[feat] === true))
      }

      return result
    }

    const { table, globalFilter, rowSelection } = useDataTable('model', columns, {
      defaultSort: [{ id: 'updated_at', desc: true }],
      defaultPageSize: 200,
      extraParams: providerExtraParams,
      enableRowSelection: true,
      dataFilter: filterRows,
    })

    const selectedRows = computed(() =>
      table.getSelectedRowModel().rows.map((r) => r.original),
    )

    function clearSelection() {
      rowSelection.value = {}
    }

    return {
      m,
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
          await this.deleteItem(item.id)
        }
        this.clearSelection()
        this.showDeleteDialog = false
        notify.success('Models deleted successfully.')
      } catch (error) {
        notify.error('Error deleting models.')
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
        notify.error('Failed to load available models.')
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
          notify.success(`Successfully imported ${successCount} model(s).`)
        }

        if (errorCount > 0) {
          notify.warning(`Failed to import ${errorCount} model(s).`)
        }
      } catch (error) {
        notify.error('Error importing models.')
      } finally {
        this.importingModels = false
      }
    },
  },
}
</script>

<style>
.km-import-list {
  max-block-size: 24rem;
  overflow-block: auto;
  overscroll-behavior: contain;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
}
.km-import-list__items {
  list-style: none;
  margin: 0;
  padding: 0;
}
.km-import-list__item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-md);
  padding: var(--ds-space-sm) var(--ds-space-md);
  border-block-end: 1px solid var(--ds-color-border-subtle);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-import-list__item:last-child { border-block-end: 0; }
.km-import-list__item:hover { background: var(--ds-color-table-hover); }
.km-import-list__item--selected { background: var(--ds-color-primary-bg); }
.km-import-list__item--selected:hover { background: var(--ds-color-primary-bg); }
.km-import-list__item--disabled { cursor: not-allowed; opacity: 0.6; }
.km-import-list__main {
  flex: 1 1 auto;
  min-inline-size: 0;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
}
.km-import-list__title {
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
.km-import-list__meta {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
}
.km-import-list__empty {
  padding: var(--ds-space-2xl);
  text-align: center;
  color: var(--ds-color-text-grey);
}
</style>
