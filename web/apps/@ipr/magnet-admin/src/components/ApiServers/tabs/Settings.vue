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
        km-btn(label='Cancel', @click='store.dispatch("toggleApiSettingsSecretsEditMode", false)', size='sm', flat)
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
    // Всегда возвращаем Map для единообразия
    if (!securityValuesData) {
      return new Map()
    }
    if (securityValuesData instanceof Map) {
      return securityValuesData
    }
    // Преобразуем объект в Map
    return new Map(Object.entries(securityValuesData))
  },
  set(value) {
    // Преобразуем Map в объект для отправки
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

const secret_names = computed(() => {
  if (!server.value.secrets_names) return []
  return server.value.secrets_names
})

const editMode = computed(() => store.getters.apiSettingsSecretsEditMode)

const hasExistingSecrets = computed(() => {
  const encryptedSecrets = server.value?.secrets_encrypted
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

const secrets = computed({
  get() {
    const encryptedSecrets = server.value?.secrets_encrypted
    if (!encryptedSecrets) {
      return new Map()
    }
    if (encryptedSecrets instanceof Map) {
      return encryptedSecrets
    }
    return new Map(Object.entries(encryptedSecrets))
  },
  set(value) {
    const objectValue = value instanceof Map ? Object.fromEntries(value) : value
    store.dispatch('updateApiServerProperty', { key: 'secrets_encrypted', value: objectValue })
  },
})

const initializeSecretsEdit = () => {
  console.log('initializeSecretsEdit called')
  
  store.dispatch("toggleApiSettingsSecretsEditMode", true)
  
  if (!hasExistingSecrets.value) {
    console.log('No existing secrets, adding empty entry')
    const newSecrets = new Map()
    newSecrets.set('', '')
    secrets.value = newSecrets
  }
}

const getSecretDisplayValue = (key, value) => {
  if (!editMode.value) {
    return '*****'
  } else {
    return value || ''
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

const getSecretsForSubmit = () => {
  const currentSecrets = secrets.value
  const result = {}
  
  if (currentSecrets instanceof Map) {
    for (const [key, value] of currentSecrets) {
      if (key && key.trim()) { 
        result[key] = value || ''
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
