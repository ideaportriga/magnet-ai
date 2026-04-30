<script setup lang="ts">
/**
 * Checkbox — supports indeterminate state via `indeterminate` prop.
 *
 *   <DsCheckbox v-model="agreed" label="I accept the terms" />
 */

import { CheckboxIndicator, CheckboxRoot } from 'reka-ui'
import { useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean | 'indeterminate'
    label?: string
    disabled?: boolean
    size?: 'sm' | 'md' | 'lg'
    id?: string
  }>(),
  {
    size: 'md',
  },
)

defineEmits<{
  'update:modelValue': [value: boolean | 'indeterminate']
}>()

const generatedId = useId()
const inputId = props.id ?? generatedId
</script>

<template>
  <label class="ds-checkbox" :data-size="size" :data-disabled="disabled || undefined">
    <CheckboxRoot
      :id="inputId"
      :model-value="modelValue ?? false"
      :disabled="disabled"
      class="ds-checkbox__root"
      data-test="ds-checkbox"
      @update:model-value="$emit('update:modelValue', $event as boolean | 'indeterminate')"
    >
      <CheckboxIndicator class="ds-checkbox__indicator">
        <svg
          v-if="modelValue === true"
          viewBox="0 0 14 14"
          width="100%"
          height="100%"
          aria-hidden="true"
        >
          <path
            d="M2.5 7.5 L5.5 10.5 L11.5 4.5"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span v-else-if="modelValue === 'indeterminate'" class="ds-checkbox__dash" aria-hidden="true" />
      </CheckboxIndicator>
    </CheckboxRoot>

    <span v-if="label" class="ds-checkbox__label">{{ label }}</span>
  </label>
</template>

<style>
.ds-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  cursor: pointer;
  user-select: none;
}
.ds-checkbox[data-disabled] { cursor: not-allowed; opacity: 0.6; }

.ds-checkbox__root {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 16px;
  block-size: 16px;
  border-radius: var(--ds-radius-xs);
  border: 1.5px solid var(--ds-color-border-2);
  background: var(--ds-color-white);
  cursor: inherit;
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-checkbox__root:hover { border-color: var(--ds-color-primary); }
.ds-checkbox__root[data-state='checked'],
.ds-checkbox__root[data-state='indeterminate'] {
  background: var(--ds-color-primary);
  border-color: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.ds-checkbox__root:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.ds-checkbox[data-size='sm'] .ds-checkbox__root { inline-size: 14px; block-size: 14px; }
.ds-checkbox[data-size='lg'] .ds-checkbox__root { inline-size: 20px; block-size: 20px; }

.ds-checkbox__indicator {
  inline-size: 100%;
  block-size: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.ds-checkbox__dash {
  inline-size: 60%;
  block-size: 2px;
  background: currentColor;
  border-radius: var(--ds-radius-full);
}

.ds-checkbox__label {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
}
</style>
