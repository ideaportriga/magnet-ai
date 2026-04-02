<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
      km-input-flat.col.km-description.text-black.full-width(
        placeholder='Enter system system_name',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
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
    km-btn(label='Run evaluation', flat, iconSize='16px', @click='runEvaluationDialog = true')
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
      confirmButtonLabel='Delete Evaluation Set',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Evaluation Set
      .row.text-center.justify-center This action will permanently delete the Evaluation Set.
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
  confirmButtonLabel='View Evaluation',
  notificationIcon='far fa-circle-check',
  cancelButtonLabel='Cancel',
  @cancel='showEvaluationCreateDialog = false',
  @confirm='navigateToEval'
)
  .row.item-center.justify-center.km-heading-7 Evaluation has started!
  .row.text-center.justify-center It may take some time for the Evaluation to finish.
  .row.text-center.justify-center You'll be able to view run results on the Evaluation screen.
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { validSystemName } from '@shared/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'

const route = useRoute()
const router = useRouter()
const q = useQuasar()
const { draft, isDirty, updateField, save, remove, revert } = useEntityDetail('evaluation_sets')
const evalSetRecordStore = useEvaluationSetRecordStore()

const tab = ref('records')
const tabs = ref([
  { name: 'records', label: 'Test Set Items' },
  { name: 'settings', label: 'Settings' },
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
const loading = computed(() => !draft.value?.id)

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
