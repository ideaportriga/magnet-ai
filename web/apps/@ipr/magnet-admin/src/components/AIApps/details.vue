<template>
  <km-inner-loading :showing="loading" />
  <div v-if="!loading" class="cluster overflow-hidden full-height" data-wrap="no" style="min-inline-size: 1200px">
    <div class="flex-1 flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
      <div class="flex-1" style="max-inline-size: 1200px; min-inline-size: 600px">
        <div class="full-height pb-md relative-position px-md">
          <div class="cluster full-width mt-lg mb-sm bg-white border-radius-8 py-md px-lg" data-gap="md" data-wrap="no">
            <div class="flex-1">
              <km-input-flat class="km-heading-4 full-width text-black" data-test="name-input" :placeholder="m.common_name()" :model-value="name" :readonly="recordReadonly" @change="name = $event" />
              <km-input-flat class="km-description full-width text-black" data-test="description-input" :placeholder="m.common_description()" :model-value="description" :readonly="recordReadonly" @change="description = $event" />
              <div class="cluster pl-sm">
                <km-glyph class="flex-none" name="info" tone="subtle">
                  <km-tooltip class="bg-white block-shadow text-secondary-text km-description" self="top middle" :offset="[-50, -50]">{{ m.tooltip_systemNameUniqueId() }}</km-tooltip>
                </km-glyph>
                <km-input-flat class="flex-1 km-description text-black full-width text-black" data-test="system-name-input" :placeholder="m.placeholder_enterSystemNameReadable()" :model-value="system_name" :readonly="recordReadonly" @change="system_name = $event" @focus="showInfo = true" @blur="showInfo = false" />
              </div>
              <div v-if="showInfo" class="km-description text-secondary pl-sm">{{ m.hint_systemNameRecommendation() }}</div>
            </div>
            <div class="flex-none cluster ml-md" data-wrap="no" data-gap="sm">
              <km-btn :label="m.common_recordInfo()" flat icon="info" icon-size="16px">
                <template #tooltip>
                  <div class="p-sm">
                    <div class="mb-sm">
                      <div class="text-secondary-text km-button-xs-text">{{ m.common_createdLabel() }}</div>
                      <div class="text-secondary-text km-description">{{ created_at }}</div>
                    </div>
                    <div class="mb-sm">
                      <div class="text-secondary-text km-button-xs-text">{{ m.common_modified() }}</div>
                      <div class="text-secondary-text km-description">{{ modified_at }}</div>
                    </div>
                    <div class="mb-sm">
                      <div class="text-secondary-text km-button-xs-text">{{ m.common_createdBy() }}</div>
                      <div class="text-secondary-text km-description">{{ created_by }}</div>
                    </div>
                    <div>
                      <div class="text-secondary-text km-button-xs-text">{{ m.common_modifiedBy() }}</div>
                      <div class="text-secondary-text km-description">{{ updated_by }}</div>
                    </div>
                  </div>
                </template>
              </km-btn>
              <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
              <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
              <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="ai-app-readonly-icon" />
              <ds-dropdown-menu-root>
                <ds-dropdown-menu-trigger as-child>
                  <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
                </ds-dropdown-menu-trigger>
                <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
                  <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
                  <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
                </ds-dropdown-menu-content>
              </ds-dropdown-menu-root>
              <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_aiApp() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
                <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_aiApp() }) }}</div>
                <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_aiAppBody() }}</div>
              </km-popup-confirm>
            </div>
          </div>
          <div class="ba-border bg-white border-radius-12 p-lg" style="min-inline-size: 300px">
            <km-tabs v-model="folderTab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
              <template v-for="t in folderTabs" :key="t.name">
                <km-tab :name="t.name" :label="t.label" />
              </template>
            </km-tabs>
            <div :inert="recordReadonly" :class="recordReadonly ? 'ai-app-readonly-zone' : null" class="stack full-height full-width overflow-auto my-md km-scroll-area-lg" data-gap="lg" data-wrap="no">
              <div class="cluster full-height full-width" data-gap="lg">
                <div class="flex-1 full-height full-width">
                  <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
                    <div class="flex-none full-width">
                      <template v-if="folderTab == &quot;records&quot;">
                        <ai-apps-records />
                      </template>
                      <template v-if="folderTab == &quot;settings&quot;">
                        <ai-apps-settings />
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="tabs.length &gt; 0" class="flex-none">
      <ai-apps-drawer v-model:open="openTest" />
    </div>
  </div>
  <ai-apps-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
