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
    .row.items-center.q-gap-8.no-wrap.q-mt-md(v-for='(secret, index) in secret_names', :key='index', v-if='!editMode')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='secret', readonly)
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', model-value='*********************', readonly)
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in secrets', v-else)
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateSecret(key, $event, value)')
        .km-description.text-secondary-text.q-mt-xs.q-ml-xs &nbsp;
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', :model-value='value', @update:model-value='updateSecret(key, key, $event)')
        .km-description.text-secondary-text.q-mt-xs After saving, the secret will get encrypted and hidden from view.
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeSecret(key)', icon='o_delete', size='sm', flat, color='negative')
        .km-description.text-secondary-text.q-mt-xs.q-ml-xs &nbsp;
    .row.q-pt-16
      template(v-if='editMode')
        km-btn(label='Add Secret', @click='addSecret', size='sm', icon='o_add', flat)
        km-btn(label='Cancel', @click='store.dispatch("toggleMcpSettingsEditMode", false)', size='sm', flat)
      template(v-else)
        km-btn(
          :label='server.secrets_names?.length > 0 ? "Edit Secrets" : "Add Secrets"',
          @click='store.dispatch("toggleMcpSettingsEditMode", true)',
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
    return store.getters.mcp_server.secrets || new Map()
  },
  set(value) {
    store.dispatch('updateMcpServerProperty', {
      key: 'secrets',
      value: value,
    })
  },
})

const secret_names = computed(() => {
  if (!server.value.secrets_names) return []
  return server.value.secrets_names
})

const toggleEditMode = (value) => {
  if (value) {
    if (!server.value.secrets_names) {
      console.log('update secrets_names')
      store.dispatch('updateMcpServerProperty', {
        key: 'secrets',
        value: new Map([['', '']]),
      })
    } else {
      store.dispatch('updateMcpServerProperty', {
        key: 'secrets',
        value: new Map(secret_names.value.map((key) => [key, ''])),
      })
    }
    editMode.value = true
  } else {
    store.dispatch('removeMcpServerProperty', 'secrets')
    editMode.value = false
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
  const newHeaders = new Map(headers.value)
  if (oldKey !== newKey) {
    newHeaders.delete(oldKey)
  }
  newHeaders.set(newKey, newValue)
  headers.value = newHeaders
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
  const newSecrets = new Map(secrets.value)
  newSecrets.set('', '')
  secrets.value = newSecrets
}

const removeSecret = (key) => {
  const newSecrets = new Map(secrets.value)
  newSecrets.delete(key)
  secrets.value = newSecrets
}
const updateSecret = (oldKey, newKey, newValue) => {
  const newSecrets = new Map(secrets.value)
  if (oldKey !== newKey) {
    newSecrets.delete(oldKey)
  }
  newSecrets.set(newKey, newValue)
  secrets.value = newSecrets
}
</script>
