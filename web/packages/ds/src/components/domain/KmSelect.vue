<script setup lang="ts">
/**
 * `<km-select>` — drop-in replacement for the legacy multi-feature select.
 *
 * Public API (preserved 1:1 for ~342 admin call-sites):
 *   modelValue, options, placeholder, permanentPlaceholder, multiple, useChips,
 *   optionLabel, optionValue, emitValue, mapOptions, disabled, height,
 *   minHeight, maxWidth, iconBefore, hasDropdownSearch, searchLabel,
 *   noOptionText, selectAll, selectAllLabel, selectedSuffix,
 *   nothingSelectedLabel, bgColor, rules, errorMessage
 *
 * Internally:
 *   - Simple single-value path renders `<DsSelect>` (the new cube-CSS
 *     primitive) so styling and a11y stay consistent with the design system.
 *   - Advanced paths (multiple, dropdown-search, select-all, slot rendering of
 *     options) fall back to Reka's Combobox primitive with the same look.
 *
 * Slots: `option` (per-option custom render), `selected` (custom selected
 * label area).
 */

import { computed, ref, toRefs, useTemplateRef, watch } from 'vue'
import useValidation from '@shared/composables/useValidation'
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxTrigger,
  ComboboxViewport,
} from 'reka-ui'
import DsSelect, { type DsSelectOption } from '../primitives/Select/DsSelect.vue'
import KmGlyph from './KmGlyph.vue'
import KmCheckbox from './KmCheckbox.vue'
import KmChip from './KmChip.vue'
import KmSeparator from './KmSeparator.vue'

interface KmSelectOption {
  label?: string
  value?: unknown
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    modelValue?: unknown
    options?: KmSelectOption[] | string[]
    placeholder?: string
    permanentPlaceholder?: string
    multiple?: boolean
    useChips?: boolean
    optionLabel?: string
    optionValue?: string
    emitValue?: boolean
    mapOptions?: boolean
    disable?: boolean
    disabled?: boolean
    readonly?: boolean
    height?: string
    minHeight?: string
    maxWidth?: string
    iconBefore?: string
    hasDropdownSearch?: boolean
    searchLabel?: string
    noOptionText?: string
    selectAll?: boolean
    selectAllLabel?: string
    selectedSuffix?: string
    nothingSelectedLabel?: string
    bgColor?: string
    dense?: boolean
    outlined?: boolean
    loading?: boolean
    displayValue?: string
    popupContentClass?: string | string[] | Record<string, boolean>
    rules?: unknown
    errorMessage?: string
  }>(),
  {
    options: () => [],
    placeholder: '',
    multiple: false,
    useChips: false,
    optionLabel: 'label',
    optionValue: 'value',
    emitValue: false,
    mapOptions: false,
    height: 'var(--ds-field-height)',
    minHeight: 'var(--ds-field-height)',
    maxWidth: 'none',
    searchLabel: 'Search',
    noOptionText: 'No options available',
    selectAllLabel: 'Select all',
    selectedSuffix: 'selected',
    nothingSelectedLabel: '—',
    bgColor: 'control-bg',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  'popup-show': []
  'popup-hide': []
}>()

const slots = defineSlots<{
  option?: (props: { opt: KmSelectOption, selected: boolean, toggleOption: () => void }) => unknown
  selected?: (props: { value: unknown, label: string }) => unknown
  append?: () => unknown
  'before-options'?: () => unknown
  'no-option'?: () => unknown
}>()

const { modelValue, rules } = toRefs(props)
const { errorMessage: ruleError } = useValidation(modelValue, rules)

const finalError = computed<string | undefined>(
  () => props.errorMessage || (ruleError.value as string) || undefined,
)

const open = ref(false)
const searchValue = ref('')
const searchInputRef = useTemplateRef<HTMLInputElement>('searchInput')

const isDisabled = computed(() => Boolean(props.disabled || props.disable || props.readonly || props.loading))

const normalisedOptions = computed<KmSelectOption[]>(() =>
  (props.options as unknown[]).map((opt) =>
    typeof opt === 'string' ? { label: opt, value: opt } : (opt as KmSelectOption),
  ),
)

const filteredOptions = computed(() => {
  if (!props.hasDropdownSearch || !searchValue.value) return normalisedOptions.value
  const needle = searchValue.value.toLowerCase()
  return normalisedOptions.value.filter((opt) =>
    String(opt[props.optionLabel] ?? opt.label ?? '').toLowerCase().includes(needle),
  )
})

const selectedSet = computed(() => {
  if (!props.multiple) return new Set<unknown>()
  if (!Array.isArray(props.modelValue)) return new Set<unknown>()
  if (props.emitValue) return new Set(props.modelValue as unknown[])
  return new Set((props.modelValue as KmSelectOption[]).map((o) => o[props.optionValue]))
})

