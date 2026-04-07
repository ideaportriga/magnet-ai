<template lang="pug">
transition(appear, enter-active-class='animated fadeIn', leave-active-class='animated fadeOut')
  km-drawer-layout(v-if='open', storageKey="drawer-prompt-queue", noScroll)
    template(#header)
      .row.items-center.justify-between
        .col-auto.km-heading-7 Execute
        q-btn(icon='close', flat, dense, @click='$emit("update:open", false)')
    .km-description.text-secondary-text.q-mb-sm Run the queue with the input values below
    .q-gutter-sm.q-mb-sm(v-if='testInputs.length')
      .km-field.text-secondary-text.q-pb-xs Test input set
      km-select(
        :model-value='selectedTestInputId',
        @update:model-value='onSelectTestInput',
        :options='testInputOptions',
        option-label='label',
        option-value='value',
        emit-value,
        map-options,
        clearable,
        :placeholder='m.promptQueue_selectSavedTestInput()',
        style='max-width: 100%'
      )
    .q-gutter-sm.q-mb-sm
      .row.q-gutter-sm(v-for='param in expectedInputParams', :key='param')
        .col-auto.km-field(style='min-width: 120px') {{ param }}
        .col
          km-input(
            :model-value='executeInput[param]',
            @update:model-value='executeInput[param] = $event',
            :placeholder='m.promptQueue_enterValue()',
            style='max-width: 400px'
          )
    .row.q-gutter-sm.items-center.q-mb-sm
      km-btn(:label='m.common_execute()', icon='play_arrow', @click='execute')
      q-spinner(v-if='executing', size='24px', color='primary')
      .km-description.text-secondary-text(v-if='!expectedInputParams.length') No input params. Add in Expected input tab or use empty input.
    .ba-border.border-radius-8.q-pa-8.q-mt-sm(v-if='executeResult !== null')
      .km-field.text-secondary-text.q-mb-sm Result
      km-codemirror(
        :model-value='executeResultJson',
        readonly,
        language='json',
        :options='{ mode: "application/json" }',
        style='min-height: 200px; max-height: 400px; font-size: 13px'
      )
</template>

<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { usePromptQueueStore } from '@/stores/promptQueueStore'
import { useNotify } from '@/composables/useNotify'

const props = defineProps({
  open: Boolean,
  configId: String,
  expectedInputParams: {
    type: Array,
    default: () => [],
  },
  testInputs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:open'])

const pqStore = usePromptQueueStore()
const { notifySuccess, notifyError } = useNotify()

const executing = ref(false)
const executeInput = ref({})
const executeResult = ref(null)
const selectedTestInputId = ref(null)

const testInputs = computed(() => props.testInputs || [])

const testInputOptions = computed(() =>
  testInputs.value.map((ti, idx) => ({ label: ti.name, value: String(idx) }))
)

const onSelectTestInput = (val) => {
  selectedTestInputId.value = val
  if (val == null) {
    executeInput.value = {}
    return
  }
  const idx = parseInt(val, 10)
  const ti = testInputs.value[idx]
  if (ti?.values) {
    executeInput.value = { ...ti.values }
  }
}

const executeResultJson = computed(() => {
  if (executeResult.value === null) return ''
  try {
    return JSON.stringify(executeResult.value, null, 2)
  } catch {
    return String(executeResult.value)
  }
})

const execute = async () => {
  if (!props.configId) return
  executing.value = true
  executeResult.value = null
  try {
    const input = {}
    for (const param of (props.expectedInputParams || [])) {
      const val = executeInput.value[param]
      if (val != null && val !== '') input[param] = String(val)
    }
    const result = await pqStore.executePromptQueue({
      configId: props.configId,
      input,
    })
    executeResult.value = result
    notifySuccess('Execution completed')
  } catch (error) {
    notifyError(error?.message || 'Execution failed')
    executeResult.value = { error: error?.message || 'Execution failed' }
  } finally {
    executing.value = false
  }
}
</script>
