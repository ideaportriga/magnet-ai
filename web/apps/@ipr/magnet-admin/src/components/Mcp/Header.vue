<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ server?.name }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
  q-tooltip.bg-white.block-shadow
    .q-pa-sm
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created:
        .text-secondary-text.km-description {{ info.created_at }}
      div
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ info.updated_at }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')
.col-auto.text-white.q-mr-md
  km-btn(label='Save & Sync Tools', icon='fa-solid fa-sync', color='primary', bg='background', iconSize='16px', @click='showConfirmDialog = true')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      //- q-item(clickable, @click='clone', dense)
      //-   q-item-section
      //-     .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete
q-inner-loading(:showing='loading')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Ok, delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteServer',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete an MCP Server
  .row.text-center.justify-center If any of your Agents are using MCP Tools provided by this server, according Actions will stop working after deletion.

km-popup-confirm(
  :visible='showConfirmDialog',
  confirmButtonLabel='Sync Tools',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-info-circle',
  @confirm='syncTools',
  @cancel='showConfirmDialog = false'
)
  .row.item-center.justify-center.km-heading-7.q-mb-md You are about to sync all tools with the MCP Server
  .row.text-center.justify-center Syncing will load current tools from the MCP server and replace existing MCP Tools.
</template>
<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useChroma } from '@shared'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@shared/utils/dateTime'

const store = useStore()
const q = useQuasar()
const router = useRouter()
const { delete: deleteMcpServer } = useChroma('mcp_servers')
const showDeleteDialog = ref(false)
const showConfirmDialog = ref(false)
const loading = ref(false)

const server = computed(() => store.getters.mcp_server)

const info = computed(() => {
  return {
    created_at: formatDateTime(server.value?.created_at),
    updated_at: formatDateTime(server.value?.updated_at),
  }
})

const save = async () => {
  loading.value = true
  await store.dispatch('saveMcpServer')
  loading.value = false
}
const deleteServer = async () => {
  await deleteMcpServer({ id: store.getters.mcp_server.id })
  q.notify({
    position: 'top',
    message: 'MCP Server has been deleted.',
    color: 'positive',
    textColor: 'black',
    timeout: 1000,
  })
  store.dispatch('setMcpServer', null)
  showDeleteDialog.value = false
  router.push('/mcp')
}
const syncTools = async () => {
  loading.value = true
  await store.dispatch('saveMcpServer')
  const res = await store.dispatch('syncMcpTools')
  if (res) {
    q.notify({
      position: 'top',
      message: 'MCP Tools have been synced.',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } else {
    q.notify({
      position: 'top',
      message: 'Failed to sync MCP Tools.',
      color: 'negative',
      textColor: 'black',
      timeout: 1000,
    })
  }
  loading.value = false
  showConfirmDialog.value = false
}
</script>
