<template lang="pug">
.q-gutter-md

  //- ── Toolbar ────────────────────────────────────────────────────────
  .row.items-center.q-mb-sm
    .col
      km-input(:placeholder='m.common_search()', iconBefore='search', v-model='searchString', clearable, style='max-width: 320px')
    .col-auto
      km-btn(:label='m.common_newProvider()', icon='add', @click='openCreate')

  //- ── Table ──────────────────────────────────────────────────────────
  q-table(
    :rows='visibleRows',
    :columns='columns',
    row-key='id',
    flat,
    dense,
    :loading='loading',
    hide-pagination,
    :rows-per-page-options='[0]'
  )
    template(#body-cell-system_name='props')
      q-td(:props='props')
        .row.items-center.q-gap-4.no-wrap
          span.text-mono.km-description {{ props.row.system_name }}
          q-btn(flat, dense, round, size='xs', icon='content_copy', @click.stop='copy(props.row.system_name)')
            q-tooltip Copy system name

    template(#body-cell-webhook='props')
      q-td(:props='props')
        .row.items-center.q-gap-4.no-wrap(v-if='props.row.system_name')
          span.text-mono.km-description.text-grey-7(style='font-size: 11px') {{ webhookUrl(props.row.system_name) }}
          q-btn(flat, dense, round, size='xs', icon='content_copy', @click.stop='copy(webhookUrl(props.row.system_name))')
            q-tooltip Copy webhook URL
        span.text-grey-4(v-else) —

    template(#body-cell-oauth='props')
      q-td(:props='props')
        span {{ props.row.connection_config?.auth_handler_id || '—' }}

    template(#body-cell-actions='props')
      q-td(:props='props', auto-width)
        .row.items-center.no-wrap
          km-btn(flat, dense, icon='edit', size='sm', @click.stop='openEdit(props.row)')
            q-tooltip Edit
          km-btn(flat, dense, icon='delete', size='sm', color='negative', @click.stop='confirmDelete(props.row)')
            q-tooltip Delete

  //- ── Create / Edit dialog ───────────────────────────────────────────
  km-popup-confirm(
    :visible='showDialog',
    :title='editingProvider ? "Edit Provider" : "New Teams Note Taker Provider"',
    :confirmButtonLabel='m.common_save()',
    :cancelButtonLabel='m.common_cancel()',
    notification='Credentials are encrypted at rest.',
    @confirm='saveProvider',
    @cancel='closeDialog'
  )
    .column.q-gap-16
      .col
        .km-field.text-secondary-text.q-pb-xs Provider Name
        km-input(
          v-if='showDialog',
          height='30px',
          placeholder='My Teams Bot',
          v-model='form.name',
          :rules='[required()]',
          @input='onNameInput'
        )
      .col
        .km-field.text-secondary-text.q-pb-xs System Name
        km-input(
          height='30px',
          placeholder='MY_TEAMS_BOT',
          v-model='form.system_name',
          :rules='[required()]',
          :disable='!!editingProvider'
        )
        .km-description.text-secondary-text.q-pt-2(v-if='!editingProvider') Auto-generated from name. Used in the webhook URL.
      .col
        .km-field.text-secondary-text.q-pb-xs Client ID (App ID)
        km-input(
          v-if='showDialog',
          height='30px',
          placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
          v-model='form.client_id'
        )
      .col
        .km-field.text-secondary-text.q-pb-xs Client Secret
        km-input(
          v-if='showDialog',
          height='30px',
          type='password',
          :placeholder='editingProvider ? "Leave blank to keep existing secret" : "Azure Bot client secret"',
          v-model='form.client_secret'
        )
      .col
        .km-field.text-secondary-text.q-pb-xs Tenant ID
        km-input(
          v-if='showDialog',
          height='30px',
          placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
          v-model='form.tenant_id'
        )
      .col
        .km-field.text-secondary-text.q-pb-xs OAuth Connection Name
        km-input(
          v-if='showDialog',
          height='30px',
          placeholder='e.g. Recordings',
          v-model='form.auth_handler_id'
        )
        .km-description.text-secondary-text.q-pt-2 Name of the OAuth Connection in Azure Bot Service settings.

  //- ── Delete confirmation ────────────────────────────────────────────
  km-popup-confirm(
    :visible='showDeleteConfirm',
    title='Delete Provider',
    :confirmButtonLabel='m.common_delete()',
    :cancelButtonLabel='m.common_cancel()',
    confirm-button-color='negative',
    @confirm='deleteProvider',
    @cancel='showDeleteConfirm = false'
  )
    .km-description
      | Are you sure you want to delete provider
      strong.q-mx-xs {{ deletingProvider?.name }}
      | ? This cannot be undone.
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'

const appStore = useAppStore()
const { notifySuccess, notifyError, notifyCopied } = useNotify()
const queries = useEntityQueries()

const { data: providerListData } = queries.provider.useList()
const { mutateAsync: createProviderMutation } = queries.provider.useCreate()
const { mutateAsync: updateProviderMutation } = queries.provider.useUpdate()
const { mutateAsync: deleteProviderMutation } = queries.provider.useRemove()

const searchString = ref('')
const loading = ref(false)
const showDialog = ref(false)
const showDeleteConfirm = ref(false)
const editingProvider = ref<any>(null)
const deletingProvider = ref<any>(null)

const form = reactive({
  name: '',
  system_name: '',
  client_id: '',
  client_secret: '',
  tenant_id: '',
  auth_handler_id: '',
})

// ── Providers data ───────────────────────────────────────────────────
const allProviders = computed(() => providerListData.value?.items || [])
const providers = computed(() =>
  allProviders.value.filter((p: any) => p.type === 'teams_note_taker')
)

const visibleRows = computed(() => {
  const q = searchString.value.toLowerCase()
  if (!q) return providers.value
  return providers.value.filter(
    (p: any) =>
      p.name?.toLowerCase().includes(q) ||
      p.system_name?.toLowerCase().includes(q)
  )
})

// ── Webhook URL ──────────────────────────────────────────────────────
const apiBase = computed(() => {
  const adminUrl: string = appStore.config?.api?.aiBridge?.urlAdmin || ''
  try {
    return new URL(adminUrl).origin
  } catch {
    return ''
  }
})

const webhookUrl = (systemName: string) => {
  const base = apiBase.value || '<your-domain>'
  return `${base}/api/user/agents/teams/note-taker/${systemName}/messages`
}

// ── Table columns ────────────────────────────────────────────────────
const columns = [
  { name: 'name',        label: 'Name',            field: 'name',        align: 'left' as const, sortable: true },
  { name: 'system_name', label: 'System Name',      field: 'system_name', align: 'left' as const, sortable: true },
  { name: 'oauth',       label: 'OAuth Connection', field: 'connection_config', align: 'left' as const },
  { name: 'webhook',     label: 'Webhook URL',      field: 'system_name', align: 'left' as const },
  { name: 'actions',     label: '',                 field: 'id',          align: 'right' as const },
]

// ── Name → system_name auto-fill ─────────────────────────────────────
const onNameInput = (val: string) => {
  if (!editingProvider.value) {
    form.system_name = toUpperCaseWithUnderscores(val)
  }
}

// ── Create / Edit ─────────────────────────────────────────────────────
const openCreate = () => {
  editingProvider.value = null
  Object.assign(form, { name: '', system_name: '', client_id: '', client_secret: '', tenant_id: '', auth_handler_id: '' })
  showDialog.value = true
}

const openEdit = (provider: any) => {
  editingProvider.value = provider
  const secrets = provider.secrets_encrypted || {}
  const conn = provider.connection_config || {}
  Object.assign(form, {
    name: provider.name || '',
    system_name: provider.system_name || '',
    client_id: secrets.client_id || '',
    client_secret: '',
    tenant_id: secrets.tenant_id || '',
    auth_handler_id: conn.auth_handler_id || '',
  })
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  editingProvider.value = null
}

const saveProvider = async () => {
  if (!form.name.trim() || !form.system_name.trim()) return
  loading.value = true
  try {
    const secrets: any = {
      client_id: form.client_id,
      tenant_id: form.tenant_id,
    }
    if (form.client_secret) secrets.client_secret = form.client_secret

    if (editingProvider.value) {
      await updateProviderMutation({
        id: editingProvider.value.id,
        data: {
          name: form.name,
          secrets_encrypted: secrets,
          connection_config: { auth_handler_id: form.auth_handler_id || '' },
        } as any,
      })
      notifySuccess('Provider updated')
    } else {
      await createProviderMutation({
        name: form.name,
        system_name: form.system_name,
        type: 'teams_note_taker',
        secrets_encrypted: secrets,
        connection_config: { auth_handler_id: form.auth_handler_id || '' },
      } as any)
      notifySuccess('Provider created')
    }
    closeDialog()
  } catch (err: any) {
    notifyError(err?.message || 'Failed to save provider')
  } finally {
    loading.value = false
  }
}

// ── Delete ────────────────────────────────────────────────────────────
const confirmDelete = (provider: any) => {
  deletingProvider.value = provider
  showDeleteConfirm.value = true
}

const deleteProvider = async () => {
  if (!deletingProvider.value) return
  loading.value = true
  try {
    await deleteProviderMutation(deletingProvider.value.id)
    notifySuccess('Provider deleted')
  } catch (err: any) {
    notifyError(err?.message || 'Failed to delete provider')
  } finally {
    loading.value = false
    showDeleteConfirm.value = false
    deletingProvider.value = null
  }
}

// ── Clipboard ─────────────────────────────────────────────────────────
const copy = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    notifyCopied('Copied')
  })
}
</script>
