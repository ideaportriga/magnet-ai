<template>
  <transition appear enter-active-class="animated fadeIn" leave-active-class="animated fadeOut">
    <km-drawer-layout v-if="open" storage-key="drawer-prompt-queue" no-scroll>
      <template #header>
        <div class="cluster" data-justify="between">
          <div class="flex-none km-heading-7">Execute</div>
          <km-btn icon="close" flat dense @click="$emit(&quot;update:open&quot;, false)" />
        </div>
      </template>
      <div class="km-description text-secondary-text mb-sm">Run the queue with the input values below</div>
      <div v-if="testInputs.length" class="gap-sm mb-sm">
        <div class="km-field text-secondary-text pb-xs">Test input set</div>
        <km-select :model-value="selectedTestInputId" :options="testInputOptions" option-label="label" option-value="value" emit-value map-options clearable :placeholder="m.promptQueue_selectSavedTestInput()" style="max-inline-size: 100%" @update:model-value="onSelectTestInput" />
      </div>
      <div class="gap-sm mb-sm">
        <div v-for="param in expectedInputParams" :key="param" class="cluster" data-gap="sm">
          <div class="flex-none km-field" style="min-inline-size: 120px">{{ param }}</div>
          <div class="flex-1">
            <km-input :model-value="executeInput[param]" :placeholder="m.promptQueue_enterValue()" style="max-inline-size: 400px" @update:model-value="executeInput[param] = $event" />
          </div>
        </div>
      </div>
      <div class="cluster mb-sm" data-gap="sm">
        <km-btn :label="m.common_execute()" icon="play" @click="execute" />
        <km-loader v-if="executing" size="24px" />
        <div v-if="!expectedInputParams.length" class="km-description text-secondary-text">No input params. Add in Expected input tab or use empty input.</div>
      </div>
      <div v-if="executeResult !== null" class="ba-border border-radius-8 p-sm mt-sm">
        <div class="km-field text-secondary-text mb-sm">Result</div>
        <km-codemirror :model-value="executeResultJson" readonly language="json" :options="{ mode: &quot;application/json&quot; }" style="min-block-size: 200px; max-block-size: 400px; font-size: 13px" />
      </div>
    </km-drawer-layout>
  </transition>
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
