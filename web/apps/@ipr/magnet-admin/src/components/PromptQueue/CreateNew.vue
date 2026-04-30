<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newPromptQueueConfig()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_addStepsAfterSaving()" @confirm="createConfig" @cancel="emit(&quot;cancel&quot;)">
    <div class="stack" data-gap="lg">
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
        <div class="full-width">
          <km-input v-if="showNewDialog" ref="nameRef" v-model="name" height="30px" :placeholder="m.promptQueue_myQueue()" :rules="[required()]" />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pl-sm">{{ m.common_systemName() }}</div>
        <div class="full-width">
          <km-input v-if="showNewDialog" ref="system_nameRef" v-model="system_name" height="30px" placeholder="" :rules="[required()]" />
        </div>
        <div class="km-description text-secondary-text pb-xs pl-sm">{{ m.hint_systemNameUniqueId() }}</div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { usePromptQueueStore } from '@/stores/promptQueueStore'
import { useNotify } from '@/composables/useNotify'

const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['cancel', 'created'])
const pqStore = usePromptQueueStore()
const { notifySuccess, notifyError } = useNotify()

const name = ref('')
const system_name = ref('')
const nameRef = ref(null)
const system_nameRef = ref(null)

watch(name, (newVal) => {
  if (newVal && !system_name.value) {
    system_name.value = toUpperCaseWithUnderscores(newVal)
  }
})

const validateFields = () => {
  const validStates = [nameRef.value?.validate(), system_nameRef.value?.validate()]
  return !validStates.includes(false)
}

const createConfig = async () => {
  if (!validateFields()) return

  try {
    const result = await pqStore.createPromptQueueConfig({
      name: name.value,
      system_name: system_name.value,
      description: '',
      config: { steps: [] },
    })

    notifySuccess('Prompt Queue Config has been created')

    name.value = ''
    system_name.value = ''

    emit('created', result.id)
  } catch (error) {
    notifyError(error?.message || 'Failed to create configuration')
  }
}
</script>
