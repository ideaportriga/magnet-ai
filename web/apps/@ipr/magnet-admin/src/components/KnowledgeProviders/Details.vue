<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :system-name="system_name" :created-at="provider?.created_at" :updated-at="provider?.updated_at" :created-by="provider?.created_by" :updated-by="provider?.updated_by" show-record-info :show-description="false" :readonly="recordReadonly" :content-container-style="{ maxWidth: &quot;1200px&quot;, margin: &quot;0 auto&quot; }" @update:name="name = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="knowledge-provider-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_knowledgeSourceProvider() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_knowledgeSourceProvider() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_knowledgeSourceProvider() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <div class="stack full-height" data-gap="0" style="min-block-size: 0">
        <km-tabs v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs" />
        <div :inert="recordReadonly" :class="recordReadonly ? 'knowledge-provider-readonly-zone' : null" class="flex-1" style="min-block-size: 0; padding-block: 16px">
          <knowledge-providers-knowledge-sources v-if="tab == &quot;knowledge-sources&quot;" />
          <knowledge-providers-settings v-if="tab == &quot;settings&quot;" />
        </div>
      </div>
    </template>
  </layouts-details-layout>
</template>

<script>
import { computed, ref } from 'vue'
import { beforeRouteEnter } from '@/guards'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEntityAccess } from '@/composables/useEntityAccess'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  beforeRouteEnter,
  setup() {
    const { draft, isLoading, isDirty, updateField, revert, save, remove } = useEntityDetail('provider')
    const { canCreate, canDelete, recordReadonly, provideReadonly } = useEntityAccess('knowledge_providers', draft)
    provideReadonly()

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
      canCreate,
      canDelete,
      recordReadonly,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showNewDialog: ref(false),
      tab: ref('knowledge-sources'),
      tabs: ref([
        { value: 'knowledge-sources', label: m.section_knowledgeSources() },
        { value: 'settings', label: m.common_settings() },
      ]),
    }
  },
  computed: {
    provider() {
      return this.draft
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
  methods: {
    async handleSave() {
      this.saving = true
      try {
        const { success, error } = await this.saveEntity()
        if (success) {
          notify.success('Saved successfully')
        } else {
          throw error || new Error('Failed to save')
        }
      } catch (error) {
        notify.error(error.message || 'Failed to save')
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      const { success } = await this.removeEntity()
      if (success) {
        notify.success('Knowledge Provider has been deleted.')
        this.$router.push('/knowledge-providers')
      }
    },
  },
}
</script>
