<template lang="pug">
km-inner-loading(:showing='!draft')
layouts-details-layout(v-if='draft', :contentContainerStyle='{ maxWidth: "1200px", margin: "0 auto" }')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.hint_systemNameUniqueId() }}
        km-input-flat.col.km-description.text-black.full-width(
          :placeholder='m.placeholder_enterSystemNameReadable()',
          :model-value='system_name',
          @change='system_name = $event',
          @focus='showInfo = true',
          @blur='showInfo = false'
        )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.dialog_deleteModelProvider()',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_modelProvider() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_modelProvider() }) }}
  template(#content)
    .column.full-height(style='min-height: 0')
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
      template(v-if='tab == "models"')
        .col(style='min-height: 0; padding-top: 16px; padding-bottom: 16px')
          model-providers-models(:selectedModel='selectedModel', @select-model='onSelectModel')
      template(v-if='tab == "settings"')
        .col.overflow-auto(style='padding-top: 16px; padding-bottom: 16px')
          model-providers-settings

  template(#drawer)
    model-providers-model-drawer(v-if='tab == "models" && validSelectedModel')
    model-providers-drawer(v-else-if='tab == "models" && availableModels.length > 0 && !validSelectedModel')
</template>

<script>
import { ref, computed, provide, watch } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { beforeRouteEnter } from '@/guards'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  beforeRouteEnter,
  setup() {
    const queries = useEntityQueries()
    const { draft, isDirty, updateField, revert, save, remove } = useEntityDetail('provider')

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

    return {
      m,
      draft,
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
        { name: 'models', label: 'Models' },
        { name: 'settings', label: 'Settings' },
      ]),
      showInfo: ref(false),
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
    created_at() {
      return this.provider?.created_at ? this.formatDate(this.provider.created_at) : ''
    },
    modified_at() {
      return this.provider?.updated_at ? this.formatDate(this.provider.updated_at) : ''
    },
    created_by() {
      return this.provider?.created_by || m.common_unknown()
    },
    updated_by() {
      return this.provider?.updated_by || m.common_unknown()
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
          this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: m.notify_savedSuccessfully(), timeout: 2000 })
        } else {
          throw error || new Error('Failed to save')
        }
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || m.notify_failedToSave(), timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      const { success } = await this.removeEntity()
      if (success) {
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: m.notify_deletedSuccessfully({ entity: m.entity_modelProvider() }), timeout: 1000 })
        this.$router.push('/model-providers')
      }
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
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
