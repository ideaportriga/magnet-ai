<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="tool?.label || 'Tool Coming Soon'"
    confirm-label="Close"
    cancel-label=""
    size="sm"
    @update:model-value="$emit('update:modelValue', $event)"
    @confirm="$emit('update:modelValue', false)"
  >
    <div class="column items-center justify-center q-py-md text-center">
      <q-icon name="warning" color="orange-8" size="56px" class="q-mb-md" />
      <div class="km-heading-6 text-bold text-orange-9 q-mb-xs">Coming Soon</div>
      <div class="km-description text-secondary-text q-mt-xs" style="font-size: 17px">
        <div>This tool is part of the future retrieval toolkit.</div>
        <div class="text-weight-medium">It will not execute until support for this tool is implemented.</div>
      </div>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { KgDialogBase } from '../../common';

defineProps<{
  modelValue: boolean
  tool: any
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>