</template>

<script>
import { ref, computed, provide } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useSearchStore } from '@/stores/searchStore'
import { storeToRefs } from 'pinia'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'
import { usePermissions } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { draft, isLoading, isDirty, updateField, updateFields, save: saveEntity, revert, refetch, remove, buildPayload } = useEntityDetail('ai_apps')
    const queries = useEntityQueries()
    const searchStore = useSearchStore()
    const { semanticSearchAnswers } = storeToRefs(searchStore)
    function clearSemanticSearchAnswers() {
      semanticSearchAnswers.value = []
    }
    const { mutateAsync: createEntity } = queries.ai_apps.useCreate()

    // PR 10 — record-level permission gating.
    const { can, canOn } = usePermissions()
    const canEdit = computed(() => canOn(draft?.value, 'edit', 'ai_apps'))
    const canDelete = computed(() => canOn(draft?.value, 'delete', 'ai_apps'))
    const canCreate = computed(() => can('write:ai_apps'))
    const recordReadonly = computed(() => {
      const a = draft?.value
      if (!a) return false
      return canEdit.value === false
    })
    provide('aiAppReadonly', recordReadonly)

    return {
      m,
      draft,
      canEdit,
      canDelete,
      canCreate,
      recordReadonly,
      isLoading,
      isDirty,
      updateField,
      updateFields,
      saveEntity,
      revert,
      refetch,
      removeEntity: remove,
      buildPayload,
      activeAIApp: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      openCreateDialog: ref(true),
      showInfo: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      createEntity,
      searchString: ref(''),
      hovered: ref({}),
      isMoving: ref(false),
      clickedRow: ref({}),
      folderTab: ref('records'),
      folderTabs: ref([
        { name: 'records', label: m.common_aiTabs() },
        { name: 'settings', label: m.common_settings() },
      ]),
      clearSemanticSearchAnswers,
    }
  },
  computed: {
    name: {
      get() {
        return this.draft?.name || ''
      },
      set(value) {
        this.updateField('name', value)
      },
    },
    description: {
      get() {
        return this.draft?.description || ''
      },
      set(value) {
        this.updateField('description', value)
      },
    },
    system_name: {
      get() {
        return this.draft?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    tabs: {
      get() {
        return this.draft?.tabs || []
      },
      set(value) {
        this.updateField('tabs', value)
      },
    },
    searchedTabs: {
      get() {
        return this.tabs.filter((tab) => tab.name.toLowerCase().includes(this.searchString.toLowerCase()))
      },
      set(value) {
        this.tabs = value
      },
    },
    activeAIAppId() {
      return this.$route.params?.id
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
    entity() {
      return this.draft
    },
    created_at() {
      return this.entity?.created_at ? this.formatDate(this.entity.created_at) : ''
    },
    modified_at() {
      return this.entity?.updated_at ? this.formatDate(this.entity.updated_at) : ''
    },
    created_by() {
      return this.entity?.created_by || 'Unknown'
    },
    updated_by() {
      return this.entity?.updated_by || 'Unknown'
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openTabDetails(row) {
      // Tab context passed via URL param; no Vuex needed
      this.navigate(`${this.$route.path}/items/${row.system_name}`)
    },
    async save() {
      this.saving = true
      try {
        if (this.entity?.created_at) {
          await this.saveEntity()
        } else {
          await this.createEntity(this.entity)
        }
        // Refresh the iframe
        window.postMessage({ type: 'reload_iframe' })
        notify.success('Saved successfully')
      } catch (error) {
        notify.error(error.message || 'Failed to save')
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeEntity()
      this.$emit('update:closeDrawer', null)
      notify.success('AI App has been deleted.')
      this.navigate('/ai-apps')
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
    },
  },
}
</script>

<style>
.gradient {
  background: linear-gradient(121.5deg, var(--ds-color-primary) 9.69%, var(--ds-color-error) 101.29%);
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.card-hover:hover {
  background: var(--ds-color-background);
  cursor: pointer;
  border-color: var(--ds-color-primary);
}
.ai-app-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.ai-app-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
