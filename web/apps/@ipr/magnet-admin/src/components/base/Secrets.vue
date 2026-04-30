<template>
  <km-secrets-item v-for="[key, value] in Object.entries(secrets || {})" :key="`${key}-${remountValue}`" :item-key="key" :value="value" :is-new="!originalSecrets.includes(key)" @update="updateSecret" @delete="deleteSecret" />
  <div class="cluster pt-lg">
    <km-btn :label="m.common_addSecret()" size="sm" icon="add" flat @click="addSecret" />
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps({
  secrets: {
    type: Object,
    default: () => ({}),
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
