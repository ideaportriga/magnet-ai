<template>
  <div class="stack" data-gap="md">
    <div class="km-field">
      <div class="text-secondary-text pb-xs km-title">Azure Bot Provider</div>
      <div class="cluster" data-gap="sm">
        <div class="flex-1">
          <km-select v-model="providerSystemName" :options="noteTakerProviders" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" clearable :placeholder="m.noteTaker_selectTeamsProvider()" />
        </div>
        <div v-if="providerSystemName" class="flex-none">
          <km-btn icon="external-link" flat dense @click="navigateToProvider" />
        </div>
        <div class="flex-none">
          <km-btn icon="add" :label="m.common_newProvider()" flat dense @click="showCreateProvider = true" />
        </div>
      </div>
      <div class="km-description text-secondary-text pt-2xs">Provider of type "Teams Note Taker" that stores encrypted Azure Bot credentials (client_id, client_secret, tenant_id).</div>
      <div v-if="!noteTakerProviders.length" class="km-description text-secondary-text">No providers of type "teams_note_taker" found. Create one first.</div>
    </div>
    <div class="km-field">
      <div class="cluster" data-gap="sm">
        <km-chip v-if="runtimeStatus" :tone="runtimeStatus.runtime_loaded ? &quot;success&quot; : &quot;neutral&quot;" dense>{{ runtimeStatus.runtime_loaded ? 'Online' : 'Offline' }}</km-chip>
        <km-btn :label="m.common_checkStatus()" flat dense icon="refresh" :loading="statusLoading" @click="checkRuntimeStatus" />
      </div>
    </div>
    <km-separator />
    <div class="km-field">
      <div class="text-secondary-text pb-xs km-title">Superuser (AAD Object ID)</div>
      <km-input v-model="superuserId" class="full-width" :placeholder="m.placeholder_uuidFormat()" height="30px" clearable />
      <div class="km-description text-secondary-text pt-2xs">When set, this user can access ALL transcriptions created by this note-taker bot, regardless of who initiated them.</div>
    </div>
  </div>
  <km-popup-confirm :visible="showCreateProvider" title="New Teams Note Taker Provider" confirm-button-label="Create" :cancel-button-label="m.common_cancel()" notification="Credentials will be encrypted at rest." @confirm="createProvider" @cancel="showCreateProvider = false">
    <div class="stack" data-gap="lg">
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Provider Name</div>
        <km-input v-if="showCreateProvider" v-model="newProvider.name" height="30px" :placeholder="m.noteTaker_myTeamsBot()" :rules="[required()]" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Client ID (App ID)</div>
        <km-input v-if="showCreateProvider" v-model="newProvider.client_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Client Secret</div>
        <km-input v-if="showCreateProvider" v-model="newProvider.client_secret" height="30px" type="password" :placeholder="m.noteTaker_azureBotClientSecret()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">Tenant ID</div>
        <km-input v-if="showCreateProvider" v-model="newProvider.tenant_id" height="30px" :placeholder="m.placeholder_uuidFormat()" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">OAuth Connection Name</div>
        <km-input v-if="showCreateProvider" v-model="newProvider.auth_handler_id" height="30px" :placeholder="m.noteTaker_exampleRecordings()" />
        <div class="km-description text-secondary-text pt-2xs">Name of the OAuth Connection configured in Azure Bot Service settings.</div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter, useRoute } from 'vue-router'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useSafeMutation } from '@/composables/useSafeMutation'

const ntStore = useNoteTakerStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const queries = useEntityQueries()

const { data: providerListData } = queries.provider.useList()
const createProviderMutation = useSafeMutation(queries.provider.useCreate(), {
  successMessage: 'Provider created',
  defaultErrorMessage: 'Failed to create provider',
})

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => ntStore.activeRecord)

const statusLoading = ref(false)
const runtimeStatus = ref<{ runtime_loaded: boolean; has_credentials: boolean } | null>(null)
const showCreateProvider = ref(false)

const newProvider = reactive({
  name: '',
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
    ntStore.setRecordMeta({
      key: ntStore.activeSettingsKey,
      provider_system_name: value || null,
    })
  },
})

const superuserId = computed({
  get: () => activeRecord.value?.superuser_id || '',
  set: (value: string) => {
    ntStore.setRecordMeta({
      key: ntStore.activeSettingsKey,
      superuser_id: value || null,
    })
  },
})

const apiReady = computed(() => Boolean(appStore.config?.api?.aiBridge?.urlAdmin))

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

const createProvider = async () => {
  if (!newProvider.name.trim()) return
  const systemName = toUpperCaseWithUnderscores(newProvider.name)
  const { success, data: created } = await createProviderMutation.run({
    name: newProvider.name,
    system_name: systemName,
    type: 'teams_note_taker',
    secrets_encrypted: {
      client_id: newProvider.client_id,
      client_secret: newProvider.client_secret,
      tenant_id: newProvider.tenant_id,
    },
    connection_config: {
      auth_handler_id: newProvider.auth_handler_id || '',
    },
  } as any)
  if (!success) return
  showCreateProvider.value = false
  if ((created as any)?.system_name) {
    providerSystemName.value = (created as any).system_name
  }
  newProvider.name = ''
  newProvider.client_id = ''
  newProvider.client_secret = ''
  newProvider.tenant_id = ''
  newProvider.auth_handler_id = ''
}
</script>
