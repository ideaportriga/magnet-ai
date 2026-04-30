<template>
  <div class="full-width">
    <km-section title="General info" sub-title="General Model Provider settings">
      <div class="km-field text-secondary-text pb-xs pl-sm">Type</div>
      <div class="cluster full-width" data-gap="lg" data-wrap="no">
        <!-- Type is fixed for the lifetime of a provider (changing it would
             invalidate every model + secret), so this is purely informational.
             Render as a readonly text field showing the human label rather
             than an unmappable empty select. -->
        <km-input class="full-width" :model-value="formatProviderType(provider?.type)" readonly />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Endpoint</div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <div class="flex-1">
          <div class="cluster" data-gap="sm" data-wrap="no" style="position: relative">
            <km-input class="full-width" :model-value="endpointValue" :readonly="!isEditingEndpoint" :placeholder="m.placeholder_exampleApiEndpoint()" @update:model-value="tempEndpoint = $event" />
            <div class="controls full-height cluster">
              <km-btn v-if="!isEditingEndpoint" icon="edit" flat icon-size="12px" size="xs" @click="startEditingEndpoint" />
              <km-btn v-if="isEditingEndpoint" icon="close" flat icon-size="12px" size="xs" @click="cancelEditingEndpoint" />
              <km-btn v-if="isEditingEndpoint" icon="check" flat icon-size="12px" size="xs" tone="brand" @click="saveEndpoint" />
            </div>
          </div>
        </div>
      </div>
      <div v-if="!isEditingEndpoint" class="km-description text-secondary-text pb-xs pl-sm">Click edit to change endpoint. Warning: this will clear all secrets.</div>
      <div v-if="isEditingEndpoint" class="km-description text-negative pb-xs pl-sm">Changing endpoint will permanently delete all secrets!</div>
    </km-section>
    <km-popup-confirm :visible="showEndpointWarning" title="Change Endpoint" confirm-button-label="Yes, Change Endpoint" :cancel-button-label="m.common_cancel()" notification="Changing the endpoint will permanently delete all encrypted secrets. You will need to re-enter all credentials after this change." @confirm="confirmEndpointChange" @cancel="cancelEndpointChange">
      <div class="text-body1">Are you sure you want to change the endpoint?</div>
      <div class="text-body2 mt-md">Current endpoint: {{ provider.endpoint || 'Not set' }}</div>
      <div class="text-body2">New endpoint: {{ tempEndpoint }}</div>
    </km-popup-confirm>
    <km-separator class="mt-lg mb-lg" />
    <km-section title="Connection" sub-title="Connection parameters like endpoints and headers">
      <key-value-editor :model-value="provider?.connection_config || {}" @update:model-value="updateField('connection_config', $event)">
        <template #actions>
          <km-btn flat :label="testingConnection ? &quot;Testing...&quot; : &quot;Test Connection&quot;" :loading="testingConnection" icon="plug" tone="brand" size="sm" @click="testProviderConnection" />
        </template>
      </key-value-editor>
    </km-section>
    <km-dialog v-model="showTestDialog">
      <km-card style="min-inline-size: 580px; max-inline-size: 720px">
        <div class="km-card-section cluster" data-justify="between">
          <div class="km-heading-7">Test Result</div>
          <div class="km-space" />
          <km-btn icon="close" flat round dense @click="showTestDialog = false" />
        </div>
        <div class="km-card-section">
          <div class="cluster mb-md" data-gap="md">
            <km-glyph :name="testResult?.success ? &quot;check&quot; : &quot;error&quot;" :tone="testResult?.success ? &quot;success&quot; : &quot;danger&quot;" size="32px" />
            <div class="text-h6" :class="testResult?.success ? &quot;text-positive&quot; : &quot;text-negative&quot;">{{ testResult?.success ? 'Success' : 'Failed' }}</div>
          </div>
          <div class="km-description text-secondary-text mb-sm">{{ testResult?.message }}</div>
          <div v-if="testResult?.error" class="p-sm bg-negative-light rounded-borders mt-sm">
            <div class="km-field text-negative mb-xs">Error Details</div>
            <div class="text-body2 text-negative">{{ testResult?.error }}</div>
          </div>
          <div v-if="testResult?.litellm_model_string || testResult?.effective_endpoint || testResult?.computed_url || testResult?.via_router != null" class="mt-md p-sm bg-grey-2 rounded-borders">
            <div class="km-field text-secondary-text mb-sm">Connection Details</div>
            <div class="gap-y-xs">
              <div v-if="testResult?.litellm_model_string" class="cluster" data-align="start">
                <div class="provider-settings__detail-label flex-none text-caption text-grey-7">Model string</div>
                <div class="provider-settings__detail-value flex-1 text-caption text-mono">{{ testResult.litellm_model_string }}</div>
              </div>
              <div v-if="testResult?.effective_endpoint" class="cluster" data-align="start">
                <div class="provider-settings__detail-label flex-none text-caption text-grey-7">Endpoint</div>
                <div class="provider-settings__detail-value flex-1 text-caption text-mono" style="word-break: break-all; white-space: normal">{{ testResult.effective_endpoint }}</div>
              </div>
              <div v-if="testResult?.via_router != null" class="cluster" data-align="start">
                <div class="provider-settings__detail-label flex-none text-caption text-grey-7">Via Router</div>
                <div class="provider-settings__detail-value flex-1">
                  <km-badge class="km-tiny" :tone="testResult.via_router ? &quot;success&quot; : &quot;neutral&quot;" :label="testResult.via_router ? &quot;Yes&quot; : &quot;No (direct call)&quot;" />
                </div>
              </div>
              <div v-if="testResult?.computed_url" class="cluster" data-align="start">
                <div class="provider-settings__detail-label flex-none text-caption text-grey-7">Request URL</div>
                <div class="provider-settings__detail-value flex-1 text-caption text-mono" style="word-break: break-all; white-space: normal">{{ testResult.computed_url }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="km-card-actions" align="right">
          <km-btn flat :label="m.common_close()" tone="brand" @click="showTestDialog = false" />
        </div>
      </km-card>
    </km-dialog>
    <km-separator class="mt-lg mb-lg" />
    <km-section title="Secrets" sub-title="Use to store sensitive values such as API keys or tokens.">
      <div v-if="recommendedSecretKeys.length" class="cluster mb-md" data-gap="sm" data-justify="between">
        <div class="km-description text-secondary-text">Recommended for {{ formatProviderType(provider.type) }}:</div>
        <div class="km-space" />
        <km-btn flat :label="m.common_prePopulateKeys()" size="sm" icon="o_auto_fix_high" tone="brand" :disable="allRecommendedSecretsExist" @click="prefillRecommendedSecrets" />
      </div>
      <div v-if="recommendedSecretKeys.length" class="cluster mb-md" data-gap="xs">
        <km-chip v-for="rec in recommendedSecretKeys" :key="rec.key" tone="brand" size="sm" dense>
          <km-glyph class="mr-xs" :name="secretExists(rec.key) ? &quot;check&quot; : &quot;o_key&quot;" size="14px" :tone="secretExists(rec.key) ? &quot;success&quot; : &quot;brand&quot;" />{{ rec.label }}
        </km-chip>
      </div>
      <km-secrets v-model:secrets="secrets" :original-secrets="originalProviderSecrets" :remount-value="remountValue" />
    </km-section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { onBeforeRouteLeave } from 'vue-router'
import { providerSecretKeys, providerConnectionConfigKeys, formatProviderType } from '../../config/model_providers/providerTypes'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useNotify } from '@/composables/useNotify'

