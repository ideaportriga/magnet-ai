<script setup lang="ts">
/**
 * `<km-switch>` — boolean on/off switch. Drop-in over `<DsSwitch>`.
 *
 * Public API (preserved): `modelValue`, `label`, `disable`, `size`,
 * `color`. The legacy CSS-length `size` (`32px`, etc.) is mapped to the
 * Ds size presets (`sm`/`md`/`lg`); `color` is forwarded as a `--ds-color-
 * primary` override so the toggle paints with any token (or raw colour).
 */

import { computed } from 'vue'
import DsSwitch from '../primitives/Switch/DsSwitch.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    label?: string
    disable?: boolean
    /** Either a Ds size preset (`sm`/`md`/`lg`) or a legacy CSS length. */
    size?: string
    /** Token name (`primary`, `success`, …) or any CSS colour. */
    color?: string
  }>(),
  {
    modelValue: false,
    disable: false,
    size: 'md',
    color: '',
  },
)

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

/** Normalise legacy `size` → Ds preset. */
const dsSize = computed<'sm' | 'md' | 'lg'>(() => {
  const s = props.size
  if (s === 'sm' || s === 'xs') return 'sm'
  if (s === 'lg' || s === 'xl' || s === '40px' || s === '48px') return 'lg'
  return 'md'
})

const overrideStyle = computed(() => {
  if (!props.color) return undefined
  return {
    '--ds-color-primary': resolveDsColor(props.color) ?? props.color,
  } as Record<string, string>
})
</script>

<template>
  <DsSwitch
    class="km-switch"
    :model-value="modelValue"
    :label="label"
    :disabled="disable"
    :size="dsSize"
    :style="overrideStyle"
    data-test="km-switch"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<style>
/* Inherits all visuals from .ds-switch. */
</style>
