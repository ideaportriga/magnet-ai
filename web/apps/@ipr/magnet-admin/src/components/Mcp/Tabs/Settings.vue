<template>
  <div class="full-width">
    <km-section :title="m.section_connectionSettings()" :sub-title="m.subtitle_endpointUrlTransport()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_url() }}</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-input class="full-width" :model-value="server.url" readonly />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">{{ m.label_transport() }}</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-radio class="my-sm" :model-value="server.transport" dense label="streamable-http" val="streamable-http" size="xs" disabled disable />
        <km-radio class="my-sm" :model-value="server.transport" dense label="sse" val="sse" size="xs" disabled disable />
      </div>
      <div class="cluster mt-lg">
        <km-btn :label="m.mcpServers_testConnection()" size="sm" icon="swap" flat icon-size="14px" @click="testConnection" />
      </div>
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_headers()" :sub-title="m.subtitle_useHeaders()">
      <km-notification-text :notification="m.hint_noSensitiveData()" />
      <km-key-value-editor v-model="headersObject" :add-label="m.common_addHeaderRecord()" :readonly="mcpReadonly" />
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_secrets()" :sub-title="m.subtitle_useSecretsMcp()">
      <km-secrets v-model:secrets="secrets" :original-secrets="originalMcpSecrets" :remount-value="remountValue" :readonly="mcpReadonly" />
    </km-section>
  </div>
</template>
<script setup>
import { computed, inject } from 'vue'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { m } from '@/paraglide/messages'

const { notifySuccess, notifyError } = useNotify()
const { draft, data, updateField } = useEntityDetail('mcp_servers')
const appStore = useAppStore()
const mcpReadonlyRef = inject('mcpReadonly', null)
const mcpReadonly = computed(() => Boolean(mcpReadonlyRef?.value))

const server = computed(() => draft.value)

/* MCP servers persist `headers` as a Map; the editor speaks plain objects.
 * Adapt both directions in a single computed. */
const headersObject = computed({
  get() {
    const raw = draft.value?.headers
    if (!raw) return {}
    if (raw instanceof Map) return Object.fromEntries(raw)
    return raw
  },
  set(value) {
    if (mcpReadonly.value) return
    updateField('headers', new Map(Object.entries(value || {})))
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
    if (mcpReadonly.value) return
    updateField('secrets_encrypted', value)
  },
})

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
