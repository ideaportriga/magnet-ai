<template>
  <km-select
    ref="selectRef"
    :model-value="computedModelValue"
    :display-value="selectDisplayValue"
    :class="selectClasses"
    outlined
    dense
    emit-value
    map-options
    :multiple="multiple"
    :placeholder="placeholder"
    :option-value="optionValue"
    :option-label="optionLabel"
    :options="filteredOptions"
    :disable="disable"
    :loading="loading"
    :popup-content-class="popupClasses"
    @update:model-value="handleModelValueUpdate"
    @popup-show="onPopupShow"
    @popup-hide="onPopupHide"
  >
    <template #append>
      <span v-if="hasValue && clearable" class="styled-select__clear" @click.stop="handleClear">{{ m.common_clear() }}</span>
    </template>
    <template v-if="searchable" #before-options>
      <div class="km-item styled-select__search-item">
        <div class="km-item-section">
          <km-input
            ref="searchInputRef"
            v-model="searchQuery"
            dense
            borderless
            :placeholder="m.placeholder_search()"
            class="styled-select__search-input"
            @keydown.stop
          >
            <template #prepend>
              <km-glyph name="search" size="18px" tone="muted" />
            </template>
            <template v-if="searchQuery" #append>
              <km-glyph name="close" size="16px" tone="muted" class="cursor-pointer" @click.stop="searchQuery = ''" />
            </template>
          </km-input>
        </div>
      </div>
      <km-separator />
    </template>
    <template #option="{ itemProps, opt, selected }">
      <!-- No results sentinel - render as non-clickable message -->
      <div v-if="opt.__noResults" class="km-item styled-select__option--empty styled-select__no-results">
        <div class="km-item-section text-center">
          <span class="km-item-label text-grey-5">{{ m.common_noMatchingOptions() }}</span>
        </div>
      </div>
      <!-- Select all option -->
      <div v-else-if="opt.__selectAll" class="km-item" v-bind="itemProps" :class="optionClasses(selected)">
        <div class="km-item-section">
          <div class="styled-select__option-row">
            <span class="styled-select__option-name">{{ opt[optionLabel] }}</span>
          </div>
        </div>
        <div class="km-item-section styled-select__side" side>
          <div
            :class="[
              'styled-select__check-wrapper',
              { 'styled-select__check-wrapper--dense': dense, 'styled-select__check-wrapper--visible': selected },
            ]"
          >
            <km-glyph name="check" tone="inverse" :size="dense ? '10px' : '12px'" />
          </div>
        </div>
      </div>
      <!-- Regular option -->
      <div v-else class="km-item" v-bind="itemProps" :class="optionClasses(selected)">
        <div class="km-item-section">
          <div class="styled-select__option-row">
            <span class="styled-select__option-name">{{ opt[optionLabel] || opt.label || opt }}</span>
            <span v-if="getOptionMeta(opt)" class="styled-select__option-meta">{{ getOptionMeta(opt) }}</span>
          </div>
        </div>
        <div class="km-item-section styled-select__side" side>
          <div
            :class="[
              'styled-select__check-wrapper',
              { 'styled-select__check-wrapper--dense': dense, 'styled-select__check-wrapper--visible': selected },
            ]"
          >
            <km-glyph name="check" tone="inverse" :size="dense ? '10px' : '12px'" />
          </div>
        </div>
      </div>
    </template>
    <template #no-option>
      <div class="km-item" :class="['styled-select__option--empty', { 'styled-select__option--empty--dense': dense }]">
        <div class="km-item-section text-center">
          <span class="km-item-label text-grey-5">{{ noOptionsLabel }}</span>
        </div>
      </div>
    </template>
  </km-select>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import { computed, nextTick, ref, type ComponentPublicInstance } from 'vue'

interface Props {
  modelValue: string | string[] | undefined
  options: any[]
  placeholder?: string
  noOptionsLabel?: string
  optionValue?: string
  optionLabel?: string
  showError?: boolean
  clearable?: boolean
  disable?: boolean
  loading?: boolean
  optionMeta?: string | ((opt: any) => string | undefined)
  dense?: boolean
  searchable?: boolean
  multiple?: boolean
  showAllOption?: boolean
  allOptionLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: () => m.placeholder_selectOption(),
  noOptionsLabel: () => m.common_noOptionsAvailable(),
  optionValue: 'value',
  optionLabel: 'label',
  showError: false,
  clearable: false,
  disable: false,
  loading: false,
  optionMeta: undefined,
  dense: false,
  searchable: false,
  multiple: false,
  showAllOption: false,
  allOptionLabel: () => m.common_selectAll(),
})

