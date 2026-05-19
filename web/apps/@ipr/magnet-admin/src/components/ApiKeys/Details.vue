<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout
    v-if="!loading"
    :name="name"
    :created-at="created_at"
    :updated-at="modified_at"
    :created-by="created_by"
    :updated-by="updated_by"
    show-record-info
    :show-description="false"
    :readonly="recordReadonly"
    @update:name="name = $event"
  >
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="api-key-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm
        :visible="showDeleteDialog"
        :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_apiKey() })"
        :cancel-button-label="m.common_cancel()"
        notification-icon="warning"
        @confirm="confirmDelete"
        @cancel="showDeleteDialog = false"
      >
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_apiKey() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_apiKey() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <div :inert="recordReadonly" :class="recordReadonly ? 'api-key-readonly-zone' : null" class="stack full-height overflow-auto" data-gap="16" style="min-block-size: 0; padding-block: 16px">
        <div class="cluster" data-gap="sm" data-wrap="no">
          <div class="km-description text-secondary-text">{{ m.common_key() }}:&nbsp;</div>
          <div class="km-description text-secondary-text">{{ maskedDisplay }}</div>
        </div>
        <div class="cluster items-center" data-gap="sm">
          <km-switch data-test="active-toggle" :model-value="is_active" @update:model-value="is_active = $event" />
          <div class="km-heading-3">{{ m.common_active() }}</div>
        </div>
        <div class="stack" data-gap="4">
          <div class="km-description text-secondary-text">Expires at</div>
          <km-input data-test="expires-input" class="full-width" type="datetime-local" :model-value="expires_at" clearable @change="expires_at = $event" />
        </div>
        <div class="stack" data-gap="4">
          <div class="km-description text-secondary-text">{{ m.common_notes() }}</div>
          <km-input data-test="notes-input" class="full-width" type="textarea" rows="4" autogrow :model-value="notes" @change="notes = $event" />
        </div>
      </div>
    </template>
  </layouts-details-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEntityAccess } from '@/composables/useEntityAccess'
import { m } from '@/paraglide/messages'

const router = useRouter()

const { draft, data: api_key, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('api_keys')
const { canDelete, recordReadonly, provideReadonly } = useEntityAccess('api_keys', draft)
provideReadonly()

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