const isAllSelected = computed(() => {
  if (!props.multiple) return false
  return (
    normalisedOptions.value.length > 0
    && normalisedOptions.value.every((o) => selectedSet.value.has(o[props.optionValue]))
  )
})

/**
 * Selected items resolved to `{ value, label }` pairs, used to render the
 * removable chips inside the trigger when `multiple && useChips`. Falls
 * back to the raw value when no matching option is found in `options`
 * (catalog hasn't loaded yet, or the value was set externally).
 */
interface SelectedChipItem {
  key: string
  label: string
  /** Raw selection entry — passed back to `handleSelect` to deselect. */
  raw: KmSelectOption | unknown
}

const selectedChipItems = computed<SelectedChipItem[]>(() => {
  if (!props.multiple || !Array.isArray(props.modelValue)) return []
  return (props.modelValue as unknown[]).map((entry) => {
    if (props.emitValue) {
      const match = normalisedOptions.value.find(
        (o) => o[props.optionValue] === entry,
      )
      const label = match
        ? String(match[props.optionLabel] ?? match.label ?? entry)
        : String(entry)
      return { key: String(entry), label, raw: entry }
    }
    const opt = entry as KmSelectOption
    const label = String(opt?.[props.optionLabel] ?? opt?.label ?? '')
    return {
      key: String(opt?.[props.optionValue] ?? label),
      label,
      raw: entry,
    }
  })
})

function removeSelectedChip(item: SelectedChipItem) {
  // Build a synthetic option whose [optionValue] field matches the entry,
  // so `handleSelect` can find and toggle it off.
  const optKey = props.emitValue ? item.raw : (item.raw as KmSelectOption)[props.optionValue]
  const synthetic: KmSelectOption = { [props.optionValue]: optKey, [props.optionLabel]: item.label }
  handleSelect(synthetic)
}

const triggerLabel = computed(() => {
  if (props.displayValue) return props.displayValue
  if (
    props.modelValue == null
    || props.modelValue === ''
    || (Array.isArray(props.modelValue) && props.modelValue.length === 0)
  ) {
    return props.permanentPlaceholder || props.placeholder || ''
  }
  if (Array.isArray(props.modelValue)) {
    if (props.modelValue.length === 1) {
      const first = props.modelValue[0] as KmSelectOption | string
      return typeof first === 'string' ? first : (first[props.optionLabel] as string)
    }
    return `${props.modelValue.length} ${props.selectedSuffix}`
  }
  if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    return ((props.modelValue as KmSelectOption)[props.optionLabel] as string) ?? ''
  }
  // Primitive value — find matching option for label, fall back to raw value.
  const match = normalisedOptions.value.find(
    (o) => o[props.optionValue] === props.modelValue,
  )
  if (match) return (match[props.optionLabel] as string) ?? String(props.modelValue)
  return String(props.modelValue)
})

/**
 * "Simple mode" lets us delegate fully to `<DsSelect>` — no multi-select,
 * no in-dropdown search, no select-all, no `option`/`selected` slot, no
 * icon prefix, no permanent placeholder, no chips. Everything else needs
 * the richer Combobox-based path.
 */
const useSimpleMode = computed(
  () =>
    !props.multiple
    && !props.hasDropdownSearch
    && !props.selectAll
    && !props.useChips
    && !props.iconBefore
    && !props.permanentPlaceholder
    && !slots.option
    && !slots.selected
    && !slots.append
    && !slots['before-options']
    && !slots['no-option'],
)

const dsOptions = computed<DsSelectOption[]>(() =>
  normalisedOptions.value.map((opt) => {
    const value = String(opt[props.optionValue] ?? opt.value ?? '')
    const label = String(opt[props.optionLabel] ?? opt.label ?? '')
    return {
      value,
      label: label || (value === '' ? props.nothingSelectedLabel : ''),
      disabled: Boolean(opt.disable || opt.disabled),
    }
  }),
)

const dsModelValue = computed<string | undefined>(() => {
  if (props.modelValue == null || props.modelValue === '') return undefined
  if (typeof props.modelValue === 'object') {
    const v = (props.modelValue as KmSelectOption)[props.optionValue]
    return v == null ? undefined : String(v)
  }
  return String(props.modelValue)
})

function emitFromDs(next: string) {
  if (props.emitValue) {
    emit('update:modelValue', next)
    return
  }
  const matchIndex = normalisedOptions.value.findIndex(
    (o) => String(o[props.optionValue] ?? o.value ?? '') === next,
  )
  const match = matchIndex >= 0 ? normalisedOptions.value[matchIndex] : undefined
  const originalOption = (props.options as unknown[])[matchIndex]
  if (typeof originalOption === 'string') {
    emit('update:modelValue', next)
    return
  }
  emit('update:modelValue', match ?? next)
}

