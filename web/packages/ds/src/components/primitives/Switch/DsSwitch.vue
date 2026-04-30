<script setup lang="ts">
/**
 * Switch — boolean on/off control. Replaces `<km-toggle>` for simple booleans.
 *
 *   <DsSwitch v-model="enabled" label="Notifications" />
 */

import { SwitchRoot, SwitchThumb } from 'reka-ui'
import { useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    /** Visible label. Pass an `id` if you render the label yourself. */
    label?: string
    disabled?: boolean
    size?: 'sm' | 'md' | 'lg'
    /** Additional id (auto-generated if omitted). */
    id?: string
  }>(),
  {
    size: 'md',
  },
)

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const generatedId = useId()
const inputId = props.id ?? generatedId
</script>

<template>
  <label class="ds-switch" :data-size="size" :data-disabled="disabled || undefined">
    <SwitchRoot
      :id="inputId"
      :model-value="modelValue ?? false"
      :disabled="disabled"
      class="ds-switch__root"
      data-test="ds-switch"
      @update:model-value="$emit('update:modelValue', $event as boolean)"
    >
      <SwitchThumb class="ds-switch__thumb" />
    </SwitchRoot>

    <span v-if="label" class="ds-switch__label">{{ label }}</span>
  </label>
</template>

<style>
.ds-switch {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  cursor: pointer;
  user-select: none;
}
.ds-switch[data-disabled] { cursor: not-allowed; opacity: 0.6; }

.ds-switch__root {
  position: relative;
  flex: none;
  inline-size: 36px;
  block-size: 20px;
  border-radius: var(--ds-radius-full);
  background: var(--ds-color-secondary);
  border: 0;
  cursor: inherit;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-switch__root:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
.ds-switch__root[data-state='checked'] {
  background: var(--ds-color-primary);
}

.ds-switch__thumb {
  display: block;
  inline-size: 16px;
  block-size: 16px;
  background: var(--ds-color-white);
  border-radius: 50%;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.16);
  transform: translateX(2px);
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-switch__thumb[data-state='checked'] {
  transform: translateX(18px);
}

.ds-switch[data-size='sm'] .ds-switch__root { inline-size: 28px; block-size: 16px; }
.ds-switch[data-size='sm'] .ds-switch__thumb { inline-size: 12px; block-size: 12px; transform: translateX(2px); }
.ds-switch[data-size='sm'] .ds-switch__thumb[data-state='checked'] { transform: translateX(14px); }

.ds-switch[data-size='lg'] .ds-switch__root { inline-size: 44px; block-size: 24px; }
.ds-switch[data-size='lg'] .ds-switch__thumb { inline-size: 20px; block-size: 20px; }
.ds-switch[data-size='lg'] .ds-switch__thumb[data-state='checked'] { transform: translateX(22px); }

.ds-switch__label {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
}
</style>