const $emit = defineEmits<{
  'update:modelValue': [value: string | string[] | undefined]
}>()

type FocusableComponent = ComponentPublicInstance & { focus: () => void }

const selectRef = ref<ComponentPublicInstance | null>(null)
const searchInputRef = ref<FocusableComponent | null>(null)
const searchQuery = ref('')

// Sentinel object to show "no results" message while keeping #before-options visible
const NO_RESULTS_SENTINEL = { __noResults: true }

// Sentinel value for "select all" option
const SELECT_ALL_VALUE = '__SELECT_ALL__'

// Get all regular option values (excluding select all sentinel)
const allOptionValues = computed(() => {
  return props.options.map((opt) => opt?.[props.optionValue] ?? opt?.value ?? opt)
})

// Sentinel object for "select all" option (computed to be reactive)
const SELECT_ALL_OPTION = computed(() => ({
  __selectAll: true,
  [props.optionValue]: SELECT_ALL_VALUE,
  [props.optionLabel]: props.allOptionLabel,
}))

// Check if all regular options are selected
const areAllOptionsSelected = computed(() => {
  if (!props.multiple || !props.showAllOption) return false
  if (!Array.isArray(props.modelValue)) return false

  const selectedValues = props.modelValue.filter((v) => v !== SELECT_ALL_VALUE)
  const allValues = allOptionValues.value

  if (allValues.length === 0) return false

  // Check if all option values are in the selected values
  return allValues.every((val) => selectedValues.includes(val))
})

// Computed modelValue that includes SELECT_ALL_VALUE when all options are selected
const computedModelValue = computed(() => {
  if (!props.multiple || !props.showAllOption) {
    return props.modelValue
  }

  if (!Array.isArray(props.modelValue)) {
    return areAllOptionsSelected.value ? [SELECT_ALL_VALUE, ...allOptionValues.value] : props.modelValue
  }

  // If all options are selected, include SELECT_ALL_VALUE
  if (areAllOptionsSelected.value && !props.modelValue.includes(SELECT_ALL_VALUE)) {
    return [SELECT_ALL_VALUE, ...props.modelValue]
  }

  // Remove SELECT_ALL_VALUE if not all options are selected
  return props.modelValue.filter((v) => v !== SELECT_ALL_VALUE)
})

const selectDisplayValue = computed(() => {
  if (props.multiple && props.showAllOption && areAllOptionsSelected.value) {
    return props.allOptionLabel
  }
  return undefined
})

const filteredOptions = computed(() => {
  let options = props.options

  // Apply search filter if enabled
  if (props.searchable && searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    const filtered = options.filter((opt) => {
      const label = opt[props.optionLabel] || opt.label || String(opt)
      return label.toLowerCase().includes(query)
    })

    // Return sentinel if no matches
    if (filtered.length === 0) {
      return [NO_RESULTS_SENTINEL]
    }
    options = filtered
  }

  // Add "select all" option at the beginning if enabled and in multiple mode
  if (props.showAllOption && props.multiple && !searchQuery.value) {
    // Only show select all if we have regular options (not just the no results sentinel)
    if (options.length > 0 && !options.some((opt) => opt.__noResults)) {
      return [SELECT_ALL_OPTION.value, ...options]
    }
  }

  return options
})

const onPopupShow = () => {
  if (props.searchable) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
}

const onPopupHide = () => {
  searchQuery.value = ''
}

const getOptionMeta = (opt: any): string | undefined => {
  if (!props.optionMeta) return undefined
  if (typeof props.optionMeta === 'function') {
    return props.optionMeta(opt)
  }
  return opt[props.optionMeta]
}

const hasValue = computed(() => {
  if (props.multiple) {
    return Array.isArray(props.modelValue) && props.modelValue.length > 0
  }
  return props.modelValue !== undefined && props.modelValue !== ''
})

const handleClear = () => {
  if (props.multiple) {
    $emit('update:modelValue', [])
  } else {
    $emit('update:modelValue', '')
  }
}

