<template>
  <div>
    <km-section title="Bot Credentials" sub-title="Azure Bot credentials to connect with Note Taker">
      <div class="km-field text-secondary-text pb-xs pl-sm">Azure Bot Provider</div>
      <div class="cluster" data-gap="sm">
        <div class="flex-1">
          <km-select v-model="providerSystemName" :options="noteTakerProviders" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" clearable :disabled="noteTakerReadonly" :placeholder="m.noteTaker_selectTeamsProvider()" />
        </div>
        <div v-if="providerSystemName" class="flex-none cluster" data-gap="xs" data-wrap="no">
          <km-btn v-if="canManageProviders" icon="edit" flat dense tooltip="Edit linked provider credentials" @click="openEditProvider" />
          <km-btn icon="external-link" flat dense tooltip="Open in providers page" @click="navigateToProvider" />
        </div>
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Provider of type "Teams Note Taker" that stores encrypted Azure Bot credentials (client_id, client_secret, tenant_id).</div>
      <div v-if="providerSystemName" class="km-field text-secondary-text pt-md pb-xs pl-sm">Messaging endpoint (paste into Azure Bot configuration)</div>
      <div v-if="providerSystemName" class="cluster pl-sm" data-gap="xs" data-wrap="no">
        <span class="text-mono km-description text-grey-7" style="font-size: 11px; word-break: break-all">{{ messagingEndpoint }}</span>
        <km-btn flat dense round size="xs" icon="copy" tooltip="Copy messaging endpoint" @click="copyEndpoint" />
      </div>
      <div class="cluster mt-md pl-sm" data-gap="md">
        <km-btn v-if="canManageProviders" icon="add" :label="m.noteTaker_newBotProvider()" flat dense no-caps @click="openCreateProvider" />
        <km-btn icon="refresh" :label="m.common_checkStatus()" flat dense no-caps :loading="statusLoading" @click="checkRuntimeStatus" />
        <km-chip v-if="runtimeStatus" :tone="runtimeStatus.runtime_loaded ? &quot;success&quot; : &quot;neutral&quot;" dense>{{ runtimeStatus.runtime_loaded ? 'Online' : 'Offline' }}</km-chip>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Super User" sub-title="When set, this user can access ALL transcriptions created by this note-taker bot, regardless of who initiated them.">
      <div class="km-field text-secondary-text pb-xs pl-sm">Super User AAD Object ID</div>
      <km-input v-model="superuserId" class="full-width" :placeholder="m.placeholder_uuidFormat()" height="30px" clearable :disabled="noteTakerReadonly" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Accept commands from non-organizer" sub-title="Off by default. If switched on, Note Taker will accept commands from users other than meeting organizer">
      <km-toggle v-model="acceptCommandsFromNonOrganizer" :disable="noteTakerReadonly" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Set subscription for completed recordings" sub-title="Automatically create recordings-ready subscriptions for meetings">
      <km-toggle v-model="subscriptionRecordingsReady" :disable="noteTakerReadonly" />
    </km-section>
  </div>
  <km-popup-confirm :visible="showProviderDialog" :title="editingProvider ? 'Edit Teams Note Taker Provider' : 'New Teams Note Taker Provider'" :confirm-button-label="editingProvider ? m.common_save() : 'Create'" :cancel-button-label="m.common_cancel()" notification="Credentials are encrypted at rest." @confirm="saveProvider" @cancel="closeProviderDialog">
    <div class="stack" data-gap="lg">
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Provider Name</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.name" height="30px" :placeholder="m.noteTaker_myTeamsBot()" :rules="[required()]" @input="onProviderNameInput" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">System Name</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.system_name" height="30px" :placeholder="m.noteTaker_myTeamsBotSystemName()" :rules="[required()]" :disabled="!!editingProvider" />
        <div v-if="!editingProvider" class="km-description text-secondary-text pt-2xs pl-sm">Auto-generated from name. Used in the messaging endpoint URL.</div>
      </div>
      <div v-if="providerForm.system_name">
        <div class="km-field text-secondary-text pb-xs pl-sm">Messaging endpoint (paste into Azure Bot configuration)</div>
        <div class="cluster pl-sm" data-gap="xs" data-wrap="no">
          <span class="text-mono km-description text-grey-7" style="font-size: 11px; word-break: break-all">{{ endpointFor(providerForm.system_name) }}</span>
          <km-btn flat dense round size="xs" icon="copy" tooltip="Copy messaging endpoint" @click="copy(endpointFor(providerForm.system_name))" />
        </div>
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Client ID (App ID)</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.client_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Client Secret</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.client_secret" height="30px" type="password" :placeholder="editingProvider ? m.noteTaker_leaveBlankToKeepSecret() : m.noteTaker_azureBotClientSecret()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Tenant ID</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.tenant_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">OAuth Connection Name</div>
        <km-input v-if="showProviderDialog" v-model="providerForm.auth_handler_id" height="30px" :placeholder="m.noteTaker_exampleRecordings()" />
        <div class="km-description text-secondary-text pt-xs pl-sm">Name of the OAuth Connection configured in Azure Bot Service settings.</div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { ref, reactive, computed, inject } from 'vue'
