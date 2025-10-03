<template lang="pug">
.full-width
  km-section(title='Connection settings', subTitle='Endpoint URL and transport protocol used to communicate with the server')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 URL
    .row.items-center.q-gap-16.no-wrap
      km-input.full-width(:model-value='server.url', readonly)
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg Transport
    .row.items-center.q-gap-16.no-wrap
      q-radio.q-my-sm(
        :model-value='server.transport',
        dense,
        label='streamable-http',
        val='streamable-http',
        size='xs',
        disabled,
        color='grey-6',
        disable
      )
      q-radio.q-my-sm(:model-value='server.transport', dense, label='sse', val='sse', size='xs', disabled, color='grey-6', disable)
    .row.q-mt-lg
      km-btn(label='Test connection', @click='testConnection', size='sm', icon='fa fa-arrow-right-arrow-left', flat, iconSize='14px')

  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Headers', subTitle='Use headers to send additional information with your request, such as authentication tokens.')
    km-notification-text(
      notification='Do not expose sensitive data in this section. Instead, use placeholders and provide actual values in the Secrets section. Use curly braces to insert placeholders.'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in headers', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateHeader(key, $event, value)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', :model-value='value', @update:model-value='updateHeader(key, key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeHeader(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(label='Add Header Record', @click='addHeader', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Secrets', subTitle='Use to store sensitive values such as API keys or tokens.')
    km-notification-text(
      notification='Secrets are securely stored in encrypted format. They cannot be edited individually. To update them, you need to reset all secrets.'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-md(v-for='[key, value] in secretsArray', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateSecret(key, $event, value)', :readonly='!editMode')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(
          label='Value', 
          :model-value='getSecretDisplayValue(key, value)', 
          @update:model-value='updateSecret(key, key, $event)', 
          :readonly='!editMode',
          :placeholder='editMode ? "Enter new value" : ""'
        )
      .col-auto(v-if='editMode')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeSecret(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      template(v-if='editMode')
        km-btn(label='Add Secret', @click='addSecret', size='sm', icon='o_add', flat)
        km-btn(label='Cancel', @click='store.dispatch("toggleMcpSettingsEditMode", false)', size='sm', flat)
      template(v-else)
        km-btn(
          :label='hasExistingSecrets ? "Edit Secrets" : "Add Secrets"',
          @click='initializeSecretsEdit',
          size='sm',
          icon='o_edit',
          flat
        )
</template>
<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useQuasar } from 'quasar'

const store = useStore()
const $q = useQuasar()

const editMode = computed(() => store.getters.mcpSettingsEditMode)

const hasExistingSecrets = computed(() => {
  const encryptedSecrets = server.value.secrets_encrypted
  if (!encryptedSecrets) return false
  
  if (encryptedSecrets instanceof Map) {
    return encryptedSecrets.size > 0
  } else if (typeof encryptedSecrets === 'object') {
    return Object.keys(encryptedSecrets).length > 0
  }
  return false
})

const secretsArray = computed(() => {
  const secretsMap = secrets.value
  if (secretsMap instanceof Map) {
    return Array.from(secretsMap.entries())
  }
  return []
})

const server = computed(() => {
  return store.getters.mcp_server
})

const headers = computed({
  get() {
    return store.getters.mcp_server.headers || new Map()
  },
  set(value) {
    console.log(value)
    store.dispatch('updateMcpServerProperty', {
      key: 'headers',
      value: value,
    })
  },
})
const secrets = computed({
  get() {
    const encryptedSecrets = store.getters.mcp_server.secrets_encrypted
    // Always return Map for consistency
    if (!encryptedSecrets) {
      return new Map()
    }
    if (encryptedSecrets instanceof Map) {
      return encryptedSecrets
    }
    // Convert object to Map
    return new Map(Object.entries(encryptedSecrets))
  },
  set(value) {
    // Convert Map to object for sending
    const objectValue = value instanceof Map ? Object.fromEntries(value) : value
    store.dispatch('updateMcpServerProperty', {
      key: 'secrets_encrypted',
      value: objectValue,
    })
  },
})

const secret_names = computed(() => {
  if (!server.value.secrets_encrypted) return []
  return server.value.secrets_encrypted
})

const toggleEditMode = (value) => {
  // Do nothing additional, just toggle mode
  // Always work with secrets_encrypted
}

const initializeSecretsEdit = () => {
  console.log('initializeSecretsEdit called')
  
  // Enable edit mode
  store.dispatch("toggleMcpSettingsEditMode", true)
  
  // If there are no existing secrets, add an empty entry to start
  if (!hasExistingSecrets.value) {
    console.log('No existing secrets, adding empty entry')
    const newSecrets = new Map()
    newSecrets.set('', '')
    secrets.value = newSecrets
  }
}

const addHeader = () => {
  const newHeaders = new Map(headers.value)
  newHeaders.set('', '')
  headers.value = newHeaders
}

const removeHeader = (key) => {
  const newHeaders = new Map(headers.value)
  newHeaders.delete(key)
  headers.value = newHeaders
}

const updateHeader = (oldKey, newKey, newValue) => {
  const entries = [...headers.value.entries()]
  const idx = entries.findIndex(([k]) => k === oldKey)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  headers.value = new Map(entries)
}

const testConnection = async () => {
  const res = await store.dispatch('testMcpServerConnection', { id: server.value.id })
  console.log(res)
  if (res) {
    $q.notify({
      position: 'bottom',
      message: 'MCP Server connection test: Success',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } else {
    $q.notify({
      position: 'bottom',
      message: 'MCP Server connection test: Error',
      color: 'negative',
      textColor: 'black',
      timeout: 1000,
    })
  }
}

const addSecret = () => {
  console.log('addSecret called')
  const currentSecrets = secrets.value
  console.log('current secrets:', currentSecrets)
  
  const newSecrets = new Map(currentSecrets)
  newSecrets.set('', '')
  console.log('new secrets:', newSecrets)
  
  secrets.value = newSecrets
}

const removeSecret = (key) => {
  const newSecrets = new Map(secrets.value)
  newSecrets.delete(key)
  secrets.value = newSecrets
}

const updateSecret = (oldKey, newKey, newValue) => {
  const entries = [...secrets.value.entries()]
  const idx = entries.findIndex(([k]) => k === oldKey)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  secrets.value = new Map(entries)
}

const getSecretDisplayValue = (key, value) => {
  if (!editMode.value) {
    return '*****'
  } else {
    return value || ''
  }
}

const getSecretsForSubmit = () => {
  const currentSecrets = secrets.value
  const result = {}
  
  if (currentSecrets instanceof Map) {
    for (const [key, value] of currentSecrets) {
      if (key && key.trim()) { // Ignore empty keys
        result[key] = value || '' // Send value or empty string
      }
    }
  } else if (typeof currentSecrets === 'object') {
    for (const key in currentSecrets) {
      if (key && key.trim()) {
        result[key] = currentSecrets[key] || ''
      }
    }
  }
  
  return result
}
</script>
