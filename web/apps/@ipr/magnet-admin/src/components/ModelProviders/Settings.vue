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
    km-notification-text(
      notification="Secrets are securely stored in encrypted format. They cannot be edited individually. To update them, you need to reset all secrets."
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-md(v-for='[key, value] in secretsEntries', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', :readonly='!editMode')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(
          label='Value', 
          :model-value='editMode ? "" : "••••••••"', 
          @update:model-value='updateSecretValue(key, $event)', 
          :readonly='!editMode',
          :placeholder='editMode ? "Enter new value" : ""',
          type='password'
        )
      .col-auto(v-if='editMode')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeSecret(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      template(v-if='editMode')
        km-btn(label='Add Secret', @click='addSecret', size='sm', icon='o_add', flat)
        km-btn(label='Cancel', @click='cancelSecretsEdit', size='sm', flat)
      template(v-else)
        km-btn(
          :label='hasExistingSecrets ? "Edit Secrets" : "Add Secrets"',
          @click='initializeSecretsEdit',
          size='sm',
          icon='o_edit',
          flat
        )
</template>

<script>
import { ref, computed } from 'vue'

export default {
  setup() {
    const editMode = ref(false)
    const tempSecrets = ref({})

    return {
      editMode,
      tempSecrets,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    connectionEntries() {
      const config = this.provider?.connection_config || {}
      return Object.entries(config)
    },
    secretsEntries() {
      if (this.editMode) {
        return Object.entries(this.tempSecrets)
      }
      const secrets = this.provider?.secrets_encrypted || {}
      return Object.entries(secrets)
    },
    hasExistingSecrets() {
      const secrets = this.provider?.secrets_encrypted || {}
      return Object.keys(secrets).length > 0
    },
  },
  methods: {
    addConnection() {
      const newConfig = { ...this.provider.connection_config, '': '' }
      this.$store.commit('updateProviderProperty', { 
        key: 'connection_config', 
        value: newConfig 
      })
    },
    removeConnection(key) {
      const newConfig = { ...this.provider.connection_config }
      delete newConfig[key]
      this.$store.commit('updateProviderProperty', { 
        key: 'connection_config', 
        value: newConfig 
      })
    },
    updateConnectionKey(oldKey, newKey) {
      const config = { ...this.provider.connection_config }
      const value = config[oldKey]
      delete config[oldKey]
      config[newKey] = value
      this.$store.commit('updateProviderProperty', { 
        key: 'connection_config', 
        value: config 
      })
    },
    updateConnectionValue(key, newValue) {
      const config = { ...this.provider.connection_config }
      config[key] = newValue
      this.$store.commit('updateProviderProperty', { 
        key: 'connection_config', 
        value: config 
      })
    },
    initializeSecretsEdit() {
      this.tempSecrets = { ...this.provider.secrets_encrypted }
      this.editMode = true
    },
    cancelSecretsEdit() {
      this.tempSecrets = {}
      this.editMode = false
    },
    addSecret() {
      this.tempSecrets = { ...this.tempSecrets, '': '' }
    },
    removeSecret(key) {
      const newSecrets = { ...this.tempSecrets }
      delete newSecrets[key]
      this.tempSecrets = newSecrets
    },
    updateSecretValue(key, value) {
      this.tempSecrets = { ...this.tempSecrets, [key]: value }
    },
    saveSecrets() {
      this.$store.commit('updateProviderProperty', { 
        key: 'secrets_encrypted', 
        value: this.tempSecrets 
      })
      this.editMode = false
      this.tempSecrets = {}
    },
  },
}
</script>