function handleSelect(option: KmSelectOption) {
  const value = props.emitValue ? option[props.optionValue] : option

  if (!props.multiple) {
    emit('update:modelValue', value)
    open.value = false
    return
  }

  const current = Array.isArray(props.modelValue) ? props.modelValue.slice() : []
  const optKey = option[props.optionValue]
  const idx = current.findIndex((item) => {
    const v = props.emitValue ? item : (item as KmSelectOption)[props.optionValue]
    return v === optKey
  })
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(value as never)
  }
  emit('update:modelValue', current)
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    emit('update:modelValue', [])
  } else {
    const next = normalisedOptions.value.map((o) =>
      props.emitValue ? o[props.optionValue] : o,
    )
    emit('update:modelValue', next)
  }
}

function emptySearchDisplayValue() {
  return ''
}

function handleOpenUpdate(next: boolean) {
  open.value = next
}

watch(open, (next) => {
  if (next) {
    emit('popup-show')
  } else {
    emit('popup-hide')
  }
  if (next && props.hasDropdownSearch) {
    queueMicrotask(() => {
      if (typeof searchInputRef.value?.focus === 'function') searchInputRef.value.focus()
    })
  }
  if (!next) searchValue.value = ''
})
</script>

<template>
  <span
    class="km-select"
    :data-state="finalError ? 'error' : open ? 'open' : undefined"
    :data-disabled="isDisabled ? 'true' : undefined"
    :style="{
      maxWidth,
      '--km-select-height': height,
      '--km-select-min-height': minHeight,
    }"
  >
    <!-- Simple path: delegate fully to <DsSelect>. -->
    <DsSelect
      v-if="useSimpleMode"
      class="km-select__ds"
      :model-value="dsModelValue"
      :options="dsOptions"
      :placeholder="placeholder"
      :disabled="isDisabled"
      :size="dense ? 'sm' : 'md'"
      data-test="km-select"
      @update:model-value="emitFromDs"
    />

    <!-- Advanced path: multi-select / search / select-all / custom slots. -->
    <ComboboxRoot
      v-else
      :open="open"
      :model-value="modelValue"
      :multiple="multiple"
      :disabled="isDisabled"
      class="km-select__root"
      @update:open="handleOpenUpdate"
    >
      <ComboboxAnchor as-child>
        <ComboboxTrigger class="km-select__trigger" data-test="km-select">
          <span v-if="iconBefore" class="km-select__prefix">
            <KmGlyph :name="iconBefore" size="18px" />
          </span>

          <span class="km-select__value">
            <slot name="selected" :value="modelValue" :label="triggerLabel">
              <span
                v-if="modelValue == null || modelValue === '' || (Array.isArray(modelValue) && modelValue.length === 0)"
                class="km-select__placeholder"
              >
                {{ permanentPlaceholder || placeholder }}
              </span>
              <!-- Multi-select with `useChips`: render each selection as a
                   removable chip. Click anywhere on the trigger still opens
                   the dropdown, but the chip's × button stops propagation
                   and only deselects that one entry. -->
              <span
                v-else-if="multiple && useChips"
                class="km-select__chips"
              >
                <KmChip
                  v-for="chip in selectedChipItems"
                  :key="chip.key"
                  class="km-select__chip"
                  display="input-token"
                  tone="brand"
                  removable
                  dense
                  :label="chip.label"
                  @remove="removeSelectedChip(chip)"
                />
              </span>
              <span v-else>{{ triggerLabel }}</span>
            </slot>
          </span>

          <KmGlyph
            class="km-select__chevron"
            name="chevron-down"
            size="20px"
          />

          <span v-if="$slots.append" class="km-select__append">
            <slot name="append" />
          </span>
        </ComboboxTrigger>
      </ComboboxAnchor>

      <ComboboxPortal>
        <ComboboxContent
          :class="['km-select__content', popupContentClass]"
          :side-offset="4"
          position="popper"
        >
          <div v-if="hasDropdownSearch" class="km-select__search">
            <ComboboxInput
              ref="searchInput"
              v-model="searchValue"
              :display-value="emptySearchDisplayValue"
              :placeholder="searchLabel"
              class="km-select__search-input"
            />
            <KmGlyph name="search" size="18px" />
          </div>

          <KmSeparator v-if="hasDropdownSearch" />

          <slot name="before-options" />

          <div v-if="multiple && selectAll" class="km-select__select-all">
            <KmCheckbox :model-value="isAllSelected" @update:model-value="toggleSelectAll">
              <span>{{ selectAllLabel }}</span>
            </KmCheckbox>
            <KmSeparator />
          </div>

          <ComboboxViewport class="km-select__viewport">
            <ComboboxEmpty class="km-select__empty">
              <slot name="no-option">
                {{ noOptionText }}
              </slot>
            </ComboboxEmpty>

            <ComboboxGroup>
              <ComboboxItem
                v-for="opt in filteredOptions"
                :key="String(opt[optionValue] ?? opt.label)"
                :value="opt[optionValue] ?? opt"
                class="km-select__item"
                :data-selected="selectedSet.has(opt[optionValue]) ? 'true' : undefined"
                data-test="km-select-item"
                @select="(event) => { event.preventDefault(); handleSelect(opt) }"
              >
                <KmCheckbox
                  v-if="multiple"
                  :model-value="selectedSet.has(opt[optionValue])"
                  @update:model-value="handleSelect(opt)"
                />
                <slot
                  name="option"
                  :opt="opt"
                  :selected="selectedSet.has(opt[optionValue])"
                  :toggle-option="() => handleSelect(opt)"
                >
                  <span class="km-select__option-label">{{ opt[optionLabel] ?? opt.label }}</span>
                </slot>
                <ComboboxItemIndicator v-if="!multiple" class="km-select__indicator">
                  <KmGlyph name="check" size="16px" tone="brand" />
                </ComboboxItemIndicator>
              </ComboboxItem>
            </ComboboxGroup>
          </ComboboxViewport>
        </ComboboxContent>
      </ComboboxPortal>
    </ComboboxRoot>

    <p v-if="finalError" class="km-select__error">{{ finalError }}</p>
  </span>
