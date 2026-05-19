<template>
  <km-secrets-item v-for="[key, value] in Object.entries(secrets || {})" :key="`${key}-${remountValue}`" :item-key="key" :value="value" :is-new="!originalSecrets.includes(key)" :readonly="readonly" @update="updateSecret" @delete="deleteSecret" />
  <div v-if="!readonly" class="cluster pt-lg">
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
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:secrets'])

// `default: () => ({})` only kicks in for `undefined` — if the parent passes
// `null` the prop stays `null`. Same for direct property mutation: writing to
// `props.secrets[...]` only works if it's a real object and even then it
// breaks the parent's reactivity. Coerce to `{}` and emit a fresh object on
// every change.
const safeSecrets = () => props.secrets ?? {}

const deleteSecret = (key) => {
  if (props.readonly) return
  const next = { ...safeSecrets() }
  delete next[key]
  emit('update:secrets', next)
}
const updateSecret = (key, newKey, newValue) => {
  if (props.readonly) return
  const entries = Object.entries(safeSecrets())
  const idx = entries.findIndex(([k]) => k === key)

  if (idx !== -1) {
    entries[idx] = [newKey, newValue] // replace in place
  } else {
    entries.push([newKey, newValue]) // add new
  }

  emit('update:secrets', Object.fromEntries(entries))
}

const addSecret = () => {
  if (props.readonly) return
  emit('update:secrets', { ...safeSecrets(), '': '' })
}
</script>
