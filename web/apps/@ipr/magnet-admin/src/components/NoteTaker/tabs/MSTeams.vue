<template lang="pug">
div
  km-section(title='Bot Credentials', subTitle='Azure Bot credentials to connect with Note Taker')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Azure Bot Provider
    .row.items-center.q-gutter-sm
      .col
        km-select(
          v-model='providerSystemName',
          :options='noteTakerProviders',
          option-label='name',
          option-value='system_name',
          emit-value,
          map-options,
          hasDropdownSearch,
          height='auto',
          minHeight='36px',
          clearable,
          placeholder='Select a Teams Note Taker provider'
        )
      .col-auto(v-if='providerSystemName')
        km-btn(icon='open_in_new', flat, dense, @click='navigateToProvider')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Provider of type "Teams Note Taker" that stores encrypted Azure Bot credentials (client_id, client_secret, tenant_id).
    .row.items-center.q-gap-12.q-mt-md.q-pl-8
      km-btn(
        icon='add',
        label='New Bot Provider',
        flat, dense, no-caps,
        @click='showCreateProvider = true'
      )
      km-btn(
        icon='sync',
        label='Check Status',
        flat, dense, no-caps,
        @click='checkRuntimeStatus',
        :loading='statusLoading'
      )
      q-chip(
        v-if='runtimeStatus',
        :color='runtimeStatus.runtime_loaded ? "positive" : "grey-5"',
        text-color='white',
        dense
      ) {{ runtimeStatus.runtime_loaded ? 'Online' : 'Offline' }}

  q-separator.q-my-lg

  km-section(title='Super User', subTitle='When set, this user can access ALL transcriptions created by this note-taker bot, regardless of who initiated them.')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Super User AAD Object ID
    km-input.full-width(
      v-model='superuserId',
      placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
      height='30px',
      clearable
    )

  q-separator.q-my-lg

  km-section(title='Accept commands from non-organizer', subTitle='Off by default. If switched on, Note Taker will accept commands from users other than meeting organizer')
    q-toggle(v-model='acceptCommandsFromNonOrganizer', color='primary')

  q-separator.q-my-lg

  km-section(title='Set subscription for completed recordings', subTitle='Automatically create recordings-ready subscriptions for meetings')
    q-toggle(v-model='subscriptionRecordingsReady', color='primary')

//- ── Inline Create Provider dialog ──────────────────────────────────
km-popup-confirm(
  :visible='showCreateProvider',
  title='New Teams Note Taker Provider',
  confirmButtonLabel='Create',
  cancelButtonLabel='Cancel',
  notification='Credentials will be encrypted at rest.',
  @confirm='createProvider',
  @cancel='showCreateProvider = false'
)
  .column.q-gap-16
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Provider Name
      km-input(
        v-if='showCreateProvider',
        height='30px',
        placeholder='My Teams Bot',
        v-model='newProvider.name',
        :rules='[required()]'
      )
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Client ID (App ID)
      km-input(
        v-if='showCreateProvider',
        height='30px',
        placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        v-model='newProvider.client_id'
      )
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Client Secret
      km-input(
        v-if='showCreateProvider',
        height='30px',
        type='password',
        placeholder='Azure Bot client secret',
        v-model='newProvider.client_secret'
      )
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Tenant ID
      km-input(
        v-if='showCreateProvider',
        height='30px',
        placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        v-model='newProvider.tenant_id'
      )
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 OAuth Connection Name
      km-input(
        v-if='showCreateProvider',
        height='30px',
        placeholder='e.g. Recordings',
        v-model='newProvider.auth_handler_id'
      )
      .km-description.text-secondary-text.q-pt-xs.q-pl-8 Name of the OAuth Connection configured in Azure Bot Service settings.
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter, useRoute } from 'vue-router'
import { required, toUpperCaseWithUnderscores } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'

const ntStore = useNoteTakerStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const { notifySuccess, notifyError } = useNotify()
const queries = useEntityQueries()

const { data: providerListData } = queries.provider.useList()
const { mutateAsync: createProviderMutation } = queries.provider.useCreate()

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

const subscriptionRecordingsReady = computed({
  get: () => ntStore.settings?.subscription_recordings_ready ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'subscription_recordings_ready', value: v }),
})

const acceptCommandsFromNonOrganizer = computed({
  get: () => ntStore.settings?.accept_commands_from_non_organizer ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'accept_commands_from_non_organizer', value: v }),
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
  if (prov) window.open(router.resolve({ path: `/providers/${prov.id}` }).href, '_blank')
}

const createProvider = async () => {
  if (!newProvider.name.trim()) return
  try {
    const systemName = toUpperCaseWithUnderscores(newProvider.name)
    const created = await createProviderMutation({
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
    showCreateProvider.value = false
    if (created?.system_name) {
      providerSystemName.value = created.system_name
    }
    notifySuccess('Provider created')
    newProvider.name = ''
    newProvider.client_id = ''
    newProvider.client_secret = ''
    newProvider.tenant_id = ''
    newProvider.auth_handler_id = ''
  } catch (error: any) {
    notifyError(error?.message || 'Failed to create provider')
  }
}
</script>
