<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='onCancel', @hide='onCancel')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style.q-pb-none
      .row
        .col
          .km-heading-7 Register OAuth client
        .col-auto
          q-btn(icon='close', flat, dense, @click='onCancel')
    q-card-section.card-section-style.q-mb-md
      form(@submit.prevent='create')
        km-notification-text.q-mb-lg(
          notification='Register an MCP/OAuth client. The client_id is the identifier the user will paste into the connector. Redirect URIs must match exactly what the client sends; loopback http://127.0.0.1 / http://localhost are wildcarded across ports.'
        )

        .km-field.text-secondary-text.q-pl-8.q-mb-xs Display name
        km-input.q-mb-md(:model-value='name', @input='name = $event', placeholder='Claude', autofocus)

        .km-field.text-secondary-text.q-pl-8.q-mb-xs Client ID
        km-input.q-mb-md(:model-value='clientId', @input='clientId = $event', placeholder='claude')

        .km-field.text-secondary-text.q-pl-8.q-mb-xs Public client (PKCE only — recommended)
        q-toggle.q-mb-md(:model-value='isPublic', @update:model-value='isPublic = $event', label='Public client')

        .km-field.text-secondary-text.q-pl-8.q-mb-xs(v-if='!isPublic') Client secret
        km-input.q-mb-md(v-if='!isPublic', :model-value='clientSecret', @input='clientSecret = $event', type='password', placeholder='Will be encrypted at rest')

        .km-field.text-secondary-text.q-pl-8.q-mb-xs Redirect URIs (one per line)
        q-input.q-mb-md(:model-value='redirectUrisText', @update:model-value='redirectUrisText = $event', type='textarea', autogrow, outlined, placeholder='https://claude.ai/api/mcp/auth_callback\nhttps://oauth.pstmn.io/v1/callback')

        .row.q-mt-lg
          .col-auto
            km-btn(flat, label='Cancel', color='primary', @click='onCancel')
          .col
          .col-auto.center-flex-y.q-mr-sm
            q-spinner(v-if='loading', color='primary', size='20px')
          .col-auto
            km-btn(label='Register', @click='create', :disable='loading || !canSubmit')
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { notify } from '@shared/utils/notify'

const props = defineProps<{ showNewDialog: boolean }>()
const emit = defineEmits(['cancel'])

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
  emit('cancel')
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
  emit('cancel')
}
</script>
