<template>
  <div class="stack" data-gap="md">
    <div class="cluster">
      <div class="flex-1">
        <km-input v-model="searchString" :placeholder="m.common_search()" icon-before="search" clearable style="max-inline-size: 320px" />
      </div>
      <div class="flex-none">
        <km-btn :label="m.common_newProvider()" icon="add" @click="openCreate" />
      </div>
    </div>
    <km-data-table :table="table" row-key="id" :loading="loading" hide-pagination :no-records-label="m.retrieval_noExamplesYet ? m.retrieval_noExamplesYet() : &quot;No records found&quot;">
      <template #cell-system_name="{ row }">
        <div class="cluster" data-gap="xs" data-wrap="no">
          <span class="text-mono km-description">{{ row.system_name }}</span>
          <km-btn flat dense round size="xs" icon="copy" tooltip="Copy system name" @click.stop="copy(row.system_name)" />
        </div>
      </template>
      <template #cell-oauth="{ row }"><span>{{ row.connection_config?.auth_handler_id || '—' }}</span></template>
      <template #cell-webhook="{ row }">
        <div v-if="row.system_name" class="cluster" data-gap="xs" data-wrap="no">
          <span class="text-mono km-description text-grey-7" style="font-size: 11px">{{ webhookUrl(row.system_name) }}</span>
          <km-btn flat dense round size="xs" icon="copy" tooltip="Copy webhook URL" @click.stop="copy(webhookUrl(row.system_name))" />
        </div><span v-else class="text-grey-4">—</span>
      </template>
      <template #cell-actions="{ row }">
        <div class="cluster" data-wrap="no">
          <km-btn flat dense icon="edit" size="sm" tooltip="Edit" @click.stop="openEdit(row)" />
          <km-btn flat dense icon="delete" size="sm" tone="danger" tooltip="Delete" @click.stop="confirmDelete(row)" />
        </div>
      </template>
    </km-data-table>
    <km-popup-confirm :visible="showDialog" :title="editingProvider ? &quot;Edit Provider&quot; : &quot;New Teams Note Taker Provider&quot;" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" notification="Credentials are encrypted at rest." @confirm="saveProvider" @cancel="closeDialog">
      <div class="stack" data-gap="lg">
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">Provider Name</div>
          <km-input v-if="showDialog" v-model="form.name" height="30px" :placeholder="m.noteTaker_myTeamsBot()" :rules="[required()]" @input="onNameInput" />
        </div>
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">System Name</div>
          <km-input v-model="form.system_name" height="30px" :placeholder="m.noteTaker_myTeamsBotSystemName()" :rules="[required()]" :disable="!!editingProvider" />
          <div v-if="!editingProvider" class="km-description text-secondary-text pt-2xs">Auto-generated from name. Used in the webhook URL.</div>
        </div>
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">Client ID (App ID)</div>
          <km-input v-if="showDialog" v-model="form.client_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
        </div>
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">Client Secret</div>
          <km-input v-if="showDialog" v-model="form.client_secret" height="30px" type="password" :placeholder="editingProvider ? m.noteTaker_leaveBlankToKeepSecret() : m.noteTaker_azureBotClientSecret()" />
        </div>
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">Tenant ID</div>
          <km-input v-if="showDialog" v-model="form.tenant_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
        </div>
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs">OAuth Connection Name</div>
          <km-input v-if="showDialog" v-model="form.auth_handler_id" height="30px" :placeholder="m.noteTaker_exampleRecordings()" />
          <div class="km-description text-secondary-text pt-2xs">Name of the OAuth Connection in Azure Bot Service settings.</div>
        </div>
      </div>
    </km-popup-confirm>
    <km-popup-confirm :visible="showDeleteConfirm" title="Delete Provider" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" confirm-button-color="negative" @confirm="deleteProvider" @cancel="showDeleteConfirm = false">
      <div class="km-description">Are you sure you want to delete provider<strong class="mx-xs">{{ deletingProvider?.name }}</strong>? This cannot be undone.</div>
    </km-popup-confirm>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'

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
  allProviders.value.filter((p: any) => p.type === 'teams_note_taker'),
)

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

// ── Table columns (TanStack) ─────────────────────────────────────────
interface ProviderRow {
  id: string
  name?: string
  system_name?: string
  connection_config?: { auth_handler_id?: string } | null
  [k: string]: unknown
}

const columns: ColumnDef<ProviderRow, unknown>[] = [
  { id: 'name', accessorKey: 'name', header: 'Name', enableSorting: true, meta: { align: 'left' } },
  { id: 'system_name', accessorKey: 'system_name', header: 'System Name', enableSorting: true, meta: { align: 'left' } },
  { id: 'oauth', header: 'OAuth Connection', enableSorting: false, meta: { align: 'left' } },
  { id: 'webhook', header: 'Webhook URL', enableSorting: false, meta: { align: 'left' } },
  { id: 'actions', header: '', enableSorting: false, meta: { align: 'right', width: '100px' } },
]

const { table, globalFilter } = useLocalDataTable<ProviderRow>(
  providers as unknown as import('vue').Ref<ProviderRow[]>,
  columns,
  { defaultPageSize: 1000 },
)

// Propagate the search input into TanStack's globalFilter (matches across
// all sortable fields). Keeps the existing search semantic without a
// separate `visibleRows` computed.
watch(searchString, (val) => { globalFilter.value = val }, { immediate: true })

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
