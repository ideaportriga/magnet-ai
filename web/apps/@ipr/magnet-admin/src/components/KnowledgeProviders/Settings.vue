<template lang="pug">
.full-width
  km-section(:title='m.section_generalInfo()', :subTitle='m.subtitle_generalKspSettings()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_type() }}
    .row.items-center.q-gap-16.no-wrap
      km-select.full-width(:model-value='provider.type', readonly, disabled)
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg {{ m.label_endpoint() }}
    .row.items-center.q-gap-8.no-wrap
      .col
        .row.items-center.q-gap-8.no-wrap.relative-position
          km-input.full-width(
            :model-value='endpointValue',
            @update:model-value='tempEndpoint = $event',
            :readonly='!isEditingEndpoint',
            placeholder='https://api.example.com'
          )
          .controls.full-height.row.items-center
            km-btn(v-if='!isEditingEndpoint', icon='fa fa-pen', flat, iconSize='12px', @click='startEditingEndpoint', size='xs')
            km-btn(v-if='isEditingEndpoint', icon='fa fa-xmark', flat, iconSize='12px', @click='cancelEditingEndpoint', size='xs')
            km-btn(v-if='isEditingEndpoint', icon='fa fa-check', flat, iconSize='12px', @click='saveEndpoint', size='xs', color='primary')
    .km-description.text-secondary-text.q-pb-4.q-pl-8(v-if='!isEditingEndpoint') {{ m.hint_endpointWarning() }}
    .km-description.text-negative.q-pb-4.q-pl-8(v-if='isEditingEndpoint') {{ m.hint_changeEndpointWarning() }}

  km-popup-confirm(
    :visible='showEndpointWarning',
    :title='m.dialog_changeEndpoint()',
    :confirmButtonLabel='m.confirm_yesClearSecrets()',
    :cancelButtonLabel='m.common_cancel()',
    :notification='m.hint_changeEndpointWarning()',
    @confirm='confirmEndpointChange',
    @cancel='cancelEndpointChange'
  )
    .text-body1 Are you sure you want to change the endpoint?
    .text-body2.q-mt-md Current endpoint: {{ provider.endpoint || 'Not set' }}
    .text-body2 New endpoint: {{ tempEndpoint }}

  q-separator.q-mt-lg.q-mb-lg
  km-section(:title='m.section_connection()', :subTitle='m.subtitle_connectionParams()')
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in connectionEntries', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateConnectionKey(key, $event)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', :model-value='value', @update:model-value='updateConnectionValue(key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeConnection(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(:label='m.common_addRecord()', @click='addConnection', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(:title='m.section_secrets()', :subTitle='m.subtitle_useSecretsKsp()')
    km-secrets(v-model:secrets='secrets', :original-secrets='originalProviderSecrets', :remount-value='remountValue')
</template>

<script setup>
import { computed, ref } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

const { draft, data, updateField, updateFields } = useEntityDetail('provider')

const provider = computed(() => draft.value)

const isEditingEndpoint = ref(false)
const tempEndpoint = ref('')
const showEndpointWarning = ref(false)

const endpointValue = computed(() => {
  if (isEditingEndpoint.value) {
    return tempEndpoint.value
  }
  return provider.value?.endpoint || ''
})

const startEditingEndpoint = () => {
  tempEndpoint.value = provider.value?.endpoint || ''
  isEditingEndpoint.value = true
}

const cancelEditingEndpoint = () => {
  isEditingEndpoint.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
}

const saveEndpoint = () => {
  if (tempEndpoint.value !== provider.value?.endpoint) {
    showEndpointWarning.value = true
  } else {
    isEditingEndpoint.value = false
  }
}

const confirmEndpointChange = () => {
  // Update endpoint and clear secrets in draft
  updateFields({
    endpoint: tempEndpoint.value,
    secrets_encrypted: {},
  })
  showEndpointWarning.value = false
  isEditingEndpoint.value = false
  tempEndpoint.value = ''
}

const cancelEndpointChange = () => {
  showEndpointWarning.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
}

const connectionEntries = computed(() => {
  const config = provider.value?.connection_config || {}
  return Object.entries(config)
})

const originalProviderSecrets = computed(() => {
  const secrets = data.value?.secrets_encrypted
  if (!secrets) return []
  return Object.keys(secrets)
})
const remountValue = computed(() => provider.value?.updated_at)

const secrets = computed({
  get() {
    const encryptedSecrets = provider.value?.secrets_encrypted
    if (!encryptedSecrets) {
      return {}
    }
    return { ...encryptedSecrets }
  },
  set(value) {
    updateField('secrets_encrypted', value)
  },
})

const addConnection = () => {
  const newConfig = { ...provider.value.connection_config, '': '' }
  updateField('connection_config', newConfig)
}

const removeConnection = (key) => {
  const newConfig = { ...provider.value.connection_config }
  delete newConfig[key]
  updateField('connection_config', newConfig)
}

const updateConnectionKey = (oldKey, newKey) => {
  const config = { ...provider.value.connection_config }
  const value = config[oldKey]
  delete config[oldKey]
  config[newKey] = value
  updateField('connection_config', config)
}

const updateConnectionValue = (key, newValue) => {
  const config = { ...provider.value.connection_config }
  config[key] = newValue
  updateField('connection_config', config)
}
</script>

<style lang="stylus" scoped>
.controls
  position: absolute
  right: 5px
  top: 0
</style>