const { draft, data, updateField, updateFields, save } = useEntityDetail('provider')
const { notifySuccess, notifyError, notifyWarning } = useNotify()
const queries = useEntityQueries()
const { mutateAsync: testProvider } = queries.provider.useTest()

const provider = computed(() => draft.value)

const isEditingEndpoint = ref(false)
const tempEndpoint = ref('')
const showEndpointWarning = ref(false)

// Test connection state
const testingConnection = ref(false)
const testResult = ref(null)
const showTestDialog = ref(false)

const pendingNavigation = ref(null)

// Prevent navigation when editing endpoint
onBeforeRouteLeave((to, from, next) => {
  if (isEditingEndpoint.value && tempEndpoint.value !== provider.value?.endpoint) {
    pendingNavigation.value = next
    showEndpointWarning.value = true
  } else {
    // If editing but no changes, just cancel editing and continue
    if (isEditingEndpoint.value) {
      cancelEditingEndpoint()
    }
    next()
  }
})

const endpointValue = computed(() => {
  if (isEditingEndpoint.value) {
    return tempEndpoint.value
  }
  return provider.value?.endpoint || ''
})

const startEditingEndpoint = () => {
  tempEndpoint.value = provider.value?.endpoint || ''
  isEditingEndpoint.value = true
}

