<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New MCP Server',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to add headers and secrets later in MCP Server settings.',
  @confirm='createMCPServer',
  @cancel='$emit("cancel")'
)
  .column.q-gap-16
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
      .full-width
        km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')

    .col
      .km-field.text-secondary-text.q-pl-8 System name
      .full-width
        km-input(data-test='name-input', height='30px', v-model='system_name', ref='systemRef', :rules='[required()]')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 System name serves as a unique record ID

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 URL
      .full-width
        km-input(data-test='name-input', height='30px', v-model='url', ref='urlRef', :rules='[required()]')
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Transport
      .row.q-gap-16
        q-radio.q-my-sm(name='transport', dense, label='streamable-http', val='streamable-http', v-model='transport', size='xs')
        q-radio.q-my-sm(name='transport', dense, label='sse', val='sse', v-model='transport', size='xs')
</template>

<script setup>
import { ref, watch } from 'vue'
import { required } from '@shared'
import { useChroma } from '@shared'
import { useRouter } from 'vue-router'
const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
})

const { create } = useChroma('mcp_servers')
const router = useRouter()
const name = ref('')
const system_name = ref('')
const url = ref('')
const transport = ref('streamable-http')

const emit = defineEmits(['cancel'])

const nameRef = ref(null)
const systemRef = ref(null)
const urlRef = ref(null)

const createMCPServer = async () => {
  if (!validateFields()) return
  const data = {
    name: name.value,
    system_name: system_name.value,
    url: url.value,
    transport: transport.value,
  }
  const res = await create(JSON.stringify(data))
  console.log(res)
  if (res) {
    router.push(`/mcp/${res.id}`)
  }
  emit('cancel')
}

watch(name, (newVal) => {
  if (newVal && !system_name.value) {
    system_name.value = newVal.toUpperCase().replace(/ /g, '_')
  }
})

const validateFields = () => {
  const validStates = [nameRef.value.validate(), systemRef.value.validate(), urlRef.value.validate()]
  return !validStates.includes(false)
}
</script>
