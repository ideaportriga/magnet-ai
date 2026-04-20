<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(data-test='name-input', :placeholder='m.common_name()', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(data-test='description-input', :placeholder='m.common_description()', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.text-black.full-width(
        data-test='system-name-input',
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
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
    km-btn(:label='m.common_runEvaluation()', flat, iconSize='16px', @click='runEvaluationDialog = true')
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
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_testSet() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_testSet() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_evaluationSetBody() }}
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.full-height.full-width.q-my-md(style='min-height: 0')
      template(v-if='tab == "records"')
        .col(style='min-height: 0')
          evaluation-sets-records(@record:update='evaluationSetRecord')
      template(v-if='tab == "settings"')
        .col.overflow-auto
          evaluation-sets-settings
      template(v-if='tab == "postProcess"')
  template(#drawer)
    evaluation-sets-drawer(v-if='openDrawer', :open='openDrawer')
evaluation-sets-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
evaluation-jobs-create-new(
  :showNewDialog='runEvaluationDialog',
  @create='createEvaluation',
  @cancel='runEvaluationDialog = false',
  v-if='runEvaluationDialog',
  :evaluationSetCode='evaluationSetCode'
)
km-popup-confirm(
  :visible='showEvaluationCreateDialog',
  :confirmButtonLabel='m.common_viewEvaluation()',
  notificationIcon='far fa-circle-check',
  :cancelButtonLabel='m.common_cancel()',
  @cancel='showEvaluationCreateDialog = false',
  @confirm='navigateToEval'
)
  .row.item-center.justify-center.km-heading-7 {{ m.common_evaluationStarted() }}
  .row.text-center.justify-center {{ m.common_evaluationTakeTime() }}
  .row.text-center.justify-center {{ m.common_evaluationViewResults() }}
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { validSystemName } from '@/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()
const q = useQuasar()
const { draft, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('evaluation_sets')
const evalSetRecordStore = useEvaluationSetRecordStore()

const tab = ref('records')
const tabs = ref([
  { name: 'records', label: m.common_testSetItems() },
  { name: 'settings', label: m.common_settings() },
])
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const saving = ref(false)
const runEvaluationDialog = ref(false)
const showEvaluationCreateDialog = ref(false)
const showInfo = ref(false)
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
    q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
    return
  }
  saving.value = true
  try {
    const result = await save()
    if (result.success) {
      q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
    } else if (result.error) {
      throw result.error
    }
  } catch (error) {
    q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  await remove()
  q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Evaluation Set has been deleted.', timeout: 1000 })
  router.push('/evaluation-sets')
}
</script>

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}
</style>
