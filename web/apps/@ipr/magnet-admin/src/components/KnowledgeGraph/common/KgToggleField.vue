<template>
  <div
    class="kg-toggle-field"
    :class="{
      'kg-toggle-field--active': modelValue,
      'kg-toggle-field--disabled': disabled,
    }"
    @click="toggle"
  >
    <div class="full-width cluster" data-wrap="no">
      <div class="flex-1">
        <div v-if="title" class="kg-toggle-field__title">{{ title }}</div>
        <div v-if="description" class="kg-toggle-field__description">{{ description }}</div>
      </div>
      <km-toggle
        :model-value="modelValue"
        :disable="disabled"
        dense
        class="ml-sm"
        @update:model-value="$emit('update:modelValue', $event)"
        @click.stop
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
interface Props {
  modelValue: boolean
  title?: string
  description?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const toggle = () => {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<style scoped>
.kg-toggle-field {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  transition:
    background 0.3s ease,
    border-color 0.3s ease;
}

.kg-toggle-field:hover:not(.kg-toggle-field--disabled) {
  border-color: var(--ds-color-control-hover-border);
  background: var(--ds-color-background);
}

.kg-toggle-field--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.kg-toggle-field__title {
  font-size: var(--ds-font-size-label);
  font-weight: 500;
  color: var(--ds-color-secondary);
  line-height: 1.3;
}

.kg-toggle-field__description {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-label);
  line-height: 1.4;
  margin-block-start: 2px;
}
</style>
