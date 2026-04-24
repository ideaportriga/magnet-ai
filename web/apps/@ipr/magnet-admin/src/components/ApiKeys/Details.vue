<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(data-test='name-input', :placeholder='m.common_name()', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        .km-description.text-secondary {{ m.common_key() }}:&nbsp;
        .km-description.text-secondary-text {{ maskedDisplay }}
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
        q-item(data-test='delete-btn', clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_apiKey() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_apiKey() }) }}
      .row.text-center.justify-center Access granted by this key will be immediately revoked, and any applications or services using it will no longer be able to connect. This action cannot be undone.
  template(#content)
    .column.full-height.overflow-auto(style='min-height: 0; padding-top: 16px; padding-bottom: 16px')
      .row.items-center.q-mb-16
        .col-auto.q-mr-sm
          q-toggle(data-test='active-toggle', :model-value='is_active', @update:model-value='is_active = $event', dense)
        .col.km-heading-3 {{ m.common_active() }}
      .row.q-mb-16
        .col
          .km-description.text-secondary-text.q-mb-4 Expires at
          km-input.full-width(data-test='expires-input', type='datetime-local', :model-value='expires_at', @change='expires_at = $event', clearable)
      .row.q-mb-16
        .col
          .km-description.text-secondary-text.q-mb-4 {{ m.common_notes() }}
          km-input.full-width(data-test='notes-input', type='textarea', rows='4', autogrow, :model-value='notes', @change='notes = $event')
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const router = useRouter()

const { draft, data: api_key, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('api_keys')

const loading = computed(() => isLoading.value || !api_key.value)

const saving = ref(false)
const showDeleteDialog = ref(false)

const name = computed({
  get() {
    return draft.value?.name
  },
  set(value) {
    updateField('name', value)
  },
})

const is_active = computed({
  get() {
    return draft.value?.is_active ?? true
  },
  set(value) {
    updateField('is_active', value)
  },
})

const notes = computed({
  get() {
    return draft.value?.notes ?? ''
  },
  set(value) {
    updateField('notes', value || null)
  },
})

const expires_at = computed({
  get() {
    const raw = draft.value?.expires_at
    if (!raw) return ''
    return String(raw).slice(0, 16)
  },
  set(value) {
    updateField('expires_at', value || null)
  },
})

const maskedDisplay = computed(() =>
  draft.value?.value_masked ? `................${draft.value.value_masked}` : '-',
)

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
  notify.success(m.notify_entityDeleted({ entity: m.entity_apiKey() }))
  router.push('/api-keys')
}
</script>

<style lang="stylus"></style>
