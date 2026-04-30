<script setup lang="ts">
/**
 * `<km-chips-input>` — multi-value tag/chip input. Two modes (legacy):
 *
 *   - `type="pick"` (default): pick from a fixed `options` list (Reka
 *     Combobox). Selecting toggles the value in/out of `modelValue`.
 *   - `type="add"` (free entry): user types and presses Enter (or clicks
 *     the trailing + icon) to add a string to `modelValue`.
 *
 * Public API preserves `type, modelValue, placeholder, options, noOptionText,
 * autogrow, height, maxHeight, minHeight, errorMessage, rules`.
 */

import { computed, ref, toRefs, useTemplateRef } from 'vue'
import useValidation from '@shared/composables/useValidation'
import KmGlyph from './KmGlyph.vue'

interface KmChipsOption {
  label?: string
  value?: unknown
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    type?: 'pick' | 'add'
    modelValue?: unknown[]
    placeholder?: string
    options?: KmChipsOption[] | string[]
    noOptionText?: string
    autogrow?: boolean
    height?: string
    maxHeight?: string
    minHeight?: string
    rules?: unknown
    errorMessage?: string
  }>(),
  {
    type: 'pick',
    modelValue: () => [],
    options: () => [],
    noOptionText: 'No options available',
    autogrow: false,
    height: '32px',
    maxHeight: 'unset',
    minHeight: '32px',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown[]]
  add: [value: string]
  pick: [option: unknown]
  remove: [option: unknown]
}>()

const { modelValue, rules } = toRefs(props)
const { errorMessage: ruleError } = useValidation(modelValue, rules)
const finalError = computed<string | undefined>(() => props.errorMessage || (ruleError.value as string) || undefined)

const inputRef = useTemplateRef<HTMLInputElement>('input')
const draft = ref('')

const normalisedOptions = computed<KmChipsOption[]>(() =>
  (props.options as unknown[]).map((opt) => (typeof opt === 'string' ? { label: opt, value: opt } : (opt as KmChipsOption))),
)

const filteredOptions = computed(() => {
  if (!draft.value) return normalisedOptions.value
  const needle = draft.value.toLowerCase()
  return normalisedOptions.value.filter((o) => String(o.label ?? '').toLowerCase().includes(needle))
})

function chipLabel(value: unknown): string {
  if (typeof value === 'string') return value
  if (value && typeof value === 'object') return ((value as KmChipsOption).label ?? String(value))
  return String(value)
}

function commit(next: unknown[]) {
  emit('update:modelValue', next)
}

function removeChip(value: unknown, index: number) {
  const next = props.modelValue.slice()
  next.splice(index, 1)
  commit(next)
  emit('remove', value)
}

function addFreeEntry() {
  const trimmed = draft.value.trim()
  if (!trimmed) return
  if (props.modelValue.includes(trimmed as never)) {
    draft.value = ''
    return
  }
  commit([...props.modelValue, trimmed])
  emit('add', trimmed)
  draft.value = ''
  inputRef.value?.focus()
}

function pickOption(option: KmChipsOption) {
  if (props.modelValue.includes(option as never) || props.modelValue.includes(option.value as never)) {
    return
  }
  commit([...props.modelValue, option])
  emit('pick', option)
  draft.value = ''
}

function onKeydown(event: KeyboardEvent) {
  if (props.type !== 'add') return
  if (event.key === 'Enter') {
    event.preventDefault()
    addFreeEntry()
  }
  if (event.key === 'Backspace' && !draft.value && props.modelValue.length) {
    const last = props.modelValue[props.modelValue.length - 1]
    removeChip(last, props.modelValue.length - 1)
  }
}
</script>

<template>
  <span
    class="km-chips-input"
    :data-state="finalError ? 'error' : undefined"
    :style="{ '--km-chips-height': height, '--km-chips-min-height': minHeight, '--km-chips-max-height': maxHeight }"
  >
    <div class="km-chips-input__control" @click="inputRef?.focus()">
      <span
        v-for="(value, index) in modelValue"
        :key="index"
        class="km-chips-input__chip"
        data-test="km-chips-input-chip"
      >
        {{ chipLabel(value) }}
        <button
          type="button"
          class="km-chips-input__remove"
          aria-label="Remove"
          data-test="km-chips-input-remove"
          @click.stop="removeChip(value, index)"
        >
          <KmGlyph name="close" size="14px" tone="brand" />
        </button>
      </span>

      <input
        ref="input"
        v-model="draft"
        class="km-chips-input__field"
        :placeholder="modelValue.length ? '' : placeholder"
        data-test="km-chips-input"
        @keydown="onKeydown"
      />

      <button
        v-if="type === 'add'"
        type="button"
        class="km-chips-input__add"
        aria-label="Add"
        data-test="km-chips-input-add"
        @click="addFreeEntry"
      >
        <KmGlyph name="add" size="18px" tone="seamless" />
      </button>
    </div>

    <ul v-if="type === 'pick' && filteredOptions.length" class="km-chips-input__options">
      <li
        v-for="opt in filteredOptions"
        :key="String(opt.value ?? opt.label)"
        class="km-chips-input__option"
        @click="pickOption(opt)"
      >
        {{ opt.label }}
      </li>
    </ul>
    <p v-if="type === 'pick' && !filteredOptions.length" class="km-chips-input__empty">
      {{ noOptionText }}
    </p>

    <p v-if="finalError" class="km-chips-input__error">{{ finalError }}</p>
  </span>
</template>

<style>
.km-chips-input { display: inline-flex; flex-direction: column; gap: var(--ds-space-2xs); inline-size: 100%; }

.km-chips-input__control {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-xs);
  min-block-size: var(--km-chips-min-height);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-field-radius);
  cursor: text;
}
.km-chips-input__control:focus-within { border-color: var(--ds-color-primary); }

.km-chips-input[data-state='error'] .km-chips-input__control {
  border-color: var(--ds-color-error);
  background: var(--ds-color-error-bg);
}

.km-chips-input__chip {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
  padding: 2px var(--ds-space-xs);
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  border-radius: var(--ds-radius-sm);
}
.km-chips-input__remove {
  display: inline-flex;
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
  color: inherit;
}

.km-chips-input__field {
  flex: 1 1 auto;
  min-inline-size: 4rem;
  border: 0;
  outline: none;
  background: transparent;
  font: inherit;
  color: inherit;
}

.km-chips-input__add {
  display: inline-flex;
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
  color: var(--ds-color-icon);
}

.km-chips-input__options {
  list-style: "";
  margin: 0;
  padding: 0;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  max-block-size: 200px;
  overflow: auto;
  background: var(--ds-color-panel-main-bg);
}
.km-chips-input__option {
  padding: var(--ds-space-xs) var(--ds-space-md);
  cursor: pointer;
}
.km-chips-input__option:hover { background: var(--ds-color-light); }

.km-chips-input__empty {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-placeholder);
  padding: var(--ds-space-md);
  margin: 0;
}

.km-chips-input__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  margin: 0;
}
</style>
