<template lang="pug">
.full-width
  km-section(title='General info', subTitle='General Model Provider settings')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
    .row.items-center.q-gap-16.no-wrap
      km-select.full-width(:model-value='provider.type', readonly, disabled)
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
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

const provider = computed(() => store.getters.provider)

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
