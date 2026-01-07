<template>
  <q-select
    ref="selectRef"
    :model-value="modelValue"
    :class="selectClasses"
    outlined
    dense
    emit-value
    map-options
    :placeholder="placeholder"
    :option-value="optionValue"
    :option-label="optionLabel"
    :options="filteredOptions"
    :disable="disable"
    :loading="loading"
    :popup-content-class="popupClasses"
    @update:model-value="$emit('update:modelValue', $event)"
    @popup-show="onPopupShow"
    @popup-hide="onPopupHide"
  >
    <template #append>
      <span v-if="modelValue && clearable" class="styled-select__clear" @click.stop="$emit('update:modelValue', '')">CLEAR</span>
    </template>
    <template v-if="searchable" #before-options>
      <q-item class="styled-select__search-item">
        <q-item-section>
          <q-input
            ref="searchInputRef"
            v-model="searchQuery"
            dense
            borderless
            placeholder="Search..."
            class="styled-select__search-input"
            @keydown.stop
          >
            <template #prepend>
              <q-icon name="search" size="18px" color="grey-6" />
            </template>
            <template v-if="searchQuery" #append>
              <q-icon name="close" size="16px" color="grey-5" class="cursor-pointer" @click.stop="searchQuery = ''" />
            </template>
          </q-input>
        </q-item-section>
      </q-item>
      <q-separator />
    </template>
    <template #option="{ itemProps, opt, selected }">
      <!-- No results sentinel - render as non-clickable message -->
      <q-item v-if="opt.__noResults" disable class="styled-select__option--empty styled-select__no-results">
        <q-item-section class="text-center">
          <q-item-label class="text-grey-5">No matching options</q-item-label>
        </q-item-section>
      </q-item>
      <!-- Regular option -->
      <q-item v-else v-bind="itemProps" :class="optionClasses(selected)">
        <q-item-section>
          <div class="styled-select__option-row">
            <span class="styled-select__option-name">{{ opt[optionLabel] || opt.label || opt }}</span>
            <span v-if="getOptionMeta(opt)" class="styled-select__option-meta">{{ getOptionMeta(opt) }}</span>
          </div>
        </q-item-section>
        <q-item-section side class="styled-select__side">
          <div
            :class="[
              'styled-select__check-wrapper',
              { 'styled-select__check-wrapper--dense': dense, 'styled-select__check-wrapper--visible': selected },
            ]"
          >
            <q-icon name="check" color="white" :size="dense ? '10px' : '12px'" />
          </div>
        </q-item-section>
      </q-item>
    </template>
    <template #no-option>
      <q-item :class="['styled-select__option--empty', { 'styled-select__option--empty--dense': dense }]">
        <q-item-section class="text-center">
          <q-item-label class="text-grey-5">{{ noOptionsLabel }}</q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import type { QInput, QSelect } from 'quasar'
import { computed, nextTick, ref } from 'vue'

interface Props {
  modelValue: string | undefined
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
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Select option',
  noOptionsLabel: 'No options available',
  optionValue: 'value',
  optionLabel: 'label',
  showError: false,
  clearable: false,
  disable: false,
  loading: false,
  optionMeta: undefined,
  dense: false,
  searchable: false,
})

defineEmits<{
  'update:modelValue': [value: string | undefined]
}>()

const selectRef = ref<QSelect | null>(null)
const searchInputRef = ref<QInput | null>(null)
const searchQuery = ref('')

// Sentinel object to show "no results" message while keeping #before-options visible
const NO_RESULTS_SENTINEL = { __noResults: true }

