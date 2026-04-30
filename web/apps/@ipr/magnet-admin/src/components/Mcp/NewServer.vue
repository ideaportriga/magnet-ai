<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newMcpServer()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_addHeadersMcp()" @confirm="createMCPServer" @cancel="$emit(&quot;cancel&quot;)">
    <div class="stack" data-gap="lg">
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
        <div class="full-width">
          <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :rules="[required()]" />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pl-sm">{{ m.common_systemName() }}</div>
        <div class="full-width">
          <km-input ref="systemRef" v-model="system_name" data-test="system-name-input" height="30px" :rules="[required()]" />
        </div>
        <div class="km-description text-secondary-text pb-xs pl-sm">{{ m.hint_systemNameUniqueId() }}</div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_url() }}</div>
        <div class="full-width">
          <km-input ref="urlRef" v-model="url" data-test="url-input" height="30px" :rules="[required()]" />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_transport() }}</div>
        <div class="cluster" data-gap="lg">
          <km-radio v-model="transport" class="my-sm" name="transport" dense label="streamable-http" val="streamable-http" size="xs" />
          <km-radio v-model="transport" class="my-sm" name="transport" dense label="sse" val="sse" size="xs" />
        </div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useRouter } from 'vue-router'
import { useSafeMutation } from '@/composables/useSafeMutation'
const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
})

const queries = useEntityQueries()
// §B.8 — wrap the raw mutation so a server error surfaces a toast and
// the dialog can react via `success` instead of leaving router.push +
// emit('cancel') unreachable.
const createMcp = useSafeMutation(queries.mcp_servers.useCreate())
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
  const { success, data: res } = await createMcp.run({
    name: name.value,
    system_name: system_name.value,
    url: url.value,
    transport: transport.value,
  })
  if (!success) return
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
