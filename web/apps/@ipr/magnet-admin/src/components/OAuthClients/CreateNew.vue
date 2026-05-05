<template>
  <km-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <km-card style="min-width: 800px">
      <div class="km-card-section">
        <div class="cluster" data-wrap="no">
          <div class="flex-1">
            <div class="km-heading-7">Register OAuth client</div>
          </div>
          <km-btn icon="close" flat round dense @click="onCancel" />
        </div>
      </div>

      <div class="km-card-section">
        <form @submit.prevent="create">
          <p class="text-secondary-text mb-md">
            Register an MCP/OAuth client. The client_id is the identifier the user will paste into the connector.
            Redirect URIs must match exactly what the client sends; loopback http://127.0.0.1 / http://localhost are
            wildcarded across ports.
          </p>
          <div class="stack" data-gap="md">
            <div>
              <div class="km-field text-secondary-text pb-xs pl-sm">Display name</div>
              <km-input v-model="name" placeholder="Claude" autofocus />
            </div>
            <div>
              <div class="km-field text-secondary-text pb-xs pl-sm">Client ID</div>
              <km-input v-model="clientId" placeholder="claude" />
            </div>
            <km-checkbox
              :model-value="isPublic"
              label="Public client (PKCE only — recommended)"
              @update:model-value="isPublic = $event"
            />
            <div v-if="!isPublic">
              <div class="km-field text-secondary-text pb-xs pl-sm">Client secret</div>
              <km-input v-model="clientSecret" type="password" placeholder="Will be encrypted at rest" />
            </div>
            <div>
              <div class="km-field text-secondary-text pb-xs pl-sm">Redirect URIs (one per line)</div>
              <km-input
                v-model="redirectUrisText"
                type="textarea"
                autogrow
                placeholder="https://claude.ai/api/mcp/auth_callback
https://oauth.pstmn.io/v1/callback"
              />
            </div>
          </div>
        </form>
      </div>

      <div class="km-card-actions">
        <km-btn flat label="Cancel" tone="weak" @click="onCancel" />
        <div class="km-space" />
        <km-btn label="Register" :loading="loading" :disable="loading || !canSubmit" @click="create" />
      </div>
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { notify } from '@shared/utils/notify'

defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>()

const queries = useEntityQueries()
const createClient = useSafeMutation(queries.oauth_clients.useCreate(), {
  defaultErrorMessage: 'Error registering OAuth client',
})

const name = ref('')
const clientId = ref('')
const isPublic = ref(true)
const clientSecret = ref('')
const redirectUrisText = ref('')
const loading = ref(false)

const canSubmit = computed(
  () =>
    !!name.value &&
    !!clientId.value &&
    redirectUrisText.value.trim().length > 0 &&
    (isPublic.value || !!clientSecret.value),
)

const create = async () => {
  if (loading.value || !canSubmit.value) return
  loading.value = true
  const redirectUris = redirectUrisText.value
    .split('\n')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  const payload: Record<string, unknown> = {
    name: name.value,
    client_id: clientId.value,
    is_public: isPublic.value,
    redirect_uris: redirectUris,
    enabled: true,
  }
  if (!isPublic.value) payload.client_secret = clientSecret.value
  const { success } = await createClient.run(payload)
  loading.value = false
  if (!success) return
  notify.created?.() ?? notify.success?.('OAuth client registered')
  reset()
  emit('update:modelValue', false)
}

const reset = () => {
  name.value = ''
  clientId.value = ''
  isPublic.value = true
  clientSecret.value = ''
  redirectUrisText.value = ''
}

const onCancel = () => {
  reset()
  emit('update:modelValue', false)
}
</script>
