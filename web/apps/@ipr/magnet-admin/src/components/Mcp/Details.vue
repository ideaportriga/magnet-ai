<template lang="pug">
km-inner-loading(:showing='!draft')
layouts-details-layout(v-if='draft')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
        km-input-flat.col.km-description.text-black.full-width(
          placeholder='Enter system name',
          :model-value='system_name',
          @change='system_name = $event',
          @focus='showInfo = true',
          @blur='showInfo = false'
        )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#header-actions)
    km-btn(label='Record info', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Modified:
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created by:
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text Modified by:
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
    km-btn(label='Save & Sync Tools', flat, icon='fas fa-sync', iconSize='16px', @click='saveAndSync', :loading='syncing', :disable='syncing')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 Clone
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 Delete
    km-popup-confirm(
      :visible='showDeleteDialog',
      confirmButtonLabel='Delete MCP Server',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the MCP Server
      .row.text-center.justify-center This action will permanently delete the MCP Server and disable it in all tools that are using it.
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
import { useQuasar } from 'quasar'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'

const route = useRoute()
const router = useRouter()
const q = useQuasar()
const { draft, isDirty, updateField, save, revert, remove } = useEntityDetail('mcp_servers')
const queries = useEntityQueries()

const showInfo = ref(false)
const saving = ref(false)
const syncing = ref(false)
const showDeleteDialog = ref(false)
const showNewDialog = ref(false)
const tab = ref('tools')
const tabs = ref([
  { name: 'tools', label: 'Tools' },
  { name: 'settings', label: 'Settings' },
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
      q.notify({ position: 'top', color: 'positive', message: 'Saved successfully', timeout: 2000 })
    } else if (result.error) {
      throw result.error
    }
  } catch (error) {
    q.notify({ position: 'top', color: 'negative', message: error.message || 'Failed to save', timeout: 3000 })
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
    q.notify({ position: 'top', color: 'positive', message: 'Saved and synced successfully', timeout: 2000 })
  } catch (error) {
    q.notify({ position: 'top', color: 'negative', message: error.message || 'Failed to save and sync', timeout: 3000 })
  } finally {
    syncing.value = false
  }
}

async function confirmDelete() {
  await remove()
  q.notify({ position: 'top', message: 'MCP Server has been deleted.', color: 'positive', textColor: 'black', timeout: 1000 })
  router.push('/mcp')
}
</script>

<style lang="stylus"></style>
