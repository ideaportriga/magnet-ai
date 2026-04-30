<script setup lang="ts">
/**
 * `<km-checkbox>` — drop-in for the legacy Checkbox.
 *
 * Public API (preserved): `modelValue, val, chipped, displayText, label,
 * chipColor, chipFontColor, disable, indeterminate, color, size,
 * textMaxWidth, isAlignTop`. Renders `<DsCheckbox>` and translates legacy
 * prop names. The `chipped` variant renders the label as a soft pill —
 * useful in tag-style filter lists.
 */

import { computed } from 'vue'
import DsCheckbox from '../primitives/Checkbox/DsCheckbox.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean | 'indeterminate' | unknown[]
    /** Group value when used inside a multi-checkbox set (legacy). */
    val?: unknown
    /** Label (alternate prop name; `displayText` is the legacy spelling). */
    label?: string
    chipped?: boolean
    displayText?: string
    chipColor?: string
    chipFontColor?: string
    disable?: boolean
    /** Force indeterminate visual independent of `modelValue`. */
    indeterminate?: boolean
    /** Token name (`primary`, `success`, …) — overrides primary tint. */
    color?: string
    /** Legacy CSS-length size (e.g. `32px`). Mapped to Ds size presets. */
    size?: string
    textMaxWidth?: number
    isAlignTop?: boolean
  }>(),
  {
    chipped: false,
    displayText: '',
    chipColor: '#D1D1D1',
    chipFontColor: 'var(--ds-color-gray-600)',
    disable: false,
    indeterminate: false,
    size: '32px',
    textMaxWidth: 999_999,
    isAlignTop: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean | 'indeterminate' | unknown[]]
}>()

const isGroup = computed(() => Array.isArray(props.modelValue))

/** Translate legacy `modelValue` (boolean | 'indeterminate' | array) to
 *  DsCheckbox's `boolean | 'indeterminate'`. */
const dsValue = computed<boolean | 'indeterminate'>(() => {
  if (props.indeterminate) return 'indeterminate'
  if (isGroup.value) return (props.modelValue as unknown[]).includes(props.val)
  if (props.modelValue === 'indeterminate') return 'indeterminate'
  return props.modelValue === true
})

/** Map legacy CSS-length `size` to DsCheckbox's `sm`/`md`/`lg`. */
const dsSize = computed<'sm' | 'md' | 'lg'>(() => {
  const s = props.size
  if (s === 'sm' || s === 'xs') return 'sm'
  if (s === 'lg' || s === 'xl' || s === '40px' || s === '48px') return 'lg'
  return 'md'
})

/* `color="primary"` is the default DsCheckbox uses, so resolving it here
 * would write `--ds-color-primary: var(--ds-color-primary)` — a CSS custom-
 * property cycle that the engine resolves to the guaranteed-invalid value,
 * leaving the checkbox background transparent (looks white on light rows
 * and disappears on coloured rows). Skip the override in that case. */
const overrideStyle = computed(() => {
  if (!props.color || props.color === 'primary') return undefined
  const resolved = resolveDsColor(props.color) ?? props.color
  if (resolved === 'var(--ds-color-primary)') return undefined
  return { '--ds-color-primary': resolved } as Record<string, string>
})

function handleUpdate(next: boolean | 'indeterminate') {
  if (isGroup.value) {
    const list = (props.modelValue as unknown[]).slice()
    const idx = list.indexOf(props.val)
    if (next === true && idx === -1) list.push(props.val)
    if (next !== true && idx !== -1) list.splice(idx, 1)
    emit('update:modelValue', list)
    return
  }
  emit('update:modelValue', next)
}
</script>

<template>
  <span
    class="km-checkbox"
    :data-align-top="isAlignTop ? 'true' : undefined"
    :data-disabled="disable ? 'true' : undefined"
    :style="overrideStyle"
  >
    <DsCheckbox
      :model-value="dsValue"
      :disabled="disable"
      :size="dsSize"
      data-test="km-checkbox"
      @update:model-value="handleUpdate"
    />

    <slot>
      <span
        v-if="chipped"
        class="km-checkbox__chip"
        :style="{ background: chipColor, color: chipFontColor }"
      >
        {{ displayText || label }}
      </span>
      <span
        v-else-if="displayText || label"
        class="km-checkbox__label"
        :style="{ maxWidth: `${textMaxWidth}px` }"
      >
        {{ displayText || label }}
      </span>
    </slot>
  </span>
</template>

<style>
.km-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  cursor: pointer;
  user-select: none;
}
.km-checkbox[data-align-top='true'] { align-items: flex-start; }
.km-checkbox[data-disabled='true'] { cursor: not-allowed; opacity: 0.6; }

.km-checkbox__chip {
  padding: var(--ds-space-2xs) var(--ds-space-md);
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-caption);
  white-space: nowrap;
}
.km-checkbox__label {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-secondary-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
