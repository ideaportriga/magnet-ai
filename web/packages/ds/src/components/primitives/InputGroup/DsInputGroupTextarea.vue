<script setup lang="ts">
/**
 * InputGroupTextarea — `DsTextarea` configured to sit borderless inside a
 * `DsInputGroup` (e.g. for chat-style composers with leading/trailing addons).
 */

import DsTextarea from '../Textarea/DsTextarea.vue'

defineProps<{
  modelValue?: string | number
  defaultValue?: string | number
}>()

defineEmits<{
  'update:modelValue': [value: string | number]
}>()
</script>

<template>
  <DsTextarea
    v-bind="$attrs"
    :model-value="modelValue"
    :default-value="defaultValue"
    class="ds-input-group__control"
    data-slot="input-group-control"
    data-test="ds-input-group-textarea"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<style>
.ds-input-group > .ds-input-group__control[data-test='ds-input-group-textarea'] {
  flex: 1 1 auto;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  resize: none;
  padding-block: var(--ds-space-md);
}
.ds-input-group > .ds-input-group__control[data-test='ds-input-group-textarea']:focus-visible {
  box-shadow: none;
  border-color: transparent;
}
</style>
