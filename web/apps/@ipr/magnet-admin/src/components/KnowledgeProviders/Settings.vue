<template>
  <div class="full-width">
    <km-section :title="m.section_generalInfo()" :sub-title="m.subtitle_generalKspSettings()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_type() }}</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-select class="full-width" :model-value="provider.type" readonly disabled />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">{{ m.label_endpoint() }}</div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <div class="flex-1">
          <div class="cluster relative-position" data-gap="sm" data-wrap="no">
            <km-input class="full-width" :model-value="endpointValue" :readonly="!isEditingEndpoint" :placeholder="m.placeholder_exampleApiEndpoint()" @update:model-value="tempEndpoint = $event" />
            <div class="controls full-height cluster">
              <km-btn v-if="!knowledgeProviderReadonly && !isEditingEndpoint" icon="edit" flat icon-size="12px" size="xs" @click="startEditingEndpoint" />
              <km-btn v-if="isEditingEndpoint" icon="close" flat icon-size="12px" size="xs" @click="cancelEditingEndpoint" />
              <km-btn v-if="isEditingEndpoint" icon="check" flat icon-size="12px" size="xs" tone="brand" @click="saveEndpoint" />
            </div>
          </div>
        </div>
      </div>
      <div v-if="!isEditingEndpoint" class="km-description text-secondary-text pb-xs pl-sm">{{ m.hint_endpointWarning() }}</div>
      <div v-if="isEditingEndpoint" class="km-description text-negative pb-xs pl-sm">{{ m.hint_changeEndpointWarning() }}</div>
    </km-section>
    <km-popup-confirm :visible="showEndpointWarning" :title="m.dialog_changeEndpoint()" :confirm-button-label="m.confirm_yesClearSecrets()" :cancel-button-label="m.common_cancel()" :notification="m.hint_changeEndpointWarning()" @confirm="confirmEndpointChange" @cancel="cancelEndpointChange">
      <div class="text-body1">Are you sure you want to change the endpoint?</div>
      <div class="text-body2 mt-md">Current endpoint: {{ provider.endpoint || 'Not set' }}</div>
      <div class="text-body2">New endpoint: {{ tempEndpoint }}</div>
    </km-popup-confirm>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_connection()" :sub-title="m.subtitle_connectionParams()">
      <km-key-value-editor :model-value="provider?.connection_config || {}" :readonly="knowledgeProviderReadonly" @update:model-value="updateConnectionConfig" />
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_secrets()" :sub-title="m.subtitle_useSecretsKsp()">
      <km-secrets v-model:secrets="secrets" :original-secrets="originalProviderSecrets" :remount-value="remountValue" :readonly="knowledgeProviderReadonly" />
    </km-section>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const { draft, data, updateField, updateFields } = useEntityDetail('provider')
const knowledgeProviderReadonlyRef = inject('knowledgeProviderReadonly', null)
const knowledgeProviderReadonly = computed(() => Boolean(knowledgeProviderReadonlyRef?.value))

const provider = computed(() => draft.value)

const isEditingEndpoint = ref(false)
const tempEndpoint = ref('')
const showEndpointWarning = ref(false)

const endpointValue = computed(() => {
  if (isEditingEndpoint.value) {
    return tempEndpoint.value
  }
  return provider.value?.endpoint || ''
})

const startEditingEndpoint = () => {
  if (knowledgeProviderReadonly.value) return
  tempEndpoint.value = provider.value?.endpoint || ''
  isEditingEndpoint.value = true
}

const cancelEditingEndpoint = () => {
  isEditingEndpoint.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
}

const saveEndpoint = () => {
  if (knowledgeProviderReadonly.value) return
  if (tempEndpoint.value !== provider.value?.endpoint) {
    showEndpointWarning.value = true
  } else {
    isEditingEndpoint.value = false
  }
}

const confirmEndpointChange = () => {
  if (knowledgeProviderReadonly.value) return
  // Update endpoint and clear secrets in draft
  updateFields({
    endpoint: tempEndpoint.value,
    secrets_encrypted: {},
  })
  showEndpointWarning.value = false
  isEditingEndpoint.value = false
  tempEndpoint.value = ''
}

const cancelEndpointChange = () => {
  showEndpointWarning.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
}

const originalProviderSecrets = computed(() => {
  const secrets = data.value?.secrets_encrypted
  if (!secrets) return []
  return Object.keys(secrets)
})
const remountValue = computed(() => provider.value?.updated_at)

const secrets = computed({
  get() {
    const encryptedSecrets = provider.value?.secrets_encrypted
    if (!encryptedSecrets) {
      return {}
    }
    return { ...encryptedSecrets }
  },
  set(value) {
    if (knowledgeProviderReadonly.value) return
    updateField('secrets_encrypted', value)
  },
})

const updateConnectionConfig = (value) => {
  if (knowledgeProviderReadonly.value) return
  updateField('connection_config', value)
}

</script>

<style scoped>
.controls {
  position: absolute;
  inset-inline-end: 5px;
  inset-block-start: 0;
}
</style>
