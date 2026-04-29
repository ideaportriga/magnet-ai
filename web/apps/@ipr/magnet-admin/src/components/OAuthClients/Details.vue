<template lang="pug">
q-dialog(:model-value='!!client', @hide='onClose')
  q-card.card-style(style='min-width: 720px', v-if='client')
    q-card-section.card-section-style.q-pb-none
      .row.items-center
        .col
          .km-heading-7 OAuth client details
        .col-auto
          q-btn(icon='close', flat, dense, @click='onClose')
    q-card-section.card-section-style
      .km-field.text-secondary-text.q-mb-xs Display name
      .km-description.q-mb-md {{ client.name || '-' }}

      .km-field.text-secondary-text.q-mb-xs Client ID
      .km-description.q-mb-md
        km-chip-copy(:label='client.client_id || "-"')

      .row.q-col-gutter-md.q-mb-md
        .col-6
          .km-field.text-secondary-text.q-mb-xs Public client (PKCE only)
          .km-description {{ client.is_public ? 'Yes' : 'No' }}
        .col-6
          .km-field.text-secondary-text.q-mb-xs Enabled
          .km-description {{ client.enabled ? 'Yes' : 'No' }}

      .row.q-col-gutter-md.q-mb-md(v-if='!client.is_public')
        .col-12
          .km-field.text-secondary-text.q-mb-xs Client secret
          .km-description {{ client.client_secret_set ? 'Set (encrypted at rest)' : 'Not set' }}

      .km-field.text-secondary-text.q-mb-xs Redirect URIs
      .km-description.q-mb-md(v-if='client.redirect_uris && client.redirect_uris.length')
        div(v-for='uri in client.redirect_uris', :key='uri') {{ uri }}
      .km-description.q-mb-md(v-else) -

      .row.q-col-gutter-md
        .col-6
          .km-field.text-secondary-text.q-mb-xs Created via
          .km-description {{ client.created_via || '-' }}
        .col-6
          .km-field.text-secondary-text.q-mb-xs Created
          .km-description {{ formatDate(client.created_at) }}

      .row.q-mt-lg
        .col-auto
          km-btn(flat, color='negative', label='Delete', icon='fas fa-trash', @click='askDelete', :disable='deleting')
        .col
        .col-auto.center-flex-y.q-mr-sm
          q-spinner(v-if='deleting', color='primary', size='20px')
        .col-auto
          km-btn(label='Close', @click='onClose')

  km-popup-confirm(
    :visible='showConfirmDelete',
    confirmButtonLabel='Ok, delete',
    cancelButtonLabel='Cancel',
    notificationIcon='fas fa-triangle-exclamation',
    @confirm='confirmDelete',
    @cancel='showConfirmDelete = false'
  )
    .row.item-center.justify-center.km-heading-7.q-mb-md You are about to delete an OAuth client
    .row.text-center.justify-center Any application using this client_id will be unable to complete the OAuth flow. This action cannot be undone.
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { notify } from '@shared/utils/notify'
import type { OAuthClient } from '@/types'

const props = defineProps<{ client: OAuthClient | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const queries = useEntityQueries()
const removeClient = useSafeMutation(queries.oauth_clients.useRemove(), {
  defaultErrorMessage: 'Error deleting OAuth client',
})

const showConfirmDelete = ref(false)
const deleting = ref(false)

const askDelete = () => { showConfirmDelete.value = true }

const confirmDelete = async () => {
  if (!props.client?.id) return
  showConfirmDelete.value = false
  deleting.value = true
  const { success } = await removeClient.run(props.client.id)
  deleting.value = false
  if (!success) return
  notify.success?.('OAuth client deleted')
  emit('close')
}

const onClose = () => { emit('close') }

function formatDate(date?: string) {
  if (!date) return '-'
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}
</script>