const cancelEditingEndpoint = () => {
  isEditingEndpoint.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
}

const saveEndpoint = () => {
  if (tempEndpoint.value !== provider.value?.endpoint) {
    showEndpointWarning.value = true
  } else {
    isEditingEndpoint.value = false
  }
}

const confirmEndpointChange = async () => {
  // Update endpoint and clear secrets in draft
  updateFields({
    endpoint: tempEndpoint.value,
    secrets_encrypted: {},
  })

  try {
    // Save provider via composable
    const { success, error } = await save()
    if (success) {
      notifySuccess('Endpoint updated successfully.')
    } else {
      throw error || new Error('Failed to save endpoint changes.')
    }
  } catch (error) {
    notifyError('Failed to save endpoint changes.')
  }

  showEndpointWarning.value = false
  isEditingEndpoint.value = false
  tempEndpoint.value = ''

  // Continue navigation if it was blocked
  if (pendingNavigation.value) {
    pendingNavigation.value()
    pendingNavigation.value = null
  }
}

const cancelEndpointChange = () => {
  showEndpointWarning.value = false
  tempEndpoint.value = provider.value?.endpoint || ''

  // Cancel navigation if it was blocked
  if (pendingNavigation.value) {
    pendingNavigation.value(false)
    pendingNavigation.value = null
  }
}

const recommendedSecretKeys = computed(() => {
  const type = provider.value?.type
  return providerSecretKeys[type] || []
})

const secretExists = (key) => {
  const s = provider.value?.secrets_encrypted || {}
  return key in s
}

const allRecommendedSecretsExist = computed(() => {
  return recommendedSecretKeys.value.length > 0 && recommendedSecretKeys.value.every(r => secretExists(r.key))
})

const prefillRecommendedSecrets = () => {
  const current = { ...(provider.value?.secrets_encrypted || {}) }
  let changed = false
  for (const rec of recommendedSecretKeys.value) {
    if (!(rec.key in current)) {
      current[rec.key] = ''
      changed = true
    }
  }
  if (changed) {
    updateField('secrets_encrypted', current)
  }
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
    return encryptedSecrets
  },
  set(value) {
    updateField('secrets_encrypted', value)
  },
})

// Test provider connection
const testProviderConnection = async () => {
  if (!provider.value?.id) {
    notifyWarning('Please save the provider first before testing.')
    return
  }

  testingConnection.value = true
  testResult.value = null

  try {
    const result = await testProvider({ id: provider.value.id })
    testResult.value = result
    showTestDialog.value = true
  } catch (error) {
    testResult.value = {
      success: false,
      message: 'Failed to test connection',
      error: error?.text || error?.message || 'Unknown error',
    }
    showTestDialog.value = true
  } finally {
    testingConnection.value = false
  }
}
</script>

<style scoped>
.controls {
  position: absolute;
  inset-inline-end: 5px;
  inset-block-start: 0;
}

.provider-settings__detail-label {
  flex: 0 0 25%;
  max-inline-size: 25%;
}

.provider-settings__detail-value {
  min-inline-size: 0;
}
</style>
