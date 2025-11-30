<template lang="pug">
km-secrets-item(
  :item-key='key',
  :value='value',
  @update='updateSecret',
  @delete='deleteSecret',
  v-for='[key, value] in Object.entries(secrets)',
  :is-new='!originalSecrets.includes(key)',
  :key='`${key}-${remountValue}`'
)
.row.q-pt-16
  km-btn(label='Add Secret', @click='addSecret', size='sm', icon='o_add', flat)
</template>
<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  secrets: {
    type: Object,
    required: true,
  },
  originalSecrets: {
    type: Array,
    required: false,
    default: () => [],
  },
  remountValue: {
    default: 0,
  },
})

const emit = defineEmits(['update:secrets'])

const deleteSecret = (key) => {
  const secrets = props.secrets
  delete secrets[key]
  emit('update:secrets', secrets)
}
const updateSecret = (key, newKey, newValue) => {
  const secrets = props.secrets
  const entries = [...Object.entries(secrets)]
  const idx = entries.findIndex(([k]) => k === key)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  const newSecrets = Object.fromEntries(entries)
  emit('update:secrets', newSecrets)
}

const addSecret = () => {
  const object = props.secrets
  object[''] = ''
  emit('update:secrets', object)
}
</script>
