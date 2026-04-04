<template lang="pug">
.full-width
  km-section(:title='m.section_connectionSettings()', :subTitle='m.subtitle_endpointUrlTransport()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_url() }}
    .row.items-center.q-gap-16.no-wrap
      km-input.full-width(:model-value='server.url', readonly)
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg {{ m.label_transport() }}
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
      km-btn(:label='m.mcpServers_testConnection()', @click='testConnection', size='sm', icon='fa fa-arrow-right-arrow-left', flat, iconSize='14px')

  q-separator.q-mt-lg.q-mb-lg
  km-section(:title='m.section_headers()', :subTitle='m.subtitle_useHeaders()')
    km-notification-text(
      :notification='m.hint_noSensitiveData()'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in headers', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_key() }}
        km-input(:label='m.common_key()', :model-value='key', @update:model-value='updateHeader(key, $event, value)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_value() }}
        km-input(:label='m.common_value()', :model-value='value', @update:model-value='updateHeader(key, key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeHeader(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(:label='m.common_addHeaderRecord()', @click='addHeader', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(:title='m.section_secrets()', :subTitle='m.subtitle_useSecretsMcp()')
    km-secrets(v-model:secrets='secrets', :original-secrets='originalMcpSecrets', :remount-value='remountValue')
</template>
<script setup>
import { computed } from 'vue'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { m } from '@/paraglide/messages'

const { notifySuccess, notifyError } = useNotify()
const { draft, data, updateField } = useEntityDetail('mcp_servers')
const appStore = useAppStore()

const server = computed(() => draft.value)

const headers = computed({
  get() {
    return draft.value?.headers || new Map()
  },
  set(value) {
    updateField('headers', value)
  },
})

const originalMcpSecrets = computed(() => {
  const secrets = data.value?.secrets_encrypted
  if (!secrets) return []
  return Object.keys(secrets)
})
const remountValue = computed(() => draft.value?.updated_at)
const secrets = computed({
  get() {
    return draft.value?.secrets_encrypted
  },
  set(value) {
    updateField('secrets_encrypted', value)
  },
})

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
  try {
    const response = await fetchData({
      method: 'POST',
      service: `mcp_servers/${server.value.id}/test`,
      credentials: 'include',
      body: JSON.stringify({ id: server.value.id }),
      endpoint: appStore.config?.mcp_servers?.endpoint,
      headers: { 'Content-Type': 'application/json' },
    })
    if (response.error) throw response
    notifySuccess(m.mcp_connectionTestSuccess())
  } catch (error) {
    notifyError(m.mcp_connectionTestError())
  }
}
</script>
