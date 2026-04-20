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
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_apiServer() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_apiServer() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_apiServer() }) }}
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()

const { draft, data: api_server, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('api_servers')

const loading = computed(() => isLoading.value || !api_server.value)

const showInfo = ref(false)
const saving = ref(false)
const showDeleteDialog = ref(false)
const showNewDialog = ref(false)
const tab = ref('tools')
const tabs = ref([
  { name: 'tools', label: m.common_tools() },
  { name: 'settings', label: m.common_settings() },
])

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
const created_by = computed(() => draft.value?.created_by || m.common_unknown())
const updated_by = computed(() => draft.value?.updated_by || m.common_unknown())

function formatDate(date) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function handleSave() {
  saving.value = true
  try {
    const result = await save()
    if (result.success) {
      notify.success(m.notify_savedSuccessfully())
    } else if (result.error) {
      throw result.error
    }
  } catch (error) {
    notify.error(error.message || m.notify_failedToSave())
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  await remove()
  notify.success(m.notify_entityDeleted({ entity: m.entity_apiServer() }))
  router.push('/api-servers')
}
</script>

<style lang="stylus"></style>
