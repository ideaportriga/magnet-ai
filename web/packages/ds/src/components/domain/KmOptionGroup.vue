<script setup lang="ts">
/**
 * `<km-option-group v-model :options>` — group of radios (single select)
 * or checkboxes (multi select). Replaces Quasar's `<q-option-group>`.
 *
 * `type="radio"`  → `modelValue` is a single value.
 * `type="checkbox"` → `modelValue` is an array.
 */
import { computed } from 'vue'
import KmRadio from './KmRadio.vue'
import KmCheckbox from './KmCheckbox.vue'

export interface KmOptionGroupOption {
  label: string
  value: string | number | boolean
  disable?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue?: unknown
    options: KmOptionGroupOption[]
    type?: 'radio' | 'checkbox' | 'toggle'
    inline?: boolean
    name?: string
    color?: string
  }>(),
  { type: 'radio', inline: false, name: undefined, color: undefined },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

function setRadio(value: unknown) {
  emit('update:modelValue', value)
}
function toggleCheckbox(value: unknown, checked: boolean) {
  const arr = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  const idx = arr.indexOf(value)
  if (checked && idx === -1) arr.push(value)
  if (!checked && idx !== -1) arr.splice(idx, 1)
  emit('update:modelValue', arr)
}
function isChecked(value: unknown): boolean {
  if (props.type === 'radio') return props.modelValue === value
  return Array.isArray(props.modelValue) && props.modelValue.includes(value as never)
}
// Cast needed by KmRadio's :model-value prop; done here to avoid the
// `vue/no-deprecated-filter` ESLint rule from misreading the inline
// TypeScript union-type `|` as a Vue 2 filter pipe.
const radioValue = computed(() => props.modelValue as string | number | boolean | null)
</script>

<template>
  <div
    class="km-option-group"
    :data-inline="inline ? 'true' : undefined"
    role="group"
  >
    <template v-for="opt in options" :key="String(opt.value)">
      <KmRadio
        v-if="type === 'radio'"
        :model-value="radioValue"
        :val="opt.value"
        :name="name"
        :label="opt.label"
        :disable="opt.disable"
        @update:model-value="setRadio($event)"
      />
      <label v-else class="km-option-group__checkbox-row">
        <KmCheckbox
          :model-value="isChecked(opt.value)"
          :disable="opt.disable"
          @update:model-value="toggleCheckbox(opt.value, !!$event)"
        />
        <span>{{ opt.label }}</span>
      </label>
    </template>
  </div>
</template>

<style>
.km-option-group {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-xs, 4px);
}
.km-option-group[data-inline='true'] {
  flex-flow: row wrap;
  gap: var(--ds-space-md, 12px);
}
.km-option-group__checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm, 8px);
  cursor: pointer;
  user-select: none;
}
</style>
