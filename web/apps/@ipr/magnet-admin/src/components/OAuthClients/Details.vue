<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout
    v-if="!loading"
    :name="name"
    :created-at="created_at"
    :updated-at="modified_at"
    :created-by="created_by"
    :updated-by="updated_by"
    show-record-info
    :show-description="false"
    @update:name="name = $event"
  >
    <template #header-actions>
      <km-btn
        v-if="isDirty || newClientSecret"
        data-test="revert-btn"
        label="Revert"
        icon="undo"
        icon-size="16px"
        flat
        @click="handleRevert"
      />
      <km-btn
        data-test="save-btn"
        label="Save"
        flat
        icon="save"
        icon-size="16px"
        :loading="saving"
        :disable="saving || (!isDirty && !newClientSecret)"
        @click="handleSave"
      />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">Delete</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm
        :visible="showDeleteDialog"
        confirm-button-label="Delete OAuth client"
        cancel-button-label="Cancel"
        notification-icon="warning"
        @confirm="confirmDelete"
        @cancel="showDeleteDialog = false"
      >
        <div class="cluster km-heading-7" data-justify="center">You are about to delete an OAuth client</div>
        <div class="cluster text-center" data-justify="center">Any application using this client_id will be unable to complete the OAuth flow. This action cannot be undone.</div>
      </km-popup-confirm>
    </template>

    <template #content>
      <div class="stack overflow-auto" data-gap="16" style="min-block-size: 0; padding-block: 16px">
        <div class="stack" data-gap="4">
          <div class="km-description text-secondary-text">Client ID</div>
          <km-chip-copy :label="draft?.client_id || '-'" />
        </div>

        <div class="cluster" data-gap="sm" data-align="center">
          <km-switch data-test="enabled-toggle" :model-value="enabled" @update:model-value="enabled = $event" />
          <div class="km-heading-3">Enabled</div>
        </div>

        <km-checkbox
          data-test="public-toggle"
          :model-value="isPublic"
          label="Public client (PKCE only — recommended)"
          @update:model-value="isPublic = $event"
        />

        <div v-if="!isPublic" class="stack" data-gap="4">
          <div class="km-description text-secondary-text">New client secret</div>
          <div class="km-description text-secondary-text" style="font-size: var(--ds-font-size-body-sm)">
            {{ draft?.client_secret_set ? 'A secret is set. Enter a new value to replace it, or leave empty to keep.' : 'No secret set. Enter a value to set one.' }}
          </div>
          <km-input v-model="newClientSecret" type="password" placeholder="Enter new secret…" />
        </div>

        <div class="stack" data-gap="4">
          <div class="km-description text-secondary-text">Redirect URIs (one per line)</div>
          <km-input v-model="redirectUrisText" type="textarea" autogrow />
        </div>
      </div>
    </template>
  </layouts-details-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useEntityDetail } from '@/composables/useEntityDetail'

const router = useRouter()

const { draft, data: oauthClient, isDirty, isLoading, updateField, save, remove, revert } = useEntityDetail('oauth_clients')

const loading = computed(() => isLoading.value || !oauthClient.value)

const saving = ref(false)
const showDeleteDialog = ref(false)
const newClientSecret = ref('')

const name = computed({
  get: () => draft.value?.name ?? '',
  set: (value) => updateField('name', value),
})

const enabled = computed({
  get: () => draft.value?.enabled ?? true,
  set: (value) => updateField('enabled', value),
})

const isPublic = computed({
  get: () => draft.value?.is_public ?? true,
  set: (value) => updateField('is_public', value),
})

const redirectUrisText = computed({
  get: () => (draft.value?.redirect_uris ?? []).join('\n'),
  set: (value: string) => updateField('redirect_uris', value.split('\n').map((s) => s.trim()).filter(Boolean)),
})

const created_at = computed(() => draft.value?.created_at ? formatDate(draft.value.created_at) : '')
const modified_at = computed(() => draft.value?.updated_at ? formatDate(draft.value.updated_at) : '')
const created_by = computed(() => draft.value?.created_by || 'Unknown')
const updated_by = computed(() => draft.value?.updated_by || 'Unknown')

function formatDate(date: string) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function handleSave() {
  saving.value = true
  try {
    if (newClientSecret.value) updateField('client_secret', newClientSecret.value)
    const result = await save()
    if (result.success) {
      newClientSecret.value = ''
      notify.success('Saved successfully')
    } else if (result.error) {
      throw result.error
    }
  } catch (error: any) {
    notify.error(error.message || 'Failed to save')
  } finally {
    saving.value = false
  }
}

function handleRevert() {
  revert()
  newClientSecret.value = ''
}

async function confirmDelete() {
  await remove()
  notify.success('OAuth client deleted')
  router.push('/oauth-clients')
}
</script>
