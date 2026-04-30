<script setup lang="ts">
/**
 * InputGroupInput — `DsInput` configured to sit borderless inside a
 * `DsInputGroup` so the parent owns the chrome.
 */

import DsInput from '../Input/DsInput.vue'
import type { InputHTMLAttributes } from 'vue'

defineProps<{
  modelValue?: string | number
  defaultValue?: string | number
  type?: InputHTMLAttributes['type']
}>()

defineEmits<{
  'update:modelValue': [value: string | number]
}>()
</script>

<template>
  <DsInput
    v-bind="$attrs"
    :model-value="modelValue"
    :default-value="defaultValue"
    :type="type"
    class="ds-input-group__control"
    data-slot="input-group-control"
    data-test="ds-input-group-input"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<style>
.ds-input-group > .ds-input-group__control {
  flex: 1 1 auto;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
.ds-input-group > .ds-input-group__control:focus-visible {
  box-shadow: none;
  border-color: transparent;
}
</style>
