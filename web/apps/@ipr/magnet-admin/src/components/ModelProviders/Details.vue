<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :system-name="system_name" :created-at="provider?.created_at" :updated-at="provider?.updated_at" :created-by="provider?.created_by" :updated-by="provider?.updated_by" show-record-info :show-description="false" :content-container-style="{ maxWidth: &quot;1200px&quot;, margin: &quot;0 auto&quot; }" @update:name="name = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" @select="showNewDialog = true">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.dialog_deleteModelProvider()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_modelProvider() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_modelProvider() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <div class="stack full-height km-flex-min-0" data-gap="0">
        <km-tabs v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs" />
        <template v-if="tab == &quot;models&quot;">
          <div class="flex-1 km-flex-min-0" style="padding-block: 16px">
            <model-providers-models :selected-model="selectedModel" @select-model="onSelectModel" />
          </div>
        </template>
        <template v-if="tab == &quot;settings&quot;">
          <div class="flex-1 km-flex-min-0 overflow-auto" style="padding-block: 16px">
            <model-providers-settings />
          </div>
        </template>
      </div>
    </template>
    <template #drawer>
      <model-providers-model-drawer v-if="tab == &quot;models&quot; &amp;&amp; validSelectedModel" />
      <model-providers-drawer v-else-if="tab == &quot;models&quot; &amp;&amp; availableModels.length &gt; 0 &amp;&amp; !validSelectedModel" />
    </template>
  </layouts-details-layout>
</template>

<script>
import { ref, computed, provide, watch } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { beforeRouteEnter } from '@/guards'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  beforeRouteEnter,
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, revert, save, remove } = useEntityDetail('provider')

    // Local ref for the currently selected model (replaces useModelConfigDetailStore)
    const selectedModel = ref(null)

    // Provide selected model + setter so ModelDrawer can access it
    provide('selectedModel', selectedModel)

    // Load models for this provider (server-side filter)
    const providerModelsParams = computed(() => ({
      pageSize: 500,
      provider: draft.value?.system_name ?? '',
    }))
    const { data: modelsData } = queries.model.useList(providerModelsParams)
    const allModels = computed(() => modelsData.value?.items ?? [])

    const { mutateAsync: createEntity } = queries.provider.useCreate()

    const loading = computed(() => isLoading.value || !draft.value)

    return {
      m,
      draft,
      loading,
      isDirty,
      updateField,
      revert,
      saveEntity: save,
      removeEntity: remove,
      selectedModel,
      createEntity,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showNewDialog: ref(false),
      tab: ref('models'),
      tabs: ref([
        { value: 'models', label: 'Models' },
        { value: 'settings', label: 'Settings' },
      ]),
      allModels,
    }
  },
  computed: {
    provider() {
      return this.draft
    },
    availableModels() {
      return this.allModels
    },
    validSelectedModel() {
      // Check if selectedModel exists in availableModels for current provider
      const sel = this.selectedModel
      if (!sel || !this.availableModels.length) {
        return null
      }
      return this.availableModels.find((model) => model.id === sel.id) || null
    },
    name: {
      get() {
        return this.provider?.name || ''
      },
      set(value) {
        this.updateField('name', value)
      },
    },
    system_name: {
      get() {
        return this.provider?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
  },
  watch: {
    availableModels: {
      immediate: true,
      handler(newVal, oldVal) {
        // Reset selectedModel if it's not in availableModels for current provider
        if (this.selectedModel && newVal.length > 0) {
          const modelExists = newVal.find((model) => model.id === this.selectedModel.id)
          if (!modelExists) {
            this.selectedModel = null
            // Auto-select first model if no valid selection
            this.autoSelectFirstModel(newVal)
          }
        } else if (this.selectedModel && newVal.length === 0) {
          // No models available for this provider, clear selection
          this.selectedModel = null
        } else if (!this.selectedModel && newVal.length > 0) {
          // No model selected but models are available, auto-select first
          this.autoSelectFirstModel(newVal)
        }
      },
    },
  },
  methods: {
    async handleSave() {
      this.saving = true
      try {
        const { success, error } = await this.saveEntity()
        if (success) {
          notify.success(m.notify_savedSuccessfully())
        } else {
          throw error || new Error('Failed to save')
        }
      } catch (error) {
        notify.error(error.message || m.notify_failedToSave())
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      const { success } = await this.removeEntity()
      if (success) {
        notify.success(m.notify_deletedSuccessfully({ entity: m.entity_modelProvider() }))
        this.$router.push('/model-providers')
      }
    },
    onSelectModel(row) {
      this.selectedModel = row
    },
    autoSelectFirstModel(models) {
      // Sort by is_default (descending) to prioritize default models
      const sortedModels = [...models].sort((a, b) => {
        if (a.is_default && !b.is_default) return -1
        if (!a.is_default && b.is_default) return 1
        return 0
      })

      if (sortedModels.length > 0) {
        this.selectedModel = sortedModels[0]
      }
    },
  },
}
</script>
