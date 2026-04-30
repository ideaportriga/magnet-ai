<script setup lang="ts">
/**
 * `<km-radio>` — single radio item. Drop-in for the legacy:
 *
 *   <km-radio v-model="answer" :val="'yes'" label="Yes" />
 *
 * Public API (preserved): `modelValue`, `val`, `label`, `name`, `disable`,
 * `dense`.
 *
 * A single radio inside `<DsRadioGroup>` is awkward (DsRadioGroup expects
 * an `items` array), so we render Reka UI's `RadioGroupRoot` +
 * `RadioGroupItem` directly and reuse the `.ds-radio` / `.ds-radio__root`
 * styles emitted by `DsRadioGroup` so this looks identical. The Root is
 * driven from `modelValue === val ? val : ''` so a controlled single-item
 * group emits a clean update when toggled on.
 */

import { computed, useId } from 'vue'
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

const props = withDefaults(
  defineProps<{
    modelValue?: string | number | boolean | null
    /** The value this radio represents. */
    val?: string | number | boolean
    label?: string
    name?: string
    disable?: boolean
    dense?: boolean
  }>(),
  {
    val: undefined,
    name: undefined,
    label: undefined,
    disable: false,
    dense: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | number | boolean | null]
}>()

const generatedId = useId()
const groupName = computed(() => props.name ?? generatedId)

const checked = computed(() => props.modelValue === props.val)

/** Stringify the val for Reka, which works in `string` space. */
const itemKey = computed(() => String(props.val ?? '__km_radio__'))
const groupValue = computed<string | undefined>(() =>
  checked.value ? itemKey.value : undefined,
)

function onUpdate(next: string | string[]) {
  if (props.disable) return
  // Reka emits the new selection or `''` when toggled off; we always emit
  // `props.val` because the legacy Quasar contract only supports clicking
  // an unchecked radio (radios cannot be unchecked individually).
  if (typeof next === 'string' && next === itemKey.value) {
    emit('update:modelValue', props.val ?? null)
  }
}
</script>

<template>
  <RadioGroupRoot
    :model-value="groupValue"
    :name="groupName"
    :disabled="disable"
    class="km-radio-group"
    data-test="km-radio"
    @update:model-value="onUpdate"
  >
    <label
      class="ds-radio km-radio"
      :data-checked="checked ? 'true' : undefined"
      :data-disabled="disable ? 'true' : undefined"
      :data-dense="dense ? 'true' : undefined"
    >
      <RadioGroupItem
        :value="itemKey"
        :disabled="disable"
        class="ds-radio__root km-radio__root"
      >
        <span class="ds-radio__indicator" />
      </RadioGroupItem>
      <span v-if="label || $slots.default" class="ds-radio__label km-radio__label">
        <slot>{{ label }}</slot>
      </span>
    </label>
  </RadioGroupRoot>
</template>

<style>
.km-radio-group { display: inline-flex; }
.km-radio { cursor: pointer; }
.km-radio[data-disabled='true'] { cursor: not-allowed; opacity: 0.6; }
.km-radio[data-dense='true'] { font-size: var(--ds-font-size-caption); }
.km-radio[data-dense='true'] .km-radio__root { inline-size: 14px; block-size: 14px; }
</style>