</template>

<style>
.km-select {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  inline-size: 100%;
}

/* When delegating to DsSelect we let its trigger fill the wrapper. */
.km-select__ds .ds-select__trigger {
  min-block-size: var(--km-select-min-height);
}

.km-select__trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  min-block-size: var(--km-select-min-height);
  padding: 0 var(--ds-space-md);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-field-radius);
  cursor: pointer;
  font-size: var(--ds-font-size-body);
  text-align: start;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-select__trigger:hover { border-color: var(--ds-color-control-hover-border); background: var(--ds-color-control-hover-bg); }
.km-select[data-state='open'] .km-select__trigger { border-color: var(--ds-color-primary); background: var(--ds-color-white); }
.km-select[data-state='error'] .km-select__trigger,
.km-select[data-state='error'] .km-select__ds .ds-select__trigger {
  border-color: var(--ds-color-error);
  background: var(--ds-color-error-bg);
}
.km-select[data-disabled='true'] .km-select__trigger { opacity: 0.6; pointer-events: none; }

.km-select__value {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* In chip-mode the value area must wrap (so chips flow onto multiple
 * lines as more items are selected) and grow vertically with the trigger.
 * `:has()` keeps the single-value trigger styling unchanged. */
.km-select__value:has(.km-select__chips) {
  white-space: normal;
  overflow: visible;
  padding-block: var(--ds-space-2xs);
}
.km-select__chips {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-2xs);
}
/* Compact chip dimensions tailored for the in-select tag look:
 *  - button-style border-radius (md, not the default pill) so the chips
 *    line up visually with the surrounding buttons / inputs;
 *  - a roomier inline padding than `dense` provides on its own so the
 *    label doesn't crowd the chip's edges or the × button. */
.km-select .km-select__chip {
  block-size: 24px;
  border-radius: var(--ds-radius-md);
  padding-inline: var(--ds-space-sm);
}
.km-select__placeholder { color: var(--ds-color-placeholder); }
.km-select__chevron {
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
  flex: none;
}
.km-select[data-state='open'] .km-select__chevron { transform: rotate(180deg); }
.km-select__append {
  display: inline-flex;
  align-items: center;
  flex: none;
}

.km-select__content {
  z-index: var(--ds-z-popover);
  min-inline-size: var(--reka-combobox-trigger-width);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  padding: var(--ds-space-2xs);
}
.km-select__viewport { max-block-size: 280px; overflow: auto; }

.km-select__search {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-xs) var(--ds-space-sm);
}
.km-select__search-input {
  flex: 1 1 auto;
  border: 0;
  outline: none;
  background: transparent;
  font: inherit;
  color: var(--ds-color-black);
}

.km-select__select-all { padding: var(--ds-space-xs) var(--ds-space-sm); }

.km-select__item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-xs) var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-sm);
  outline: none;
  cursor: pointer;
}
.km-select__item[data-highlighted] { background: var(--ds-color-light); }
.km-select__item[data-selected='true'] { background: var(--ds-color-primary-bg); }
.km-select__option-label {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.km-select__empty {
  padding: var(--ds-space-md);
  color: var(--ds-color-placeholder);
  font-size: var(--ds-font-size-label);
}

.km-select__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  margin: 0;
}
</style>
