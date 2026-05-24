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
    :options="toggleOptions"
    :disable="disabled"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template v-for="opt in options" :key="opt.value" #[opt.value]>
      <q-tooltip v-if="opt.hint" :delay="300">{{ opt.hint }}</q-tooltip>
    </template>
  </q-btn-toggle>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type ControlOption = {
  label: string
  value: string
  hint?: string
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

const toggleOptions = computed(() =>
  props.options.map((opt) => ({
    label: opt.label,
    value: opt.value,
    slot: opt.hint ? opt.value : undefined,
  }))
)
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