import { usePermissions } from '@shared'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter, useRoute } from 'vue-router'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { useNotify } from '@/composables/useNotify'

const ntStore = useNoteTakerStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const queries = useEntityQueries()
const { notifyCopied } = useNotify()
const { can } = usePermissions()
const noteTakerReadonlyRef = inject('noteTakerReadonly', null)
const noteTakerReadonly = computed(() => Boolean(noteTakerReadonlyRef?.value))
const canManageProviders = computed(() => !noteTakerReadonly.value && can('write:providers'))

const { data: providerListData } = queries.provider.useList()
const createProviderMutation = useSafeMutation(queries.provider.useCreate(), {
  successMessage: 'Provider created',
  defaultErrorMessage: 'Failed to create provider',
})
const updateProviderMutation = useSafeMutation(queries.provider.useUpdate(), {
  successMessage: 'Provider updated',
  defaultErrorMessage: 'Failed to update provider',
})

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => ntStore.activeRecord)

const statusLoading = ref(false)
const runtimeStatus = ref<{ runtime_loaded: boolean; has_credentials: boolean } | null>(null)
const showProviderDialog = ref(false)
const editingProvider = ref<any>(null)

const providerForm = reactive({
  name: '',
  system_name: '',
  client_id: '',
  client_secret: '',
  tenant_id: '',
  auth_handler_id: '',
})

const allProviders = computed(() => providerListData.value?.items || [])
const noteTakerProviders = computed(() =>
  allProviders.value.filter((p: any) => p.type === 'teams_note_taker')
)

const providerSystemName = computed({
  get: () => activeRecord.value?.provider_system_name || '',
  set: (value: string) => {
    if (noteTakerReadonly.value) return
    ntStore.setRecordMeta({
      key: ntStore.activeSettingsKey,
      provider_system_name: value || null,
    })
  },
})

const superuserId = computed({
  get: () => activeRecord.value?.superuser_id || '',
  set: (value: string) => {
    if (noteTakerReadonly.value) return
    ntStore.setRecordMeta({
      key: ntStore.activeSettingsKey,
      superuser_id: value || null,
    })
  },
})

const subscriptionRecordingsReady = computed({
  get: () => ntStore.settings?.subscription_recordings_ready ?? false,
  set: (v: boolean) => {
    if (noteTakerReadonly.value) return
    ntStore.updateSetting( { path: 'subscription_recordings_ready', value: v })
  },
})

const acceptCommandsFromNonOrganizer = computed({
  get: () => ntStore.settings?.accept_commands_from_non_organizer ?? false,
  set: (v: boolean) => {
    if (noteTakerReadonly.value) return
    ntStore.updateSetting( { path: 'accept_commands_from_non_organizer', value: v })
  },
})

