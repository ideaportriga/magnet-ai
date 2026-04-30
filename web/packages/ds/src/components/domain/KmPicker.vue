<script setup lang="ts">
/**
 * `<km-picker>` — searchable two-column picker. Behaves like a select but
 * the popup carries a search input on top and renders each option as a
 * two-column row with a sub-label.
 *
 * Public surface preserved (most-used subset):
 *   modelValue, options, placeholder, loading, pickLoading, searchPlaceholder,
 *   firstColumn, secondColumn, searchFields, disabled.
 */

import { computed, ref, watch } from 'vue'
import { PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'
import KmGlyph from './KmGlyph.vue'
import KmInnerLoading from './KmInnerLoading.vue'
import KmInput from './KmInput.vue'
import KmLoader from './KmLoader.vue'
import KmSeparator from './KmSeparator.vue'

interface KmPickerColumn {
  title?: string
  /** Field name(s) to display. Array gets joined with a space. */
  display: string | string[]
  /** Optional sub-text below the main display row. */
  subValue?: string
}

interface KmPickerOption {
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    modelValue?: string
    options?: KmPickerOption[]
    placeholder?: string
    loading?: boolean
    pickLoading?: boolean
    disabled?: boolean
    searchPlaceholder?: string
    /** When provided, search runs across these fields (case-insensitive). */
    searchFields?: string[]
    firstColumn?: KmPickerColumn
    secondColumn?: KmPickerColumn
  }>(),
  {
    options: () => [],
    placeholder: '',
    loading: false,
    pickLoading: false,
    disabled: false,
    searchPlaceholder: 'Search',
    searchFields: () => [],
    firstColumn: () => ({ title: '', display: '' }),
    secondColumn: () => ({ title: '', display: '' }),
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)
const search = ref('')

watch(open, (next) => {
  if (!next) search.value = ''
})

function joinDisplay(option: KmPickerOption, display: string | string[]): string {
  if (Array.isArray(display)) {
    return display.map((field) => option[field]).filter(Boolean).join(' ')
  }
  return display
}

const filteredOptions = computed(() => {
  if (!search.value) return props.options
  const needle = search.value.toLowerCase()
  const fields = props.searchFields.length
    ? props.searchFields
    : Array.isArray(props.firstColumn.display)
      ? props.firstColumn.display
      : [props.firstColumn.display]
  return props.options.filter((opt) =>
    fields.some((field) => String(opt[field] ?? '').toLowerCase().includes(needle)),
  )
})

function setValue(option: KmPickerOption) {
  const value = joinDisplay(option, props.firstColumn.display)
  emit('update:modelValue', value)
  open.value = false
}
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        class="km-picker"
        type="button"
        :data-state="open ? 'open' : undefined"
        :data-disabled="disabled ? 'true' : undefined"
        data-test="km-picker"
        :disabled="disabled"
      >
        <span class="km-picker__value">
          <span v-if="modelValue">{{ modelValue }}</span>
          <span v-else class="km-picker__placeholder">{{ placeholder }}</span>
        </span>
        <KmGlyph
          name="chevron-down"
          size="20px"
          tone="seamless"
          class="km-picker__chevron"
          :style="{ transform: open ? 'rotate(180deg)' : '' }"
        />
      </button>
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent
        class="km-picker__menu"
        side="bottom"
        align="end"
        :side-offset="4"
      >
        <div class="km-picker__search">
          <KmInput
            v-model="search"
            :placeholder="searchPlaceholder"
            icon-before="search"
            autofocus
            clearable
            dense
          />
        </div>

        <KmSeparator />

        <div v-if="firstColumn?.title" class="km-picker__heading cluster" data-justify="between">
          <span class="km-picker__heading-cell">{{ firstColumn.title }}</span>
          <span class="km-picker__heading-cell km-picker__heading-cell--right">
            {{ secondColumn?.title }}
          </span>
        </div>

        <div class="km-picker__body">
          <div v-if="loading" class="km-picker__loading">
            <KmLoader size="32px" />
          </div>

          <ul v-else-if="filteredOptions.length" class="km-picker__list">
            <li
              v-for="(opt, idx) in filteredOptions"
              :key="idx"
              class="km-picker__option"
              data-test="km-picker-option"
              @click="setValue(opt)"
            >
              <div class="cluster" data-justify="between">
                <span class="km-picker__option-main">
                  {{ joinDisplay(opt, firstColumn.display) }}
                </span>
                <span
                  v-if="secondColumn?.display"
                  class="km-picker__option-secondary"
                >
                  {{ joinDisplay(opt, secondColumn.display) }}
                </span>
              </div>
              <span v-if="firstColumn.subValue" class="km-picker__option-sub">
                {{ opt[firstColumn.subValue] }}
              </span>
            </li>
          </ul>

          <p v-else class="km-picker__empty">No results</p>
        </div>

        <KmInnerLoading :showing="pickLoading" />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
.km-picker {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  padding: 0 var(--ds-space-sm) 0 var(--ds-space-md);
  min-block-size: var(--ds-field-height);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-field-radius);
  font-size: var(--ds-font-size-body);
  text-align: start;
  cursor: pointer;
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.km-picker:hover { border-color: var(--ds-color-control-hover-border); }
.km-picker[data-state='open'] { border-color: var(--ds-color-primary); background: var(--ds-color-white); }
.km-picker[data-disabled='true'] { opacity: 0.6; pointer-events: none; }

.km-picker__value { flex: 1 1 auto; min-inline-size: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.km-picker__placeholder { color: var(--ds-color-placeholder); }
.km-picker__chevron { transition: transform var(--ds-duration-fast) var(--ds-ease-out); flex: none; }

.km-picker__menu {
  position: relative;
  z-index: var(--ds-z-popover);
  inline-size: 340px;
  min-block-size: 418px;
  max-block-size: 480px;
  background: var(--ds-color-white);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  display: flex;
  flex-direction: column;
}

.km-picker__search { padding: var(--ds-space-md) var(--ds-space-md) var(--ds-space-sm); }

.km-picker__heading {
  padding: var(--ds-space-sm) var(--ds-space-md);
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
}
.km-picker__heading-cell--right { text-align: end; min-inline-size: 120px; }

.km-picker__body { flex: 1 1 auto; overflow: auto; }

.km-picker__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--ds-space-2xl) 0;
}

.km-picker__list { list-style: ""; margin: 0; padding: var(--ds-space-2xs); }

.km-picker__option {
  padding: var(--ds-space-xs) var(--ds-space-sm);
  border-block-end: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-picker__option:hover { background: var(--ds-color-light); }
.km-picker__option-main { font-size: var(--ds-font-size-body); flex: 1 1 auto; }
.km-picker__option-secondary {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  min-inline-size: 120px;
  text-align: end;
}
.km-picker__option-sub {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  display: block;
  margin-block-start: var(--ds-space-2xs);
}

.km-picker__empty {
  padding: var(--ds-space-md);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-placeholder);
  text-align: center;
}
</style>
