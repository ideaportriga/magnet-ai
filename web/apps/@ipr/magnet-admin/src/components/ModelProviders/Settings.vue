<template lang="pug">
.full-width
  km-section(title='General info', subTitle='General Model Provider settings')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
    .row.items-center.q-gap-16.no-wrap
      km-select.full-width(:model-value='provider.type', readonly, disabled)
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg Endpoint
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
            km-btn(
              v-if='!isEditingEndpoint',
              icon='fa fa-pen',
              flat,
              iconSize='12px',
              @click='startEditingEndpoint', 
              size='xs'
            )
            km-btn(
              v-if='isEditingEndpoint',
              icon='fa fa-xmark',
              flat,
              iconSize='12px',
              @click='cancelEditingEndpoint', 
              size='xs'
            )
            km-btn(
              v-if='isEditingEndpoint',
              icon='fa fa-check',
              flat,
              iconSize='12px',
              @click='saveEndpoint', 
              size='xs',
              color='primary'
            )
    .km-description.text-secondary-text.q-pb-4.q-pl-8(v-if='!isEditingEndpoint') Click edit to change endpoint. Warning: this will clear all secrets.
    .km-description.text-negative.q-pb-4.q-pl-8(v-if='isEditingEndpoint') Changing endpoint will permanently delete all secrets!
  
  km-popup-confirm(
    :visible='showEndpointWarning',
    title='Change Endpoint',
    confirmButtonLabel='Yes, Change Endpoint',
    cancelButtonLabel='Cancel',
    notification='Changing the endpoint will permanently delete all encrypted secrets. You will need to re-enter all credentials after this change.',
    @confirm='confirmEndpointChange',
    @cancel='cancelEndpointChange'
  )
    .text-body1 Are you sure you want to change the endpoint?
    .text-body2.q-mt-md Current endpoint: {{ provider.endpoint || 'Not set' }}
    .text-body2 New endpoint: {{ tempEndpoint }}

  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Connection', subTitle='Connection parameters like endpoints and headers')
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
      km-btn(label='Add Record', @click='addConnection', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Secrets', subTitle='Use to store sensitive values such as API keys or tokens.')
    km-secrets(v-model:secrets='secrets' :original-secrets='originalProviderSecrets' :remount-value='remountValue')
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { onBeforeRouteLeave } from 'vue-router'
import { useQuasar } from 'quasar'

const store = useStore()
const $q = useQuasar()

const provider = computed(() => store.getters.provider)

const isEditingEndpoint = ref(false)
const tempEndpoint = ref('')
const showEndpointWarning = ref(false)

const pendingNavigation = ref(null)

// Prevent navigation when editing endpoint
onBeforeRouteLeave((to, from, next) => {
  if (isEditingEndpoint.value && tempEndpoint.value !== provider.value?.endpoint) {
    pendingNavigation.value = next
    showEndpointWarning.value = true
  } else {
    // If editing but no changes, just cancel editing and continue
    if (isEditingEndpoint.value) {
      cancelEditingEndpoint()
    }
    next()
  }
})

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

const confirmEndpointChange = async () => {
  // Update endpoint
  store.commit('updateProviderProperty', { 
    key: 'endpoint', 
    value: tempEndpoint.value 
  })
  // Clear secrets as backend will do
  store.commit('updateProviderProperty', { 
    key: 'secrets_encrypted', 
    value: {} 
  })
  
  try {
    // Save provider
    await store.dispatch('saveProvider')
    
    $q.notify({
      position: 'top',
      message: 'Endpoint updated successfully.',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } catch (error) {
    console.error('Error saving provider:', error)
    $q.notify({
      position: 'top',
      message: 'Failed to save endpoint changes.',
      color: 'negative',
      textColor: 'white',
      timeout: 2000,
    })
  }
  
  showEndpointWarning.value = false
  isEditingEndpoint.value = false
  tempEndpoint.value = ''
  
  // Continue navigation if it was blocked
  if (pendingNavigation.value) {
    pendingNavigation.value()
    pendingNavigation.value = null
  }
}

const cancelEndpointChange = () => {
  showEndpointWarning.value = false
  tempEndpoint.value = provider.value?.endpoint || ''
  
  // Cancel navigation if it was blocked
  if (pendingNavigation.value) {
    pendingNavigation.value(false)
    pendingNavigation.value = null
  }
}

const connectionEntries = computed(() => {
  const config = provider.value?.connection_config || {}
  return Object.entries(config)
})

const originalProviderSecrets = computed(() => store.getters.originalProviderSecrets)
const remountValue = computed(() => provider.value?.updated_at)

const secrets = computed({
  get() {
    const encryptedSecrets = provider.value?.secrets_encrypted
    if (!encryptedSecrets) {
      return {}
    }
    return encryptedSecrets
  },
  set(value) {
    store.commit('updateProviderProperty', { 
      key: 'secrets_encrypted', 
      value 
    })
  },
})

const addConnection = () => {
  const newConfig = { ...provider.value.connection_config, '': '' }
  store.commit('updateProviderProperty', { 
    key: 'connection_config', 
    value: newConfig 
  })
}

const removeConnection = (key) => {
  const newConfig = { ...provider.value.connection_config }
  delete newConfig[key]
  store.commit('updateProviderProperty', { 
    key: 'connection_config', 
    value: newConfig 
  })
}

const updateConnectionKey = (oldKey, newKey) => {
  const config = { ...provider.value.connection_config }
  const value = config[oldKey]
  delete config[oldKey]
  config[newKey] = value
  store.commit('updateProviderProperty', { 
    key: 'connection_config', 
    value: config 
  })
}

const updateConnectionValue = (key, newValue) => {
  const config = { ...provider.value.connection_config }
  config[key] = newValue
  store.commit('updateProviderProperty', { 
    key: 'connection_config', 
    value: config 
  })
}
</script>

<style lang="stylus" scoped>
.controls
  position: absolute
  right: 5px
  top: 0
</style>
