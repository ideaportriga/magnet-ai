<script setup lang="ts">
/**
 * Radio group — accepts an array of options. For richer layouts (icon next
 * to label, descriptions) use the Reka primitives directly.
 */

import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'
import { useId } from 'vue'

export interface DsRadioOption {
  value: string
  label: string
  disabled?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue?: string
    options: DsRadioOption[]
    name?: string
    disabled?: boolean
    orientation?: 'horizontal' | 'vertical'
  }>(),
  {
    orientation: 'vertical',
  },
)

defineEmits<{
  'update:modelValue': [value: string]
}>()

const generatedId = useId()
const groupName = props.name ?? generatedId
</script>

<template>
  <RadioGroupRoot
    :model-value="modelValue"
    :name="groupName"
    :disabled="disabled"
    :orientation="orientation"
    class="ds-radio-group"
    :class="orientation === 'horizontal' ? 'cluster gap-md' : 'stack'"
    data-test="ds-radio-group"
    @update:model-value="$emit('update:modelValue', $event as string)"
  >
    <label
      v-for="opt in options"
      :key="opt.value"
      class="ds-radio"
      :data-disabled="(opt.disabled || disabled) || undefined"
    >
      <RadioGroupItem
        :value="opt.value"
        :disabled="opt.disabled || disabled"
        class="ds-radio__root"
      >
        <span class="ds-radio__indicator" />
      </RadioGroupItem>
      <span class="ds-radio__label">{{ opt.label }}</span>
    </label>
  </RadioGroupRoot>
</template>

<style>
.ds-radio-group { display: inline-flex; }
.ds-radio-group[data-orientation='vertical'] { flex-direction: column; gap: var(--ds-space-sm); align-items: flex-start; }

.ds-radio {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  cursor: pointer;
  user-select: none;
}
.ds-radio[data-disabled] { cursor: not-allowed; opacity: 0.6; }

.ds-radio__root {
  position: relative;
  inline-size: 16px;
  block-size: 16px;
  border-radius: 50%;
  border: 1.5px solid var(--ds-color-border-2);
  background: var(--ds-color-white);
  cursor: inherit;
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-radio__root:hover { border-color: var(--ds-color-primary); }
.ds-radio__root[data-state='checked'] { border-color: var(--ds-color-primary); }
.ds-radio__root:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; }

.ds-radio__indicator {
  display: block;
  inline-size: 8px;
  block-size: 8px;
  border-radius: 50%;
  background: var(--ds-color-primary);
  transform: translate(-50%, -50%) scale(0);
  position: absolute;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-radio__root[data-state='checked'] .ds-radio__indicator {
  transform: translate(-50%, -50%) scale(1);
}

.ds-radio__label { font-size: var(--ds-font-size-label); color: var(--ds-color-black); }
</style>
