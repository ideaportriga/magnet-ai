<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="created_at" :updated-at="modified_at" :created-by="created_by" :updated-by="updated_by" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-btn :label="m.common_runEvaluation()" flat icon-size="16px" @click="runEvaluationDialog = true" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="evaluation-set-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_testSet() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_testSet() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_evaluationSetBody() }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'evaluation-set-readonly-zone' : null" class="stack full-height full-width my-md" data-gap="0" style="min-block-size: 0">
        <template v-if="tab == &quot;records&quot;">
          <div class="flex-1" style="min-block-size: 0">
            <evaluation-sets-records @record:update="evaluationSetRecord" />
          </div>
        </template>
        <template v-if="tab == &quot;settings&quot;">
          <div class="flex-1 overflow-auto">
            <evaluation-sets-settings />
          </div>
        </template>
        <template v-if="tab == &quot;postProcess&quot;" />
      </div>
    </template>
    <template #drawer>
      <evaluation-sets-drawer v-if="openDrawer" :open="openDrawer" />
    </template>
  </layouts-details-layout>
  <evaluation-sets-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
  <evaluation-jobs-create-new v-if="runEvaluationDialog" :show-new-dialog="runEvaluationDialog" :evaluation-set-code="evaluationSetCode" @create="createEvaluation" @cancel="runEvaluationDialog = false" />
  <km-popup-confirm :visible="showEvaluationCreateDialog" :confirm-button-label="m.common_viewEvaluation()" notification-icon="check" :cancel-button-label="m.common_cancel()" @cancel="showEvaluationCreateDialog = false" @confirm="navigateToEval">
    <div class="cluster km-heading-7" data-justify="center">{{ m.common_evaluationStarted() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.common_evaluationTakeTime() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.common_evaluationViewResults() }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@ds/composables/useNotify'
import { usePermissions } from '@shared'
import { validSystemName } from '@/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()
const { draft, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('evaluation_sets')

// PR 10 — record-level permission gating.
const { can, canOn } = usePermissions()
const canEdit = computed(() => canOn(draft?.value, 'edit', 'evaluations'))
const canDelete = computed(() => canOn(draft?.value, 'delete', 'evaluations'))
const canCreate = computed(() => can('write:evaluations'))
const recordReadonly = computed(() => {
  const e = draft?.value
  if (!e) return false
  return canEdit.value === false
})
provide('evaluationSetReadonly', recordReadonly)
const evalSetRecordStore = useEvaluationSetRecordStore()

const tab = ref('records')
const tabs = ref([
  { value: 'records', label: m.common_testSetItems() },
  { value: 'settings', label: m.common_settings() },
])
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const saving = ref(false)
const runEvaluationDialog = ref(false)
const showEvaluationCreateDialog = ref(false)
let evaluationId = null

const openDrawer = computed(() => tab.value === 'records' && Object.keys(evalSetRecordStore.record).length > 0)

const name = computed({
  get() { return draft.value?.name || '' },
  set(value) { updateField('name', value) },
})
const description = computed({
  get() { return draft.value?.description || '' },
  set(value) { updateField('description', value) },
})
const system_name = computed({
  get() { return draft.value?.system_name || '' },
  set(value) { updateField('system_name', value) },
})
const evaluationSetCode = computed(() => draft.value?.system_name)
const loading = computed(() => isLoading.value || !draft.value?.id)

const created_at = computed(() => draft.value?.created_at ? formatDate(draft.value.created_at) : '')
const modified_at = computed(() => draft.value?.updated_at ? formatDate(draft.value.updated_at) : '')
const created_by = computed(() => draft.value?.created_by || 'Unknown')
const updated_by = computed(() => draft.value?.updated_by || 'Unknown')

const evaluationSetRecord = ref({})

function formatDate(date) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

function createEvaluation(obj) {
  evaluationId = obj?.job_id || obj?.id
  showNewDialog.value = false
  if (evaluationId) showEvaluationCreateDialog.value = true
}

function navigateToEval() {
  const query = { job_id: evaluationId }
  router.push({ path: '/evaluation-jobs', query })
}

async function handleSave() {
  const systemNameValidation = validSystemName()(draft.value?.system_name)
  if (systemNameValidation !== true) {
    notify.error(systemNameValidation)
    return
  }
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

async function confirmDelete() {
  await remove()
  notify.success('Evaluation Set has been deleted.')
  router.push('/evaluation-sets')
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.evaluation-set-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.evaluation-set-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
