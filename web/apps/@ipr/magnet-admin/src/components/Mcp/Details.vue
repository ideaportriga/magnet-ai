<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(data-test='name-input', :placeholder='m.common_name()', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
        km-input-flat.col.km-description.text-black.full-width(
          data-test='system-name-input',
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
    km-btn(data-test='revert-btn', :label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(data-test='save-btn', :label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
    km-btn(:label='m.common_saveAndSyncTools()', flat, icon='fas fa-sync', iconSize='16px', @click='saveAndSync', :loading='syncing', :disable='syncing')
    q-btn.q-px-xs(data-test='show-more-btn', flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(data-test='clone-btn', clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(data-test='delete-btn', clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_mcpServer() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_mcpServer() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_mcpServer() }) }}
  template(#content)
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
    .column.q-gap-16.overflow-auto.q-pt-lg.q-pb-lg
      mcp-tabs-settings(v-if='tab == "settings"')
      mcp-tabs-tools(v-if='tab == "tools"')
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()

const { draft, isLoading, isDirty, updateField, save, revert, remove } = useEntityDetail('mcp_servers')
const queries = useEntityQueries()

const loading = computed(() => isLoading.value || !draft.value)

const showInfo = ref(false)
const saving = ref(false)
const syncing = ref(false)
const showDeleteDialog = ref(false)
const showNewDialog = ref(false)
const tab = ref('tools')
const tabs = ref([
  { name: 'tools', label: m.common_tools() },
  { name: 'settings', label: m.common_settings() },
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

<style lang="stylus"></style>
