<template lang="pug">
.q-gutter-md
  //- ── Provider selection ────────────────────────────────────────────
  .km-field
    .text-secondary-text.q-pb-xs.km-title Azure Bot Provider
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
          height='30px',
          clearable,
          placeholder='Select a Teams Note Taker provider'
        )
      .col-auto(v-if='providerSystemName')
        km-btn(
          icon='open_in_new',
          flat, dense,
          @click='navigateToProvider'
        )
      .col-auto
        km-btn(
          icon='add',
          label='New Provider',
          flat, dense,
          @click='showCreateProvider = true'
        )
    .km-description.text-secondary-text.q-pt-2 Provider of type "Teams Note Taker" that stores encrypted Azure Bot credentials (client_id, client_secret, tenant_id).
    .km-description.text-secondary-text(v-if='!noteTakerProviders.length') No providers of type "teams_note_taker" found. Create one first.

  //- ── Runtime status ────────────────────────────────────────────────
  .km-field
    .row.items-center.q-gap-8
      q-chip(
        v-if='runtimeStatus',
        :color='runtimeStatus.runtime_loaded ? "positive" : "grey-5"',
        text-color='white',
        dense
      ) {{ runtimeStatus.runtime_loaded ? 'Online' : 'Offline' }}
      km-btn(
        label='Check Status',
        flat, dense, icon='refresh',
        @click='checkRuntimeStatus',
        :loading='statusLoading'
      )

  q-separator

  //- ── Superuser ─────────────────────────────────────────────────────
  .km-field
    .text-secondary-text.q-pb-xs.km-title Superuser (AAD Object ID)
    km-input.full-width(
      v-model='superuserId',
      placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
      height='30px',
      clearable
    )
    .km-description.text-secondary-text.q-pt-2 When set, this user can access ALL transcriptions created by this note-taker bot, regardless of who initiated them.

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
      .km-description.text-secondary-text.q-pt-2 Name of the OAuth Connection configured in Azure Bot Service settings.
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { required, toUpperCaseWithUnderscores } from '@shared'

const store = useStore()
const router = useRouter()
const route = useRoute()
const $q = useQuasar()

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)

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

const allProviders = computed(() => store.getters['chroma/provider']?.items || [])
const noteTakerProviders = computed(() =>
  allProviders.value.filter((p: any) => p.type === 'teams_note_taker')
)

const providerSystemName = computed({
  get: () => activeRecord.value?.provider_system_name || '',
  set: (value: string) => {
    store.commit('setNoteTakerRecordMeta', {
      key: store.getters.noteTakerSettingsActiveKey,
      provider_system_name: value || null,
    })
  },
})

const superuserId = computed({
  get: () => activeRecord.value?.superuser_id || '',
  set: (value: string) => {
    store.commit('setNoteTakerRecordMeta', {
      key: store.getters.noteTakerSettingsActiveKey,
      superuser_id: value || null,
    })
  },
})

const apiReady = computed(() => Boolean(store.getters.config?.api?.aiBridge?.urlAdmin))

watch(apiReady, (ready) => {
  if (ready && !allProviders.value.length) {
    store.dispatch('chroma/get', { entity: 'provider' })
  }
}, { immediate: true })

const checkRuntimeStatus = async () => {
  if (!configId.value) return
  statusLoading.value = true
  try {
    runtimeStatus.value = await store.dispatch('fetchNoteTakerRuntimeStatus', configId.value)
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
    const created = await store.dispatch('chroma/create', {
      entity: 'provider',
      payload: {
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
      },
    })
    showCreateProvider.value = false
    // Refresh providers list
    await store.dispatch('chroma/get', { entity: 'provider' })
    // Auto-select newly created provider
    if (created?.system_name) {
      providerSystemName.value = created.system_name
    }
    $q.notify({ position: 'top', message: 'Provider created', color: 'positive', textColor: 'black', timeout: 1200 })
    // Reset form
    newProvider.name = ''
    newProvider.client_id = ''
    newProvider.client_secret = ''
    newProvider.tenant_id = ''
    newProvider.auth_handler_id = ''
  } catch (error: any) {
    $q.notify({ position: 'top', message: error?.message || 'Failed to create provider', color: 'negative', textColor: 'white', timeout: 2000 })
  }
}
</script>
