<script setup lang="ts">
/**
 * Select — single-value dropdown. For type-ahead / search use a Combobox
 * primitive (added later).
 *
 *   <DsSelect v-model="lang" :options="langs" placeholder="Choose…" />
 */

import {
  SelectContent,
  SelectGroup,
  SelectIcon,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport,
} from 'reka-ui'
import { computed } from 'vue'

export interface DsSelectOption {
  value: string
  label: string
  disabled?: boolean
}

const EMPTY_SELECT_ITEM_VALUE_PREFIX = '__ds-select-empty-value__'

interface InternalDsSelectOption extends DsSelectOption {
  key: string
  rekaValue: string
}

const props = withDefaults(
  defineProps<{
    modelValue?: string
    options: DsSelectOption[]
    placeholder?: string
    disabled?: boolean
    size?: 'sm' | 'md'
  }>(),
  {
    size: 'md',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const internalModelValue = computed(() => (props.modelValue === '' ? undefined : props.modelValue))

const internalOptions = computed<InternalDsSelectOption[]>(() =>
  props.options.map((opt, index) => {
    const rekaValue = opt.value === '' ? `${EMPTY_SELECT_ITEM_VALUE_PREFIX}${index}` : opt.value
    return {
      ...opt,
      key: `${rekaValue}-${index}`,
      rekaValue,
    }
  }),
)

function handleModelValueUpdate(next: unknown) {
  const value = String(next ?? '')
  const matchedOption = internalOptions.value.find((opt) => opt.rekaValue === value)
  emit('update:modelValue', matchedOption?.value ?? value)
}
</script>

<template>
  <SelectRoot
    :model-value="internalModelValue"
    :disabled="disabled"
    @update:model-value="handleModelValueUpdate"
  >
    <SelectTrigger class="ds-select__trigger" :data-size="size" data-test="ds-select">
      <SelectValue :placeholder="placeholder" />
      <SelectIcon class="ds-select__chevron">
        <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
          <path d="M2 4 L6 8 L10 4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </SelectIcon>
    </SelectTrigger>

    <SelectPortal>
      <SelectContent class="ds-select__content" :side-offset="4" position="popper">
        <SelectViewport class="ds-select__viewport">
          <SelectGroup>
            <SelectItem
              v-for="opt in internalOptions"
              :key="opt.key"
              :value="opt.rekaValue"
              :disabled="opt.disabled"
              class="ds-select__item"
              data-test="ds-select-item"
            >
              <SelectItemIndicator class="ds-select__indicator">
                <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                  <path d="M2 6 L5 9 L10 3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </SelectItemIndicator>
              <SelectItemText>{{ opt.label }}</SelectItemText>
            </SelectItem>
          </SelectGroup>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>

<style>
.ds-select__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  block-size: var(--ds-field-height);
  padding: 0 var(--ds-space-md);
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-black);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-field-radius);
  cursor: pointer;
}
.ds-select__trigger[data-size='sm'] { block-size: var(--ds-btn-height-sm); padding-inline: var(--ds-space-sm); font-size: var(--ds-font-size-label); }
.ds-select__trigger:hover:not([data-disabled], [data-state='open']) { border-color: var(--ds-color-control-hover-border); }
.ds-select__trigger:focus-visible {
  outline: none;
  border-color: var(--ds-color-focus-border);
  box-shadow: 0 0 0 3px var(--ds-color-focus-ring);
}
.ds-select__trigger[aria-invalid='true'] { border-color: var(--ds-color-invalid-border); }
.ds-select__trigger[aria-invalid='true']:focus-visible {
  border-color: var(--ds-color-invalid-border);
  box-shadow: 0 0 0 3px var(--ds-color-invalid-ring);
}
.ds-select__trigger[data-disabled] {
  background: var(--ds-color-disabled-bg);
  color: var(--ds-color-disabled-fg);
  border-color: var(--ds-color-disabled-border);
  cursor: not-allowed;
}
.ds-select__trigger[data-placeholder] { color: var(--ds-color-placeholder-fg); }
.ds-select__chevron { color: var(--ds-color-icon); }

.ds-select__content {
  z-index: var(--ds-z-popover);
  min-inline-size: var(--reka-select-trigger-width);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  overflow: hidden;
  animation: ds-menu-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-select__content[data-state='closed'] {
  animation: ds-menu-out var(--ds-duration-instant) var(--ds-ease-in);
}
.ds-select__viewport { padding: var(--ds-space-2xs); }

.ds-select__item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-xs) var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  border-radius: var(--ds-radius-sm);
  color: var(--ds-color-black);
  outline: none;
  user-select: none;
  cursor: pointer;
}
.ds-select__item[data-highlighted] { background: var(--ds-color-light); }
.ds-select__item[data-disabled] { color: var(--ds-color-disabled-fg); pointer-events: none; }
.ds-select__indicator {
  inline-size: 14px;
  block-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ds-color-primary);
}
</style>