const handleModelValueUpdate = (value: string | string[] | undefined) => {
  if (!props.multiple || !props.showAllOption) {
    $emit('update:modelValue', value)
    return
  }

  if (!Array.isArray(value)) {
    $emit('update:modelValue', value)
    return
  }

  const prev = computedModelValue.value
  const prevHasSelectAll = Array.isArray(prev) && prev.includes(SELECT_ALL_VALUE)
  const nextHasSelectAll = value.includes(SELECT_ALL_VALUE)
  const regularValues = value.filter((v) => v !== SELECT_ALL_VALUE)

  // If SELECT_ALL_VALUE got added, user clicked "select all" -> select everything
  if (!prevHasSelectAll && nextHasSelectAll) {
    $emit('update:modelValue', allOptionValues.value)
    return
  }

  // If SELECT_ALL_VALUE got removed, user clicked "select all" again -> clear everything
  if (prevHasSelectAll && !nextHasSelectAll) {
    $emit('update:modelValue', [])
    return
  }

  // Regular toggle (also covers the case: select-all still checked but a regular option was toggled)
  // -> drop SELECT_ALL_VALUE and keep only regular values
  $emit('update:modelValue', regularValues)
}

const selectClasses = computed(() => [
  'styled-select',
  {
    'styled-select--error': props.showError && !hasValue.value,
    'styled-select--dense': props.dense,
  },
])

const popupClasses = computed(() => (props.dense ? 'styled-select-popup styled-select-popup--dense' : 'styled-select-popup'))

const optionClasses = (selected: boolean) => [
  'styled-select__option',
  {
    'styled-select__option--selected': selected,
    'styled-select__option--dense': props.dense,
  },
]
</script>

<style>
.styled-select-dense {
  block-size: 36px !important;
}

.styled-select .km-select__trigger,
.styled-select .ds-select__trigger {
  border-radius: var(--ds-radius-sm);
  background: var(--ds-color-white);
  border-color: var(--ds-color-control-border);
}

.styled-select--dense .km-select__trigger,
.styled-select--dense .ds-select__trigger {
  block-size: 36px !important;
  min-block-size: 36px !important;
  max-block-size: 36px !important;
}

.styled-select--dense .km-select__value {
  min-block-size: 36px !important;
}

.styled-select--dense .km-select__chevron,
.styled-select--dense .km-select__append {
  block-size: 36px !important;
}

.styled-select .km-select__trigger:hover,
.styled-select .ds-select__trigger:hover {
  border-color: var(--ds-color-primary-light);
}

.styled-select[data-state='open'] .km-select__trigger,
.styled-select .ds-select__trigger[data-state='open'] {
  background: var(--ds-color-white);
  border-color: var(--ds-color-primary);
  border-width: 2px;
  border-radius: var(--ds-radius-md);
}

.styled-select .km-select__value,
.styled-select .ds-select__trigger {
  color: var(--ds-color-black);
  font-weight: 500;
  letter-spacing: 0;
}

.styled-select .km-select__append {
  padding-inline-end: 4px;
}

.styled-select--error .km-select__trigger,
.styled-select--error .ds-select__trigger {
  border-color: var(--ds-color-error);
}

.styled-select--error .km-select__trigger:hover,
.styled-select--error .ds-select__trigger:hover {
  border-color: var(--ds-color-error-text);
}

.styled-select__clear {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--ds-color-icon);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--ds-radius-sm);
  transition: var(--ds-transition-colors);
  user-select: none;
}

.styled-select__clear:hover {
  color: var(--ds-color-primary);
  background-color: var(--ds-color-primary-bg);
}

.styled-select__clear:active {
  background-color: var(--ds-color-primary-transparent);
}
</style>

<style>
/* Dropdown popup container */
.styled-select-popup {
  border-radius: var(--ds-radius-lg);
  box-shadow:
    0 4px 16px var(--ds-color-primary-transparent),
    0 12px 32px rgba(0, 0, 0, 0.12);
  padding: 5px;
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  overflow: hidden;
}

.styled-select-popup .km-select__viewport,
.styled-select-popup .ds-select__viewport {
  padding: 0;
}

/* Dense popup - tighter, lighter */
.styled-select-popup--dense {
  border-radius: var(--ds-radius-md);
  padding: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--ds-color-border);
}

/* Option item base */
.styled-select__option {
  position: relative;
  border-radius: var(--ds-radius-md);
  margin: 2px 0;
  min-block-size: 40px;
  padding: 10px 12px;
  transition: var(--ds-transition-colors), var(--ds-transition-transform);
  cursor: pointer;
}

/* Dense option - compact */
.styled-select__option--dense {
  min-block-size: 38px !important;
  padding: 6px 10px;
  margin: 1px 0;
  border-radius: var(--ds-radius-sm);
}

