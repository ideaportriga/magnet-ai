<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="tool?.label || m.knowledgeGraph_toolComingSoon()"
    :confirm-label="m.common_close()"
    cancel-label=""
    size="sm"
    @update:model-value="$emit('update:modelValue', $event)"
    @confirm="$emit('update:modelValue', false)"
  >
    <div class="column items-center justify-center q-py-md text-center">
      <q-icon name="warning" color="orange-8" size="56px" class="q-mb-md" />
      <div class="km-heading-6 text-bold text-orange-9 q-mb-xs">{{ m.common_comingSoon() }}</div>
      <div class="km-description km-body-lg text-secondary-text q-mt-xs">
        <div>{{ m.knowledgeGraph_toolComingSoonDesc() }}</div>
        <div class="text-weight-medium">{{ m.knowledgeGraph_toolComingSoonWarning() }}</div>
      </div>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { KgDialogBase } from '../../common';
import { m } from '@/paraglide/messages'

defineProps<{
  modelValue: boolean
  tool: any
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>
