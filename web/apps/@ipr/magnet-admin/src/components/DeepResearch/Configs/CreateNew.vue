<template>
  <km-popup-confirm :visible="showNewDialog" :title="copy ? &quot;Clone Deep Research Config&quot; : &quot;New Deep Research Config&quot;" confirm-button-label="Save" cancel-button-label="Cancel" notification="You will be able to configure prompts, iterations, and other settings after saving." @confirm="createConfig" @cancel="emit(&quot;cancel&quot;)">
    <div class="stack" data-gap="lg">
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">Name</div>
        <div class="full-width">
          <km-input v-if="showNewDialog" ref="nameRef" v-model="name" height="30px" :placeholder="m.deepResearch_research()" :rules="[required()]" />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pl-sm">System name</div>
        <div class="full-width">
          <km-input v-if="showNewDialog" ref="system_nameRef" v-model="system_name" height="30px" placeholder="" :rules="[required()]" />
        </div>
        <div class="km-description text-secondary-text pb-xs pl-sm">System name serves as a unique record ID</div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useDeepResearchStore } from '@/stores/deepResearchStore'
import { useNotify } from '@/composables/useNotify'

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
const drStore = useDeepResearchStore()
const { notifySuccess, notifyError } = useNotify()

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
    const currentConfig = drStore.selectedConfig
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

    const result = await drStore.createConfig(configData)

    notifySuccess(props.copy ? 'Deep Research Config has been cloned' : 'Deep Research Config has been created')

    // Reset form
    name.value = ''
    system_name.value = ''
    configToCopy.value = null

    emit('created', result.id)
  } catch (error) {
    notifyError(error?.message || 'Failed to create configuration')
  }
}
</script>
