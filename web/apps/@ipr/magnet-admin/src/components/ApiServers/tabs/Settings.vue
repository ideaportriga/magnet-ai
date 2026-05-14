<template>
  <div class="full-width">
    <km-section :title="m.section_connectionSettings()" :sub-title="m.subtitle_endpointUrl()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_url() }}</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-input class="full-width" :model-value="server?.url" readonly />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm pt-lg">{{ m.apiServers_verifySsl() }}</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-toggle v-model="verifySsl">
          <div class="text-secondary-text">{{ verifySsl ? 'Yes' : 'No' }}</div>
        </km-toggle>
      </div>
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_customHeaders()" :sub-title="m.apiServers_customHeadersNotification()">
      <km-notification-text notification="Define custom headers that will be sent with each API request. Use placeholders in curly braces to reference secrets." />
      <km-key-value-editor v-model="customHeadersObject" :key-label="m.common_headerName()" :value-label="m.common_headerValue()" :add-label="m.apiServers_addCustomHeader()" />
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_securitySchema()" :sub-title="m.apiServers_securitySchemaSubtitle()">
      <km-notification-text>
        <div>
          Supported types: apiKey, basic, oauth2. Check&nbsp;<a class="text-primary" href="https://swagger.io/docs/specification/v3_0/authentication/" target="_blank">OpenAPI documentation</a>
          for information.
        </div>
      </km-notification-text>
      <div class="km-field text-secondary-text pb-xs pl-sm pt-lg">Security schema</div>
      <div class="cluster" data-gap="lg" data-wrap="no">
        <km-input v-model="serverSecurityScheme" class="full-width" type="textarea" rows="4" />
      </div>
      <div v-if="parsingError" class="km-small-chip p-xs pl-sm text-error-text">Invalid JSON format. Please check your input and ensure it follows valid JSON syntax.</div>
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_securityValues()" :sub-title="m.apiServers_securityValuesSubtitle()">
      <km-notification-text notification="Do not expose sensitive data in this section. Instead, use placeholders and provide actual values in the Secrets section. Use curly braces to insert placeholders." />
      <km-key-value-editor v-model="securityValuesObject" :add-label="m.apiServers_addSecurityValue()" />
    </km-section>
    <km-separator class="mt-lg mb-lg" />
    <km-section :title="m.section_secrets()" :sub-title="m.apiServers_secretsSubtitle()">
      <km-secrets v-model:secrets="secrets" :original-secrets="originalApiSecrets" :remount-value="remountValue" />
    </km-section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'

const { draft, data, updateField } = useEntityDetail('api_servers')

const server = computed(() => draft.value)
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
      updateField('security_scheme', parsedNewValue)
      parsingError.value = false
    } catch (e) {
      updateField('security_scheme', newValue)
      parsingError.value = true
    }
  },
})

const verifySsl = computed({
  get: () => server.value?.verify_ssl,
  set: (value) => {
    updateField('verify_ssl', value)
  },
})

const originalApiSecrets = computed(() => {
  const secrets = data.value?.secrets_encrypted
  if (!secrets) return []
  if (secrets instanceof Map) {
    return Array.from(secrets.keys())
  }
  return Object.keys(secrets)
})
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
    updateField('secrets_encrypted', value)
  },
})

/* `custom_headers` and `security_values` are persisted as Maps elsewhere in
 * the app, but `<km-key-value-editor>` works with plain objects. Adapt both
 * directions in a single computed so the editor's `v-model` can drive
 * `updateField` directly without bespoke add/remove/update helpers. */
const customHeadersObject = computed({
  get() {
    const raw = server.value?.custom_headers
    if (!raw) return {}
    if (raw instanceof Map) return Object.fromEntries(raw)
    return raw
  },
  set(value) {
    updateField('custom_headers', new Map(Object.entries(value || {})))
  },
})

const securityValuesObject = computed({
  get() {
    const raw = server.value?.security_values
    if (!raw) return {}
    if (raw instanceof Map) return Object.fromEntries(raw)
    return raw
  },
  set(value) {
    updateField('security_values', value || {})
  },
})
</script>
