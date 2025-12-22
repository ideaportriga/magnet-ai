<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='copy ? "Clone Deep Research Config" : "New Deep Research Config"',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to configure prompts, iterations, and other settings after saving.',
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
          placeholder='Research',
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
import { ref, watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useQuasar } from 'quasar'
import { required, toUpperCaseWithUnderscores } from '@shared'

const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
  copy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['cancel', 'created'])
const store = useStore()
const $q = useQuasar()

const name = ref('')
const system_name = ref('')
const configToCopy = ref(null)
const nameRef = ref(null)
const system_nameRef = ref(null)

watch(name, (newVal) => {
  if (newVal && !system_name.value) {
    system_name.value = toUpperCaseWithUnderscores(newVal)
  }
})

onMounted(() => {
  if (props.copy) {
    const currentConfig = store.getters.selectedConfig
    if (currentConfig) {
      configToCopy.value = JSON.parse(JSON.stringify(currentConfig))
      name.value = (currentConfig.name || '') + '_COPY'
      system_name.value = (currentConfig.system_name || '') + '_COPY'
    }
  }
})

const validateFields = () => {
  const validStates = [nameRef.value?.validate(), system_nameRef.value?.validate()]
  return !validStates.includes(false)
}

const createConfig = async () => {
  if (!validateFields()) return

  try {
    const configData = {
      name: name.value,
      system_name: system_name.value,
      description: configToCopy.value?.description || '',
      config: configToCopy.value?.config || {},
    }

    const result = await store.dispatch('createConfig', configData)

    $q.notify({
      position: 'top',
      message: props.copy ? 'Deep Research Config has been cloned' : 'Deep Research Config has been created',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })

    // Reset form
    name.value = ''
    system_name.value = ''
    configToCopy.value = null

    emit('created', result.id)
  } catch (error) {
    $q.notify({
      position: 'top',
      message: error?.message || 'Failed to create configuration',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  }
}
</script>