const filteredOptions = computed(() => {
  if (!props.searchable || !searchQuery.value) {
    return props.options
  }
  const query = searchQuery.value.toLowerCase()
  const filtered = props.options.filter((opt) => {
    const label = opt[props.optionLabel] || opt.label || String(opt)
    return label.toLowerCase().includes(query)
  })
  // Return sentinel if no matches, so #before-options stays rendered and search input keeps focus
  if (filtered.length === 0) {
    return [NO_RESULTS_SENTINEL]
  }
  return filtered
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

const selectClasses = computed(() => [
  'styled-select',
  {
    'styled-select--error': props.showError && !props.modelValue,
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

<style scoped>
.styled-select-dense {
  height: 36px !important;
}

.styled-select :deep(.q-field__control) {
  border-radius: 4px;
  background: white;
}

.styled-select--dense :deep(.q-field__control) {
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
}

.styled-select--dense :deep(.q-field__native) {
  min-height: 36px !important;
}

.styled-select--dense :deep(.q-field__marginal) {
  height: 36px !important;
}

.styled-select :deep(.q-field__control:before) {
  border-color: var(--q-control-border) !important;
  border-radius: 4px;
}

.styled-select :deep(.q-field__control:hover:before) {
  border-color: #c4b5d4;
}

.styled-select :deep(.q-field--focused .q-field__control) {
  background: #fff;
}

.styled-select :deep(.q-field--focused .q-field__control:after) {
  border-color: #6840c2;
  border-width: 2px;
  border-radius: 6px;
}

.styled-select :deep(.q-field__native) {
  color: #2d2438;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.styled-select :deep(.q-field__append) {
  padding-right: 4px;
}

.styled-select--error :deep(.q-field__control:before) {
  border-color: #e53935;
}

.styled-select--error :deep(.q-field__control:hover:before) {
  border-color: #c62828;
}

.styled-select__clear {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #8b7a9e;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.12s ease;
  user-select: none;
}

.styled-select__clear:hover {
  color: #6840c2;
  background-color: #f3eef8;
}

.styled-select__clear:active {
  background-color: #e8dff2;
}
</style>

<style>
/* Dropdown popup container */
.styled-select-popup {
  border-radius: 8px;
  box-shadow:
    0 4px 16px rgba(104, 64, 194, 0.08),
    0 12px 32px rgba(45, 36, 56, 0.12);
  padding: 5px;
  background: #ffffff;
  border: 1px solid #ebe6f2;
  overflow: hidden;
}

.styled-select-popup .q-virtual-scroll__content {
  padding: 0;
}

/* Dense popup - tighter, lighter */
.styled-select-popup--dense {
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 2px 12px rgba(45, 36, 56, 0.1);
  border: 1px solid #e8e4ed;
}

/* Option item base */
.styled-select__option {
  position: relative;
  border-radius: 6px;
  margin: 2px 0;
  min-height: 40px;
  padding: 10px 12px;
  transition: all 0.12s ease;
  cursor: pointer;
}

/* Dense option - compact */
.styled-select__option--dense {
  min-height: 30px;
  padding: 6px 10px;
  margin: 1px 0;
  border-radius: 4px;
}

/* Hover state */
.styled-select__option:hover {
  background-color: #f8f5fb;
}

/* Active/pressed state */
.styled-select__option:active {
  background-color: #f0eaf6;
  transform: scale(0.995);
}

/* Selected state - no background, icon only */
.styled-select__option--selected {
  background: transparent;
}

.styled-select__option--selected:hover {
  background-color: #f8f5fb;
}

/* Option row layout */
.styled-select__option-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  overflow: hidden;
}

.styled-select__option--dense .styled-select__option-row {
  gap: 8px;
}

/* Option name text */
.styled-select__option-name {
  font-size: 13px;
  font-weight: 500;
  color: #3d3252;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  letter-spacing: -0.01em;
  transition: color 0.12s ease;
}

.styled-select__option--dense .styled-select__option-name {
  font-size: 12px;
  font-weight: 450;
}

.styled-select__option:hover .styled-select__option-name {
  color: #2d2438;
}

.styled-select__option--selected .styled-select__option-name {
  color: #6840c2;
  font-weight: 550;
}

/* Option meta badge */
.styled-select__option-meta {
  font-size: 10px;
  font-weight: 600;
  color: #8b7a9e;
  background-color: #f5f2f8;
  padding: 3px 7px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  letter-spacing: 0.01em;
  flex-shrink: 0;
  text-transform: uppercase;
  border: 1px solid #e8e2ef;
  transition: all 0.12s ease;
}

.styled-select__option--dense .styled-select__option-meta {
  font-size: 9px;
  padding: 2px 5px;
  border-radius: 3px;
}

.styled-select__option:hover .styled-select__option-meta {
  background-color: #efe9f5;
  border-color: #ddd4e8;
  color: #6840c2;
}

.styled-select__option--selected .styled-select__option-meta {
  color: #6840c2;
  background-color: #f0eaf8;
  border-color: #d8cce8;
}

/* Side section with checkmark */
.styled-select__side {
  padding-left: 6px !important;
  min-width: 26px;
}

.styled-select__option--dense .styled-select__side {
  padding-left: 4px !important;
  min-width: 18px;
}

/* Checkmark wrapper */
.styled-select__check-wrapper {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--q-primary);
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
  width: 16px;
  height: 16px;
}

/* Empty state */
.styled-select__option--empty {
  padding: 24px 16px;
}

.styled-select__option--empty--dense {
  padding: 14px 12px;
}

.styled-select__option--empty .q-item-label {
  font-size: 12px;
  font-weight: 500;
  color: #a99bba;
  letter-spacing: 0.01em;
}

.styled-select__option--empty--dense .q-item-label {
  font-size: 11px;
}

.styled-select__option--dense {
  min-height: 38px !important;
}

/* Search input styling */
.styled-select__search-item {
  padding: 8px 8px 4px 8px !important;
  min-height: auto !important;
}

.styled-select__search-input {
  font-size: 13px;
}

.styled-select__search-input .q-field__control {
  height: 36px !important;
  min-height: 36px !important;
}

.styled-select__search-input .q-field__control:before {
  border-color: transparent !important;
}

.styled-select__search-input .q-field__control:hover:before {
  border-color: #e8e4ed !important;
}

.styled-select__search-input.q-field--focused .q-field__control {
  background: #fff;
}

.styled-select__search-input.q-field--focused .q-field__control:after {
  border-color: #6840c2;
  border-width: 2px;
  border-radius: 6px;
}

.styled-select__search-input .q-field__native {
  padding-left: 4px;
  color: #2d2438;
}

.styled-select__search-input .q-field__native::placeholder {
  color: #a99bba;
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
