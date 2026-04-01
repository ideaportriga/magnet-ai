<template lang="pug">
km-inner-loading(:showing='!api_server')
layouts-details-layout(v-if='api_server')
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='apiServerStore.revert()', v-if='apiServerStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !apiServerStore.isChanged')
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
      confirmButtonLabel='Delete API Server',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the API Server
      .row.text-center.justify-center This action will permanently delete the API Server and disable it in all tools that are using it.
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
      template(v-if='tab == "tools"')
        .col(style='min-height: 0; padding-top: 16px; padding-bottom: 16px')
          api-servers-tabs-tools
      template(v-if='tab == "settings"')
        .col.overflow-auto(style='padding-top: 16px; padding-bottom: 16px')
          api-servers-tabs-settings
</template>

<script setup>
import { ref, computed, watch, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useEntityQueries } from '@/queries/entities'
import { useApiServerDetailStore } from '@/stores/entityDetailStores'

const route = useRoute()
const router = useRouter()
const q = useQuasar()
const apiServerStore = useApiServerDetailStore()
const queries = useEntityQueries()

const showInfo = ref(false)
const saving = ref(false)
const showDeleteDialog = ref(false)
const showNewDialog = ref(false)
const tab = ref('tools')
const tabs = ref([
  { name: 'tools', label: 'Tools' },
  { name: 'settings', label: 'Settings' },
])

const id = ref(route.params.id)
const { data: api_server } = queries.api_servers.useDetail(id)
const { mutateAsync: updateEntity } = queries.api_servers.useUpdate()
const { mutateAsync: createEntity } = queries.api_servers.useCreate()
const removeMutation = queries.api_servers.useRemove()

const name = computed({
  get() {
    return apiServerStore.entity?.name
  },
  set(value) {
    apiServerStore.updateProperty({ key: 'name', value })
  },
})
const system_name = computed({
  get() {
    return apiServerStore.entity?.system_name
  },
  set(value) {
    apiServerStore.updateProperty({ key: 'system_name', value })
  },
})

const entity = computed(() => apiServerStore.entity)
const created_at = computed(() => entity.value?.created_at ? formatDate(entity.value.created_at) : '')
const modified_at = computed(() => entity.value?.updated_at ? formatDate(entity.value.updated_at) : '')
const created_by = computed(() => entity.value?.created_by || 'Unknown')
const updated_by = computed(() => entity.value?.updated_by || 'Unknown')

function formatDate(date) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function save() {
  saving.value = true
  try {
    if (entity.value?.created_at) {
      const data = apiServerStore.buildPayload()
      await updateEntity({ id: entity.value.id, data })
    } else {
      await createEntity(entity.value)
    }
    apiServerStore.setInit()
    q.notify({ position: 'top', color: 'positive', message: 'Saved successfully', timeout: 2000 })
  } catch (error) {
    q.notify({ position: 'top', color: 'negative', message: error.message || 'Failed to save', timeout: 3000 })
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  await removeMutation.mutateAsync(route.params.id)
  q.notify({ position: 'top', message: 'API Server has been deleted.', color: 'positive', textColor: 'black', timeout: 1000 })
  router.push('/api-servers')
}

watch(
  () => api_server.value,
  (newVal) => {
    if (!newVal) return
    apiServerStore.setEntity(newVal)
  },
  { immediate: true, deep: true }
)

onActivated(() => {
  id.value = route.params.id
  // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
  const currentData = api_server.value
  if (currentData && currentData.id !== apiServerStore.entity?.id) {
    apiServerStore.setEntity(currentData)
  }
})
</script>

<style lang="stylus"></style>
