<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :system-name="system_name" :created-at="created_at" :updated-at="modified_at" :created-by="created_by" :updated-by="updated_by" show-record-info :show-description="false" :readonly="recordReadonly" @update:name="name = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-btn v-if="!recordReadonly" :label="m.common_saveAndSyncTools()" flat icon="refresh" icon-size="16px" :loading="syncing" :disable="syncing" @click="saveAndSync" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="mcp-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_mcpServer() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_mcpServer() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_mcpServer() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'mcp-readonly-zone' : null" class="stack overflow-auto pt-lg pb-lg" data-gap="lg">
        <mcp-tabs-settings v-if="tab == &quot;settings&quot;" />
        <mcp-tabs-tools v-if="tab == &quot;tools&quot;" />
      </div>
    </template>
  </layouts-details-layout>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { usePermissions } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()

const { draft, isLoading, isDirty, updateField, save, revert, remove } = useEntityDetail('mcp_servers')
const queries = useEntityQueries()

// PR 10 — record-level permission gating.
const { can, canOn } = usePermissions()
const canEdit = computed(() => canOn(draft?.value, 'edit', 'mcp_servers'))
const canDelete = computed(() => canOn(draft?.value, 'delete', 'mcp_servers'))
const canCreate = computed(() => can('write:mcp_servers'))
const recordReadonly = computed(() => {
  const m = draft?.value
  if (!m) return false
  return canEdit.value === false
})
provide('mcpReadonly', recordReadonly)

const loading = computed(() => isLoading.value || !draft.value)

const saving = ref(false)
const syncing = ref(false)
const showDeleteDialog = ref(false)
const showNewDialog = ref(false)
const tab = ref('tools')
const tabs = ref([
  { value: 'tools', label: m.common_tools() },
  { value: 'settings', label: m.common_settings() },
])

const { mutateAsync: syncMcpServer } = queries.mcp_servers.useSync()

const name = computed({
  get() {
    return draft.value?.name
  },
  set(value) {
    updateField('name', value)
  },
})
const system_name = computed({
  get() {
    return draft.value?.system_name
  },
  set(value) {
    updateField('system_name', value)
  },
})

const created_at = computed(() => draft.value?.created_at ? formatDate(draft.value.created_at) : '')
const modified_at = computed(() => draft.value?.updated_at ? formatDate(draft.value.updated_at) : '')
const created_by = computed(() => draft.value?.created_by || 'Unknown')
const updated_by = computed(() => draft.value?.updated_by || 'Unknown')

function formatDate(date) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function handleSave() {
  saving.value = true
  try {
    const result = await save()
    if (result.success) {
      notify.success('Saved successfully')
    } else if (result.error) {
      throw result.error
    }
  } catch (error) {
    notify.error(error.message || 'Failed to save')
  } finally {
    saving.value = false
  }
}

async function saveAndSync() {
  syncing.value = true
  try {
    const result = await save()
    if (!result.success) throw result.error || new Error('Failed to save')
    await syncMcpServer(draft.value.id)
    notify.success('Saved and synced successfully')
  } catch (error) {
    notify.error(error.message || 'Failed to save and sync')
  } finally {
    syncing.value = false
  }
}

async function confirmDelete() {
  await remove()
  notify.success('MCP Server has been deleted.')
  router.push('/mcp')
}
</script>

<style scoped>
.mcp-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.mcp-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
