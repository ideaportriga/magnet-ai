<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Prompt Queue Config',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to add steps and prompt templates after saving.',
  @confirm='createConfig',
  @cancel='emit("cancel")'
)
  .column.q-gap-16
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
      .full-width
        km-input(
          v-if='showNewDialog',
          height='30px',
          placeholder='My Queue',
          v-model='name',
          ref='nameRef',
          :rules='[required()]'
        )

    .col
      .km-field.text-secondary-text.q-pl-8 System name
      .full-width
        km-input(
          v-if='showNewDialog',
          height='30px',
          placeholder='',
          v-model='system_name',
          ref='system_nameRef',
          :rules='[required()]'
        )
      .km-description.text-secondary-text.q-pb-4.q-pl-8 System name serves as a unique record ID
</template>

<script setup>
import { ref, watch } from 'vue'
import { required, toUpperCaseWithUnderscores } from '@shared'
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
