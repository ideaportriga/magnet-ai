<script setup lang="ts">
import { computed, toRefs, useAttrs } from 'vue'
import useValidation from '@shared/composables/useValidation'
import DsDropdownMenuContent from '../primitives/Menu/DsDropdownMenuContent.vue'
import DsDropdownMenuItem from '../primitives/Menu/DsDropdownMenuItem.vue'
import DsDropdownMenuRoot from '../primitives/Menu/DsDropdownMenuRoot.vue'
import DsDropdownMenuTrigger from '../primitives/Menu/DsDropdownMenuTrigger.vue'
import KmChip, { type KmChipTone } from './KmChip.vue'
import KmGlyph from './KmGlyph.vue'

export interface KmDropdownSelectOption {
  label?: string
  value?: unknown
  icon?: string
  disabled?: boolean
  badgeLabel?: string
  badgeTone?: KmChipTone
  badgeIcon?: string
  [key: string]: unknown
}

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    modelValue?: unknown
    options?: KmDropdownSelectOption[]
    placeholder?: string
    selectedIcon?: string
    showSelectedIcon?: boolean
    disabled?: boolean
    disable?: boolean
    rules?: unknown
    errorMessage?: string
    hideBottomSpace?: boolean
  }>(),
  {
    options: () => [],
    placeholder: '',
    selectedIcon: 'check',
    showSelectedIcon: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  select: [value: unknown, option: KmDropdownSelectOption]
}>()

const attrs = useAttrs()
const { modelValue, rules } = toRefs(props)
const { errorMessage: ruleError, validate, resetValidation } = useValidation(modelValue, rules)

const rootAttrs = computed(() => {
  const rest = { ...attrs }
  delete rest['data-test']
  delete rest.class
  delete rest.style
  return rest
})
const rootClass = computed(() => ['km-dropdown-select', attrs.class])
const rootStyle = computed(() => attrs.style)
const triggerDataTest = computed(() => String(attrs['data-test'] ?? 'km-dropdown-select-trigger'))
const isDisabled = computed(() => Boolean(props.disabled || props.disable))
const finalError = computed<string | undefined>(() => props.errorMessage || (ruleError.value as string) || undefined)

const modelOptionValue = computed(() => {
  if (props.modelValue && typeof props.modelValue === 'object') {
    return (props.modelValue as KmDropdownSelectOption).value
  }
  return props.modelValue
})

const selectedOption = computed(() => props.options.find((option) => option.value === modelOptionValue.value))
const triggerLabel = computed(() => {
  if (selectedOption.value?.label) return selectedOption.value.label
  if (typeof props.modelValue === 'string') return props.modelValue
  return props.placeholder
})

function isSelected(option: KmDropdownSelectOption) {
  return option.value === modelOptionValue.value
}

function selectOption(option: KmDropdownSelectOption) {
  if (isDisabled.value || option.disabled) return
  emit('update:modelValue', option.value)
  emit('select', option.value, option)
}

defineExpose({ validate, resetValidation })
</script>

<template>
  <span v-bind="rootAttrs" :class="rootClass" :style="rootStyle" :data-state="finalError ? 'error' : undefined" :data-disabled="isDisabled ? 'true' : undefined">
    <DsDropdownMenuRoot>
      <DsDropdownMenuTrigger as-child>
        <button type="button" class="km-dropdown-select__trigger" :data-test="triggerDataTest" :disabled="isDisabled" :aria-invalid="finalError ? true : undefined">
          <span class="km-dropdown-select__trigger-label">{{ triggerLabel }}</span>
          <KmGlyph name="chevron-down" size="16px" tone="current" />
        </button>
      </DsDropdownMenuTrigger>
      <DsDropdownMenuContent class="km-dropdown-select__menu" side="bottom" align="start" :side-offset="4" data-test="km-dropdown-select-menu">
        <DsDropdownMenuItem
          v-for="option in options"
          :key="String(option.value ?? option.label)"
          class="km-dropdown-select__option"
          :data-selected="isSelected(option) ? 'true' : undefined"
          :disabled="isDisabled || option.disabled"
          @select="selectOption(option)"
        >
          <KmGlyph v-if="showSelectedIcon && isSelected(option)" :name="selectedIcon" size="14px" tone="current" />
          <KmGlyph v-else-if="option.icon" :name="option.icon" size="14px" tone="current" />
          <span v-else class="km-dropdown-select__option-marker" aria-hidden="true" />
          <span class="km-dropdown-select__option-label">{{ option.label }}</span>
          <KmChip v-if="option.badgeLabel" :tone="option.badgeTone || 'brand'" dense size="20px" :icon="option.badgeIcon || ''" icon-size="12px" icon-margin-right="4px" :label="option.badgeLabel" />
        </DsDropdownMenuItem>
      </DsDropdownMenuContent>
    </DsDropdownMenuRoot>
    <span v-if="finalError && !hideBottomSpace" class="km-dropdown-select__error">{{ finalError }}</span>
  </span>
</template>

<style>
.km-dropdown-select {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
}

.km-dropdown-select__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-2xs);
  min-block-size: 30px;
  padding-block: var(--ds-space-2xs);
  padding-inline: var(--ds-space-sm);
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  color: var(--ds-color-black);
  border: 0;
  border-radius: var(--ds-radius-full);
  cursor: pointer;
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}

.km-dropdown-select.full-width .km-dropdown-select__trigger {
  inline-size: 100%;
}

.km-dropdown-select__trigger:hover {
  background: var(--ds-color-light);
}

.km-dropdown-select__trigger:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.km-dropdown-select[data-state='error'] .km-dropdown-select__trigger {
  outline: 2px solid var(--ds-color-error);
  outline-offset: 2px;
}

.km-dropdown-select[data-disabled='true'] .km-dropdown-select__trigger {
  cursor: not-allowed;
  opacity: 0.5;
}

.km-dropdown-select__trigger-label {
  max-inline-size: 14rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.km-dropdown-select__menu {
  min-inline-size: 14rem;
}

.km-dropdown-select__option {
  cursor: pointer;
}

.km-dropdown-select__option[data-selected='true'] {
  --km-glyph-color: currentColor;
  color: var(--ds-color-primary);
  font-weight: var(--ds-font-weight-medium);
}

.km-dropdown-select__option[data-selected='true']:not([data-highlighted]) {
  background: var(--ds-color-primary-bg);
}

.km-dropdown-select__option-marker {
  flex: none;
  inline-size: 14px;
  block-size: 14px;
}

.km-dropdown-select__option-label {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.km-dropdown-select__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
}
</style>
