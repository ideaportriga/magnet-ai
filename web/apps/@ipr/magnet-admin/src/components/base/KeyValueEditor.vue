<template>
  <div class="km-kv-editor">
    <div
      v-for="(pair, index) in entries"
      :key="index"
      class="cluster mt-lg"
      data-gap="sm"
      data-wrap="no"
    >
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ keyLabel || m.common_key() }}</div>
        <km-input
          :model-value="pair[0]"
          :placeholder="keyPlaceholder"
          :readonly="keyReadonly"
          @update:model-value="updateKey(index, $event)"
        />
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ valueLabel || m.common_value() }}</div>
        <km-input
          :model-value="pair[1]"
          :placeholder="valuePlaceholder"
          :readonly="valueReadonly"
          @update:model-value="updateValue(index, $event)"
        />
      </div>
      <div class="flex-none">
        <div class="km-field text-secondary-text pb-xs pl-sm">&nbsp;</div>
        <km-btn icon="delete" size="sm" flat tone="danger" @click="removeRow(index)" />
      </div>
    </div>
    <div class="cluster pt-lg" data-justify="between">
      <km-btn :label="addLabel || m.common_addRecord()" size="sm" icon="add" flat @click="addRow" />
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
/**
 * `<km-key-value-editor v-model="record">` — generic editor for a
 * `Record<string, string>` shape. Renders one row per entry with key + value
 * inputs and a delete button, plus an "Add record" trigger underneath.
 *
 * Replaces the inlined Connection / Custom-Headers / Security-Values markup
 * that lived in 3+ provider settings screens.
 *
 * The `#actions` slot lets call-sites drop extra trailing buttons next to
 * "Add record" (e.g. "Test connection" on the provider settings).
 */

import { computed } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps({
  /** Current map. Plain object — keys preserve insertion order. */
  modelValue: { type: Object, default: () => ({}) },
  keyLabel: { type: String, default: '' },
  valueLabel: { type: String, default: '' },
  keyPlaceholder: { type: String, default: '' },
  valuePlaceholder: { type: String, default: '' },
  addLabel: { type: String, default: '' },
  keyReadonly: { type: Boolean, default: false },
  valueReadonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

/* `:key="index"` rather than `:key="pair[0]"` — keeping the row identity
 * stable on key edits avoids Vue unmounting / remounting the input on every
 * keystroke (which dropped focus mid-word in the legacy markup). */
const entries = computed(() => Object.entries(props.modelValue || {}))

function emitFromEntries(nextEntries) {
  emit('update:modelValue', Object.fromEntries(nextEntries))
}

function addRow() {
  emitFromEntries([...entries.value, ['', '']])
}

function removeRow(index) {
  const next = entries.value.slice()
  next.splice(index, 1)
  emitFromEntries(next)
}

function updateKey(index, newKey) {
  const next = entries.value.slice()
  if (!next[index]) return
  next[index] = [newKey, next[index][1]]
  emitFromEntries(next)
}

function updateValue(index, newValue) {
  const next = entries.value.slice()
  if (!next[index]) return
  next[index] = [next[index][0], newValue]
  emitFromEntries(next)
}
</script>