/* Hover state */
.styled-select__option:hover {
  background-color: var(--ds-color-primary-bg);
}

/* Active/pressed state */
.styled-select__option:active {
  background-color: var(--ds-color-primary-transparent);
  transform: scale(0.995);
}

/* Selected state - no background, icon only */
.styled-select__option--selected {
  background: transparent;
}

.styled-select__option--selected:hover {
  background-color: var(--ds-color-primary-bg);
}

/* Option row layout */
.styled-select__option-row {
  display: flex;
  align-items: center;
  gap: 10px;
  inline-size: 100%;
  overflow: hidden;
}

.styled-select__option--dense .styled-select__option-row {
  gap: 8px;
}

/* Option name text */
.styled-select__option-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--ds-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-inline-size: 0;
  letter-spacing: 0;
  transition: color 0.12s ease;
}

.styled-select__option--dense .styled-select__option-name {
  font-size: 12px;
  font-weight: 450;
}

.styled-select__option:hover .styled-select__option-name {
  color: var(--ds-color-black);
}

.styled-select__option--selected .styled-select__option-name {
  color: var(--ds-color-primary);
  font-weight: 550;
}

/* Option meta badge */
.styled-select__option-meta {
  font-size: 10px;
  font-weight: 600;
  color: var(--ds-color-icon);
  background-color: var(--ds-color-primary-bg);
  padding: 3px 7px;
  border-radius: var(--ds-radius-sm);
  font-family: var(--ds-font-mono);
  letter-spacing: 0.01em;
  flex-shrink: 0;
  text-transform: uppercase;
  border: 1px solid var(--ds-color-border);
  transition: var(--ds-transition-colors);
}

.styled-select__option--dense .styled-select__option-meta {
  font-size: 9px;
  padding: 2px 5px;
  border-radius: var(--ds-radius-xs);
}

.styled-select__option:hover .styled-select__option-meta {
  background-color: var(--ds-color-primary-transparent);
  border-color: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
}

.styled-select__option--selected .styled-select__option-meta {
  color: var(--ds-color-primary);
  background-color: var(--ds-color-primary-bg);
  border-color: var(--ds-color-primary-light);
}

/* Side section with checkmark */
.styled-select__side {
  padding-inline-start: 6px !important;
  min-inline-size: 26px;
}

.styled-select__option--dense .styled-select__side {
  padding-inline-start: 4px !important;
  min-inline-size: 18px;
}

/* Checkmark wrapper */
.styled-select__check-wrapper {
  inline-size: 20px;
  block-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--ds-radius-full);
  background-color: var(--ds-color-primary);
  opacity: 0;
  transform: scale(0.5);
  transition:
    opacity 0.15s ease,
    transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.styled-select__check-wrapper--visible {
  opacity: 1;
  transform: scale(1);
}

.styled-select__check-wrapper--dense {
  inline-size: 16px;
  block-size: 16px;
}

/* Empty state */
.styled-select__option--empty {
  padding: 24px 16px;
}

.styled-select__option--empty--dense {
  padding: 14px 12px;
}

.styled-select__option--empty .km-item-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--ds-color-icon);
  letter-spacing: 0.01em;
}

.styled-select__option--empty--dense .km-item-label {
  font-size: 11px;
}

/* Search input styling */
.styled-select__search-item {
  padding: 8px 8px 4px !important;
  min-block-size: auto !important;
}

.styled-select__search-input {
  font-size: 13px;
}

.styled-select__search-input .km-input__control,
.styled-select__search-input .ds-input {
  block-size: 36px !important;
  min-block-size: 36px !important;
}

.styled-select__search-input .ds-input:hover {
  border-color: var(--ds-color-border) !important;
}

.styled-select__search-input[data-state='focused'] .ds-input {
  background: var(--ds-color-white);
  border-color: var(--ds-color-primary);
  border-width: 2px;
  border-radius: var(--ds-radius-md);
}

.styled-select__search-input .ds-input {
  padding-inline-start: 4px;
  color: var(--ds-color-black);
  border-color: transparent !important;
}

.styled-select__search-input .ds-input::placeholder {
  color: var(--ds-color-icon);
}

/* No results state (when search yields no matches) */
.styled-select__no-results {
  cursor: default;
  padding: 16px;
}

.styled-select__no-results:hover {
  background: transparent;
}
</style>
