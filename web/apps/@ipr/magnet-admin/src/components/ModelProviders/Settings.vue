<template lang="pug">
.full-width
  km-section(title='General info', subTitle='General Model Provider settings')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
    .row.items-center.q-gap-16.no-wrap
      km-select.full-width(:model-value='type', readonly, disabled)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Connection', subTitle='Connection parameters like endpoints and headers')
    km-notification-text(
      notification='Secrets are securely stored in encrypted format. They cannot be edited individually. To update them, you need to reset all secrets.'
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-lg(v-for='[key, value] in connection', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateRecord(key, $event, value)')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(label='Value', :model-value='value', @update:model-value='updateRecord(key, key, $event)')
      .col-auto
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeRecord(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      km-btn(label='Add Record', @click='addRecord', size='sm', icon='o_add', flat)
  q-separator.q-mt-lg.q-mb-lg
  km-section(title='Secrets', subTitle='Use to store sensitive values such as API keys or tokens.')
    km-notification-text(
      notification="Secrets are securely stored in encrypted format. They cannot be edited individually. To update them, you need to reset all secrets."
    )
    .row.items-center.q-gap-8.no-wrap.q-mt-md(v-for='[key, value] in secretsArray', :key='key')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Key
        km-input(label='Key', :model-value='key', @update:model-value='updateSecret(key, $event, value)', :readonly='!editMode')
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Value
        km-input(
          label='Value', 
          :model-value='getSecretDisplayValue(key, value)', 
          @update:model-value='updateSecret(key, key, $event)', 
          :readonly='!editMode',
          :placeholder='editMode ? "Enter new value" : ""'
        )
      .col-auto(v-if='editMode')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 &nbsp;
        km-btn(@click='removeSecret(key)', icon='o_delete', size='sm', flat, color='negative')
    .row.q-pt-16
      template(v-if='editMode')
        km-btn(label='Add Secret', @click='addSecret', size='sm', icon='o_add', flat)
        km-btn(label='Cancel', @click='store.dispatch("toggleApiSettingsSecretsEditMode", false)', size='sm', flat)
      template(v-else)
        km-btn(
          :label='hasExistingSecrets ? "Edit Secrets" : "Add Secrets"',
          @click='initializeSecretsEdit',
          size='sm',
          icon='o_edit',
          flat
        )


</template>
<script setup>
import { ref, computed, reactive } from 'vue'

const type = ref('')
const editMode = ref(false)

const temp = reactive({
  connection: new Map(),
  secrets: new Map(),
})

const connection = computed({
  get() {
    return temp.connection
  },
  set(value) {
    console.log(value)
    temp.connection = value
  },
})

const addRecord = () => {
  const newConnection = new Map(connection.value)
  newConnection.set('', '')
  connection.value = newConnection
}

const removeRecord = (key) => {
  const newConnection = new Map(connection.value)
  newConnection.delete(key)
  connection.value = newConnection
}

const updateRecord = (oldKey, newKey, newValue) => {
  const currentConnection = connection.value
  const entries = [...currentConnection.entries()]
  const idx = entries.findIndex(([k]) => k === oldKey)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  connection.value = new Map(entries)
}


//secrets
const secrets = computed({
  get() {
    return temp.secrets
  },
  set(value) {
    temp.secrets = value
  },
})


const secretsArray = computed(() => {
  const secretsMap = secrets.value
  if (secretsMap instanceof Map) {
    return Array.from(secretsMap.entries())
  }
  return []
})

</script>
