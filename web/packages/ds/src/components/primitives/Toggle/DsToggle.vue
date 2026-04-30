<script setup lang="ts">
/**
 * Toggle — single on/off pressable button. Wraps reka-ui `<Toggle>`.
 *
 *   <DsToggle v-model="bold" aria-label="Bold"><BoldIcon /></DsToggle>
 */

import {
  Toggle as TogglePrimitive,
  type ToggleEmits,
  type ToggleProps,
  useForwardPropsEmits,
} from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'

export type DsToggleVariant = 'default' | 'outline'
export type DsToggleSize = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<
    ToggleProps & {
      variant?: DsToggleVariant
      size?: DsToggleSize
    }
  >(),
  {
    variant: 'default',
    size: 'md',
    disabled: false,
  },
)

const emit = defineEmits<ToggleEmits>()

const delegated = reactiveOmit(props, 'variant', 'size')
const forwarded = useForwardPropsEmits(delegated, emit)
</script>

<template>
  <TogglePrimitive
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-toggle"
    :data-variant="variant"
    :data-size="size"
    data-test="ds-toggle"
  >
    <slot v-bind="slotProps" />
  </TogglePrimitive>
</template>

<style>
.ds-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  flex: none;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  background: transparent;
  color: var(--ds-color-black);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-none);
  cursor: pointer;
  transition:
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-toggle:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.ds-toggle:hover {
  background: var(--ds-color-control-hover-bg);
  color: var(--ds-color-black);
}

.ds-toggle[data-state='on'] {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
}

.ds-toggle:disabled,
.ds-toggle[data-disabled] {
  opacity: 0.5;
  pointer-events: none;
}

.ds-toggle[data-variant='outline'] {
  border-color: var(--ds-color-border);
  background: transparent;
}

.ds-toggle > svg {
  flex: none;
  inline-size: 1em;
  block-size: 1em;
  pointer-events: none;
}

.ds-toggle[data-size='sm'] {
  block-size: 32px;
  min-inline-size: 32px;
  padding-inline: var(--ds-space-sm);
}
.ds-toggle[data-size='md'] {
  block-size: 36px;
  min-inline-size: 36px;
  padding-inline: var(--ds-space-md);
}
.ds-toggle[data-size='lg'] {
  block-size: 40px;
  min-inline-size: 40px;
  padding-inline: var(--ds-space-md);
}
</style>
