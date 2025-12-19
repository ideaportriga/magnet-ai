<template>
  <q-btn-toggle
    :model-value="modelValue"
    class="kg-section-control"
    no-caps
    rounded
    unelevated
    toggle-color="primary"
    color="grey-3"
    text-color="grey-8"
    dense
    :options="options"
    :disable="disabled"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup lang="ts">
export type ControlOption = {
  label: string
  value: string
}

interface Props {
  modelValue: string
  options?: ControlOption[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [
    { label: 'Agent decides', value: 'agent' },
    { label: 'Static', value: 'configuration' },
  ],
  disabled: false,
})

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<style scoped>
.kg-section-control :deep(.q-btn) {
  padding: 4px 8px;
  min-height: 24px;
  font-size: 12px;
  font-weight: 500;
}

.kg-section-control :deep(.q-btn .block) {
  font-size: 12px;
}
</style>

