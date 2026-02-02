<template lang="pug">
.full-width
  km-section(title='Connection settings', subTitle='Endpoint URL')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 URL
    .row.items-center.q-gap-16.no-wrap
      km-input.full-width(:model-value='server?.url', readonly)
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-lg Verify ssl certificate
    .row.items-center.q-gap-16.no-wrap
      q-toggle(v-model='verifySsl')
        .text-secondary-text {{ verifySsl ? 'Yes' : 'No' }}
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Custom Headers', subTitle='Add custom HTTP headers to include with every request')
    km-notification-text(
      notification='Define custom headers that will be sent with each API request. Use placeholders in curly braces to reference secrets.'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in customHeaders', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Header Name
        km-input(label='Header Name', :model-value='key', @update:model-value='updateCustomHeader(key, $event, value)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Header Value
        km-input(label='Header Value', :model-value='value', @update:model-value='updateCustomHeader(key, key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeCustomHeader(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(label='Add Custom Header', @click='addCustomHeader', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Security schema', subTitle='Authentication and authorization scheme to access the endpoint')
    km-notification-text
      div Supported types: apiKey, basic, oauth2. Check
        | &nbsp;
        a.text-primary(href='https://swagger.io/docs/specification/v3_0/authentication/', target='_blank') OpenAPI documentation
        |
        | for information.
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-lg Security schema
    .row.items-center.q-gap-16.no-wrap
      km-input.full-width(v-model='serverSecurityScheme', type='textarea', rows='4')
    .km-small-chip.q-pa-4.q-pl-8.text-error-text(v-if='parsingError') Invalid JSON format. Please check your input and ensure it follows valid JSON syntax.
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Security Values', subTitle='Security values depending on security schema type')
    km-notification-text(
      notification='Do not expose sensitive data in this section. Instead, use placeholders and provide actual values in the Secrets section. Use curly braces to insert placeholders.'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in securityValues', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateSecurityValue(key, $event, value)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', :model-value='value', @update:model-value='updateSecurityValue(key, key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeSecurityValue(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(label='Add Security Value', @click='addSecurityValue', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Secrets', subTitle='Use to store sensitive values such as API keys or passwords.')
    km-secrets(v-model:secrets='secrets', :original-secrets='originalApiSecrets', :remount-value='remountValue')
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

const server = computed(() => store.getters.api_server)
const parsingError = ref(false)

const serverSecurityScheme = computed({
  get() {
    if (typeof server.value?.security_scheme === 'string') {
      return server.value?.security_scheme
    }
    return JSON.stringify(server.value?.security_scheme || {}, null, 2)
  },
  set(newValue) {
    try {
      const parsedNewValue = JSON.parse(newValue)
      server.value.security_scheme = parsedNewValue
      parsingError.value = false
    } catch (e) {
      server.value.security_scheme = newValue
      parsingError.value = true
      console.log('failed to parse JSON for security_scheme')
    }
  },
})

const securityValues = computed({
  get() {
    const securityValuesData = server.value.security_values
    // Always return Map for consistency
    if (!securityValuesData) {
      return new Map()
    }
    if (securityValuesData instanceof Map) {
      return securityValuesData
    }
    // Convert object to Map
    return new Map(Object.entries(securityValuesData))
  },
  set(value) {
    // Convert Map to object for sending
    const objectValue = value instanceof Map ? Object.fromEntries(value) : value
    store.dispatch('updateApiServerProperty', { key: 'security_values', value: objectValue })
  },
})

const verifySsl = computed({
  get: () => server.value.verify_ssl,
  set: (value) => {
    store.dispatch('updateApiServerProperty', { key: 'verify_ssl', value })
  },
})

const originalApiSecrets = computed(() => store.getters.originalApiSecrets)
const remountValue = computed(() => server.value?.updated_at)

const secrets = computed({
  get() {
    const encryptedSecrets = server.value?.secrets_encrypted
    if (!encryptedSecrets) {
      return {}
    }
    if (encryptedSecrets instanceof Map) {
      return Object.fromEntries(encryptedSecrets)
    }
    return encryptedSecrets
  },
  set(value) {
    store.dispatch('updateApiServerProperty', { key: 'secrets_encrypted', value })
  },
})

const customHeaders = computed({
  get: () => server.value.custom_headers || new Map(),
  set: (value) => {
    store.dispatch('updateApiServerProperty', { key: 'custom_headers', value })
  },
})

const updateCustomHeader = (oldKey, newKey, newValue) => {
  const entries = [...customHeaders.value.entries()]
  const idx = entries.findIndex(([k]) => k === oldKey)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue]
  } else {
    entries.push([newKey, newValue])
  }

  customHeaders.value = new Map(entries)
}

const addCustomHeader = () => {
  const newCustomHeaders = new Map(customHeaders.value)
  newCustomHeaders.set('', '')
  customHeaders.value = newCustomHeaders
}

const removeCustomHeader = (key) => {
  const newCustomHeaders = new Map(customHeaders.value)
  newCustomHeaders.delete(key)
  customHeaders.value = newCustomHeaders
}

const updateSecurityValue = (oldKey, newKey, newValue) => {
  const currentSecurityValues = securityValues.value
  const entries = [...currentSecurityValues.entries()]
  const idx = entries.findIndex(([k]) => k === oldKey)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  securityValues.value = new Map(entries)
}

const addSecurityValue = () => {
  const newSecurityValues = new Map(securityValues.value)
  newSecurityValues.set('', '')
  securityValues.value = newSecurityValues
}

const removeSecurityValue = (key) => {
  const newSecurityValues = new Map(securityValues.value)
  newSecurityValues.delete(key)
  securityValues.value = newSecurityValues
}
</script>