// Messaging endpoint for Azure Bot configuration.
// Path mirrors backend `/api/user/agents/teams/note-taker/{provider_system_name}/messages`
// so Azure routes activities to the right runtime in NoteTakerRegistry.
const apiBase = computed(() => {
  const adminUrl: string = appStore.config?.api?.aiBridge?.urlAdmin || ''
  try {
    return new URL(adminUrl).origin
  } catch {
    return ''
  }
})

const endpointFor = (systemName: string) => {
  const base = apiBase.value || '<your-domain>'
  return `${base}/api/user/agents/teams/note-taker/${systemName}/messages`
}

const messagingEndpoint = computed(() => endpointFor(providerSystemName.value))

const copy = (text: string) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => notifyCopied('Copied'))
}

const copyEndpoint = () => copy(messagingEndpoint.value)

const checkRuntimeStatus = async () => {
  if (!configId.value) return
  statusLoading.value = true
  try {
    runtimeStatus.value = await ntStore.fetchRuntimeStatus(configId.value)
  } finally {
    statusLoading.value = false
  }
}

const navigateToProvider = () => {
  const prov = allProviders.value.find((p: any) => p.system_name === providerSystemName.value)
  if (prov) router.push(`/providers/${prov.id}`)
}

const resetProviderForm = () => {
  providerForm.name = ''
  providerForm.system_name = ''
  providerForm.client_id = ''
  providerForm.client_secret = ''
  providerForm.tenant_id = ''
  providerForm.auth_handler_id = ''
}

const onProviderNameInput = (val: string) => {
  // Auto-fill system_name on create; on edit it's locked anyway.
  if (!editingProvider.value) providerForm.system_name = toUpperCaseWithUnderscores(val)
}

const openCreateProvider = () => {
  if (!canManageProviders.value) return
  editingProvider.value = null
  resetProviderForm()
  showProviderDialog.value = true
}

const openEditProvider = () => {
  if (!canManageProviders.value) return
  const prov = allProviders.value.find((p: any) => p.system_name === providerSystemName.value)
  if (!prov) return
  editingProvider.value = prov
  const secrets = prov.secrets_encrypted || {}
  const conn = prov.connection_config || {}
  Object.assign(providerForm, {
    name: prov.name || '',
    system_name: prov.system_name || '',
    client_id: secrets.client_id || '',
    client_secret: '', // never round-trip secret back; empty means "keep existing"
    tenant_id: secrets.tenant_id || '',
    auth_handler_id: conn.auth_handler_id || '',
  })
  showProviderDialog.value = true
}

const closeProviderDialog = () => {
  showProviderDialog.value = false
  editingProvider.value = null
  resetProviderForm()
}

const saveProvider = async () => {
  if (!canManageProviders.value) return
  if (!providerForm.name.trim() || !providerForm.system_name.trim()) return

  // Build secrets payload. On edit, an empty value means "leave as-is";
  // the backend preserves existing values only for keys that are present.
  const secrets: any = {
    client_id: providerForm.client_id,
    client_secret: providerForm.client_secret,
    tenant_id: providerForm.tenant_id,
  }

  if (editingProvider.value) {
    const { success } = await updateProviderMutation.run({
      id: editingProvider.value.id,
      data: {
        name: providerForm.name,
        secrets_encrypted: secrets,
        connection_config: { auth_handler_id: providerForm.auth_handler_id || '' },
      },
    } as any)
    if (!success) return
  } else {
    const { success, data: created } = await createProviderMutation.run({
      name: providerForm.name,
      system_name: providerForm.system_name,
      type: 'teams_note_taker',
      secrets_encrypted: secrets,
      connection_config: { auth_handler_id: providerForm.auth_handler_id || '' },
    } as any)
    if (!success) return
    if ((created as any)?.system_name) {
      providerSystemName.value = (created as any).system_name
    }
  }
  closeProviderDialog()
}
</script>
