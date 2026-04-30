<script setup lang="ts">
/**
 * `<km-toggle>` — boolean on/off switch (legacy Quasar `<q-toggle>` shape).
 *
 * Public API (preserved): `modelValue`, `label`, `disable`, `size`,
 * `tone`, `color`, plus `errorMessage` for inline validation hints.
 *
 * Renders `<DsSwitch>`; the legacy file already wrapped DsSwitch — this
 * version keeps the same shape but forwards `label` through (instead of
 * relying on a sibling label element) and propagates `color` as a CSS-var
 * override. This is a single boolean toggle, *not* a press-button toggle,
 * so we use DsSwitch (not DsToggle).
 */

import { computed } from 'vue'
import DsSwitch from '../primitives/Switch/DsSwitch.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

export type KmToggleTone = 'brand' | 'warning'

const toneColorMap: Record<KmToggleTone, string> = {
  brand: 'var(--ds-color-primary)',
  warning: 'var(--ds-color-warning-text)',
}

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    /** Visible label rendered next to the switch. */
    label?: string
    /** Semantic active colour intent. Legacy `color` wins when present. */
    tone?: KmToggleTone
    /** Token name (e.g. `primary`, `success`). */
    color?: string
    /** Size preset; legacy default was `'sm'`. */
    size?: 'sm' | 'md' | 'lg'
    disable?: boolean
    errorMessage?: string
  }>(),
  {
    modelValue: false,
    label: '',
    tone: 'brand',
    color: '',
    size: 'sm',
    disable: false,
    errorMessage: '',
  },
)

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const overrideStyle = computed(() => {
  if (props.color && props.color !== 'primary') {
    return {
      '--ds-color-primary': resolveDsColor(props.color) ?? props.color,
    } as Record<string, string>
  }
  if (!props.tone || props.tone === 'brand') return undefined
  return {
    '--ds-color-primary': toneColorMap[props.tone],
  } as Record<string, string>
})
</script>

<template>
  <span class="km-toggle">
    <DsSwitch
      :model-value="modelValue"
      :disabled="disable"
      :size="size"
      :label="label"
      :style="overrideStyle"
      data-test="km-toggle"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <span v-if="errorMessage" class="km-toggle__error">{{ errorMessage }}</span>
  </span>
</template>

<style>
.km-toggle {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
}
.km-toggle__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
  padding: var(--ds-space-2xs) var(--ds-space-2xs) 0;
  white-space: nowrap;
}
</style>
